"""Pure detectors consuming the existing Section 1.6 analytics schemas.

Callers supply consecutive trading observations and externally normalized strengths.
No historical calibration, provider access, or UI decisions occur here.
"""
from dataclasses import dataclass
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
                         is_fixture: bool = False) -> tuple[MaterialEventCandidate, ...]:
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
    return tuple(events)


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
