"""Groq wire adapter. Live use requires a fresh, key-bound Free-plan review."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import http.client
import os
from pathlib import Path
import ssl
from typing import Literal

from pydantic import Field

from src.schemas.financial_tools import Digest, ToolModel
from src.services.financial_model_adapter import EvaluationStopped, config_digest, json_text

GROQ_MODEL = 'openai/gpt-oss-120b'
# Official Standard text prices reviewed 2026-10-24, not an assertion of free eligibility.
GROQ_MODELS = {GROQ_MODEL: (Decimal('0.15'), Decimal('0.60'))}


class GroqAccountLimits(ToolModel):
    rpm: int = Field(ge=1, le=100000)
    rpd: int = Field(ge=1, le=1000000)
    tpm: int = Field(ge=1, le=10000000)
    tpd: int = Field(ge=1, le=100000000)


class GroqFreePlanReview(ToolModel):
    reference: str = Field(min_length=1, max_length=100)
    organization: str = Field(min_length=1, max_length=100)
    plan: Literal['free']
    billing_enabled: Literal[False]
    model_enabled: Literal[True]
    model: Literal['openai/gpt-oss-120b']
    credential_sha256: Digest
    config_sha256: Digest
    reviewed_at: datetime
    expires_at: datetime
    limits: GroqAccountLimits


class GroqChatTransport:
    """One HTTPS POST, no SDK retries, automatic tier selection, tools or fallback.

    The local review is operator evidence, not an online account-plan lookup.
    Groq provides no per-request free-only billing flag. An organization upgrade
    outside this process cannot be detected from ordinary inference responses.
    """
    def __init__(self, config, api_key, review_path, *, timeout=10):
        self.config = config.model_copy(deep=True)
        self._api_key = api_key
        self._review_path = Path(review_path)
        self.timeout = timeout
        self.preflight()

    @classmethod
    def from_environment(cls, config):
        key = os.environ.get('WOOFI_GROQ_API_KEY', '')
        review = os.environ.get('WOOFI_GROQ_FREE_PLAN_REVIEW', '')
        if not key or not review:
            raise EvaluationStopped('groq_free_plan_review_or_credential_missing')
        return cls(config, key, review)

    def preflight(self):
        # Re-read on each request so expiry or local revocation takes effect.
        from src.services.financial_llm_gateway import _strict_json
        try:
            with self._review_path.open('rb') as handle:
                raw = handle.read(16385)
            if len(raw) > 16384:
                raise ValueError
            _strict_json(raw)
            review = GroqFreePlanReview.model_validate_json(raw)
            now = datetime.now(timezone.utc)
            if (review.reviewed_at.tzinfo is None or review.expires_at.tzinfo is None or
                    not review.reviewed_at <= now < review.expires_at or
                    review.expires_at > review.reviewed_at + timedelta(hours=1) or
                    review.credential_sha256 != hashlib.sha256(self._api_key.encode()).hexdigest() or
                    review.config_sha256 != config_digest(self.config) or
                    self.config.provider != 'groq' or self.config.model != GROQ_MODEL):
                raise ValueError
            limits, budget = review.limits, self.config.budget
            if (budget.max_requests > limits.rpd or
                    budget.max_input_tokens + budget.max_output_tokens > limits.tpd or
                    budget.per_request_input_tokens + budget.per_request_output_tokens > limits.tpm):
                raise ValueError
            return limits.model_dump()
        except Exception:
            raise EvaluationStopped('groq_free_plan_review_invalid') from None

    def send(self, payload):
        from src.services.financial_llm_gateway import MAX_PROVIDER_RESPONSE_BYTES, _strict_json
        self.preflight()
        if payload['model'] != GROQ_MODEL:
            raise EvaluationStopped('groq_model_not_approved')
        schema = payload['text']['format']
        body = json_text(dict(model=GROQ_MODEL, messages=payload['input'],
            max_completion_tokens=payload['max_output_tokens'], stream=False, n=1,
            reasoning_effort='low', reasoning_format='hidden', service_tier='on_demand',
            response_format=dict(type='json_schema', json_schema=dict(
                name=schema['name'], strict=True, schema=schema['schema'])))).encode()
        if len(body) + self.config.input_token_overhead > self.config.budget.per_request_input_tokens:
            raise EvaluationStopped('groq_serialized_input_bound_exceeded')
        connection = http.client.HTTPSConnection('api.groq.com', timeout=self.timeout,
            context=ssl.create_default_context())
        try:
            connection.request('POST', '/openai/v1/chat/completions', body=body, headers={
                'Authorization': f'Bearer {self._api_key}', 'Content-Type': 'application/json',
                'Accept': 'application/json'})
            response = connection.getresponse()
            if response.status != 200:
                code = {401: 'groq_authentication_failed', 403: 'groq_permission_denied',
                    429: 'groq_rate_limited'}.get(response.status, 'groq_request_failed')
                raise EvaluationStopped(code)
            raw = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
            if len(raw) > MAX_PROVIDER_RESPONSE_BYTES:
                raise EvaluationStopped('groq_response_size_limit')
            value = _strict_json(raw)
            if (value.get('model') != GROQ_MODEL or value.get('object') != 'chat.completion' or
                    value.get('service_tier', 'on_demand') not in ('on_demand', 'default') or
                    value.get('error') is not None):
                raise ValueError
            choices = value['choices']
            if len(choices) != 1 or choices[0].get('index') != 0 or choices[0].get('finish_reason') != 'stop':
                raise ValueError
            message = choices[0]['message']
            if (message.get('role') != 'assistant' or not isinstance(message.get('content'), str) or
                    message.get('tool_calls') or message.get('function_call') or message.get('refusal')):
                raise ValueError
            usage = value['usage']
            tokens = [usage.get(key) for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')]
            if (any(type(count) is not int or count < 0 for count in tokens) or
                    tokens[0] + tokens[1] != tokens[2]):
                raise ValueError
            # Completion usage includes generated reasoning. Do not count only visible JSON.
            return json_text(dict(status='completed', model=GROQ_MODEL,
                output=[dict(type='message', content=[dict(type='output_text', text=message['content'])])],
                usage=dict(input_tokens=tokens[0], output_tokens=tokens[1]))).encode()
        finally:
            connection.close()
