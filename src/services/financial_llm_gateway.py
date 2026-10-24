"""Minimal provider-backed HTTPS gateway for the V5.15 synthetic-only contract."""
from datetime import datetime, timezone
from decimal import Decimal
import hmac
import json
import os
import threading
import time

from src.schemas.financial_assistant import ModelDraft
from src.schemas.financial_evaluation import GatewayReply, LiveEvaluationConfig
from src.services.financial_model_adapter import EvaluationStopped, config_digest, json_text, prompt_contract, prompt_digest
from src.services.financial_evaluation import DATASET_HASHES
from src.services.financial_groq_adapter import GROQ_MODELS, GroqChatTransport


# Standard text rates, USD per million tokens, reviewed from official model pages 2026-10-24.
OPENAI_MODELS = {
    'gpt-6-luna': (Decimal('0.10'), Decimal('0.50')),
    'gpt-6.1-sol': (Decimal('1.00'), Decimal('5.00')),
}
PROVIDER_MODELS = {'openai': OPENAI_MODELS, 'groq': GROQ_MODELS}
MAX_REQUEST_BYTES = 65536
MAX_PROVIDER_RESPONSE_BYTES = 131072
MIN_PROVIDER_INPUT_OVERHEAD = 2048


def _cost(input_tokens, output_tokens, input_rate, output_rate):
    return (Decimal(input_tokens) * input_rate + Decimal(output_tokens) * output_rate) / Decimal(1_000_000)


def _strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def _strict_model_draft_schema():
    # Keep to the JSON Schema subset accepted by Structured Outputs. Pydantic
    # applies the remaining length and array constraints after the response.
    return {'type': 'object', 'additionalProperties': False,
        'properties': {'answer': {'type': 'string'},
            'fact_ids': {'type': 'array', 'items': {'type': 'string'}},
            'evidence_ids': {'type': 'array', 'items': {'type': 'string'}}},
        'required': ['answer', 'fact_ids', 'evidence_ids']}


class OpenAIResponsesTransport:
    """Single bounded HTTPS call; injectable fake transport is used by tests."""
    def __init__(self, api_key, *, timeout=30):
        self.api_key = api_key
        self.timeout = timeout

    def send(self, payload):
        import http.client
        import ssl
        connection = http.client.HTTPSConnection('api.openai.com', timeout=self.timeout,
            context=ssl.create_default_context())
        try:
            connection.request('POST', '/v1/responses', body=json_text(payload).encode(), headers={
                'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json',
                'Accept': 'application/json'})
            response = connection.getresponse()
            if response.status != 200:
                raise EvaluationStopped('provider_request_failed')
            data = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
            if len(data) > MAX_PROVIDER_RESPONSE_BYTES:
                raise EvaluationStopped('provider_response_size_limit')
            return data
        finally:
            connection.close()


class GatewayUsageLedger:
    """Process-persistent reservation ledger; one gateway process owns a run."""
    def __init__(self, config, state_path):
        self.config = config
        self.config_sha256 = config_digest(config)
        self.path = state_path
        self.lock = threading.RLock()
        self.state = dict(requests=0, input_reserved=0, output_reserved=0,
            cost_reserved='0', input_actual=0, output_actual=0, actual_cost_usd='0',
            stopped=False, usage_missing=False, in_flight=False, request_times=[])
        if os.path.exists(self.path):
            try:
                with open(self.path, 'rb') as handle:
                    raw = handle.read(16385)
                if len(raw) > 16384:
                    raise ValueError
                saved = _strict_json(raw)
                if (saved.get('run_id') != config.approval.reference or
                        saved.get('config_sha256') != self.config_sha256):
                    raise ValueError
                self.state.update(saved['state'])
                b, s = config.budget, self.state
                if (any(type(s[key]) is not int or s[key] < 0 for key in (
                        'requests', 'input_reserved', 'output_reserved', 'input_actual', 'output_actual')) or
                        any(type(s[key]) is not bool for key in ('stopped', 'usage_missing', 'in_flight')) or
                        s['input_reserved'] != s['requests'] * b.per_request_input_tokens or
                        s['output_reserved'] != s['requests'] * b.per_request_output_tokens or
                        Decimal(s['cost_reserved']) != s['requests'] * _cost(b.per_request_input_tokens,
                            b.per_request_output_tokens, config.input_usd_per_million, config.output_usd_per_million) or
                        not Decimal(0) <= Decimal(s['actual_cost_usd']) <= Decimal(s['cost_reserved']) or
                        s['input_actual'] > s['input_reserved'] or s['output_actual'] > s['output_reserved'] or
                        not isinstance(s['request_times'], list) or len(s['request_times']) != s['requests'] or
                        any(type(stamp) not in (int, float) or not 0 < stamp <= time.time()
                            for stamp in s['request_times'])):
                    raise ValueError
                if s['in_flight']:
                    s.update(stopped=True, usage_missing=True)
                    self.save()  # Never resume an interrupted, possibly billed request.
            except Exception:
                raise EvaluationStopped('gateway_state_invalid') from None

    def save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        temp = self.path + '.tmp'
        data = json.dumps({'run_id': self.config.approval.reference,
            'config_sha256': self.config_sha256, 'state': self.state},
            sort_keys=True, separators=(',', ':')).encode()
        with open(temp, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)

    def reserve(self, account_limits=None):
        c, b, s = self.config, self.config.budget, self.state
        now = time.time()
        if account_limits is not None:
            minute = sum(stamp > now - 60 for stamp in s['request_times']) + 1
            day = sum(stamp > now - 86400 for stamp in s['request_times']) + 1
            per_request_tokens = b.per_request_input_tokens + b.per_request_output_tokens
            if (any(stamp > now for stamp in s['request_times']) or
                    minute > account_limits['rpm'] or day > account_limits['rpd'] or
                    minute * per_request_tokens > account_limits['tpm'] or
                    day * per_request_tokens > account_limits['tpd']):
                s['stopped'] = True
                self.save()
                raise EvaluationStopped('gateway_account_rate_limit')
        amount = _cost(b.per_request_input_tokens, b.per_request_output_tokens,
            c.input_usd_per_million, c.output_usd_per_million)
        if (s['stopped'] or s['requests'] + 1 > b.max_requests
                or s['input_reserved'] + b.per_request_input_tokens > b.max_input_tokens
                or s['output_reserved'] + b.per_request_output_tokens > b.max_output_tokens
                or Decimal(s['cost_reserved']) + amount > b.max_cost_usd):
            s['stopped'] = True
            self.save()
            raise EvaluationStopped('gateway_run_budget_exhausted')
        s['requests'] += 1
        s['input_reserved'] += b.per_request_input_tokens
        s['output_reserved'] += b.per_request_output_tokens
        s['cost_reserved'] = str(Decimal(s['cost_reserved']) + amount)
        s['in_flight'] = True
        s['request_times'].append(now)
        self.save()  # Reserve the full worst-case amount before billable egress.
        return amount


