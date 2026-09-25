"""Versioned local evaluation contracts using existing normalized payloads."""
from datetime import date, datetime
from typing import Literal
from pydantic import ConfigDict, Field, model_validator, field_validator
from src.schemas.data import DataModel, MarketBar, TechnicalBar, FundamentalPeriod, NewsItem
from src.materiality.models import MaterialEventCandidate, EventType


class EvaluationModel(DataModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class HistoricalObservation(EvaluationModel):
    ticker: str
    data_type: Literal["market", "benchmark", "fundamental", "news"]
    observation_time: str
    available_at: datetime | None
    source: str
    is_fixture: bool = False
    payload: TechnicalBar | MarketBar | FundamentalPeriod | NewsItem
    availability_basis: Literal["published", "end_of_day_assumption", "unknown"] = "unknown"

    @field_validator("payload", mode="before")
    @classmethod
    def typed_payload(cls, value, info):
        if not isinstance(value, dict):
            return value
        kind = info.data.get("data_type")
        if kind in ("market", "benchmark"):
            model = TechnicalBar if any(k in value for k in ("ma20", "ma50", "rsi14")) else MarketBar
        else:
            model = FundamentalPeriod if kind == "fundamental" else NewsItem
        return model.model_validate(value)

    @model_validator(mode="after")
    def valid_identity(self):
        row = self.payload
        if row.ticker != self.ticker or row.source != self.source:
            raise ValueError("Observation/payload identity mismatch")
        if self.available_at and self.available_at.utcoffset() is None:
            raise ValueError("available_at must be timezone aware")
        if self.data_type in ("market", "benchmark"):
            if not isinstance(row, MarketBar) or self.observation_time != row.date.isoformat():
                raise ValueError("Market observation must match bar date")
            if self.available_at and self.available_at.date() < row.date:
                raise ValueError("Market data available before observation")
        elif self.data_type == "fundamental":
            if not isinstance(row, FundamentalPeriod) or self.observation_time != row.period:
                raise ValueError("Fundamental observation must match annual period")
        elif not isinstance(row, NewsItem) or self.observation_time != row.published_at.isoformat():
            raise ValueError("News observation must match publication")
        if isinstance(row, NewsItem) and row.is_fixture and not self.is_fixture:
            raise ValueError("Fixture provenance cannot be removed")
        if self.available_at is None and self.availability_basis != "unknown":
            raise ValueError("Availability basis requires a timestamp")
        return self


class DatasetManifest(EvaluationModel):
    dataset_version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    created_at: datetime
    source: list[str]
    tickers: list[str]
    benchmark: str | None
    coverage: dict
    adjustment_basis: Literal["adjusted", "raw", "unknown"] = "unknown"
    known_limitations: list[str]
    observation_count: int
    content_sha256: str


class Period(EvaluationModel):
    start: date
    end: date

    @model_validator(mode="after")
    def ordered(self):
        if self.start > self.end:
            raise ValueError("Period start exceeds end")
        return self


class ReplayConfig(EvaluationModel):
    primary_start: date
    calibration_period: Period
    validation_period: Period
    holdout_period: Period
    stress_period: Period | None = None
    lookback_sessions: int = Field(default=252, ge=2)
    min_history: int = Field(default=60, ge=2)
    context_version: Literal["empirical-v0.1"] = "empirical-v0.1"

    @model_validator(mode="after")
    def ordered_splits(self):
        if not (self.primary_start <= self.calibration_period.start <= self.calibration_period.end
                < self.validation_period.start <= self.validation_period.end
                < self.holdout_period.start <= self.holdout_period.end):
            raise ValueError("Chronological splits overlap or precede primary era")
        if self.stress_period and self.stress_period.end >= self.primary_start:
            raise ValueError("Stress period must precede primary era")
        if self.min_history > self.lookback_sessions:
            raise ValueError("min_history exceeds lookback")
        return self

    def split(self, day: date) -> str:
        for name in ("calibration", "validation", "holdout", "stress"):
            period = getattr(self, name + "_period")
            if period and period.start <= day <= period.end:
                return name
        return "unassigned"


class ReplayCase(EvaluationModel):
    case_id: str
    ticker: str
    replay_time: datetime
    event_type: EventType
    category: str
    candidate: MaterialEventCandidate
    significance: float | None
    novelty: float
    confidence: float
    base_score: float | None
    raw_context_features: dict
    normalized_context_features: dict[str, float | None]
    reason_codes: list[str]
    excluded: bool
    exclusion_reason: str | None
    source_provenance: dict
    score_version: str = "v0"
    context_version: str
    split: Literal["calibration", "validation", "holdout", "stress", "unassigned"]


class HumanReview(EvaluationModel):
    case_id: str
    verdict: Literal["approve", "reject", "modify", "uncertain"]
    attention_level: int = Field(ge=0, le=3, strict=True)
    corrected_event_type: EventType | None = None
    review_note: str | None = None
    reviewed_at: datetime
    review_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def aware(self):
        if self.reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must be timezone aware")
        return self
