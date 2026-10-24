"""Explicit future-run consent, pricing and resource contracts. No defaults for consent."""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, model_validator

from src.schemas.financial_tools import Digest, ToolModel

Money = Annotated[Decimal, Field(ge=0, le=1000, max_digits=18, decimal_places=10)]
Identifier = Annotated[str, Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,99}$')]


class EvaluationBudget(ToolModel):
    max_requests: int = Field(ge=1, le=100)
    max_input_tokens: int = Field(ge=1, le=4000000)
    max_output_tokens: int = Field(ge=1, le=1000000)
    max_cost_usd: Money
    per_request_input_tokens: int = Field(ge=1, le=65536)
    per_request_output_tokens: int = Field(ge=1, le=16384)


class EgressApproval(ToolModel):
    reference: Identifier
    classification: Literal['synthetic_non_sensitive']
    external_usage_approved: Literal[True]
    dataset_sha256: Digest
    prompt_sha256: Digest
    provider: Identifier
    model: Identifier
    endpoint: str = Field(max_length=2048)
    expires_at: datetime


class LiveEvaluationConfig(ToolModel):
    contract: Literal['woofi-llm-gateway-v1']
    provider: Identifier
    model: Identifier
    endpoint: str = Field(max_length=2048)
    # Reviewed gateway must enforce token/cost caps before billing; no implicit
    # chat, Responses, SDK or tokenizer compatibility is claimed.
    gateway_enforces_hard_limits: Literal[True]
    input_usd_per_million: Money
    output_usd_per_million: Money
    input_token_overhead: int = Field(ge=0, le=8192)
    budget: EvaluationBudget
    approval: EgressApproval

    @model_validator(mode='after')
    def approved_destination(self):
        if any(getattr(self, key) != getattr(self.approval, key) for key in ('provider', 'model', 'endpoint')):
            raise ValueError('approval_destination_mismatch')
        return self


class GatewayReply(ToolModel):
    contract: Literal['woofi-llm-gateway-v1']
    draft: str = Field(max_length=20000)
    input_tokens: int = Field(ge=0, le=65536)
    output_tokens: int = Field(ge=0, le=16384)
    actual_cost_usd: Money
