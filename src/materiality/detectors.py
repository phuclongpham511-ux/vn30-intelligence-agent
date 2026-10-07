"""Pure detectors consuming the existing Section 1.6 analytics schemas.

Callers supply consecutive trading observations and externally normalized strengths.
No historical calibration, provider access, or UI decisions occur here.
"""
from dataclasses import dataclass, replace
from math import isfinite

from src.analytics.market import market_snapshot
from src.schemas.data import TechnicalBar, FundamentalPeriod
from .models import EvidenceItem, EventDirection, EventType, MaterialEventCandidate, MaterialityCategory


@dataclass(frozen=True)
class ScoringContext:
    own_history_abnormality: float | None = None
    market_relative_abnormality: float | None = None
    sector_relative_abnormality: float | None = None
    economic_magnitude: float | None = None
    days_since_similar_event: int | None = None
    source_quality: float = 1.0


def _valid(*values: float | None) -> bool:
    return all(type(v) in (int, float) and isfinite(v) for v in values)


def _validate_pair(prior, current) -> None:
    if prior and (prior.ticker != current.ticker or prior.source != current.source
                  or prior.currency != current.currency):
        raise ValueError("Mixed ticker, source or currency")


def _evidence(row, metric: str, unit: str) -> EvidenceItem:
    as_of = row.date if isinstance(row, TechnicalBar) else row.period
    return EvidenceItem(metric=metric, value=getattr(row, metric), source=row.source,
                        unit=unit, as_of=as_of)


def _candidate(current, kind, category, direction, evidence, context, is_fixture, transition=False):
    observed_at = current.date if isinstance(current, TechnicalBar) else current.period
    return MaterialEventCandidate(
        ticker=current.ticker, event_type=kind, category=category, direction=direction,
        observed_at=observed_at, evidence=tuple(evidence),
        reason_codes=(f"detected:{kind.value}",), **vars(context),
        is_state_transition=transition, data_completeness=1.0, is_fixture=is_fixture,
    )


def detect_market_events(prior: TechnicalBar | None, current: TechnicalBar,
                         contexts: dict[str, ScoringContext] | None = None, *,
                         is_fixture: bool = False, recent_bars: list[TechnicalBar] | None = None,
                         relative_volume: float | None = None) -> tuple[MaterialEventCandidate, ...]:
    """Consume adjacent rows from technical_history, preserving VND/share units.

    is_fixture applies to the entire input pair and supplied scoring context.
    Existing normalized market schemas do not carry fixture provenance.
    """
    _validate_pair(prior, current)
    if prior and prior.date >= current.date:
        raise ValueError("Market observations must be strictly chronological")
    contexts = contexts or {}
    events = []

    def emit(kind, direction, evidence, transition=False):
        events.append(_candidate(current, kind,
            MaterialityCategory.TECHNICAL if transition else MaterialityCategory.MARKET,
            direction, evidence, contexts.get(kind.value, ScoringContext()), is_fixture, transition))

    if prior and _valid(prior.ma20, prior.ma50, current.ma20, current.ma50):
        before, after = prior.ma20 - prior.ma50, current.ma20 - current.ma50
        if before <= 0 < after or before >= 0 > after:
            emit(EventType.MA_CROSS, EventDirection.POSITIVE if after > 0 else EventDirection.NEGATIVE,
                 [_evidence(row, metric, current.currency) for metric in ("ma20", "ma50")
                  for row in (prior, current)], True)
    if prior and _valid(prior.rsi14, current.rsi14):
        if prior.rsi14 <= 70 < current.rsi14 or prior.rsi14 >= 30 > current.rsi14:
            emit(EventType.RSI_REGIME_ENTRY,
                 EventDirection.POSITIVE if current.rsi14 > 70 else EventDirection.NEGATIVE,
                 [_evidence(row, "rsi14", "index") for row in (prior, current)], True)

    context = contexts.get(EventType.ABNORMAL_PRICE_MOVE.value)
    if prior and context and context.own_history_abnormality is not None:
        # Reuse the existing factual return calculation; do not duplicate analytics.
        daily_return = market_snapshot(current.ticker, [prior, current], current.source).daily_return
        if _valid(daily_return):
            direction = (EventDirection.POSITIVE if daily_return > 0 else
                         EventDirection.NEGATIVE if daily_return < 0 else EventDirection.NEUTRAL)
            emit(EventType.ABNORMAL_PRICE_MOVE, direction,
                 [_evidence(row, "close", current.currency) for row in (prior, current)] +
                 [EvidenceItem("daily_return", daily_return, current.source, unit="fraction", as_of=current.date)])
    context = contexts.get(EventType.UNUSUAL_VOLUME.value)
    if context and context.own_history_abnormality is not None and _valid(current.volume):
        emit(EventType.UNUSUAL_VOLUME, EventDirection.NEUTRAL, [_evidence(current, "volume", "shares")])
    recent = recent_bars if recent_bars is not None else ([prior, current] if prior else [current])
    if not recent or recent[-1] != current or (prior and (len(recent) < 2 or recent[-2] != prior)):
        raise ValueError("Recent bars must end with the current/prior pair")
    for left, right in zip(recent, recent[1:]):
        _validate_pair(left, right)
        if left.date >= right.date:
            raise ValueError("Recent bars must be strictly chronological")
    events.extend(_bollinger_events(prior, current, recent, contexts, relative_volume, is_fixture))
    return tuple(events)


