"""Offline protocol and security tests. The provider transport is always fake."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

from src.services.financial_assistant import DeterministicFinancialModel
from src.services.financial_evaluation import load_dataset, prepare_case, assess_draft
from src.services.financial_model_adapter import EvaluationStopped, json_text, prompt_contract, prompt_digest
from src.services.financial_llm_gateway import GatewayProcessLock, OPENAI_MODELS, RealLLMGateway
from scripts.serve_financial_llm_gateway import BIND_HOST, configured_port

TOKEN = 'test-only-caller-token-that-is-longer-than-32-bytes'


def test_listener_address_is_loopback_and_public_bind_configuration_is_rejected():
    assert BIND_HOST == '127.0.0.1'
    assert configured_port('https://127.0.0.1:8765/evaluate') == 8765
    for endpoint in ('https://0.0.0.0:8765/evaluate', 'https://example.test/evaluate',
        'https://127.0.0.1:8765/other'):
        with pytest.raises(ValueError, match='loopback'):
            configured_port(endpoint)


def test_only_one_gateway_process_can_own_a_run_ledger(tmp_path):
    state = str(tmp_path / 'run' / 'usage.json')
    lock = GatewayProcessLock(state)
    try:
        with pytest.raises(EvaluationStopped, match='already_locked'):
            GatewayProcessLock(state)
    finally:
        lock.close()
    reopened = GatewayProcessLock(state)
    reopened.close()


def make_config(dataset, **overrides):
    input_rate, output_rate = OPENAI_MODELS['gpt-6-luna']
    endpoint = 'https://127.0.0.1:8765/evaluate'
    raw = dict(contract='woofi-llm-gateway-v1', provider='openai', model='gpt-6-luna',
        endpoint=endpoint, gateway_enforces_hard_limits=True,
        input_usd_per_million=str(input_rate), output_usd_per_million=str(output_rate),
        input_token_overhead=4096,
        budget=dict(max_requests=3, max_input_tokens=98304, max_output_tokens=24576,
            max_cost_usd='1', per_request_input_tokens=32768, per_request_output_tokens=8192),
        approval=dict(reference='pilot:2026-10-24', classification='synthetic_non_sensitive',
            external_usage_approved=True, dataset_sha256=dataset.sha256, prompt_sha256=prompt_digest(),
            provider='openai', model='gpt-6-luna', endpoint=endpoint,
            expires_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat()))
    for key, value in overrides.items():
        if key == 'budget': raw['budget'].update(value)
        else: raw[key] = value
    from src.schemas.financial_evaluation import LiveEvaluationConfig
    return LiveEvaluationConfig.model_validate_json(json.dumps(raw))


class FakeProvider:
    def __init__(self, mutate=None):
        self.payloads = []
        self.mutate = mutate

    def send(self, payload):
        self.payloads.append(payload)
        text = DeterministicFinancialModel().generate(payload['input'][1]['content'],
            max_output_tokens=8192)
        response = dict(status='completed', output=[dict(type='message', content=[
            dict(type='output_text', text=text)])], usage=dict(input_tokens=1000, output_tokens=500))
        if self.mutate:
            response = self.mutate(response)
        return json.dumps(response).encode()


def subject(tmp_path, dataset=None, provider=None, **config_changes):
    dataset = dataset or load_dataset()
    fake = provider or FakeProvider()
    gateway = RealLLMGateway(make_config(dataset, **config_changes), TOKEN,
        str(tmp_path / 'usage.json'), provider_transport=fake)
    req_context = next(dataset.approved_contexts())
    request = dict(contract='woofi-llm-gateway-v1', model='gpt-6-luna', prompt=prompt_contract(),
        context=json.loads(req_context), max_input_tokens=32768, max_output_tokens=8192,
        max_cost_usd=str((Decimal(32768) * Decimal('.10') + Decimal(8192) * Decimal('.50')) / 1_000_000))
    return gateway, fake, request


def call(gateway, request, *, token=TOKEN, run_id='pilot:2026-10-24'):
    return gateway.handle(json_text(request).encode(), f'Bearer {token}', run_id)


def test_gateway_returns_contract_reply_and_server_enforces_usage(tmp_path):
    gateway, provider, request = subject(tmp_path)
    reply = json.loads(call(gateway, request))
    assert set(reply) == {'contract', 'draft', 'input_tokens', 'output_tokens', 'actual_cost_usd'}
    assert reply['contract'] == 'woofi-llm-gateway-v1'
    assert reply['input_tokens'] == 1000 and reply['output_tokens'] == 500
    assert Decimal(reply['actual_cost_usd']) == Decimal('.00035')
    assert provider.payloads[0]['store'] is False
    assert provider.payloads[0]['text']['format']['strict'] is True
    assert provider.payloads[0]['model'] == 'gpt-6-luna'
    assert gateway.ledger.state['requests'] == 1


@pytest.mark.parametrize('token,run_id', [(None, 'pilot:2026-10-24'), ('wrong-secret-token-with-more-than-32-bytes', 'pilot:2026-10-24'),
    (TOKEN, 'another-run')])
def test_unauthorized_callers_and_unapproved_run_ids_never_egress(tmp_path, token, run_id):
    gateway, provider, request = subject(tmp_path)
    auth = None if token is None else f'Bearer {token}'
    with pytest.raises(EvaluationStopped):
        gateway.handle(json_text(request).encode(), auth, run_id)
    assert provider.payloads == [] and gateway.ledger.state['requests'] == 0


@pytest.mark.parametrize('change', [
    lambda r: r.update(model='gpt-6.1-sol'),
    lambda r: r.update(max_input_tokens=32769),
    lambda r: r.update(max_output_tokens=8193),
    lambda r: r.update(max_cost_usd='1'),
    lambda r: r.update(private_capture='must-not-egress'),
    lambda r: r.update(prompt={'unapproved': True}),
])
def test_schema_model_token_cost_and_payload_admission_fail_closed(tmp_path, change):
    gateway, provider, request = subject(tmp_path)
    change(request)
    with pytest.raises(EvaluationStopped, match='payload_not_approved'):
        call(gateway, request)
    assert provider.payloads == [] and gateway.ledger.state['requests'] == 0


@pytest.mark.parametrize('mutate', [
    lambda r: b'{invalid-json',
    lambda r: json.dumps({'status': 'completed', 'output': [], 'usage': {'input_tokens': 10, 'output_tokens': 3}}).encode(),
    lambda r: json.dumps({'status': 'completed', 'output': r['output'], 'usage': {}}).encode(),
    lambda r: json.dumps({'status': 'completed', 'output': r['output'], 'usage': {'input_tokens': 40000, 'output_tokens': 3}}).encode(),
    lambda r: json.dumps({'status': 'completed', 'output': r['output'], 'usage': {'input_tokens': 10, 'output_tokens': 9000}}).encode(),
    lambda r: json.dumps({'status': 'incomplete', 'output': r['output'], 'usage': r['usage']}).encode(),
])
def test_invalid_json_wrong_schema_missing_usage_and_token_overruns_stop_run(tmp_path, mutate):
    class Provider:
        def send(self, payload):
            draft = DeterministicFinancialModel().generate(payload['input'][1]['content'], max_output_tokens=8192)
            response = dict(status='completed', output=[dict(type='message', content=[dict(type='output_text', text=draft)])],
                usage=dict(input_tokens=1000, output_tokens=500))
            return mutate(response)
    gateway, provider, request = subject(tmp_path, provider=Provider())
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway, request)
    assert gateway.ledger.state['stopped'] is True
    assert gateway.ledger.state['requests'] == 1
    assert Decimal(gateway.ledger.state['cost_reserved']) > 0


def test_timeout_and_provider_error_are_sanitized_and_not_retried(tmp_path):
    class Timeout:
        calls = 0
        def send(self, payload):
            self.calls += 1
            raise TimeoutError('private/provider details')
    timeout = Timeout()
    gateway, _, request = subject(tmp_path, provider=timeout)
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway, request)
    assert timeout.calls == 1 and gateway.ledger.state['stopped']


def test_hard_request_budget_persists_across_restart(tmp_path):
    dataset = load_dataset()
    config = make_config(dataset, budget={'max_requests': 1})
    state = str(tmp_path / 'usage.json')
    gateway = RealLLMGateway(config, TOKEN, state, provider_transport=FakeProvider())
    request = subject(tmp_path / 'other', dataset)[2]
    call(gateway, request)
    resumed = RealLLMGateway(config, TOKEN, state, provider_transport=FakeProvider())
    with pytest.raises(EvaluationStopped, match='run_budget_exhausted'):
        call(resumed, request)
    assert resumed.ledger.state['requests'] == 1


def test_cost_ceiling_blocks_before_any_provider_call(tmp_path):
    dataset = load_dataset()
    gateway, provider, request = subject(tmp_path, dataset,
        budget={'max_cost_usd': '0.000001'})
    with pytest.raises(EvaluationStopped, match='run_budget_exhausted'):
        call(gateway, request)
    assert provider.payloads == [] and gateway.ledger.state['requests'] == 0


def test_duplicate_request_keys_are_rejected_before_provider(tmp_path):
    gateway, provider, request = subject(tmp_path)
    raw = json_text(request).encode().replace(b'"model":"gpt-6-luna"',
        b'"model":"gpt-6-luna","model":"gpt-6-luna"', 1)
    with pytest.raises(EvaluationStopped, match='payload_not_approved'):
        gateway.handle(raw, f'Bearer {TOKEN}', 'pilot:2026-10-24')
    assert provider.payloads == []


def test_server_refuses_unapproved_provider_prices_and_expired_consent(tmp_path, monkeypatch):
    dataset = load_dataset()
    config = make_config(dataset)
    config.provider = config.approval.provider = 'gemini'
    with pytest.raises(EvaluationStopped, match='provider_model_or_price'):
        RealLLMGateway(config, TOKEN, str(tmp_path / 'provider.json'), provider_transport=FakeProvider())
    config = make_config(dataset)
    config.approval.expires_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(EvaluationStopped, match='approval_invalid'):
        RealLLMGateway(config, TOKEN, str(tmp_path / 'expired.json'), provider_transport=FakeProvider())
    monkeypatch.delenv('WOOFI_OPENAI_API_KEY', raising=False)
    config = make_config(dataset)
    with pytest.raises(EvaluationStopped, match='credential_missing'):
        RealLLMGateway(config, TOKEN, str(tmp_path / 'no-key.json'))


@pytest.mark.parametrize('attack', ['number', 'citation'])
def test_structurally_valid_wrong_financial_numbers_and_fabricated_citations_fail_evaluator(tmp_path, attack):
    dataset = load_dataset()
    case = next(case for case in dataset.cases() if case['id'] == 'annual_growth')
    prepared = prepare_case(case)
    class AdversarialProvider:
        def send(self, payload):
            draft = json.loads(DeterministicFinancialModel().generate(payload['input'][1]['content'],
                max_output_tokens=8192))
            if attack == 'number': draft['answer'] = draft['answer'].replace('1000.0', '9000.0', 1)
            else: draft['evidence_ids'].append('invented-citation')
            output = json.dumps(draft, ensure_ascii=False)
            return json.dumps(dict(status='completed', output=[dict(type='message', content=[
                dict(type='output_text', text=output)])], usage=dict(input_tokens=1000, output_tokens=500))).encode()
    gateway, _, request = subject(tmp_path, dataset, provider=AdversarialProvider())
    from src.services.financial_assistant import model_context
    request['context'] = json.loads(model_context(prepared['intent'], prepared['facts']))
    reply = json.loads(call(gateway, request))
    # Provider schema validity is not evidence validity; V5.15 verifier remains the gate.
    assert not assess_draft(reply['draft'], prepared)['accepted']
