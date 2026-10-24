"""Bounded native tool contracts. Capture selection is mandatory and immutable."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.financial_intelligence import FinancialInsightsResponse
from src.schemas.financials import FinancialLine, StatementKind

Ticker = Annotated[str, Field(pattern=r'^[A-Z0-9]{1,20}$')]
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Period = Annotated[str, Field(pattern=r'^(?:19|20|21)\d{2}(?:-Q[1-4])?$')]
Metric = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]{0,79}$')]
Frequency = Literal['annual', 'quarterly']
ToolName = Literal['get_financial_statements', 'get_financial_metrics', 'get_financial_insights']


class ToolModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class CaptureRequest(ToolModel):
    ticker: Ticker
    capture_id: Digest
    frequency: Frequency
    periods: list[Period] | None = Field(default=None, min_length=1, max_length=4)

    @model_validator(mode='after')
    def period_selection(self):
        if self.periods is not None and (len(set(self.periods)) != len(self.periods)
                or any(('-Q' in p) != (self.frequency == 'quarterly') for p in self.periods)):
            raise ValueError('Choose distinct periods matching frequency')
        return self


class StatementsRequest(CaptureRequest):
    statement: StatementKind


class MetricsRequest(CaptureRequest):
    metrics: list[Metric] = Field(min_length=1, max_length=8)

    @model_validator(mode='after')
    def distinct_metrics(self):
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError('Choose distinct metrics')
        return self


class InsightsRequest(MetricsRequest):
    comparison: Literal['yoy', 'qoq'] = 'yoy'

    @model_validator(mode='after')
    def supported_comparison(self):
        if self.frequency == 'annual' and self.comparison == 'qoq':
            raise ValueError('Annual QoQ is unsupported')
        return self


class CaptureReference(ToolModel):
    ticker: str
    source: str
    source_version: str
    capture_id: Digest
    capture_sha256: Digest
    packet_sha256: Digest
    is_fixture: bool


class EvidenceReference(ToolModel):
    """Allowlisted lineage; no raw metadata, private paths or document text."""
    capture_id: Digest
    capture_sha256: Digest
    packet_sha256: Digest
    source: str
    statement: str
    period: str
    field: str | None = None
    code: str | None = None
    value: float | None = None
    currency: str = 'VND'
    scope: str | None = None
    basis: str | None = None
    content_sha256: str | None = None
    record_sha256: str | None = None
    document_sha256: str | None = None
    original_unit: str | None = None
    amount_multiplier: int | None = None
    period_start: str | None = None
    period_end: str | None = None
    page: int | None = None


class StatementFact(ToolModel):
    period: str
    frequency: Frequency
    scope: str | None
    basis: str
    currency: str
    lines: list[FinancialLine]
    line_evidence: list[EvidenceReference]
    evidence: EvidenceReference
    qualification_status: Literal['SOURCE_REPORTED', 'UNQUALIFIED', 'WITHHELD']
    missing_information: list[str]


class MetricFact(ToolModel):
    period: str
    metric: str
    value: float | None
    unit: str
    formula: str | None
    qualification_status: str
    display_eligible: bool
    verification_dimensions: dict[str, bool]
    evidence_references: list[EvidenceReference]
    missing_information: list[str]


class ToolResponse(ToolModel):
    contract: Literal['woofi-native-financial-tools-v1'] = 'woofi-native-financial-tools-v1'
    data_engine: Literal['financial-engine-v1'] = 'financial-engine-v1'
    tool: ToolName
    display_scope: Literal['internal_research'] = 'internal_research'
    public_display_activated: Literal[False] = False
    capture: CaptureReference
    frequency: Frequency
    selected_periods: list[str]
    available_periods: list[str]
    missing_information: list[str]
    statements: list[StatementFact] = Field(default_factory=list)
    metrics: list[MetricFact] = Field(default_factory=list)
    insights: list[FinancialInsightsResponse] = Field(default_factory=list)


class ScriptedQuestion(ToolModel):
    question: str = Field(min_length=1, max_length=300)
    tool: ToolName
    arguments: dict


class ScriptedAnswer(ToolModel):
    question: str
    result: ToolResponse
    explanation: Literal['Saved evidence only. Missing information limits conclusions; numerical movements do not establish causes or investment recommendations.'] = 'Saved evidence only. Missing information limits conclusions; numerical movements do not establish causes or investment recommendations.'
