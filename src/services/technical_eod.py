"""Bounded one-stock EOD adapter using the existing reader and D1/D4/D5 seams."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.analytics.market import market_snapshot, technical_history
from src.evaluation.benchmark.inputs import ZONE, eod, visible_bar
from src.evaluation.context import build_context
from src.evaluation.models import HistoricalObservation
from src.corporate_actions.models import CorporateActionContext
from src.materiality import evaluate_d4_market_events, build_technical_daily_packet
from src.materiality.delivery import TechnicalDailySignalPacket
from src.models import Security
from src.providers.base import ProviderError
from src.schemas.data import MarketBar, MarketSnapshot
from src.schemas.stocks import SymbolRequest
from .data import history
from .session_evidence import (CalendarEvidence, EODCompletionEvidence,
    completion_matches_bar, resolve_calendar)

MAX_HISTORY_DAYS = 730  # Existing SSI reader limit.
MAX_SESSION_RECORDS = 512


class EODModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid', allow_inf_nan=False)


class EODHistoryRead(EODModel):
    """Receipt sidecar over existing normalized HistoricalObservation contracts.

    observed_at is operational knowledge time, not an invented vendor revision or
    historical publication time. Reader cache fetch time may remain unavailable.
    """
    observations: tuple[HistoricalObservation, ...]
    observed_at: datetime
    source: str = 'SSI:FastConnect'
    source_version: str
    fetched_at: datetime | None = None
    adjustment_semantics: str = 'adjusted'
    price_unit: str = 'VND'
    volume_unit: str = 'shares'
    observation_mode: Literal['current_reconstruction', 'preserved_operational_snapshot'] = 'current_reconstruction'
    noncomparable_price_sessions: tuple[date, ...] = ()
    noncomparable_volume_sessions: tuple[date, ...] = ()
    is_fixture: bool = False
    completion_evidence: tuple[EODCompletionEvidence, ...] = Field(default=(), max_length=MAX_SESSION_RECORDS)


class VerifiedSessionCalendar(EODModel):
    """Caller-supplied verified venue sessions; NEVER inferred from returned bars."""
    venue: str
    sessions: tuple[date, ...]
    coverage_start: date
    coverage_end: date
    source_ref: str = Field(min_length=1)
    version: str = Field(min_length=1)
    observed_at: datetime


class TechnicalEODDiagnostic(EODModel):
    status: Literal['INVALID_REQUEST', 'INCOMPLETE_EVIDENCE', 'SOURCE_UNAVAILABLE', 'INFRASTRUCTURE_FAILURE']
    ticker: str | None
    trading_session: str | None
    evaluation_as_of: datetime | None
    reason_codes: tuple[str, ...]
    source_summary: dict[str, Any] = Field(default_factory=dict)
    available_observations: tuple[HistoricalObservation, ...] = ()
    consumer_version: str = 'technical-eod-consumer-v1'


def _aware(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError('An explicit aware timestamp is required')
    return value.astimezone(timezone.utc)


def _observation_time():
    # Actual read receipt; intentionally never the caller's historical cutoff.
    return datetime.now(timezone.utc)


def read_eod_history(ticker, provider, start, end) -> EODHistoryRead:
    """Reuse the normalized/cache-backed reader; no transport or persistence here."""
    if type(start) is not date or type(end) is not date or not 0 <= (end-start).days <= MAX_HISTORY_DAYS:
        raise ValueError('EOD acquisition requires an ordered bounded date range')
    if provider.source != 'SSI:FastConnect':
        raise ProviderError('Technical EOD requires the qualified SSI daily source')
    bars = history(ticker, provider, start, end)
    receipt = _observation_time()
    if len(bars) > MAX_SESSION_RECORDS:
        raise ValueError('Bounded EOD history record limit exceeded')
    observations = tuple(HistoricalObservation(ticker=bar.ticker, data_type='market',
        observation_time=bar.date.isoformat(), available_at=eod(bar.date.isoformat()),
        availability_basis='end_of_day_assumption', source=bar.source, payload=bar)
        for bar in bars)
    # Logical content fingerprint, NOT a SSI vendor-vintage ID.
    import json
    canonical = json.dumps([o.model_dump(mode='json') for o in sorted(observations,
        key=lambda o: o.observation_time)], sort_keys=True, allow_nan=False)
    return EODHistoryRead(observations=observations, observed_at=receipt,
        source_version=sha256(canonical.encode()).hexdigest())


def summarize_eod_result(result: TechnicalDailySignalPacket | TechnicalEODDiagnostic) -> dict:
    """Bounded developer output, without raw exception/configuration details."""
    if isinstance(result, TechnicalDailySignalPacket):
        return dict(status='EVALUATED', packet_state=result.packet_state,
            event_count=len(result.all_current_session_events),
            selected_insight_count=len(result.top_insights), overflow_count=len(result.overflow_event_ids),
            unresolved_checks=result.unresolved_checks,
            source_summary={key:result.data_provenance.get(key) for key in
                ('source','venue','source_observed_at','fetched_at','observation_mode','calendar_version')})
    return dict(status=result.status, reason_codes=result.reason_codes,
                available_observation_count=len(result.available_observations), source_summary=result.source_summary)


def _scoring_context(ticker, days, rows):
    """Reuse native indicators/returns and empirical-v0.1; no factual detector."""
    technicals, segment = {}, []
    def save_segment():
        if segment:
            technicals.update({r.date: r for r in technical_history(ticker, segment, 'SSI:FastConnect')})
    for day in days:
        row = rows.get(day)
        if not row or not row['price_comparable'] or not row['volume_comparable']:
            save_segment(); segment = []
        else:
            segment.append(MarketBar(ticker=ticker, date=day, source=row['source'],
                **{key: row[key] for key in ('open','high','low','close','volume')}))
    save_segment()
    prior_features, previous, raw, contexts = [], None, None, None
    config = SimpleNamespace(lookback_sessions=252, min_history=60)
    for day in days:
        row = rows.get(day)
        current_price = (MarketBar(ticker=ticker, date=day, source=row['source'],
            **{key:row[key] for key in ('open','high','low','close','volume')})
            if row and row['price_comparable'] else None)
        current_snapshot = (market_snapshot(ticker, [previous, current_price], 'SSI:FastConnect')
                            if previous and current_price else
                            MarketSnapshot(ticker=ticker, source='SSI:FastConnect'))
        indicator = technicals.get(day) or SimpleNamespace(ma20=None, ma50=None, rsi14=None)
        volume = row['volume'] if row and row['volume_comparable'] else None
        raw, contexts = build_context(current_snapshot, indicator, prior_features, volume, None, config)
        prior_features.append(raw)
        previous = current_price
    return raw, contexts


class _CAContextReader:
    """A missing optional CA source cannot erase factual technical events."""
    def __init__(self, repository):
        self.repository = repository
        self.unavailable = False

    def context_for(self, ticker, session, *, as_of):
        try:
            return self.repository.context_for(ticker, session, as_of=as_of)
        except Exception:
            self.unavailable = True
            return CorporateActionContext(as_of=as_of, reason='source_unavailable')


def evaluate_technical_eod_packet(ticker, trading_session, *, evaluation_as_of,
                                  generated_at, db_session, provider=None,
                                  history_read: EODHistoryRead | None = None,
                                  calendar: VerifiedSessionCalendar | CalendarEvidence | None = None,
                                  history_start: date | None = None,
                                  corporate_actions=None) -> TechnicalDailySignalPacket | TechnicalEODDiagnostic:
    """One explicit completed stock-day; no new calendar, API, archive or worker.

    For live reads, acquire read_eod_history FIRST and choose the explicit as-of
    afterwards. A newly acquired receipt later than an earlier requested cutoff
    cannot be silently backdated. Persisted operational reads may supply their
    actual receipt, but do not certify lost historical SSI vendor vintages.
    """
    symbol, target, cutoff, observations, summary = None, None, None, (), {}
    def diagnostic(status, *reasons):
        return TechnicalEODDiagnostic(status=status, ticker=symbol,
            trading_session=target.isoformat() if target else None, evaluation_as_of=cutoff,
            reason_codes=tuple(reasons), source_summary=summary, available_observations=observations)
    try:
        symbol = SymbolRequest(symbol=ticker).symbol
        target = trading_session if type(trading_session) is date else date.fromisoformat(trading_session)
        cutoff, generation = _aware(evaluation_as_of), _aware(generated_at)
        if target > cutoff.astimezone(ZONE).date() or generation < cutoff:
            return diagnostic('INVALID_REQUEST', 'session_not_completed_or_invalid_generation_time')
        start = history_start or (max(calendar.coverage_start, target-timedelta(days=MAX_HISTORY_DAYS))
                                 if calendar else target-timedelta(days=MAX_HISTORY_DAYS))
        if type(start) is not date or not 0 <= (target-start).days <= MAX_HISTORY_DAYS:
            return diagnostic('INVALID_REQUEST', 'history_range_outside_reader_bound')
    except (ValueError, TypeError):
        return diagnostic('INVALID_REQUEST', 'invalid_ticker_session_or_timestamp')
    try:
        if target == cutoff.astimezone(ZONE).date() and (history_read is None or not history_read.completion_evidence):
            return diagnostic('INCOMPLETE_EVIDENCE', 'eod_completion_proof_unavailable')
        security = db_session.get(Security, symbol)
        if not security or not security.is_active:
            return diagnostic('INCOMPLETE_EVIDENCE', 'active_security_metadata_unavailable')
        if security.source != 'SSI:FastConnect' or security.instrument_type != 'Stock' or security.exchange not in ('HOSE','HNX','UPCOM'):
            return diagnostic('INCOMPLETE_EVIDENCE', 'incompatible_security_metadata')
        # Existing SQLite security cache stores UTC timestamps without tzinfo.
        security_time = security.last_synced_at
        if security_time is None:
            return diagnostic('INCOMPLETE_EVIDENCE', 'security_metadata_timestamp_unavailable')
        security_time = security_time.replace(tzinfo=timezone.utc) if security_time.tzinfo is None else _aware(security_time)
        if security_time > cutoff:
            return diagnostic('INCOMPLETE_EVIDENCE', 'security_metadata_after_cutoff')
        if history_read is None:
            if provider is None:
                from .stocks import get_market_provider
                provider = get_market_provider()
            history_read = read_eod_history(symbol, provider, start, target)
        if not isinstance(history_read, EODHistoryRead):
            return diagnostic('INCOMPLETE_EVIDENCE', 'invalid_normalized_history_contract')
        receipt = _aware(history_read.observed_at)
        fetched = _aware(history_read.fetched_at) if history_read.fetched_at is not None else None
        summary.update(source=history_read.source, source_version=history_read.source_version,
            source_observed_at=receipt.isoformat(), fetched_at=fetched.isoformat() if fetched else None,
            observation_mode=history_read.observation_mode, venue=security.exchange,
            security_metadata_observed_at=security_time.isoformat())
        if receipt > cutoff or (fetched is not None and (fetched > receipt or fetched > cutoff)):
            return diagnostic('INCOMPLETE_EVIDENCE', 'history_observed_after_cutoff')
        if (history_read.source != 'SSI:FastConnect' or history_read.adjustment_semantics != 'adjusted'
                or history_read.price_unit != 'VND' or history_read.volume_unit != 'shares' or not history_read.source_version):
            return diagnostic('INCOMPLETE_EVIDENCE', 'incompatible_history_source_basis_or_units')
        # Filter date scope BEFORE using/hashing values. Future corrections remain
        # excluded; malformed current/prior rows fail safely instead of zero fill.
        scoped = [o for o in history_read.observations if start.isoformat() <= o.observation_time <= target.isoformat()]
        if len(scoped) > MAX_SESSION_RECORDS:
            return diagnostic('INCOMPLETE_EVIDENCE', 'history_record_bound_exceeded')
        observations = tuple(HistoricalObservation.model_validate(o.model_dump()) for o in scoped)
        if any(o.ticker != symbol or o.source != history_read.source or o.data_type != 'market'
               or o.payload.currency != 'VND' for o in observations):
            return diagnostic('INCOMPLETE_EVIDENCE', 'history_identity_mismatch')
        if len({o.observation_time for o in observations}) != len(observations):
            return diagnostic('INCOMPLETE_EVIDENCE', 'duplicate_source_session')
        observations = tuple(sorted(observations, key=lambda o:o.observation_time))
        if calendar is None:
            return diagnostic('INCOMPLETE_EVIDENCE', 'verified_session_calendar_unavailable')
        if calendar.venue != security.exchange:
            return diagnostic('INCOMPLETE_EVIDENCE', 'calendar_venue_mismatch')
        if calendar.coverage_start > start or calendar.coverage_end < target:
            return diagnostic('INCOMPLETE_EVIDENCE', 'calendar_coverage_or_knowledge_unverified')
        calendar_details, blocked_days = {}, set()
        if isinstance(calendar, CalendarEvidence):
            try:
                days, blocked_days, calendar_details = resolve_calendar(calendar,start,target,cutoff,symbol)
            except ValueError:
                return diagnostic('INCOMPLETE_EVIDENCE', 'calendar_evidence_insufficient_or_contradictory')
            calendar_source = tuple(sorted({r['source_ref'] for r in calendar_details['calendar_records']}))
            calendar_times=[_aware(datetime.fromisoformat(r['observed_at'])) for r in calendar_details['calendar_records']]
            calendar_time=max(calendar_times).isoformat() if calendar_times else None
        else:
            if (_aware(calendar.observed_at) > cutoff or calendar.coverage_start > calendar.coverage_end):
                return diagnostic('INCOMPLETE_EVIDENCE', 'calendar_coverage_or_knowledge_unverified')
            days = sorted(d for d in calendar.sessions if start <= d <= target)
            if any(not calendar.coverage_start <= d <= calendar.coverage_end for d in calendar.sessions):
                return diagnostic('INCOMPLETE_EVIDENCE','invalid_or_unverified_trading_session_calendar')
            calendar_source, calendar_time = calendar.source_ref, _aware(calendar.observed_at).isoformat()
            calendar_details['calendar_contract']='caller_attested_session_list_legacy'
            calendar_details['calendar_knowledge_cutoff']=cutoff.isoformat()
        if (not days or days[-1] != target or len(set(days)) != len(days) or len(days) > MAX_SESSION_RECORDS):
            return diagnostic('INCOMPLETE_EVIDENCE', 'invalid_or_unverified_trading_session_calendar')
        summary.update(calendar_details)
        summary['withheld_calendar_observations']=[o.model_dump(mode='json') for o in observations if o.payload.date in blocked_days]
        # Cut off knowledge before inspecting finalization status or corrections.
        known_completion=tuple(p for p in history_read.completion_evidence
            if start<=p.session<=target and _aware(p.observed_at)<=min(receipt,cutoff))
        current = next((o for o in observations if o.payload.date==target),None)
        completion = None
        if current is not None:
            proofs = [p for p in known_completion if p.session==target]
            if len(proofs)!=1:
                return diagnostic('INCOMPLETE_EVIDENCE', 'eod_completion_proof_unavailable_or_duplicate')
            completion=proofs[0]
            if (not completion_matches_bar(completion,current.payload,history_read.source_version,cutoff,security.exchange)
                    or _aware(completion.observed_at)>receipt):
                return diagnostic('INCOMPLETE_EVIDENCE', 'eod_completion_evidence_invalid_or_not_available')
            summary.update(completion_assurance='VERIFIED',completion_evidence=completion.model_dump(mode='json'),
                completion_verification_basis='caller_attestation_not_automatic_ssi_finalization')
        elif target==cutoff.astimezone(ZONE).date():
            return diagnostic('INCOMPLETE_EVIDENCE','eod_completion_observation_unavailable')
        else:
            summary.update(completion_assurance='UNAVAILABLE')
        decision_cutoff=min(eod(target.isoformat()),cutoff.astimezone(ZONE))
        raw_rows, visible_rows = [], {}
        for observation in observations:
            bar = observation.payload
            row = dict(ticker=symbol, session=bar.date.isoformat(), source=bar.source, currency=bar.currency,
                **{key:getattr(bar,key) for key in ('open','high','low','close','volume')},
                timeframe='1d', is_complete=True, adjustment_semantics=history_read.adjustment_semantics,
                volume_unit=history_read.volume_unit, price_comparable=bar.date not in history_read.noncomparable_price_sessions,
                volume_comparable=bar.date not in history_read.noncomparable_volume_sessions,
                is_fixture=observation.is_fixture)
            # HistoricalObservation stores the assumed timestamp as well. Do not
            # accidentally promote it to an audited publication by copying it as
            # available_at (visible_bar gives that field audited precedence).
            if observation.availability_basis == 'end_of_day_assumption':
                if observation.available_at != eod(row['session']):
                    return diagnostic('INCOMPLETE_EVIDENCE', 'invalid_assumed_eod_availability')
                row['availability_basis'] = 'end_of_day_assumption'
            elif observation.availability_basis == 'published':
                row['available_at'] = observation.available_at.isoformat() if observation.available_at else None
                row['availability_basis'] = 'published'
            else:
                row['availability_basis'] = 'unknown'
            if bar.date in blocked_days:
                continue  # Preserve raw observation in diagnostic receipt; never bridge unknown venue/ticker evidence.
            if bar.date == target and target == cutoff.astimezone(ZONE).date():
                if observation.availability_basis != 'published' or observation.available_at is None:
                    return diagnostic('INCOMPLETE_EVIDENCE','eod_completion_availability_unverified')
                if _aware(observation.available_at) != _aware(completion.available_at):
                    return diagnostic('INCOMPLETE_EVIDENCE','eod_completion_availability_conflict')
            prior_proofs=[p for p in known_completion if p.session==bar.date] if bar.date!=target else []
            if prior_proofs:
                if len(prior_proofs)!=1 or not completion_matches_bar(prior_proofs[0],bar,history_read.source_version,cutoff,security.exchange):
                    row['is_complete']=False  # Explicit contrary evidence overrides any daily assumption.
            bar_proof=completion if bar.date==target else prior_proofs[0] if len(prior_proofs)==1 and row['is_complete'] else None
            if bar_proof and _aware(bar_proof.available_at)>eod(row['session']):
                # A known late finalization cannot hide under the earlier EOD assumption.
                at=_aware(bar_proof.available_at)
                if row.get('available_at'):
                    at=max(at,_aware(datetime.fromisoformat(row['available_at'])))
                row.update(available_at=at.isoformat(),availability_basis='published')
            raw_rows.append(row)
            visible = visible_bar(row, decision_cutoff) if row['is_complete'] else None
            if visible is not None:
                visible_rows[bar.date] = visible
        if any(date.fromisoformat(row['session']) not in days for row in raw_rows):
            return diagnostic('INCOMPLETE_EVIDENCE', 'source_observation_outside_verified_calendar')
        raw_context, contexts = _scoring_context(symbol, days, visible_rows)
        provenance = dict(summary, price_unit=history_read.price_unit, volume_unit=history_read.volume_unit,
            adjustment_semantics=history_read.adjustment_semantics, version=history_read.source_version,
            downloaded_at=receipt.isoformat(), downloaded_at_basis='operational_reader_receipt_not_vendor_fetch_time',
            calendar_version=calendar.version, calendar_evidence=calendar_source,
            calendar_observed_at=calendar_time,
            history_start=start.isoformat(), history_end=target.isoformat(),
            episode_history_boundary='unknown', context_version='empirical-v0.1',
            context_lookback_sessions=252, context_minimum_history=60,
            raw_context_features=raw_context,
            limitations=('market_relative_context_unavailable', 'sector_relative_context_unavailable',
                'recurrence_history_unavailable', 'bounded_episode_history_unverified_left_boundary',
                'current_security_metadata_not_historical_listing_vintage') +
                (('reader_cache_fetch_time_unavailable',) if fetched is None else ()) +
                (('calendar_continuity_unresolved',) if blocked_days else ()) +
                ('prior_daily_availability_assumed_not_verified',))
        snapshot = dict(calendar=[d.isoformat() for d in days], bars=raw_rows, provenance=provenance,
            is_fixture=history_read.is_fixture, episode_history_boundary='unknown')
        if corporate_actions is None:
            from src.corporate_actions.repository import CorporateActionRepository
            corporate_actions = CorporateActionRepository(db_session)
        action_reader = _CAContextReader(corporate_actions)
        evaluation = evaluate_d4_market_events(snapshot, symbol, target.isoformat(), generated_at=cutoff,
            contexts=contexts, corporate_actions=action_reader)
        if action_reader.unavailable:
            from dataclasses import replace
            evaluation = replace(evaluation, data_provenance={**evaluation.data_provenance,
                'limitations': evaluation.data_provenance['limitations'] + ('corporate_action_source_unavailable',)})
        # Consumer diagnostics belong to input provenance, so semantic identity is
        # still computed by the sole D5 builder rather than patched afterwards.
        # D5 carries these supplied source limitations through the packet contract.
        return build_technical_daily_packet(evaluation, generated_at=generation)
    except (ProviderError, TimeoutError):
        return diagnostic('SOURCE_UNAVAILABLE', 'market_source_unavailable')
    except (ValueError, TypeError, AttributeError):
        return diagnostic('INCOMPLETE_EVIDENCE', 'invalid_or_incomplete_eod_evidence')
    except Exception:
        return diagnostic('INFRASTRUCTURE_FAILURE', 'technical_eod_infrastructure_failure')