def _bollinger_events(prior, current, recent, contexts, relative_volume, is_fixture):
    """Inclusive touch, strict recovery on confirmation; delay 0..2 observations.

    Existing trailing volume midrank >= .95 is a provisional confirmation gate,
    not a calibrated Materiality cutoff. It uses confirmation-day volume only.
    Reconfirmation can occur inside the short window; event memory lowers novelty.
    """
    volume = contexts.get(EventType.UNUSUAL_VOLUME.value)
    rank = volume.own_history_abnormality if volume else None
    if (not prior or not _valid(rank, current.volume, current.bb50_std) or
            rank < .95 or current.volume <= 0 or current.bb50_std <= 0):
        return []
    output = []
    for kind, band, extreme, direction in (
        (EventType.BOLLINGER_LOWER_REVERSAL_VOLUME, 'bb50_lower', 'low', EventDirection.POSITIVE),
        (EventType.BOLLINGER_UPPER_REVERSAL_VOLUME, 'bb50_upper', 'high', EventDirection.NEGATIVE)):
        boundary = getattr(current, band)
        if not _valid(boundary):
            continue
        upward = direction == EventDirection.POSITIVE
        if not ((current.close > boundary and current.close > prior.close) if upward else
                (current.close < boundary and current.close < prior.close)):
            continue
        touch = next((row for row in reversed(recent[-3:])
            if _valid(getattr(row, band), row.bb50_std) and row.bb50_std > 0 and
            (row.low <= row.bb50_lower if upward else row.high >= row.bb50_upper)), None)
        if touch is None:
            continue
        evidence = [_evidence(current, name, current.currency) for name in
            ('close', 'low', 'high', 'ma50', 'bb50_lower', 'bb50_upper', 'bb50_std')]
        evidence.extend((EvidenceItem('touch_'+extreme, getattr(touch, extreme), touch.source,
                unit=touch.currency, as_of=touch.date),
            EvidenceItem('touch_band', getattr(touch, band), touch.source, unit=touch.currency, as_of=touch.date),
            EvidenceItem('touch_session', touch.date.isoformat(), touch.source, as_of=touch.date),
            EvidenceItem('confirmation_session', current.date.isoformat(), current.source, as_of=current.date),
            EvidenceItem('touch_distance_fraction', getattr(touch, extreme)/getattr(touch, band)-1
                if getattr(touch, band) != 0 else None, touch.source, unit='fraction', as_of=touch.date),
            EvidenceItem('previous_close', prior.close, prior.source, unit=prior.currency, as_of=prior.date),
            EvidenceItem('confirmation_return', current.close/prior.close-1, current.source,
                unit='fraction', as_of=current.date),
            _evidence(current, 'volume', 'shares'),
            EvidenceItem('volume_percentile', rank, current.source, unit='fraction', as_of=current.date),
            EvidenceItem('relative_volume', relative_volume, current.source, unit='ratio', as_of=current.date)))
        # No extra volume/BB score channel: reuse the price context, volume gates eligibility.
        context = contexts.get(kind.value)
        if context is None:
            context = replace(contexts.get(EventType.ABNORMAL_PRICE_MOVE.value, ScoringContext()),
                days_since_similar_event=None)  # Price-event recurrence is not BB recurrence.
        output.append(_candidate(current, kind, MaterialityCategory.TECHNICAL, direction,
            evidence, context, is_fixture))
    return output


def detect_fundamental_events(prior: FundamentalPeriod | None, current: FundamentalPeriod,
                              contexts: dict[str, ScoringContext] | None = None, *,
                              is_fixture: bool = False) -> tuple[MaterialEventCandidate, ...]:
    """Compare adjacent annual analytics periods; never invent bank fields.

    Reporting periods are evidence dates, not historical publication timestamps.
    Point-in-time availability is a separate Phase 2 contract.
    """
    _validate_pair(prior, current)
    if prior is None:
        return ()
    if int(prior.period) >= int(current.period):
        raise ValueError("Fundamental observations must be strictly chronological")
    if int(current.period) != int(prior.period) + 1:
        return ()
    contexts = contexts or {}
    events = []
    for kind, metric in ((EventType.REVENUE_GROWTH_CHANGE, "revenue_growth_yoy"),
                         (EventType.NET_PROFIT_GROWTH_CHANGE, "net_profit_growth_yoy"),
                         (EventType.MARGIN_CHANGE, "gross_margin"),
                         (EventType.MARGIN_CHANGE, "net_margin")):
        before, after = getattr(prior, metric), getattr(current, metric)
        if not _valid(before, after) or before == after:
            continue
        events.append(_candidate(current, kind, MaterialityCategory.FUNDAMENTAL,
            EventDirection.POSITIVE if after > before else EventDirection.NEGATIVE,
            [_evidence(row, metric, "fraction") for row in (prior, current)],
            contexts.get(metric, contexts.get(kind.value, ScoringContext())), is_fixture))
    return tuple(events)
