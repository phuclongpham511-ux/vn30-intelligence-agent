"""Separate provisional operational readiness; never a VERIFIED EOD attestation.

The inputs are transient. This module neither stores SSI history nor certifies
that a caller-supplied external URL really contains the claimed exchange record.
Acquisition must qualify that source before constructing these evidence objects.
"""
from datetime import date, datetime, timedelta, timezone
from threading import Lock
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field

from src.evaluation.benchmark.inputs import ZONE
from src.schemas.stocks import SymbolRequest
from src.providers.ssi import SsiMarketDataProvider
from src.analytics.factual import FAMILIES
from src.materiality.delivery import TechnicalDailySignalPacket
from .session_evidence import CalendarEvidence, aware, resolve_calendar
from .technical_eod import (EODHistoryRead, EODModel, MAX_HISTORY_DAYS, MAX_SESSION_RECORDS,
    TechnicalEODDiagnostic, _evaluate_technical_eod_packet,
    fingerprint_eod_observations, read_eod_history)

POLICY_VERSION = 'provisional-operational-eod-v1'


class AuthenticatedSsiHistoryRead(EODModel):
    """Receipt of one fresh authenticated SSI request, without credentials."""
    requested_ticker: str
    range_start: date
    range_end: date
    history: EODHistoryRead
    request_started_at: datetime
    received_at: datetime
    transport: Literal['ssi-sdk-authenticated-raw'] = 'ssi-sdk-authenticated-raw'
    cache_bypassed: bool = True


class AuthenticatedSsiReadReceipt(EODModel):
    """Persistable metadata/hash only; no SSI OHLCV or authentication material."""
    requested_ticker: str
    range_start: date
    range_end: date
    request_started_at: datetime
    observed_at: datetime
    received_at: datetime
    source_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    observation_count: int = Field(gt=0, le=MAX_SESSION_RECORDS)
    target_present: bool
    source: Literal['SSI:FastConnect'] = 'SSI:FastConnect'
    adjustment_semantics: Literal['adjusted'] = 'adjusted'
    price_unit: Literal['VND'] = 'VND'
    volume_unit: Literal['shares'] = 'shares'
    observation_mode: Literal['current_reconstruction'] = 'current_reconstruction'
    is_fixture: bool = False
    transport: Literal['ssi-sdk-authenticated-raw'] = 'ssi-sdk-authenticated-raw'
    cache_bypassed: bool = True


class HosePublicationEvidence(EODModel):
    """Qualified caller evidence for a specific HOSE post-session publication."""
    venue: Literal['HOSE']
    session: date
    source_ref: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    published_at: datetime
    observed_at: datetime
    verified_at: datetime
    evidence_kind: Literal['official_post_session_bulletin'] = 'official_post_session_bulletin'


class ProvisionalEODAssessment(EODModel):
    status: Literal['PROVISIONAL', 'INCOMPLETE_EVIDENCE']
    assurance: Literal['PROVISIONAL'] | None = None
    reason_codes: tuple[str, ...]
    ticker: str | None = None
    session: date | None = None
    source_version: str | None = None
    calendar_version: str | None = None
    publication_source: str | None = None
    first_received_at: datetime | None = None
    second_received_at: datetime | None = None
    policy_version: str = POLICY_VERSION


class ProvisionalTechnicalDailyPacket(EODModel):
    """Explicit provisional envelope; never the verified API packet type."""
    assurance: Literal['PROVISIONAL'] = 'PROVISIONAL'
    safe_to_display_as_verified: Literal[False] = False
    policy_version: str = POLICY_VERSION
    publication_source: str
    publication_sha256: str
    first_received_at: datetime
    second_received_at: datetime
    source_version: str
    packet: TechnicalDailySignalPacket


class ProvisionalInvalidation(EODModel):
    status: Literal['INVALIDATED'] = 'INVALIDATED'
    packet_id: str
    ticker: str
    session: date
    previous_source_version: str
    revised_source_version: str
    detected_at: datetime
    reason_code: Literal['ssi_history_revision_detected'] = 'ssi_history_revision_detected'


