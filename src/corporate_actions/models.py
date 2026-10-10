"""Normalized source facts and immutable knowledge-time views; incomplete coverage."""
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Literal
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_serializer, model_validator
from src.schemas.data import DataModel
from src.schemas.stocks import SymbolRequest


def aware_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError('Knowledge timestamps must be timezone aware')
    return value.astimezone(timezone.utc)


class ActionType(StrEnum):
    CASH_DIVIDEND = 'cash_dividend'
    STOCK_DIVIDEND = 'stock_dividend'
    BONUS_SHARES = 'bonus_shares'
    RIGHTS_OFFERING = 'rights_offering'
    ADDITIONAL_ISSUANCE = 'additional_issuance'
    OTHER = 'other'


class ActionModel(DataModel):
    model_config = ConfigDict(frozen=True, extra='forbid', allow_inf_nan=False)


class ActionTerms(ActionModel):
    cash_vnd_per_share: float | None = Field(default=None, ge=0)
    new_shares_per_old: float | None = Field(default=None, ge=0)
    subscription_price_vnd: float | None = Field(default=None, ge=0)


class CorporateActionNotice(ActionModel):
    symbol: str
    action_type: ActionType
    effective_date: date | None = None
    record_date: date | None = None
    payment_date: date | None = None
    announced_at: datetime | None = None
    announced_on: date | None = None  # date precision only, never fabricated midnight
    source: str = Field(min_length=1)
    source_url: str | None = None
    supporting_urls: tuple[str, ...] = ()
    source_id: str | None = None
    component_id: str | None = None
    source_revision: str | None = None
    source_updated_at: datetime | None = None
    source_title: str | None = None
    evidence_text: str | None = Field(default=None, max_length=6000)
    terms: ActionTerms | None = None
    verified: bool = False
    withdrawn: bool = False
    is_fixture: bool = False
    verification_note: str | None = None

    @field_validator('symbol')
    @classmethod
    def normalized_symbol(cls, value):
        return SymbolRequest(ticker=value).symbol

    @model_serializer(mode='wrap')
    def preserve_legacy_shape(self, handler):
        # Absent extensions must not alter legacy content hashes/packet shapes.
        # Explicit nulls in stored WIP remain explicit; source text is unchanged.
        output = handler(self)
        for field in ('source_updated_at', 'source_title', 'evidence_text'):
            if field not in self.model_fields_set:
                output.pop(field, None)
        return output

    @field_validator('announced_at', 'source_updated_at')
    @classmethod
    def announcement_timezone(cls, value):
        return aware_utc(value) if value is not None else None

    @field_validator('source', 'source_id', 'component_id', 'source_revision')
    @classmethod
    def nonempty(cls, value):
        if value is not None and not value.strip():
            raise ValueError('Empty source identity')
        return value.strip() if value is not None else None

    @field_validator('source_url')
    @classmethod
    def public_url(cls, value):
        if value is not None:
            parts = urlsplit(value)
            if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password:
                raise ValueError('Source URL must be an HTTP(S) reference without credentials')
        return value

    @field_validator('supporting_urls')
    @classmethod
    def public_references(cls, values):
        return tuple(cls.public_url(v) for v in values)

    @model_validator(mode='after')
    def provenance(self):
        if not self.source_id and not self.source_url:
            raise ValueError('Source ID or URL required')
        if self.announced_at and self.announced_on:
            raise ValueError('Use one announcement precision: timestamp or source-local date')
        return self


class CorporateActionObservation(CorporateActionNotice):
    observation_id: str
    action_id: str
    observed_at: datetime

    @field_validator('observed_at')
    @classmethod
    def observed_timezone(cls, value):
        return aware_utc(value)


class CorporateActionContext(ActionModel):
    status: Literal['UNKNOWN', 'KNOWN_MATCH'] = 'UNKNOWN'
    as_of: datetime | None = None
    actions: tuple[CorporateActionObservation, ...] = ()
    coverage: Literal['INCOMPLETE'] = 'INCOMPLETE'
    reason: Literal['not_configured', 'not_observed', 'source_unavailable', 'pending_verification', 'verified_exact_session'] = 'not_configured'

    @field_validator('as_of')
    @classmethod
    def cutoff_timezone(cls, value):
        return aware_utc(value) if value is not None else None

    @model_validator(mode='after')
    def valid_matches(self):
        if self.as_of is not None:
            aware_utc(self.as_of)
        if (self.status == 'KNOWN_MATCH') != bool(self.actions):
            raise ValueError('Context status must agree with observed matches')
        if self.actions and (self.as_of is None or any(a.observed_at > self.as_of for a in self.actions)):
            raise ValueError('Context cannot expose future observations')
        if any(not a.verified or a.withdrawn or a.effective_date is None or a.action_type == ActionType.OTHER for a in self.actions):
            raise ValueError('Context requires verified, active, dated action evidence')
        return self


class IngestionResult(ActionModel):
    status: Literal['inserted', 'duplicate', 'revision']
    observation: CorporateActionObservation
