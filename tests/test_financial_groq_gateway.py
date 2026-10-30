"""Groq integration uses synthetic account reviews and fake HTTPS responses only."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import socket
import ssl

import pytest

from src.services.financial_assistant import DeterministicFinancialModel
from src.services.financial_evaluation import evaluate, load_dataset
from src.services.financial_groq_adapter import GROQ_MODEL, GROQ_MODELS
from src.services.financial_llm_gateway import RealLLMGateway
from src.services.financial_model_adapter import (
    EvaluationStopped, SyntheticEgressGate, SyntheticGatewayModel, config_digest, json_text, prompt_contract,
)
from test_financial_llm_gateway import TOKEN, FakeProvider, make_config

KEY = 'synthetic-groq-key-never-valid-for-a-real-provider'


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Groq implementation tests must never connect to a network')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)


def groq_config():
    config = make_config(load_dataset())
    config.provider = config.approval.provider = 'groq'
    config.model = config.approval.model = GROQ_MODEL
    config.input_usd_per_million, config.output_usd_per_million = GROQ_MODELS[GROQ_MODEL]
    config.input_token_overhead = 2048
    b = config.budget
    b.max_requests = 21
    b.per_request_input_tokens, b.per_request_output_tokens = 6656, 1280
    b.max_input_tokens, b.max_output_tokens = 139776, 26880
    b.max_cost_usd = Decimal('.04')
    return config


def review(config, **changes):
    now = datetime.now(timezone.utc)
    value = dict(reference='synthetic-review-fixture', organization='synthetic-free-org',
        plan='free', billing_enabled=False, model_enabled=True, model=GROQ_MODEL,
        credential_sha256=hashlib.sha256(KEY.encode()).hexdigest(), config_sha256=config_digest(config),
        reviewed_at=now.isoformat(), expires_at=(now + timedelta(minutes=30)).isoformat(),
        # Synthetic exception quota permits a fast offline comparison. This is
        # not evidence of any real account's model access or quota.
        limits=dict(rpm=30, rpd=1000, tpm=1000000, tpd=200000))
    value.update(changes)
    return value


class FakeGroqHTTP:
    def __init__(self, *, status=200, mutation=None, raw=None, timeout=False, headers=None):
        self.status, self.mutation, self.raw, self.timeout = status, mutation, raw, timeout
        self.headers = {key.lower(): value for key, value in (headers or {}).items()}
        self.requests = []
        self.connections = []

    def connection(self, host, *, timeout, context):
        self.connections.append((host, timeout, context))
        owner = self
        class Connection:
            def request(self, method, path, body, headers):
                owner.requests.append(dict(method=method, path=path, body=json.loads(body), headers=headers))
            def getresponse(self):
                if owner.timeout:
                    raise TimeoutError('private-provider-text-must-not-leak')
                return self
            @property
            def status(self): return owner.status
            def getheader(self, name, default=None): return owner.headers.get(name.lower(), default)
            def read(self, limit):
                if owner.raw is not None:
                    return owner.raw[:limit]
                payload = owner.requests[-1]['body']
                draft = DeterministicFinancialModel().generate(payload['messages'][1]['content'],
                    max_output_tokens=payload['max_completion_tokens'])
                value = dict(model=GROQ_MODEL, object='chat.completion', service_tier='on_demand',
                    choices=[dict(index=0, finish_reason='stop', message=dict(role='assistant', content=draft))],
                    usage=dict(prompt_tokens=1000, completion_tokens=500, total_tokens=1500))
                if owner.mutation:
                    owner.mutation(value)
                return json_text(value).encode()[:limit]
            def close(self): pass
        return Connection()


def setup(tmp_path, monkeypatch, *, config=None, http=None, review_changes=None):
    config = config or groq_config()
    path = tmp_path / 'account-review.json'
    path.write_text(json.dumps(review(config, **(review_changes or {}))), encoding='utf-8')
    monkeypatch.setenv('WOOFI_GROQ_API_KEY', KEY)
    monkeypatch.setenv('WOOFI_GROQ_FREE_PLAN_REVIEW', str(path))
    http = http or FakeGroqHTTP()
    monkeypatch.setattr('http.client.HTTPSConnection', http.connection)
    gateway = RealLLMGateway(config, TOKEN, str(tmp_path / 'usage.json'))
    return gateway, http, path


def request(config):
    b = config.budget
    ceiling = (b.per_request_input_tokens * config.input_usd_per_million +
        b.per_request_output_tokens * config.output_usd_per_million) / Decimal(1000000)
    return dict(contract=config.contract, model=config.model, prompt=prompt_contract(),
        context=json.loads(next(load_dataset().approved_contexts())),
        max_input_tokens=b.per_request_input_tokens, max_output_tokens=b.per_request_output_tokens,
        max_cost_usd=str(ceiling))


def call(gateway, body=None, token=TOKEN):
    return gateway.handle(json_text(body or request(gateway.config)).encode(),
        f'Bearer {token}', gateway.config.approval.reference)


def test_valid_groq_wire_mapping_contract_tls_and_notional_accounting(tmp_path, monkeypatch):
    gateway, http, _ = setup(tmp_path, monkeypatch)
    reply = json.loads(call(gateway))
    assert set(reply) == {'contract', 'draft', 'input_tokens', 'output_tokens', 'actual_cost_usd'}
    assert reply['contract'] == 'woofi-llm-gateway-v1'
    assert reply['input_tokens'] == 1000 and reply['output_tokens'] == 500
    assert Decimal(reply['actual_cost_usd']) == Decimal('.00045')
    wire = http.requests[0]
    assert wire['path'] == '/openai/v1/chat/completions' and wire['method'] == 'POST'
    assert wire['headers']['Authorization'] == f'Bearer {KEY}'
    assert KEY not in json_text(wire['body'])
    payload = wire['body']
    assert json.loads(payload['messages'][0]['content']) == prompt_contract()
    assert payload['model'] == GROQ_MODEL and payload['max_completion_tokens'] == 1280
    assert payload['response_format']['json_schema']['strict'] is True
    schema = payload['response_format']['json_schema']['schema']
    assert schema['type'] == 'object' and schema['additionalProperties'] is False
    assert set(schema['required']) == set(schema['properties']) == {'answer', 'fact_ids', 'evidence_ids'}
    assert schema['properties']['answer']['type'] == 'string'
    for field in ('fact_ids', 'evidence_ids'):
        assert schema['properties'][field] == {'type': 'array', 'items': {'type': 'string'}}
    assert payload['service_tier'] == 'on_demand' and payload['reasoning_format'] == 'hidden'
    assert payload['reasoning_effort'] == 'low' and not payload['stream']
    assert 'tools' not in payload and 'store' not in payload
    host, timeout, tls = http.connections[0]
    assert host == 'api.groq.com' and timeout == 10
    assert tls.check_hostname and tls.verify_mode == ssl.CERT_REQUIRED
    assert gateway.ledger.state['input_actual'] == 1000


@pytest.mark.parametrize('status,code,category,error_type,error_code,rate_limited', [
    (400, 'groq_request_failed', 'request_rejected', 'invalid_request_error', 'bad_request', False),
    (401, 'groq_authentication_failed', 'authentication', 'authentication_error', 'invalid_api_key', False),
    (403, 'groq_permission_denied', 'permission', 'permission_error', 'insufficient_permissions', False),
    (404, 'groq_request_failed', 'not_found', 'not_found_error', 'model_not_found', False),
    (422, 'groq_request_failed', 'request_rejected', 'unprocessable_entity_error', 'unprocessable_entity', False),
    (429, 'groq_rate_limited', 'rate_limit', 'rate_limit_error', 'rate_limit_exceeded', True),
    (500, 'groq_request_failed', 'provider_server_error', 'server_error', 'unrecognized', False),
    (502, 'groq_request_failed', 'provider_server_error', 'server_error', 'unrecognized', False),
    (503, 'groq_request_failed', 'provider_server_error', 'server_error', 'unrecognized', True),
])
def test_http_errors_persist_allowlisted_diagnostics_and_stop_once_without_retry(
        tmp_path, monkeypatch, status, code, category, error_type, error_code, rate_limited):
    body = json.dumps({'error': {'message': 'secret sk-test-private Bearer private-token',
        'type': error_type, 'code': error_code, 'debug': 'private diagnostic payload'}}).encode()
    headers = {'Retry-After': '7'} if status == 503 else {'X-Private-Header': 'do-not-save'}
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(status=status, raw=body, headers=headers))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway)
    assert len(http.requests) == 1 and gateway.ledger.state['stopped']
    assert gateway.ledger.state['failure_code'] == code
    assert Decimal(gateway.ledger.state['cost_reserved']) == Decimal('.0017664')
    diagnostic = gateway.ledger.state['provider_failure']
    assert diagnostic == {'http_status': status, 'provider_error_type': error_type,
        'provider_error_code': error_code, 'failure_category': category,
        'rate_limit_indicated': rate_limited, 'usage_received': False}
    persisted = (tmp_path / 'usage.json').read_text()
    assert 'secret sk-test-private' not in persisted and 'private-token' not in persisted
    assert 'private diagnostic payload' not in persisted and 'do-not-save' not in persisted
    with pytest.raises(EvaluationStopped):
        call(gateway)
    assert len(http.requests) == 1


@pytest.mark.parametrize('mutation', [
    lambda v: v.pop('usage'),
    lambda v: v['usage'].pop('completion_tokens'),
    lambda v: v['usage'].update(prompt_tokens=True),
    lambda v: v['usage'].update(total_tokens=2000),
    lambda v: v['usage'].update(prompt_tokens=7000, total_tokens=7500),
    lambda v: v['usage'].update(completion_tokens=2000, total_tokens=3000),
    lambda v: v.update(model='openai/gpt-oss-20b'),
    lambda v: v['choices'][0].update(finish_reason='length'),
    lambda v: v['choices'][0]['message'].update(content='{malformed-json'),
    lambda v: v['choices'][0]['message'].update(tool_calls=[{'name': 'private-tool'}]),
])
def test_bad_model_json_or_uncertain_usage_stops_and_retains_budget(tmp_path, monkeypatch, mutation):
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(mutation=mutation))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway)
    assert len(http.requests) == 1 and gateway.ledger.state['stopped']
    assert gateway.ledger.state['usage_missing']
    assert gateway.ledger.state['requests'] == 1


@pytest.mark.parametrize('http', [FakeGroqHTTP(raw=b'{malformed-json'), FakeGroqHTTP(timeout=True)])
def test_malformed_envelope_and_timeout_are_sanitized(tmp_path, monkeypatch, http):
    gateway, http, _ = setup(tmp_path, monkeypatch, http=http)
    with pytest.raises(EvaluationStopped, match='^gateway_provider_failed_run_stopped$'):
        call(gateway)
    assert len(http.requests) == 1 and gateway.ledger.state['stopped']


def test_timeout_diagnostics_are_safe_and_uncertain_reservation_is_retained(tmp_path, monkeypatch):
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(timeout=True))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped') as error:
        call(gateway)
    assert str(error.value) == 'gateway_provider_failed_run_stopped'
    assert len(http.requests) == 1
    assert gateway.ledger.state['provider_failure'] == {
        'http_status': None, 'provider_error_type': None, 'provider_error_code': None,
        'failure_category': 'network_timeout', 'rate_limit_indicated': False, 'usage_received': False}
    assert gateway.ledger.state['in_flight'] and gateway.ledger.state['usage_missing']
    assert Decimal(gateway.ledger.state['cost_reserved']) == Decimal('.0017664')


def test_http_error_usage_signal_does_not_release_uncertain_reservation(tmp_path, monkeypatch):
    body = json.dumps({'error': {'type': 'invalid_request_error', 'code': 'bad_request'},
        'usage': {'prompt_tokens': 7}}).encode()
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(status=400, raw=body))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway)
    assert len(http.requests) == 1
    assert gateway.ledger.state['provider_failure']['usage_received'] is True
    assert gateway.ledger.state['usage_missing'] and gateway.ledger.state['in_flight']
    assert Decimal(gateway.ledger.state['cost_reserved']) == Decimal('.0017664')


def test_json_validation_failure_preserves_safe_code_and_discards_failed_generation(tmp_path, monkeypatch):
    # Reconstructed error envelope, not a retained Trial #2 response body.
    body = json.dumps({'error': {'type': 'invalid_request_error', 'code': 'json_validate_failed',
        'message': 'unapproved provider message', 'failed_generation': 'private failed draft'},
        'usage': {'prompt_tokens': 1275, 'completion_tokens': 1280, 'total_tokens': 2555}}).encode()
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(status=400, raw=body))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway)
    assert gateway.ledger.state['provider_failure'] == {
        'http_status': 400, 'provider_error_type': 'invalid_request_error',
        'provider_error_code': 'json_validate_failed', 'failure_category': 'request_rejected',
        'rate_limit_indicated': False, 'usage_received': True}
    assert gateway.ledger.state['usage_missing'] and gateway.ledger.state['in_flight']
    assert Decimal(gateway.ledger.state['cost_reserved']) == Decimal('.0017664')
    persisted = (tmp_path / 'usage.json').read_text()
    assert 'unapproved provider message' not in persisted and 'private failed draft' not in persisted
    with pytest.raises(EvaluationStopped):
        call(gateway)
    assert len(http.requests) == 1


@pytest.mark.parametrize('scenario', ['truncated_json', 'empty_response', 'missing_property',
    'extra_property', 'wrong_array_type', 'null_answer', 'output_exhaustion', 'reasoning_in_content'])
def test_structured_output_failures_stop_with_full_reservation(tmp_path, monkeypatch, scenario):
    def mutate(value):
        message = value['choices'][0]['message']
        draft = json.loads(message['content'])
        if scenario == 'truncated_json': message['content'] = message['content'][:-1]
        elif scenario == 'empty_response': message['content'] = ''
        elif scenario == 'reasoning_in_content': message['content'] = '<think>synthetic reasoning</think>' + message['content']
        elif scenario == 'output_exhaustion':
            # Even complete-looking JSON cannot override an explicit length finish.
            value['choices'][0]['finish_reason'] = 'length'
            value['usage'].update(completion_tokens=1280, total_tokens=2280)
        else:
            if scenario == 'missing_property': draft.pop('fact_ids')
            elif scenario == 'extra_property': draft['unapproved'] = 'synthetic extra field'
            elif scenario == 'wrong_array_type': draft['evidence_ids'] = [42]
            elif scenario == 'null_answer': draft['answer'] = None
            message['content'] = json_text(draft)
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(mutation=mutate))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway)
    assert gateway.ledger.state['provider_failure']['failure_category'] == 'invalid_response'
    assert gateway.ledger.state['provider_failure']['usage_received'] is True
    assert gateway.ledger.state['stopped'] and gateway.ledger.state['in_flight']
    assert gateway.ledger.state['usage_missing']
    assert gateway.ledger.state['input_reserved'] == 6656
    assert gateway.ledger.state['output_reserved'] == 1280
    assert Decimal(gateway.ledger.state['cost_reserved']) == Decimal('.0017664')
    with pytest.raises(EvaluationStopped):
        call(gateway)
    assert len(http.requests) == 1


def test_complete_json_at_token_cap_counts_reasoning_in_total_without_exposing_it(tmp_path, monkeypatch):
    def mutate(value):
        # Synthetic accounting example, not a tokenizer estimate of fixture text.
        value['usage'].update(prompt_tokens=1275, completion_tokens=1280, total_tokens=2555,
            completion_tokens_details={'reasoning_tokens': 256})
        value['choices'][0]['message']['reasoning'] = 'synthetic reasoning must not be persisted'
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(mutation=mutate))
    reply = json.loads(call(gateway))
    assert reply['output_tokens'] == gateway.ledger.state['output_actual'] == 1280
    assert gateway.ledger.state['provider_receipt'] == {
        'http_status': 200, 'finish_reason': 'stop', 'reasoning_tokens': 256}
    assert Decimal(reply['actual_cost_usd']) == Decimal('.00095925')
    assert not gateway.ledger.state['stopped'] and not gateway.ledger.state['in_flight']
    assert 'synthetic reasoning' not in json_text(reply)
    assert 'synthetic reasoning' not in (tmp_path / 'usage.json').read_text()
    assert len(http.requests) == 1


def test_success_receipt_does_not_invent_missing_reasoning_count(tmp_path, monkeypatch):
    gateway, _, _ = setup(tmp_path, monkeypatch)
    call(gateway)
    assert gateway.ledger.state['provider_receipt'] == {
        'http_status': 200, 'finish_reason': 'stop', 'reasoning_tokens': None}


@pytest.mark.parametrize('count', [True, -1, 501, 'secret-provider-text'])
def test_invalid_reasoning_receipt_stops_without_persisting_untrusted_fields(tmp_path, monkeypatch, count):
    def mutate(value):
        value['usage']['completion_tokens_details'] = {'reasoning_tokens': count}
    gateway, http, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(mutation=mutate))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway)
    assert gateway.ledger.state['stopped'] and gateway.ledger.state['in_flight']
    assert 'provider_receipt' not in gateway.ledger.state
    assert 'secret-provider-text' not in (tmp_path / 'usage.json').read_text()
    assert len(http.requests) == 1


def test_malformed_provider_json_and_missing_usage_have_bounded_diagnostics(tmp_path, monkeypatch):
    malformed, _, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(raw=b'{"api_key":"sk-private"'))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(malformed)
    assert malformed.ledger.state['provider_failure'] == {
        'http_status': 200, 'provider_error_type': None, 'provider_error_code': None,
        'failure_category': 'malformed_response', 'rate_limit_indicated': False, 'usage_received': False}
    assert 'sk-private' not in (tmp_path / 'usage.json').read_text()

    missing_dir = tmp_path / 'missing-usage'; missing_dir.mkdir()
    missing, _, _ = setup(missing_dir, monkeypatch, http=FakeGroqHTTP(mutation=lambda value: value.pop('usage')))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(missing)
    assert missing.ledger.state['provider_failure'] == {
        'http_status': 200, 'provider_error_type': None, 'provider_error_code': None,
        'failure_category': 'usage_missing', 'rate_limit_indicated': False, 'usage_received': False}
    assert missing.ledger.state['in_flight'] and missing.ledger.state['usage_missing']


def test_unrecognized_provider_labels_are_redacted_and_ledger_allowlist_is_strict(tmp_path, monkeypatch):
    body = json.dumps({'error': {'message': 'sk-sensitive-body', 'type': 'Bearer secret-type',
        'code': 'sk-sensitive-code'}}).encode()
    gateway, _, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(status=400, raw=body))
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped'):
        call(gateway)
    diagnostic = gateway.ledger.state['provider_failure']
    assert diagnostic['provider_error_type'] == diagnostic['provider_error_code'] == 'unrecognized'
    persisted_path = tmp_path / 'usage.json'
    persisted = persisted_path.read_text()
    assert 'sk-sensitive' not in persisted and 'Bearer secret-type' not in persisted
    state = json.loads(persisted)
    state['state']['provider_failure']['provider_message'] = 'unapproved persisted field'
    persisted_path.write_text(json.dumps(state), encoding='utf-8')
    with pytest.raises(EvaluationStopped, match='state_invalid'):
        RealLLMGateway(gateway.config, TOKEN, str(persisted_path))


def test_draft_validation_failure_records_received_usage_without_leaking_text(tmp_path, monkeypatch):
    http = FakeGroqHTTP(mutation=lambda value: value['choices'][0]['message'].update(
        content='Bearer private-token malformed draft'))
    gateway, http, _ = setup(tmp_path, monkeypatch, http=http)
    with pytest.raises(EvaluationStopped, match='provider_failed_run_stopped') as error:
        call(gateway)
    assert str(error.value) == 'gateway_provider_failed_run_stopped'
    diagnostic = gateway.ledger.state['provider_failure']
    assert diagnostic == {'http_status': 200, 'provider_error_type': None, 'provider_error_code': None,
        'failure_category': 'invalid_response', 'rate_limit_indicated': False, 'usage_received': True}
    assert 'private-token' not in (tmp_path / 'usage.json').read_text()
    assert len(http.requests) == 1 and gateway.ledger.state['stopped']


@pytest.mark.parametrize('changes', [dict(plan='developer'), dict(billing_enabled=True),
    dict(credential_sha256='0' * 64), dict(config_sha256='0' * 64), dict(model_enabled=False),
    dict(expires_at='2000-01-01T00:00:00Z'),
    dict(expires_at=(datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()),
    dict(limits=dict(rpm=30, rpd=1000, tpm=1000, tpd=200000))])
def test_free_review_blocks_wrong_key_paid_expired_or_insufficient_account_evidence(tmp_path, monkeypatch, changes):
    with pytest.raises(EvaluationStopped, match='free_plan_review_invalid'):
        setup(tmp_path, monkeypatch, review_changes=changes)


def test_missing_credential_or_account_review_cannot_enable_live_transport(tmp_path, monkeypatch):
    monkeypatch.delenv('WOOFI_GROQ_API_KEY', raising=False)
    monkeypatch.delenv('WOOFI_GROQ_FREE_PLAN_REVIEW', raising=False)
    with pytest.raises(EvaluationStopped, match='review_or_credential_missing'):
        RealLLMGateway(groq_config(), TOKEN, str(tmp_path / 'usage.json'))


def test_revoked_review_and_expired_run_are_checked_before_every_request(tmp_path, monkeypatch):
    gateway, http, path = setup(tmp_path, monkeypatch)
    path.unlink()
    with pytest.raises(EvaluationStopped, match='free_plan_review_invalid'):
        call(gateway)
    assert http.requests == [] and gateway.ledger.state['requests'] == 0
    gateway.config.approval.expires_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(EvaluationStopped, match='approval_invalid'):
        call(gateway)
    assert http.requests == []


@pytest.mark.parametrize('change', ['token', 'dataset', 'prompt', 'model'])
def test_caller_or_unapproved_payload_cannot_reach_groq(tmp_path, monkeypatch, change):
    gateway, http, _ = setup(tmp_path, monkeypatch)
    body = request(gateway.config)
    if change == 'dataset': body['context']['private_data'] = 'C:/private/financial.sqlite'
    elif change == 'prompt': body['prompt']['introduction'] = 'unapproved prompt'
    elif change == 'model': body['model'] = 'gpt-6-luna'
    with pytest.raises(EvaluationStopped):
        call(gateway, body, token='wrong-caller' if change == 'token' else TOKEN)
    assert http.requests == [] and gateway.ledger.state['requests'] == 0


def test_provider_model_and_dataset_mismatch_refused_at_startup(tmp_path):
    for field in ('model', 'dataset'):
        config = groq_config()
        if field == 'model': config.model = config.approval.model = 'gpt-6-luna'
        else: config.approval.dataset_sha256 = '0' * 64
        with pytest.raises(EvaluationStopped):
            RealLLMGateway(config, TOKEN, str(tmp_path / f'{field}.json'), provider_transport=FakeProvider())


def test_account_rate_limit_and_spending_cap_block_before_upstream(tmp_path, monkeypatch):
    gateway, http, _ = setup(tmp_path, monkeypatch, review_changes={
        'limits': dict(rpm=30, rpd=1000, tpm=8000, tpd=200000)})
    call(gateway)
    with pytest.raises(EvaluationStopped, match='account_rate_limit'):
        call(gateway)
    assert len(http.requests) == 1 and gateway.ledger.state['requests'] == 1
    config = groq_config()
    config.budget.max_cost_usd = Decimal(0)
    sub = tmp_path / 'zero-budget'
    sub.mkdir()
    gateway, http, _ = setup(sub, monkeypatch, config=config)
    with pytest.raises(EvaluationStopped, match='run_budget_exhausted'):
        call(gateway)
    assert http.requests == []


def test_ledger_rejects_changed_run_config_and_interrupted_request(tmp_path, monkeypatch):
    gateway, http, _ = setup(tmp_path, monkeypatch)
    gateway.ledger.reserve()  # Simulated crash after reservation, before a receipt.
    resumed = RealLLMGateway(gateway.config, TOKEN, str(tmp_path / 'usage.json'))
    with pytest.raises(EvaluationStopped, match='run_budget_exhausted'):
        call(resumed)
    assert http.requests == [] and resumed.ledger.state['usage_missing']
    changed = gateway.config.model_copy(deep=True)
    changed.budget.max_cost_usd += Decimal('.01')
    with pytest.raises(EvaluationStopped, match='state_invalid'):
        RealLLMGateway(changed, TOKEN, str(tmp_path / 'usage.json'))


class GatewayWire:
    def __init__(self, gateway): self.gateway = gateway
    def send(self, endpoint, body):
        return self.gateway.handle(body, f'Bearer {TOKEN}', self.gateway.config.approval.reference)


def run_through(gateway, *, interval=0):
    dataset = load_dataset()
    model = SyntheticGatewayModel(gateway.config, SyntheticEgressGate(dataset),
        operator_enabled=True, egress_authorized=True, transport=GatewayWire(gateway))
    return evaluate(dataset, model=model, real=True,
        output_tokens=gateway.config.budget.per_request_output_tokens, request_interval_seconds=interval)


def test_same_frozen_cases_prompts_host_and_draft_metrics_for_both_fake_providers(tmp_path, monkeypatch):
    gateway, http, _ = setup(tmp_path, monkeypatch)
    groq_report = run_through(gateway)
    config = make_config(load_dataset())
    config.budget.max_requests = 30
    config.budget.max_input_tokens, config.budget.max_output_tokens = 983040, 245760
    openai = RealLLMGateway(config, TOKEN, str(tmp_path / 'openai-usage.json'), provider_transport=FakeProvider())
    openai_report = run_through(openai)
    for key in ('dataset_sha256', 'prompt_sha256', 'host_routing_metrics', 'raw_model_metrics',
            'clean_model_metrics', 'verified_delivery_rate'):
        assert groq_report[key] == openai_report[key]
    assert groq_report['acceptance_pass'] and openai_report['acceptance_pass']
    assert groq_report['usage']['requests'] == len(http.requests) == 21
    assert groq_report['model_configuration']['provider'] == 'groq'
    assert openai_report['model_configuration']['model'] == 'gpt-6-luna'
    assert http.requests[0]['body']['messages'] == openai.provider.payloads[0]['input']
    assert Decimal(groq_report['usage']['actual_cost_usd']) > 0  # Notional tariff, never claimed free invoice.


def test_existing_harness_can_pace_full_free_quota_run_without_sleeping_in_tests(tmp_path, monkeypatch):
    gateway, http, _ = setup(tmp_path, monkeypatch, review_changes={
        'limits': dict(rpm=30, rpd=1000, tpm=8000, tpd=200000)})
    import time
    clock = [time.time()]
    waits = []
    def pause(seconds):
        waits.append(seconds)
        clock[0] += seconds
    monkeypatch.setattr(time, 'time', lambda: clock[0])
    monkeypatch.setattr(time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(time, 'sleep', pause)
    report = run_through(gateway, interval=65)
    assert report['acceptance_pass'] and len(http.requests) == 21
    assert waits == [65] * 20
    assert report['pacing']['scheduled_wait_seconds'] == 1300
    assert all(row['latency_ms'] < 15000 for row in report['outcomes'])


def test_mock_cli_refuses_live_pacing_switch(capsys):
    from scripts.evaluate_financial_llm import run
    assert run(['--request-interval-seconds', '65']) == 2
    assert not capsys.readouterr().out


@pytest.mark.parametrize('attack', ['number', 'citation'])
def test_false_groq_drafts_fail_raw_metrics_while_verified_fallback_stays_correct(tmp_path, monkeypatch, attack):
    def mutation(value):
        draft = json.loads(value['choices'][0]['message']['content'])
        if attack == 'number': draft['answer'] += ' Doanh thu bằng 999999.'
        else: draft['evidence_ids'].append('invented-citation')
        value['choices'][0]['message']['content'] = json_text(draft)
    gateway, _, _ = setup(tmp_path, monkeypatch, http=FakeGroqHTTP(mutation=mutation))
    report = run_through(gateway)
    assert not report['acceptance_pass']
    assert report['clean_model_metrics']['accepted_draft_rate'] == 0
    assert report['verified_delivery_rate'] == 1