def capture_fresh_ssi_read(ticker, start, end, *, provider=None) -> AuthenticatedSsiHistoryRead:
    """One bounded authenticated SDK read; bars and receipts stay in memory."""
    symbol = SymbolRequest(symbol=ticker).symbol
    owned = provider is None
    source = provider if provider is not None else SsiMarketDataProvider()
    if not isinstance(source, SsiMarketDataProvider):
        raise TypeError('Provisional acquisition requires the SSI SDK provider')
    try:
        if (type(start) is not date or type(end) is not date
                or not 0 <= (end-start).days <= MAX_HISTORY_DAYS
                or end >= source._today()):
            raise ValueError('Fresh provisional history requires a bounded prior-day range')
        begun = datetime.now(timezone.utc)
        read = read_eod_history(symbol, source, start, end, fresh=True)
        received = datetime.now(timezone.utc)
        return AuthenticatedSsiHistoryRead(requested_ticker=symbol,
            range_start=start, range_end=end, history=read,
            request_started_at=begun, received_at=received)
    finally:
        if owned:
            source.close()


def _official_hose_url(value: str) -> bool:
    try:
        parts = urlsplit(value)
        host = parts.hostname or ''
        return (parts.scheme == 'https' and (host == 'hsx.vn' or host.endswith('.hsx.vn'))
            and parts.username is None and parts.password is None and not parts.query)
    except (TypeError, ValueError):
        return False


def _fingerprint(read: EODHistoryRead) -> str:
    return fingerprint_eod_observations(read.observations)


def compact_ssi_receipt(read: AuthenticatedSsiHistoryRead) -> AuthenticatedSsiReadReceipt:
    """Check the full fresh read before retaining only its comparison receipt."""
    if not isinstance(read, AuthenticatedSsiHistoryRead):
        raise ValueError('A full authenticated SSI read is required')
    if _receipt_reasons(read, read.requested_ticker, read.range_start,
            read.range_end, datetime.now(timezone.utc)):
        raise ValueError('Cannot compact an invalid SSI read')
    history = read.history
    return AuthenticatedSsiReadReceipt(requested_ticker=read.requested_ticker,
        range_start=read.range_start, range_end=read.range_end,
        request_started_at=read.request_started_at, observed_at=history.observed_at,
        received_at=read.received_at, source_version=history.source_version,
        observation_count=len(history.observations), target_present=True,
        source=history.source, adjustment_semantics=history.adjustment_semantics,
        price_unit=history.price_unit, volume_unit=history.volume_unit,
        observation_mode=history.observation_mode, is_fixture=history.is_fixture,
        transport=read.transport, cache_bypassed=read.cache_bypassed)


def parse_compact_ssi_receipt(payload: dict) -> AuthenticatedSsiReadReceipt:
    """Load the bounded metadata-only first-read file; reject altered schema."""
    if (not isinstance(payload, dict)
            or payload.get('schema_version') != 'ssi-provisional-receipt-v1'
            or payload.get('policy_version') != POLICY_VERSION
            or payload.get('raw_ohlcv_persisted') is not False
            or set(payload) != {'schema_version', 'policy_version', 'ticker',
                'range_start', 'range_end', 'transport', 'cache_bypassed',
                'request_started_at', 'source_observed_at', 'received_at', 'source',
                'canonical_observations_sha256', 'observation_count', 'target_present',
                'adjustment_semantics', 'price_unit', 'volume_unit',
                'observation_mode', 'is_fixture', 'raw_ohlcv_persisted'}):
        raise ValueError('Unexpected SSI receipt schema')
    return AuthenticatedSsiReadReceipt(requested_ticker=payload['ticker'],
        range_start=payload['range_start'], range_end=payload['range_end'],
        request_started_at=payload['request_started_at'],
        observed_at=payload['source_observed_at'], received_at=payload['received_at'],
        source_version=payload['canonical_observations_sha256'],
        observation_count=payload['observation_count'], target_present=payload['target_present'],
        source=payload['source'], adjustment_semantics=payload['adjustment_semantics'],
        price_unit=payload['price_unit'], volume_unit=payload['volume_unit'],
        observation_mode=payload['observation_mode'], is_fixture=payload['is_fixture'],
        transport=payload['transport'], cache_bypassed=payload['cache_bypassed'])


