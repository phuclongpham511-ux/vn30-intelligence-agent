"""Immutable, validated materiality domain objects. No provider dependencies."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from math import isfinite


def bounded(value: float) -> float:
    """Clamp finite normalized features; reject invalid numeric evidence."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError("Normalized inputs must be finite numbers")
    return min(1.0, max(0.0, float(value)))


class MaterialityCategory(StrEnum):
    MARKET = "market"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    NEWS = "news"


class EventDirection(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EventType(StrEnum):
    ABNORMAL_PRICE_MOVE = "abnormal_price_move"
    UNUSUAL_VOLUME = "unusual_volume"
    MA_CROSS = "ma_cross"
    RSI_REGIME_ENTRY = "rsi_regime_entry"
    REVENUE_GROWTH_CHANGE = "revenue_growth_change"
    NET_PROFIT_GROWTH_CHANGE = "net_profit_growth_change"
    MARGIN_CHANGE = "margin_change"


@dataclass(frozen=True)
class EvidenceItem:
    metric: str
    value: float | str | None
    source: str
    prior_value: float | str | None = None
    unit: str | None = None
    as_of: date | datetime | str | None = None


@dataclass(frozen=True)
class MaterialEventCandidate:
    ticker: str
    event_type: EventType
    category: MaterialityCategory
    direction: EventDirection
    observed_at: date | datetime | str
    evidence: tuple[EvidenceItem, ...] = ()
    reason_codes: tuple[str, ...] = ()
    own_history_abnormality: float | None = None
    market_relative_abnormality: float | None = None
    sector_relative_abnormality: float | None = None
    economic_magnitude: float | None = None
    days_since_similar_event: int | None = None
    is_state_transition: bool = False
    source_quality: float = 1.0
    data_completeness: float = 1.0
    is_fixture: bool = False

    def __post_init__(self) -> None:
        if not self.ticker.strip():
            raise ValueError("ticker is required")
        for name, enum in (("event_type", EventType), ("category", MaterialityCategory), ("direction", EventDirection)):
            object.__setattr__(self, name, enum(getattr(self, name)))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        reasons = list(self.reason_codes)
        for name in SIGNIFICANCE_CHANNELS + ("source_quality", "data_completeness"):
            value = getattr(self, name)
            if value is None and name in SIGNIFICANCE_CHANNELS:
                continue
            normalized = bounded(value)
            object.__setattr__(self, name, normalized)
            if normalized != value:
                reasons.append(f"input_clamped:{name}")
        days = self.days_since_similar_event
        if days is not None and (type(days) is not int or days < 0):
            raise ValueError("days_since_similar_event must be a nonnegative integer or None")
        object.__setattr__(self, "reason_codes", tuple(dict.fromkeys(reasons)))


SIGNIFICANCE_CHANNELS = (
    "own_history_abnormality", "market_relative_abnormality",
    "sector_relative_abnormality", "economic_magnitude",
)


@dataclass(frozen=True)
class MaterialityComponents:
    # None explicitly represents an unavailable component, never a fabricated zero.
    significance: float | None
    novelty: float
    confidence: float


@dataclass(frozen=True)
class MaterialityResult:
    candidate: MaterialEventCandidate
    components: MaterialityComponents
    base_score: float | None
    score_version: str = "v0"
    excluded: bool = False
    exclusion_reason: str | None = None
    reason_codes: tuple[str, ...] = ()
