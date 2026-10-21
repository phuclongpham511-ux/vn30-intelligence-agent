"""Versioned facts for offline ingestion and compatible industry comparisons."""
from datetime import date
from typing import Literal
from pydantic import AwareDatetime, Field, model_validator
from src.schemas.data import DataModel
from src.schemas.financials import Frequency


class MetricObservation(DataModel):
    ticker: str = Field(pattern=r'^[A-Z0-9]{1,20}$')
    metric_id: str = Field(pattern=r'^[a-z][a-z0-9_]{0,79}$')
    value: float | None
    unit: Literal['VND','VND/share','shares','fraction','multiple']
    currency: Literal['VND'] = 'VND'
    period: str = Field(pattern=r'^\d{4}(?:-Q[1-4])?$')
    period_start: date | None = None
    period_end: date | None = None
    period_type: Frequency
    fiscal_year: int = Field(ge=1900,le=2200)
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    report_scope: Literal['consolidated','standalone','unknown']
    source: str = Field(min_length=1,max_length=200)
    published_at: AwareDatetime | None = None
    fetched_at: AwareDatetime
    revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    formula_version: str = 'woofi-financial-intelligence-v1'
    metric_kind: Literal['reported','derived','estimated','unavailable']
    quality_status: Literal['QUALIFIED','UNQUALIFIED','UNAVAILABLE','DEMO','INVALID','CONFLICT','ESTIMATED']
    quality_reasons: list[str] = Field(default_factory=list)
    formula: str
    profile: Literal['non_financial','bank','financial_other','unknown']
    company_type: Literal['CT','NH','CK','BH','UNKNOWN']
    is_fixture: bool = False
    input_refs: list[dict] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def no_numeric_coercion(cls,data):
        if isinstance(data,dict) and data.get('value') is not None and type(data['value']) not in (int,float):
            raise ValueError('Metric values must be JSON numbers, never booleans or strings')
        return data

    @model_validator(mode='after')
    def coherent_fact(self):
        if (self.metric_kind=='estimated') != (self.quality_status=='ESTIMATED'):
            raise ValueError('Estimates require a distinct status and cannot become qualified facts')
        quarter = int(self.period[-1]) if '-Q' in self.period else None
        if self.fiscal_year != int(self.period[:4]) or self.fiscal_quarter != quarter:
            raise ValueError('Fiscal labels do not match the source period')
        if (self.period_type == 'annual') != (quarter is None):
            raise ValueError('Incompatible frequency and period')
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError('Reversed fiscal boundaries')
        if self.quality_status in ('UNQUALIFIED','UNAVAILABLE','INVALID','CONFLICT') and self.value is not None:
            raise ValueError('Blocked observations cannot contain a display value')
        if self.quality_status == 'QUALIFIED' and (self.is_fixture or self.report_scope == 'unknown' or self.value is None):
            raise ValueError('Unqualified fact cannot be marked qualified')
        if self.quality_status == 'DEMO' and not self.is_fixture:
            raise ValueError('Fixture status requires fixture evidence')
        return self


class MetricSeriesResponse(DataModel):
    contract: Literal['financial-metrics-v1'] = 'financial-metrics-v1'
    ticker: str
    frequency: Frequency
    observations: list[MetricObservation]
    point_in_time_qualified: Literal[False] = False
    limitations: list[str] = Field(default_factory=list)


class IndustryDefinition(DataModel):
    id: str = Field(pattern=r'^[a-z0-9][a-z0-9_-]{0,63}$')
    name_en: str
    name_vi: str
    model: Literal['non_financial','bank','securities','insurance','real_estate']


class IndustryMembership(DataModel):
    ticker: str = Field(pattern=r'^[A-Z0-9]{1,20}$')
    industry_id: str
    effective_from: date
    effective_to: date | None = None
    source_reference: str = Field(min_length=1)


class IndustryTaxonomy(DataModel):
    contract: Literal['woofi-industry-taxonomy-v1'] = 'woofi-industry-taxonomy-v1'
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    industries: list[IndustryDefinition] = Field(max_length=200)
    memberships: list[IndustryMembership] = Field(max_length=10000)

    @model_validator(mode='after')
    def unambiguous_memberships(self):
        identifiers = [i.id for i in self.industries]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError('Duplicate industry definition')
        grouped = {}
        for member in self.memberships:
            if member.industry_id not in identifiers or member.effective_to and member.effective_to < member.effective_from:
                raise ValueError('Invalid industry membership')
            for before in grouped.setdefault(member.ticker, []):
                if member.effective_from <= (before.effective_to or date.max) and before.effective_from <= (member.effective_to or date.max):
                    raise ValueError('Overlapping industry memberships')
            grouped[member.ticker].append(member)
        return self