def _receipt_reasons(receipt, ticker, start, target, cutoff):
    if (not isinstance(receipt, (AuthenticatedSsiHistoryRead, AuthenticatedSsiReadReceipt)) or not receipt.cache_bypassed
            or receipt.transport != 'ssi-sdk-authenticated-raw'):
        return ['authenticated_fresh_read_unavailable']
    if (receipt.requested_ticker != ticker or receipt.range_start != start
            or receipt.range_end != target):
        return ['read_request_scope_mismatch']
    try:
        begun, observed, ended = (aware(receipt.request_started_at),
            aware(receipt.observed_at if isinstance(receipt, AuthenticatedSsiReadReceipt)
                  else receipt.history.observed_at), aware(receipt.received_at))
        if not begun <= observed <= ended <= cutoff:
            return ['read_receipt_invalid']
        if (isinstance(receipt, AuthenticatedSsiHistoryRead) and receipt.history.fetched_at is not None
                and not begun <= aware(receipt.history.fetched_at) <= ended):
            return ['read_receipt_invalid']
    except ValueError:
        return ['read_receipt_invalid']
    if isinstance(receipt, AuthenticatedSsiReadReceipt):
        if (receipt.is_fixture or not receipt.target_present or receipt.observation_count < 1
                or receipt.source != 'SSI:FastConnect' or receipt.adjustment_semantics != 'adjusted'
                or receipt.price_unit != 'VND' or receipt.volume_unit != 'shares'
                or receipt.observation_mode != 'current_reconstruction'):
            return ['incompatible_or_fixture_ssi_read']
        return []
    read = receipt.history
    if (read.source != 'SSI:FastConnect' or read.adjustment_semantics != 'adjusted'
            or read.price_unit != 'VND' or read.volume_unit != 'shares'
            or read.observation_mode != 'current_reconstruction'
            or read.is_fixture or any(o.is_fixture for o in read.observations)):
        return ['incompatible_or_fixture_ssi_read']
    if read.source_version != _fingerprint(read):
        return ['read_content_fingerprint_invalid']
    observations = read.observations
    days = [o.payload.date for o in observations]
    if (len(days) != len(set(days)) or not days or target not in days
            or any(not start <= d <= target or o.ticker != ticker or o.payload.ticker != ticker
                or o.source != read.source for d, o in zip(days, observations))):
        return ['read_identity_scope_or_target_invalid']
    return []


