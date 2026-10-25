"""Groq wire adapter. Live use requires a fresh, key-bound Free-plan review."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import http.client
import os
from pathlib import Path
import socket
import ssl
from typing import Literal

from pydantic import Field

from src.schemas.financial_tools import Digest, ToolModel
from src.services.financial_model_adapter import EvaluationStopped, config_digest, json_text

GROQ_MODEL = 'openai/gpt-oss-120b'
# Official Standard text prices reviewed 2026-10-24, not an assertion of free eligibility.
GROQ_MODELS = {GROQ_MODEL: (Decimal('0.15'), Decimal('0.60'))}

PROVIDER_ERROR_TYPES = frozenset({
    'invalid_request_error', 'authentication_error', 'permission_error', 'rate_limit_error',
    'server_error', 'not_found_error', 'unprocessable_entity_error', 'api_error', 'unrecognized',
})
PROVIDER_ERROR_CODES = frozenset({
    'bad_request', 'invalid_request', 'invalid_api_key', 'insufficient_permissions',
    'model_not_found', 'unprocessable_entity', 'rate_limit_exceeded', 'rate_limit_reached',
    'context_length_exceeded', 'token_limit_exceeded', 'insufficient_quota', 'request_too_large',
    'json_validate_failed', 'unrecognized',
})
FAILURE_CATEGORIES = frozenset({
    'authentication', 'permission', 'rate_limit', 'request_rejected', 'not_found',
    'provider_server_error', 'unexpected_http_status', 'transport_error', 'network_timeout',
    'malformed_response', 'invalid_response', 'provider_error_response', 'response_too_large',
    'usage_missing', 'usage_invalid', 'provider_response',
})
FAILURE_DIAGNOSTIC_FIELDS = frozenset({
    'http_status', 'provider_error_type', 'provider_error_code', 'failure_category',
    'rate_limit_indicated', 'usage_received',
})
RATE_LIMIT_CODES = frozenset({'rate_limit_exceeded', 'rate_limit_reached', 'token_limit_exceeded'})
GROQ_FAILURE_CODES = frozenset({
    'groq_authentication_failed', 'groq_permission_denied', 'groq_rate_limited',
    'groq_request_failed', 'groq_network_timeout', 'groq_transport_failed',
    'groq_response_invalid', 'groq_usage_missing', 'groq_usage_invalid',
    'groq_response_size_limit', 'groq_free_plan_review_invalid',
})


def validate_failure_diagnostics(value):
    """Return a copy of the strict, non-sensitive provider diagnostic allowlist."""
    if not isinstance(value, dict) or set(value) != FAILURE_DIAGNOSTIC_FIELDS:
        raise ValueError('invalid_groq_failure_diagnostics')
    status = value['http_status']
    if status is not None and (type(status) is not int or not 100 <= status <= 599):
        raise ValueError('invalid_groq_failure_diagnostics')
    if value['provider_error_type'] is not None and (type(value['provider_error_type']) is not str or
            value['provider_error_type'] not in PROVIDER_ERROR_TYPES):
        raise ValueError('invalid_groq_failure_diagnostics')
    if value['provider_error_code'] is not None and (type(value['provider_error_code']) is not str or
            value['provider_error_code'] not in PROVIDER_ERROR_CODES):
        raise ValueError('invalid_groq_failure_diagnostics')
    if type(value['failure_category']) is not str or value['failure_category'] not in FAILURE_CATEGORIES:
        raise ValueError('invalid_groq_failure_diagnostics')
    if type(value['rate_limit_indicated']) is not bool or type(value['usage_received']) is not bool:
        raise ValueError('invalid_groq_failure_diagnostics')
    return {key: value[key] for key in (
        'http_status', 'provider_error_type', 'provider_error_code', 'failure_category',
        'rate_limit_indicated', 'usage_received')}


class GroqProviderFailure(EvaluationStopped):
    """Stable failure code plus strictly allowlisted diagnostic metadata."""
    def __init__(self, code, diagnostics):
        if code not in GROQ_FAILURE_CODES:
            code = 'groq_request_failed'
        super().__init__(code)
        self.diagnostics = validate_failure_diagnostics(diagnostics)


def _safe_provider_label(value, allowed):
    if value is None:
        return None
    return value if type(value) is str and value in allowed else 'unrecognized'


def _error_labels(raw):
    error_type, error_code, _ = _error_details(raw)
    return error_type, error_code


def _error_details(raw):
    try:
        from src.services.financial_llm_gateway import _strict_json
        value = _strict_json(raw)
        error = value.get('error') if isinstance(value, dict) else None
        if not isinstance(error, dict):
            return None, None, bool(isinstance(value, dict) and isinstance(value.get('usage'), dict))
        return (_safe_provider_label(error.get('type'), PROVIDER_ERROR_TYPES - {'unrecognized'}),
            _safe_provider_label(error.get('code'), PROVIDER_ERROR_CODES - {'unrecognized'}),
            isinstance(value.get('usage'), dict))
    except Exception:
        return None, None, False


def _rate_limit_signal(response, status, error_code):
    if status == 429 or error_code in RATE_LIMIT_CODES:
        return True
    getheader = getattr(response, 'getheader', None)
    if getheader is None:
        return False
    try:
        return any(getheader(name) not in (None, '') for name in (
            'Retry-After', 'X-RateLimit-Limit-Requests', 'X-RateLimit-Limit-Tokens',
            'X-RateLimit-Remaining-Requests', 'X-RateLimit-Remaining-Tokens',
            'X-RateLimit-Reset-Requests', 'X-RateLimit-Reset-Tokens'))
    except Exception:
        return False


def _http_failure(status):
    if status == 401:
        return 'groq_authentication_failed', 'authentication'
    if status == 403:
        return 'groq_permission_denied', 'permission'
    if status == 429:
        return 'groq_rate_limited', 'rate_limit'
    if status in (400, 413, 422):
        return 'groq_request_failed', 'request_rejected'
    if status == 404:
        return 'groq_request_failed', 'not_found'
    if 500 <= status <= 599:
        return 'groq_request_failed', 'provider_server_error'
    return 'groq_request_failed', 'unexpected_http_status'


def _diagnostics(*, status=None, error_type=None, error_code=None, category,
        rate_limited=False, usage_received=False):
    return validate_failure_diagnostics(dict(http_status=status, provider_error_type=error_type,
        provider_error_code=error_code, failure_category=category,
        rate_limit_indicated=rate_limited, usage_received=usage_received))


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
        status = None
        try:
            try:
                connection.request('POST', '/openai/v1/chat/completions', body=body, headers={
                    'Authorization': f'Bearer {self._api_key}', 'Content-Type': 'application/json',
                    'Accept': 'application/json'})
                response = connection.getresponse()
                status = response.status
            except (TimeoutError, socket.timeout):
                raise GroqProviderFailure('groq_network_timeout', _diagnostics(category='network_timeout')) from None
            except (OSError, http.client.HTTPException):
                raise GroqProviderFailure('groq_transport_failed', _diagnostics(category='transport_error')) from None

            if status != 200:
                try:
                    error_raw = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
                    error_type, error_code, usage_received = (_error_details(error_raw)
                        if len(error_raw) <= MAX_PROVIDER_RESPONSE_BYTES else (None, None, False))
                except Exception:
                    error_type, error_code, usage_received = None, None, False
                code, category = _http_failure(status)
                raise GroqProviderFailure(code, _diagnostics(status=status, error_type=error_type,
                    error_code=error_code, category=category,
                    rate_limited=_rate_limit_signal(response, status, error_code),
                    usage_received=usage_received))

            try:
                raw = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
            except (TimeoutError, socket.timeout):
                raise GroqProviderFailure('groq_network_timeout',
                    _diagnostics(status=status, category='network_timeout')) from None
            except (OSError, http.client.HTTPException):
                raise GroqProviderFailure('groq_transport_failed',
                    _diagnostics(status=status, category='transport_error')) from None
            if len(raw) > MAX_PROVIDER_RESPONSE_BYTES:
                raise GroqProviderFailure('groq_response_size_limit',
                    _diagnostics(status=status, category='response_too_large'))
            try:
                value = _strict_json(raw)
            except Exception:
                raise GroqProviderFailure('groq_response_invalid',
                    _diagnostics(status=status, category='malformed_response')) from None
            if not isinstance(value, dict):
                raise GroqProviderFailure('groq_response_invalid',
                    _diagnostics(status=status, category='invalid_response'))

            usage = value.get('usage')
            usage_received = isinstance(usage, dict)
            error_type, error_code = _error_labels(raw)
            rate_limited = _rate_limit_signal(response, status, error_code)
            if value.get('error') is not None:
                raise GroqProviderFailure('groq_response_invalid', _diagnostics(status=status,
                    error_type=error_type, error_code=error_code, category='provider_error_response',
                    rate_limited=rate_limited, usage_received=usage_received))
            if (value.get('model') != GROQ_MODEL or value.get('object') != 'chat.completion' or
                    value.get('service_tier', 'on_demand') not in ('on_demand', 'default')):
                raise GroqProviderFailure('groq_response_invalid', _diagnostics(status=status,
                    category='invalid_response', rate_limited=rate_limited, usage_received=usage_received))
            if not usage_received:
                raise GroqProviderFailure('groq_usage_missing', _diagnostics(status=status,
                    category='usage_missing', rate_limited=rate_limited))
            tokens = [usage.get(key) for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')]
            if (any(type(count) is not int or count < 0 for count in tokens) or
                    tokens[0] + tokens[1] != tokens[2]):
                raise GroqProviderFailure('groq_usage_invalid', _diagnostics(status=status,
                    category='usage_invalid', rate_limited=rate_limited, usage_received=True))
            try:
                choices = value['choices']
                if len(choices) != 1 or choices[0].get('index') != 0 or choices[0].get('finish_reason') != 'stop':
                    raise ValueError
                message = choices[0]['message']
                if (message.get('role') != 'assistant' or not isinstance(message.get('content'), str) or
                        message.get('tool_calls') or message.get('function_call') or message.get('refusal')):
                    raise ValueError
            except Exception:
                raise GroqProviderFailure('groq_response_invalid', _diagnostics(status=status,
                    category='invalid_response', rate_limited=rate_limited, usage_received=True)) from None
            # Completion usage includes generated reasoning. Do not count only visible JSON.
            metadata = _diagnostics(status=status, category='provider_response',
                rate_limited=rate_limited, usage_received=True)
            return json_text(dict(status='completed', model=GROQ_MODEL,
                output=[dict(type='message', content=[dict(type='output_text', text=message['content'])])],
                usage=dict(input_tokens=tokens[0], output_tokens=tokens[1]),
                diagnostics=metadata)).encode()
        finally:
            connection.close()