class GatewayProcessLock:
    """Exclusive owner for a run ledger; stale locks require operator review."""
    def __init__(self, state_path):
        os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
        self.path = state_path + '.lock'
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(self.fd, str(os.getpid()).encode())
            os.fsync(self.fd)
        except FileExistsError:
            raise EvaluationStopped('gateway_run_already_locked') from None

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass


class RealLLMGateway:
    """Validates only V5.15-pinned development contexts before provider egress."""
    def __init__(self, config, caller_token, state_path, provider_transport=None):
        self.config = LiveEvaluationConfig.model_validate(config).model_copy(deep=True)
        self._token = caller_token
        self._check_config()
        self.ledger = GatewayUsageLedger(self.config, state_path)
        if provider_transport is not None:
            self.provider = provider_transport
        elif self.config.provider == 'groq':
            self.provider = GroqChatTransport.from_environment(self.config)
        else:
            if not os.environ.get('WOOFI_OPENAI_API_KEY'):
                raise EvaluationStopped('gateway_provider_credential_missing')
            self.provider = OpenAIResponsesTransport(os.environ['WOOFI_OPENAI_API_KEY'], timeout=30)

    def _check_config(self):
        c = LiveEvaluationConfig.model_validate(self.config.model_dump())
        rates = PROVIDER_MODELS.get(c.provider, {}).get(c.model)
        if (rates is None or
                (c.input_usd_per_million, c.output_usd_per_million) != rates):
            raise EvaluationStopped('gateway_provider_model_or_price_not_approved')
        if not self._token or len(self._token) < 32:
            raise EvaluationStopped('gateway_caller_token_invalid')
        if c.input_token_overhead < MIN_PROVIDER_INPUT_OVERHEAD:
            raise EvaluationStopped('gateway_input_overhead_too_small')
        if (c.approval.classification != 'synthetic_non_sensitive' or
                c.approval.dataset_sha256 != DATASET_HASHES['development'] or
                c.approval.prompt_sha256 != prompt_digest() or
                c.approval.expires_at.tzinfo is None or
                c.approval.expires_at <= datetime.now(timezone.utc)):
            raise EvaluationStopped('gateway_approval_invalid')
        if not 1 <= c.budget.max_requests <= 100:
            raise EvaluationStopped('gateway_request_cap_invalid')

    def handle(self, raw, authorization, run_id):
        if not isinstance(authorization, str) or not authorization.startswith('Bearer '):
            raise EvaluationStopped('gateway_unauthorized')
        if not hmac.compare_digest(authorization[7:], self._token):
            raise EvaluationStopped('gateway_unauthorized')
        if not isinstance(raw, bytes) or not raw or len(raw) > MAX_REQUEST_BYTES:
            raise EvaluationStopped('gateway_request_size_invalid')
        if run_id != self.config.approval.reference:
            raise EvaluationStopped('gateway_run_not_approved')
        self._check_config()
        try:
            request = _strict_json(raw)
            if not isinstance(request, dict) or set(request) != {'contract', 'model', 'prompt', 'context',
                    'max_input_tokens', 'max_output_tokens', 'max_cost_usd'}:
                raise ValueError
            if request['contract'] != self.config.contract or request['model'] != self.config.model:
                raise ValueError
            if request['prompt'] != prompt_contract():
                raise ValueError
            if type(request['max_input_tokens']) is not int or type(request['max_output_tokens']) is not int:
                raise ValueError
            b, c = self.config.budget, self.config
            if (request['max_input_tokens'] != b.per_request_input_tokens or
                    request['max_output_tokens'] != b.per_request_output_tokens or
                    request['max_output_tokens'] > 16384):
                raise ValueError
            ceiling = _cost(b.per_request_input_tokens, b.per_request_output_tokens,
                c.input_usd_per_million, c.output_usd_per_million)
            if type(request['max_cost_usd']) is not str or Decimal(request['max_cost_usd']) != ceiling:
                raise ValueError
            context_json = json_text(request['context'])
            from src.services.financial_evaluation import load_dataset
            dataset = load_dataset('development')  # Holdout path is unreachable here.
            if dataset.sha256 != c.approval.dataset_sha256 or context_json not in set(dataset.approved_contexts()):
                raise ValueError
            serialized = json_text(request).encode('utf-8')
            # UTF-8 byte length is a conservative token upper bound; overhead is
            # separately operator-approved. OpenAI also enforces output tokens.
            if len(serialized) + c.input_token_overhead > b.per_request_input_tokens:
                raise ValueError
        except Exception:
            raise EvaluationStopped('gateway_payload_not_approved') from None

        with self.ledger.lock:
            self._check_config()  # A waiting request must not outlive consent.
            if config_digest(self.config) != self.ledger.config_sha256:
                raise EvaluationStopped('gateway_run_configuration_changed')
            limits = self.provider.preflight() if c.provider == 'groq' else None
            reserved = self.ledger.reserve(limits)
            try:
                provider_payload = {'model': c.model, 'store': False,
                    'reasoning': {'effort': 'none'},
                    'input': [{'role': 'system', 'content': json_text(request['prompt'])},
                        {'role': 'user', 'content': json_text(request['context'])}],
                    'max_output_tokens': b.per_request_output_tokens,
                    'text': {'format': {'type': 'json_schema', 'name': 'model_draft',
                        'strict': True, 'schema': _strict_model_draft_schema()}}}
                if len(json_text(provider_payload).encode()) + c.input_token_overhead > b.per_request_input_tokens:
                    raise EvaluationStopped('provider_serialized_input_bound_exceeded')
                started = time.perf_counter()
                raw_reply = self.provider.send(provider_payload)
                if not isinstance(raw_reply, bytes) or len(raw_reply) > MAX_PROVIDER_RESPONSE_BYTES:
                    raise ValueError
                provider_reply = _strict_json(raw_reply)
                usage = provider_reply.get('usage')
                if not isinstance(usage, dict):
                    self.ledger.state['usage_missing'] = True
                    raise ValueError
                input_tokens, output_tokens = usage.get('input_tokens'), usage.get('output_tokens')
                if (type(input_tokens) is not int or type(output_tokens) is not int or
                        input_tokens < 0 or output_tokens < 0 or
                        input_tokens > b.per_request_input_tokens or output_tokens > b.per_request_output_tokens):
                    raise ValueError
                if provider_reply.get('status') != 'completed':
                    raise ValueError
                texts = [item.get('text') for item in provider_reply.get('output', [])
                    if item.get('type') == 'message' for item in item.get('content', [])
                    if item.get('type') == 'output_text']
                if len(texts) != 1:
                    raise ValueError
                draft = ModelDraft.model_validate_json(texts[0])
                actual_cost = _cost(input_tokens, output_tokens, *PROVIDER_MODELS[c.provider][c.model])
                if actual_cost > reserved or actual_cost > Decimal(request['max_cost_usd']):
                    raise ValueError
                reply = GatewayReply(contract=c.contract, draft=draft.model_dump_json(),
                    input_tokens=input_tokens, output_tokens=output_tokens, actual_cost_usd=actual_cost)
                self.ledger.state['input_actual'] += input_tokens
                self.ledger.state['output_actual'] += output_tokens
                self.ledger.state['actual_cost_usd'] = str(
                    Decimal(self.ledger.state['actual_cost_usd']) + actual_cost)
                self.ledger.state['last_latency_ms'] = round((time.perf_counter() - started) * 1000, 3)
                self.ledger.state['in_flight'] = False
                self.ledger.save()
                return reply.model_dump_json().encode()
            except Exception as error:
                # Any uncertain provider outcome retains its full reservation and
                # closes the run. There is no retry or model fallback.
                self.ledger.state['stopped'] = True
                self.ledger.state['usage_missing'] = True
                code = str(error) if isinstance(error, EvaluationStopped) else ''
                if code in {'groq_authentication_failed', 'groq_permission_denied', 'groq_rate_limited',
                        'groq_request_failed', 'groq_response_size_limit', 'groq_free_plan_review_invalid'}:
                    self.ledger.state['failure_code'] = code
                self.ledger.save()
                raise EvaluationStopped('gateway_provider_failed_run_stopped') from None