def assess_provisional_eod(ticker, trading_session, *, history_start,
                           calendar: CalendarEvidence | None,
                           publication: HosePublicationEvidence | None,
                           first: AuthenticatedSsiHistoryRead | AuthenticatedSsiReadReceipt | None,
                           second: AuthenticatedSsiHistoryRead | None,
                           evaluation_as_of) -> ProvisionalEODAssessment:
    """Check policy gates without invoking D1/D4/D5 or storing source data."""
    symbol, target, cutoff = None, None, None
    def result(*reasons, accepted=False):
        return ProvisionalEODAssessment(status='PROVISIONAL' if accepted else 'INCOMPLETE_EVIDENCE',
            assurance='PROVISIONAL' if accepted else None, reason_codes=tuple(dict.fromkeys(reasons)),
            ticker=symbol, session=target,
            source_version=second.history.source_version if accepted else None,
            calendar_version=calendar.version if accepted and calendar else None,
            publication_source=publication.source_ref if accepted and publication else None,
            first_received_at=first.received_at if isinstance(first,(AuthenticatedSsiHistoryRead,AuthenticatedSsiReadReceipt)) else None,
            second_received_at=second.received_at if isinstance(second,AuthenticatedSsiHistoryRead) else None)
    try:
        symbol = SymbolRequest(symbol=ticker).symbol
        target = trading_session if type(trading_session) is date else date.fromisoformat(trading_session)
        cutoff = aware(evaluation_as_of)
        if (type(history_start) is not date or not 0 <= (target-history_start).days <= MAX_HISTORY_DAYS
                or target >= cutoff.astimezone(ZONE).date()):
            return result('invalid_provisional_session_or_range')
    except (ValueError, TypeError):
        return result('invalid_provisional_session_or_range')
    if calendar is None:
        return result('verified_session_calendar_unavailable')
    if not isinstance(calendar, CalendarEvidence) or calendar.venue != 'HOSE' or (
            calendar.coverage_start > history_start or calendar.coverage_end < target):
        return result('hose_calendar_coverage_unqualified')
    try:
        _, blocked, details = resolve_calendar(calendar, history_start, target, cutoff, symbol)
        records = details['calendar_records']
        if (blocked or len(records) != (target-history_start).days+1
                or any(not _official_hose_url(r['source_ref']) or r['verified_at'] is None
                    or (r['status']=='OCCURRED' and r['evidence_kind']=='official_schedule')
                    for r in records)):
            return result('hose_calendar_continuity_unqualified')
    except (ValueError, TypeError, KeyError):
        return result('hose_calendar_continuity_unqualified')
    if publication is None:
        return result('publication_evidence_unavailable')
    if (not isinstance(publication,HosePublicationEvidence) or publication.venue != calendar.venue
            or publication.session != target or not _official_hose_url(publication.source_ref)):
        return result('publication_source_not_qualified')
    try:
        published, observed, verified = (aware(publication.published_at),
            aware(publication.observed_at), aware(publication.verified_at))
        if (not published <= observed <= verified <= cutoff
                or publication.published_at.astimezone(ZONE).date() < target):
            return result('publication_timestamp_invalid')
    except ValueError:
        return result('publication_timestamp_invalid')
    reasons = _receipt_reasons(first,symbol,history_start,target,cutoff) + _receipt_reasons(
        second,symbol,history_start,target,cutoff)
    if reasons:
        return result(*reasons)
    first_begun, first_at = aware(first.request_started_at), aware(first.received_at)
    second_begun, second_at = aware(second.request_started_at), aware(second.received_at)
    if observed > second_begun or verified > second_begun:
        return result('publication_not_visible_at_read')
    if first_begun < published:
        return result('first_read_before_publication')
    if second_begun - first_at < timedelta(hours=6):
        return result('reads_less_than_six_hours_apart')
    if second_begun - published < timedelta(hours=24):
        return result('second_read_before_publication_delay')
    first_version = (first.source_version if isinstance(first, AuthenticatedSsiReadReceipt)
        else first.history.source_version)
    if first_version != second.history.source_version:
        return result('ssi_history_revision_detected')
    return result(accepted=True)


def evaluate_provisional_technical_eod_packet(ticker, trading_session, *,
        history_start, calendar, publication, first, second, evaluation_as_of,
        generated_at, db_session, corporate_actions=None):
    """Run the existing D1/D4/D5 consumer only after separate provisional gates."""
    assessment = assess_provisional_eod(ticker, trading_session,
        history_start=history_start, calendar=calendar, publication=publication,
        first=first, second=second, evaluation_as_of=evaluation_as_of)
    if assessment.status != 'PROVISIONAL':
        return TechnicalEODDiagnostic(status='INCOMPLETE_EVIDENCE',
            ticker=assessment.ticker,
            trading_session=assessment.session.isoformat() if assessment.session else None,
            evaluation_as_of=evaluation_as_of,
            reason_codes=assessment.reason_codes,
            available_observations=(second.history.observations
                if isinstance(second, AuthenticatedSsiHistoryRead) else ()),
            source_summary={'provisional_policy_version': POLICY_VERSION})
    evaluated = _evaluate_technical_eod_packet(ticker, trading_session,
        evaluation_as_of=evaluation_as_of, generated_at=generated_at,
        db_session=db_session, history_read=second.history, calendar=calendar,
        history_start=history_start, corporate_actions=corporate_actions,
        _provisional=assessment)
    if isinstance(evaluated, TechnicalEODDiagnostic):
        return evaluated
    incomplete = (evaluated.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
        or bool(evaluated.data_provenance.get('calendar_unresolved_sessions'))
        or any(check.family in FAMILIES[:2] and (check.state=='UNRESOLVED'
            or not check.delivery_complete) for check in evaluated.family_checks))
    if incomplete:
        return TechnicalEODDiagnostic(status='INCOMPLETE_EVIDENCE',
            ticker=assessment.ticker, trading_session=assessment.session.isoformat(),
            evaluation_as_of=evaluation_as_of,
            reason_codes=('provisional_critical_evidence_incomplete',),
            available_observations=second.history.observations,
            source_summary={'provisional_policy_version': POLICY_VERSION})
    return ProvisionalTechnicalDailyPacket(publication_source=publication.source_ref,
        publication_sha256=publication.content_sha256,
        first_received_at=first.received_at, second_received_at=second.received_at,
        source_version=second.history.source_version, packet=evaluated)


