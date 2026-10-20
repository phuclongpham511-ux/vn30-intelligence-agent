"""Financial source packets and calculated API contracts; no database models."""
from datetime import datetime
from typing import Literal
from pydantic import Field
from src.schemas.data import DataModel

Frequency = Literal['annual', 'quarterly', 'ttm']
StatementKind = Literal['income', 'balance', 'cash']
FinancialConfidence = Literal['OFFICIAL_VERIFIED', 'RECONCILED', 'SOURCE_REPORTED', 'UNVERIFIED', 'INVALID']
FinancialAccess = Literal['PERSONAL_RESEARCH', 'PUBLIC_DISPLAY_REVIEW_REQUIRED', 'PUBLIC_DISPLAY_APPROVED']


class FinancialLine(DataModel):
    code: str
    name_en: str
    name_vi: str
    parent: str | None = None
    unit: Literal['VND', 'VND/share', 'source_units'] = 'VND'
    value: float | None = None
    raw_value: float | None = None
    semantic_status: Literal['reported', 'conflicted', 'unqualified'] = 'reported'
    source_labels: list[dict[str, str | None]] = Field(default_factory=list)


class FinancialSourceContext(DataModel):
    """Evidence facts, not an issuer filing certification or a rights grant."""
    contract: Literal['financial-source-context-v2'] = 'financial-source-context-v2'
    data_confidence: FinancialConfidence = 'UNVERIFIED'
    access_classification: FinancialAccess = 'PUBLIC_DISPLAY_REVIEW_REQUIRED'
    fiscal_year: int
    fiscal_quarter: int | None = None
    period_start: str | None = None
    period_end: str | None = None
    original_currency: str | None = None
    original_unit: str | None = None
    amount_multiplier: Literal[1, 1000, 1000000, 1000000000] = 1
    unit_evidence: Literal['audited_vci_adapter_contract', 'original_filing'] = 'audited_vci_adapter_contract'
    record_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    audit_status: Literal['unknown'] = 'unknown'
    restatement_status: Literal['unknown'] = 'unknown'
    publication_time_qualified: Literal[False] = False
    display_rights: Literal['unreviewed', 'permitted', 'prohibited'] = 'unreviewed'
    display_rights_reference: str | None = None
    original_metadata: dict = Field(default_factory=dict)


class StatementObservation(DataModel):
    ticker: str
    source: str
    currency: Literal['VND'] = 'VND'
    statement: StatementKind
    period: str = Field(pattern=r'^\d{4}(?:-Q[1-4])?$')
    frequency: Literal['annual', 'quarterly']
    basis: Literal['annual', 'standalone', 'ytd', 'point_in_time', 'unknown']
    consolidation: str | None = None
    source_dates: dict[str, str | None] = Field(default_factory=dict)
    fields: dict[str, float | None]
    field_codes: dict[str, str]
    items: list[FinancialLine]
    diagnostics: list[str] = Field(default_factory=list)
    source_context: FinancialSourceContext | None = None


class StatementReceipt(DataModel):
    statement: StatementKind
    status: Literal['healthy', 'unavailable', 'error']
    observations: list[StatementObservation] = Field(default_factory=list)
    observed_at: datetime
    content_sha256: str | None = None
    source_url: str
    error_type: str | None = None


class FinancialPacket(DataModel):
    ticker: str
    source: str
    source_version: str
    company_type: Literal['CT', 'NH', 'CK', 'BH', 'UNKNOWN'] = 'UNKNOWN'
    profile: Literal['non_financial', 'bank', 'financial_other', 'unknown']
    metadata_sha256: str
    reports: dict[StatementKind, StatementReceipt]
    is_fixture: bool = False


class CalculationEvidence(DataModel):
    formula: str
    inputs: list[dict] = Field(default_factory=list)
    reason: str | None = None


class FinancialStatementResponse(DataModel):
    ticker: str
    source: str
    currency: Literal['VND'] = 'VND'
    statement: StatementKind
    frequency: Literal['annual', 'quarterly']
    rows: list[StatementObservation]
    receipt: StatementReceipt
    metadata_sha256: str
    source_version: str
    is_fixture: bool


class FinancialPeriod(DataModel):
    ticker: str
    source: str
    currency: Literal['VND'] = 'VND'
    period: str = Field(pattern=r'^\d{4}(?:-Q[1-4])?$')
    frequency: Frequency
    values: dict[str, float | None]
    calculations: dict[str, CalculationEvidence]
    statement_periods: dict[str, str]
    publication_date: str | None = None
    consolidation: str | None = None
    is_fixture: bool = False


class FundamentalMetricDisplay(DataModel):
    key: str
    group: Literal['valuation', 'performance', 'profitability', 'health']
    label: str
    unit: Literal['VND', 'VND/share', 'fraction', 'multiple']
    status: Literal['QUALIFIED', 'UNAVAILABLE', 'UNQUALIFIED', 'DEMO']
    value: float | None = None
    formula: str
    reason: str | None = None
    blockers: list[str] = Field(default_factory=list)
    consolidation: str | None = None


class FundamentalSummary(DataModel):
    contract: Literal['fundamental-display-v1'] = 'fundamental-display-v1'
    period: str | None
    frequency: Frequency
    consolidation: str | None
    publication_date: str | None
    metrics: list[FundamentalMetricDisplay]


class FinancialEngineResponse(DataModel):
    display_scope: Literal['public', 'internal_research'] = 'public'
    internal_authorization_reference: str | None = None
    data_engine: Literal['financial-engine-v1'] = 'financial-engine-v1'
    ticker: str
    source: str
    currency: Literal['VND'] = 'VND'
    period_type: Frequency
    profile: str
    rows: list[dict]
    chart_rows: list[dict]
    changes: list[dict]
    statements: dict[str, dict]
    available_period_types: list[Frequency]
    available_statements: list[str]
    source_receipts: list[dict]
    source_version: str
    metadata_sha256: str
    financial_identity_guard: bool
    read_at: datetime
    read_kind: Literal['provider_or_process_cache', 'saved_filing_review'] = 'provider_or_process_cache'
    publication_date: str | None = None
    consolidation: str | None = None
    sector: str | None = None
    industry: str | None = None
    is_fixture: bool = False
    limitations: list[str]
    reconciliations: list[dict] = Field(default_factory=list)
    fundamental_summary: FundamentalSummary | None = None
    research_panels: list[dict] = Field(default_factory=list)
    verification: dict | None = None
