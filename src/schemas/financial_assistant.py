"""Strict local assistant contracts; no model-supplied financial values."""
from typing import Literal

from pydantic import Field

from src.schemas.financial_tools import Digest, Frequency, Period, Ticker, ToolModel, ToolName


class AssistantBudget(ToolModel):
    tool_calls: int = Field(default=2, ge=0, le=2)
    model_calls: int = Field(default=1, ge=0, le=1)
    input_tokens: int = Field(default=32768, ge=1, le=32768)
    output_tokens: int = Field(default=16384, ge=1, le=16384)
    cost_usd: Literal[0] = 0


class AssistantQuestion(ToolModel):
    question: str = Field(min_length=1, max_length=500)
    capture_id: Digest | None = None
    budget: AssistantBudget = Field(default_factory=AssistantBudget)


class QuestionIntent(ToolModel):
    contract: Literal['woofi-vi-financial-intent-v1'] = 'woofi-vi-financial-intent-v1'
    kind: Literal['performance', 'metrics', 'comparison', 'statement']
    ticker: Ticker
    frequency: Frequency
    periods: list[Period] = Field(default_factory=list, max_length=2)
    metrics: list[str] = Field(default_factory=list, max_length=4)
    statement: Literal['income', 'balance', 'cash'] | None = None
    comparison: Literal['yoy', 'qoq'] = 'yoy'


class GroundedFact(ToolModel):
    id: str
    kind: Literal['metric', 'insight', 'statement']
    ticker: str
    source: str
    capture_id: str
    frequency: str
    period: str
    comparison_period: str | None = None
    metric: str | None = None
    statement: str | None = None
    unit: str | None = None
    values: dict[str, float | None] = Field(default_factory=dict)
    formula: str | None = None
    qualification_status: str
    evidence_ids: list[str]
    missing_information: list[str]
    attention_reasons: list[str] = Field(default_factory=list)


class AssistantCitation(ToolModel):
    id: str
    tool: ToolName
    reference: dict


class ModelDraft(ToolModel):
    answer: str = Field(max_length=8192)
    fact_ids: list[str] = Field(min_length=1, max_length=8)
    evidence_ids: list[str] = Field(max_length=80)


class AssistantUsage(ToolModel):
    tool_calls: int = 0
    model_calls: int = 0
    input_token_upper_bound: int = 0
    output_token_upper_bound: int = 0
    cost_usd: Literal[0] = 0


class AssistantAnswer(ToolModel):
    contract: Literal['woofi-local-financial-assistant-v1'] = 'woofi-local-financial-assistant-v1'
    status: Literal['ANSWERED', 'SAFE_FALLBACK', 'REJECTED', 'UNAVAILABLE', 'NEEDS_CAPTURE']
    answer: str
    used_tools: list[ToolName] = Field(default_factory=list)
    facts: list[GroundedFact] = Field(default_factory=list)
    evidence_references: list[AssistantCitation] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=lambda: [
        'Prototype local dùng mock xác định; chưa đánh giá LLM thật.',
        'Chỉ dùng capture đã lưu trong phạm vi nghiên cứu riêng tư; không cấp quyền công bố.',
        'Biến động số liệu không chứng minh nguyên nhân và không phải khuyến nghị đầu tư.',
        'Phạm vi hiểu tiếng Việt còn giới hạn; không hỗ trợ mọi câu hỏi.',
    ])
    intent: QuestionIntent | None = None
    usage: AssistantUsage = Field(default_factory=AssistantUsage)
