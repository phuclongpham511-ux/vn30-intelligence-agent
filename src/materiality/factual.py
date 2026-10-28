"""Prospective D1 runtime evidence from completed adjusted daily source snapshots.

Uses the benchmark's calendar/visibility policy, but never its research admission
or synthetic-only builder. Callers must supply calendar evidence; provider bars
alone cannot prove continuity. No fetching, persistence or calendar inference.
"""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from inspect import getsource
import json

from src.analytics.factual import FAMILIES, factual_inputs, finite
from src.analytics.market import technical_history
from src.evaluation.benchmark.inputs import ZONE, eod, visible_bar
from src.schemas.data import MarketBar
from src.services.session_evidence import completion_matches_bar


@dataclass(frozen=True)
class D1MarketEvaluation:
    factual_decisions: dict
    results: tuple
    runtime_version: str = 'technical-d1-runtime-v1'


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def prepare_d1_evidence(snapshot, ticker, session, generated_at):
    """Return independent factual checks and a contiguous native indicator prefix.

    downloaded_at is query receipt, not proof of historical vendor vintages.
    available_at follows the existing audited/EOD-assumption visibility policy.
    This product seam does not qualify SSI for the official PIT benchmark.
    """
    if not isinstance(generated_at, datetime) or generated_at.utcoffset() is None:
        raise ValueError('D1 requires a timezone-aware generation timestamp')
    date.fromisoformat(session)
    provenance = snapshot.get('provenance', {})
    calendar = snapshot.get('calendar', [])
    reason = None
    current_day=generated_at.astimezone(ZONE).date()
    operational_completion=False
    if date.fromisoformat(session)==current_day:
        current_rows=[r for r in snapshot.get('bars',[]) if r.get('ticker')==ticker and r.get('session')==session]
        if len(current_rows)==1:
            try:
                raw=current_rows[0]
                bar=MarketBar(ticker=ticker,date=session,source=raw['source'],currency=raw['currency'],
                    **{k:raw[k] for k in ('open','high','low','close','volume')})
                operational_completion=completion_matches_bar(provenance.get('completion_evidence'),
                    bar,provenance.get('version'),generated_at,provenance.get('venue'))
            except (ValueError,KeyError,TypeError):
                pass
    cutoff=min(eod(session),generated_at.astimezone(ZONE))
    if date.fromisoformat(session) > current_day or (date.fromisoformat(session)==current_day and not operational_completion):
        reason = 'session_not_completed'
    elif provenance.get('source') != 'SSI:FastConnect' or provenance.get('adjustment_semantics') != 'adjusted':
        reason = 'incompatible_daily_source_or_adjustment'
    elif not all(provenance.get(k) for k in ('version', 'calendar_version', 'calendar_evidence', 'downloaded_at')):
        reason = 'source_or_calendar_provenance_unavailable'
    else:
        try:
            downloaded = datetime.fromisoformat(provenance['downloaded_at'])
            if downloaded.utcoffset() is None or downloaded > generated_at:
                reason = 'invalid_source_receipt_time'
        except (TypeError, ValueError):
            reason = 'invalid_source_receipt_time'
    try:
        sessions = sorted(d for d in calendar if d <= session)
        for day in sessions:
            date.fromisoformat(day)
        if not sessions or sessions[-1] != session or len(set(sessions)) != len(sessions):
            reason = reason or 'invalid_session_calendar'
    except (TypeError, ValueError):
        sessions, reason = [], 'invalid_session_calendar'
    if reason:
        decisions = {family: {**factual_inputs(family, session, None, [], comparable=False),
                              'reason': reason, 'source': dict(provenance)} for family in FAMILIES[:2]}
        return decisions, None, [], bool(snapshot.get('is_fixture', False))

    rows, bad, duplicates = {}, {}, set()
    for raw in snapshot.get('bars', []):
        if raw.get('ticker') != ticker or raw.get('session', '') > session:
            continue
        day = raw.get('session')
        if day not in sessions:
            # A visible out-of-calendar observation invalidates calendar assurance.
            decisions = {family: {**factual_inputs(family, session, None, [], comparable=False),
                                  'reason': 'observation_outside_calendar', 'source': dict(provenance)}
                         for family in FAMILIES[:2]}
            return decisions, None, [], bool(snapshot.get('is_fixture', False))
        if day in rows or day in bad:
            duplicates.add(day)
        if (raw.get('source') != provenance['source'] or raw.get('currency') != MarketBar.model_fields['currency'].default
                or raw.get('timeframe') != '1d'
                or raw.get('is_complete', True) is not True
                or raw.get('adjustment_semantics', 'adjusted') != 'adjusted'):
            rows[day], bad[day] = None, 'incompatible_source_units_or_daily_session'
            continue
        try:
            rows[day] = visible_bar(raw, cutoff)
            if rows[day] is None:
                bad[day] = 'observation_not_visible_at_cutoff'
        except (TypeError, ValueError):
            rows[day], bad[day] = None, 'invalid_observation_availability'
    for day in duplicates:
        rows[day], bad[day] = None, 'duplicate_source_session'

    def price_valid(row):
        return (row is not None and row.get('price_comparable') is True
                and all(finite(row.get(k)) and row[k] > 0 for k in ('open', 'high', 'low', 'close'))
                and row['low'] <= min(row['open'], row['close'])
                and row['high'] >= max(row['open'], row['close']))

    def volume_valid(row):
        return (row is not None and row.get('volume_comparable') is True
                and provenance.get('volume_unit') == 'shares'
                and row.get('volume_unit', 'shares') == 'shares'
                and finite(row.get('volume')) and row['volume'] >= 0)

    price_history, volume_history, values, prefix = [], [], {}, []
    previous = None
    for day in sessions:
        row = rows.get(day)
        continuous = price_valid(previous) and price_valid(row)
        value = row['close'] / previous['close'] - 1 if continuous else None
        values[day] = value
        price_history.append(dict(session=day, value=value, comparable=continuous))
        volume_history.append(dict(session=day, value=row.get('volume') if row else None,
                                   comparable=volume_valid(row)))
        # Native schemas require complete volume; never fill missing values.
        if price_valid(row) and volume_valid(row):
            if not continuous:
                prefix = []
            prefix.append(MarketBar(ticker=ticker, date=day, source=row['source'],
                                    **{k: row[k] for k in ('open', 'high', 'low', 'close', 'volume')}))
        else:
            prefix = []
        previous = row

    current = rows.get(session)
    decisions = {
        'abnormal_price_move': factual_inputs('abnormal_price_move', session, values[session], price_history,
                                             comparable=values[session] is not None),
        'unusual_volume': factual_inputs('unusual_volume', session, current.get('volume') if current else None,
                                         volume_history, comparable=volume_valid(current)),
    }
    calculation_hash = _hash(getsource(prepare_d1_evidence) + getsource(factual_inputs)
                             + getsource(finite) + getsource(visible_bar))
    for family, decision in decisions.items():
        selected = decision['history']
        current_value = values[session] if family == 'abnormal_price_move' else current.get('volume') if current else None
        # Keep invalid numeric evidence inspectable without emitting NaN/Infinity
        # in a JSON response. This is not a zero or a factual negative.
        invalid_value = repr(current_value) if current_value is not None and not finite(current_value) else None
        decision.update(signed_return=values[session] if family == 'abnormal_price_move' else None,
                        current_value=None if invalid_value else current_value,
                        invalid_current_value=invalid_value,
                        session=session, cutoff=cutoff.isoformat(), source=dict(provenance),
                        return_definition='close(t)/close(previous_calendar_session)-1',
                        calculation_version='technical-d1-runtime-v1',
                        calculation_sha256=calculation_hash,
                        selected_evidence=[{'session': h['session'], 'value': h['value'],
                                            'source_observation_id': _hash(rows[h['session']]),
                                            'available_at': rows[h['session']]['available_at']}
                                           for h in selected],
                        source_subset_sha256=_hash([rows.get(d) for d in sessions]))
        if family == 'abnormal_price_move':
            for evidence in decision['selected_evidence']:
                prior_day = sessions[sessions.index(evidence['session']) - 1]
                evidence.update(previous_session=prior_day, previous_close=rows[prior_day]['close'],
                                previous_source_observation_id=_hash(rows[prior_day]),
                                previous_available_at=rows[prior_day]['available_at'])
        for exclusion in decision['excluded']:
            exclusion['reason'] = bad.get(exclusion['session'], 'missing_or_noncomparable')
        if decision['reason'] == 'invalid_current_evidence':
            decision['reason'] = bad.get(session, 'missing_or_noncomparable_current_pair' if family == 'abnormal_price_move'
                                         else 'missing_invalid_or_incompatible_volume')
    technicals = technical_history(ticker, prefix, provenance['source']) if prefix else []
    fixture = bool(snapshot.get('is_fixture', False)) or any(row.get('is_fixture', False) for row in rows.values() if row)
    return decisions, current, technicals, fixture