def invalidate_on_ssi_revision(accepted: ProvisionalTechnicalDailyPacket,
                               latest: AuthenticatedSsiHistoryRead) -> ProvisionalInvalidation | None:
    """A changed, valid fresh read invalidates the affected in-memory packet."""
    if not isinstance(accepted, ProvisionalTechnicalDailyPacket):
        raise ValueError('A provisional packet is required')
    target = date.fromisoformat(accepted.packet.trading_session)
    start = date.fromisoformat(accepted.packet.data_provenance['history_start'])
    reasons = _receipt_reasons(latest, accepted.packet.ticker, start, target,
        aware(latest.received_at) if isinstance(latest, AuthenticatedSsiHistoryRead) else aware(accepted.second_received_at))
    if reasons or aware(latest.request_started_at) <= aware(accepted.second_received_at):
        raise ValueError('A later valid fresh SSI read of the same bounded scope is required')
    if latest.history.source_version == accepted.source_version:
        return None
    return ProvisionalInvalidation(packet_id=accepted.packet.packet_id,
        ticker=accepted.packet.ticker, session=target,
        previous_source_version=accepted.source_version,
        revised_source_version=latest.history.source_version,
        detected_at=latest.received_at)


class ProvisionalInMemoryRegistry:
    """Bounded ephemeral active outputs; restart loses them and requires requalification."""
    def __init__(self, max_packets=128):
        if max_packets < 1:
            raise ValueError('Positive packet bound required')
        self.max_packets = max_packets
        self._packets = {}
        self._lock = Lock()

    def add(self, packet: ProvisionalTechnicalDailyPacket):
        if not isinstance(packet, ProvisionalTechnicalDailyPacket):
            raise ValueError('Only provisional packets may enter the registry')
        with self._lock:
            if packet.packet.packet_id not in self._packets and len(self._packets) >= self.max_packets:
                raise ValueError('Provisional runtime capacity reached')
            self._packets[packet.packet.packet_id] = packet

    def get(self, packet_id):
        with self._lock:
            return self._packets.get(packet_id)

    def observe(self, latest: AuthenticatedSsiHistoryRead) -> tuple[ProvisionalInvalidation, ...]:
        if not isinstance(latest, AuthenticatedSsiHistoryRead):
            raise ValueError('A fresh SSI receipt is required')
        invalidations = []
        with self._lock:
            for packet_id, packet in tuple(self._packets.items()):
                if packet.packet.ticker != latest.requested_ticker or packet.packet.trading_session != latest.range_end.isoformat():
                    continue
                invalidation = invalidate_on_ssi_revision(packet, latest)
                if invalidation is not None:
                    self._packets.pop(packet_id)
                    invalidations.append(invalidation)
        return tuple(invalidations)


def summarize_provisional_result(result) -> dict:
    """Bounded operational status without raw bars, credentials or token fields."""
    if isinstance(result, ProvisionalTechnicalDailyPacket):
        return dict(status='PROVISIONAL', safe_to_display_as_verified=False,
            ticker=result.packet.ticker, session=result.packet.trading_session,
            packet_state=result.packet.packet_state,
            event_count=len(result.packet.all_current_session_events),
            source_version=result.source_version,
            first_received_at=result.first_received_at.isoformat(),
            second_received_at=result.second_received_at.isoformat(),
            publication_source=result.publication_source,
            policy_version=result.policy_version)
    if isinstance(result, TechnicalEODDiagnostic):
        return dict(status=result.status, safe_to_display_as_verified=False,
            ticker=result.ticker, session=result.trading_session,
            reason_codes=result.reason_codes,
            available_observation_count=len(result.available_observations),
            policy_version=POLICY_VERSION)
    if isinstance(result, ProvisionalInvalidation):
        return dict(status='INVALIDATED', safe_to_display_as_verified=False,
            ticker=result.ticker, session=result.session.isoformat(),
            packet_id=result.packet_id, reason_code=result.reason_code,
            detected_at=result.detected_at.isoformat(), policy_version=POLICY_VERSION)
    raise TypeError('Unknown provisional result')
