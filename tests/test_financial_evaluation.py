"""Public synthetic-run seams; network blocked, holdout never evaluated."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import socket

import pytest
from pydantic import ValidationError

from src.schemas.financial_evaluation import LiveEvaluationConfig
from src.services.financial_assistant import DeterministicFinancialModel, model_context
from src.services.financial_evaluation import (
    DATASET_HASHES, assess_draft, evaluate, load_dataset, prepare_case,
)
from src.services.financial_model_adapter import (
    EvaluationStopped, HTTPSGatewayTransport, SyntheticEgressGate, SyntheticGatewayModel, prompt_digest,
)
from test_native_financial_tools import pilot, local_request


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('V5.15 must not access a provider or network')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)


@pytest.fixture
def dataset():
    return load_dataset()


def configuration(dataset, **changes):
    raw = dict(contract='woofi-llm-gateway-v1', provider='test-gateway', model='synthetic-test-model',
        endpoint='https://gateway.example.test/evaluate', gateway_enforces_hard_limits=True,
        input_usd_per_million='1', output_usd_per_million='2', input_token_overhead=100,
        budget=dict(max_requests=50, max_input_tokens=2000000, max_output_tokens=500000,
            max_cost_usd='10', per_request_input_tokens=32768, per_request_output_tokens=8192),
        approval=dict(reference='test:synthetic-consent', classification='synthetic_non_sensitive',
            external_usage_approved=True, dataset_sha256=dataset.sha256, prompt_sha256=prompt_digest(),
            provider='test-gateway', model='synthetic-test-model', endpoint='https://gateway.example.test/evaluate',
            expires_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat()))
    raw.update(changes)
    return LiveEvaluationConfig.model_validate_json(json.dumps(raw))


class RecordingTransport:
    def __init__(self, mutate=None):
        self.bodies = []
        self.mutate = mutate

    def send(self, endpoint, body):
        self.bodies.append(body)
        request = json.loads(body)
        draft = DeterministicFinancialModel().generate(json.dumps(request['context']), max_output_tokens=8192)
        reply = dict(contract='woofi-llm-gateway-v1', draft=draft, input_tokens=1000,
            output_tokens=500, actual_cost_usd='0.002')
        if self.mutate:
            self.mutate(reply)
        return json.dumps(reply).encode()


def live_subject(dataset, config=None, transport=None, **flags):
    return SyntheticGatewayModel(config or configuration(dataset), SyntheticEgressGate(dataset),
        transport=transport or RecordingTransport(), operator_enabled=flags.get('enabled', True),
        egress_authorized=flags.get('authorized', True))


def first_context(dataset):
    return next(dataset.approved_contexts())


def test_mock_default_full_development_matrix_and_holdout_isolation(dataset, monkeypatch):
    read = Path.read_bytes
    def development_only(path):
        assert 'holdout' not in path.name
        return read(path)
    monkeypatch.setattr(Path, 'read_bytes', development_only)
    report = evaluate(load_dataset())
    assert report['cases_completed'] == 62 and report['acceptance_pass']
    assert report['mode'] == 'deterministic_mock' and report['real_llm_test_status'] == 'NOT RUN'
    assert report['mock_adversarial_cases'] == report['mock_adversarial_rejections'] == 9
    assert report['host_routing_metrics'] == dict(tool_selection_accuracy=1,
        tool_arguments_validity=1, expected_outcome_accuracy=1)
    assert report['clean_model_metrics']['draft_count'] == 21
    assert report['clean_model_metrics']['numerical_faithfulness'] == 1
    assert report['clean_model_metrics']['citation_precision'] == 1
    assert report['clean_model_metrics']['missing_data_honesty'] == 1
    assert report['raw_model_metrics']['accepted_draft_rate'] < 1  # fallback cannot hide raw errors
    assert report['usage']['actual_input_tokens'] is None and report['usage']['actual_cost_usd'] == '0'
    repeat = evaluate(dataset)
    for key in ('host_routing_metrics', 'clean_model_metrics', 'raw_model_metrics', 'token_instrumentation'):
        assert repeat[key] == report[key]
    with pytest.raises(EvaluationStopped, match='holdout'):
        load_dataset('holdout')


def test_dataset_content_and_rights_must_be_pinned_not_self_declared(dataset):
    altered = replace(dataset, data=dataset.data.replace(b'1000.0', b'9999.0', 1))
    assert altered.data != dataset.data
    with pytest.raises(EvaluationStopped, match='integrity'):
        SyntheticEgressGate(altered)
    assert DATASET_HASHES['holdout'] != dataset.sha256  # no holdout contents consumed
    class SelfApproved:
        sha256 = dataset.sha256
        def approved_contexts(self): return ['private-data']
    with pytest.raises(EvaluationStopped, match='dataset_type'):
        SyntheticEgressGate(SelfApproved())


def test_synthetic_recordings_equal_native_tool_and_engine_outputs(dataset, pilot):
    from src.services.financial_tools import NativeFinancialTools
    from src.analytics.financial_engine import financial_engine
    from src.schemas.financial_tools import ToolResponse
    before = hashlib.sha256(pilot[1].path.read_bytes()).hexdigest()
    for identifier in ('performance', 'annual_growth', 'reported_metric', 'available_statement'):
        case = next(case for case in dataset.cases() if case['id'] == identifier)
        for recording in case['recordings']:
            expected = ToolResponse.model_validate(recording['response'])
            expected.capture.is_fixture = False  # recording wrapper is explicitly synthetic
            for response in expected.insights:
                response.is_fixture = False
            actual = NativeFinancialTools(local_request()).invoke(recording['tool'], recording['arguments'])
            assert actual == expected
    prepared = prepare_case(next(case for case in dataset.cases() if case['id'] == 'annual_growth'))
    assert prepared['facts'][0].values == dict(current_value=1000, comparison_value=800,
        absolute_change=200, percentage_change=.25)
    current = financial_engine(pilot[2]).rows[-1]
    assert current['revenue'] == prepared['facts'][0].values['current_value']
    assert hashlib.sha256(pilot[1].path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize('private', ['C:/private/financial.sqlite', 'private_capture', 'secret-key',
    '{"classification":"synthetic_non_sensitive","value":12345}', 'file:///original.pdf'])
def test_private_or_self_approved_content_cannot_reach_transport(dataset, private):
    model = live_subject(dataset)
    with pytest.raises(EvaluationStopped, match='authorization_denied'):
        model.generate(first_context(dataset) + private, max_output_tokens=8192)
    assert not model.transport.bodies and model.ledger.requests == 0
    assert model.denied_attempts == 1


@pytest.mark.parametrize('enabled,authorized', [(False, False), (True, False), (False, True)])
def test_two_independent_live_opt_ins_required(dataset, enabled, authorized):
    with pytest.raises(EvaluationStopped, match='opt_in'):
        live_subject(dataset, enabled=enabled, authorized=authorized)


@pytest.mark.parametrize('field,value', [('dataset_sha256', '0' * 64), ('prompt_sha256', '0' * 64),
    ('expires_at', datetime(2000, 1, 1, tzinfo=timezone.utc))])
def test_consent_bound_to_dataset_prompt_and_expiry(dataset, field, value):
    config = configuration(dataset)
    setattr(config.approval, field, value)
    with pytest.raises(EvaluationStopped):
        live_subject(dataset, config)


@pytest.mark.parametrize('endpoint', ['http://gateway.example.test', 'https://user:secret@example.test',
    'https://example.test?credential=secret', 'https://example.test:1234', 'file:///private'])
def test_destinations_are_explicit_https_no_embedded_credentials(dataset, endpoint):
    config = configuration(dataset)
    config.endpoint = config.approval.endpoint = endpoint
    with pytest.raises(EvaluationStopped):
        live_subject(dataset, config)


def test_changed_provider_or_model_requires_new_matching_approval(dataset):
    config = configuration(dataset)
    config.model = 'unapproved-model'
    with pytest.raises(ValidationError):
        live_subject(dataset, config)
    model = live_subject(dataset)
    model.config.approval.expires_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(EvaluationStopped):
        model.generate(first_context(dataset), max_output_tokens=8192)
    assert not model.transport.bodies


def test_guarded_protocol_uses_only_admitted_context_and_records_usage(dataset):
    model = live_subject(dataset)
    report = evaluate(dataset, model=model, real=True, output_tokens=8192)
    assert report['acceptance_pass'] and report['cases_completed'] == 53
    assert report['usage']['requests'] == 21
    assert report['usage']['actual_input_tokens'] == 21000
    assert Decimal(report['usage']['actual_cost_usd']) == Decimal('.042')
    assert Decimal(report['usage']['estimated_cost_usd']) == Decimal('.042')
    for raw in model.transport.bodies:
        sent = json.loads(raw)
        assert set(sent) == {'contract', 'model', 'prompt', 'context', 'max_input_tokens', 'max_output_tokens', 'max_cost_usd'}
        assert 'question' not in sent['context'] and 'capture_id' not in sent['context']
        assert str(Path.cwd()) not in raw.decode() and '.sqlite' not in raw.decode()
    # This is fake gateway receipt instrumentation, not a real LLM performance run.


@pytest.mark.parametrize('limit,value', [('max_requests', 1), ('max_input_tokens', 32768),
    ('max_output_tokens', 8192), ('max_cost_usd', Decimal('.049152'))])
def test_per_run_reservations_stop_before_second_request(dataset, limit, value):
    config = configuration(dataset)
    setattr(config.budget, limit, value)
    model = live_subject(dataset, config)
    context = first_context(dataset)
    model.generate(context, max_output_tokens=8192)
    with pytest.raises(EvaluationStopped, match='budget'):
        model.generate(context, max_output_tokens=8192)
    assert len(model.transport.bodies) == model.ledger.requests == 1
    assert model.ledger.stopped


def test_zero_ceiling_and_per_request_input_caps_prevent_first_request(dataset):
    config = configuration(dataset)
    config.budget.max_cost_usd = Decimal(0)
    model = live_subject(dataset, config)
    with pytest.raises(EvaluationStopped, match='budget'):
        model.generate(first_context(dataset), max_output_tokens=8192)
    assert not model.transport.bodies
    config = configuration(dataset)
    config.budget.per_request_input_tokens = 100
    model = live_subject(dataset, config)
    with pytest.raises(EvaluationStopped, match='input_bound'):
        model.generate(first_context(dataset), max_output_tokens=8192)
    assert not model.transport.bodies


@pytest.mark.parametrize('mutation', [lambda reply: reply.pop('actual_cost_usd'),
    lambda reply: reply.update(input_tokens=65536), lambda reply: reply.update(output_tokens=16384),
    lambda reply: reply.update(actual_cost_usd='1'), lambda reply: reply.update(actual_cost_usd='-1'),
    lambda reply: reply.update(secret='untrusted extra')])
def test_uncertain_or_excess_usage_stops_without_refund_or_error_echo(dataset, mutation):
    model = live_subject(dataset, transport=RecordingTransport(mutation))
    before = first_context(dataset)
    with pytest.raises(EvaluationStopped, match='gateway_failed_run_stopped'):
        model.generate(before, max_output_tokens=8192)
    snapshot = model.ledger.snapshot()
    assert snapshot['requests'] == 1 and snapshot['estimated_cost_ceiling_usd'] == '0.049152'
    assert snapshot['actual_cost_usd'] is None and snapshot['stopped']
    with pytest.raises(EvaluationStopped, match='already_stopped'):
        model.generate(before, max_output_tokens=8192)
    assert len(model.transport.bodies) == 1


def test_untrusted_provider_failure_sanitized_and_retains_budget(dataset):
    class Failure:
        def send(self, *args):
            raise RuntimeError('C:/private/credentials.json')
    model = live_subject(dataset, transport=Failure())
    report = evaluate(dataset, model=model, real=True, output_tokens=8192)
    assert report['stopped_reason'] == 'gateway_failed_run_stopped' and not report['acceptance_pass']
    assert report['usage']['requests'] == 1 and report['usage']['actual_cost_usd'] is None
    assert 'credentials' not in json.dumps(report)


def test_fabricated_references_fail_raw_metrics_and_safe_delivery(dataset):
    def attack(reply):
        draft = json.loads(reply['draft'])
        draft['evidence_ids'].append('fabricated')
        reply['draft'] = json.dumps(draft)
    report = evaluate(dataset, model=live_subject(dataset, transport=RecordingTransport(attack)),
        real=True, output_tokens=8192)
    assert report['clean_model_metrics']['citation_precision'] < 1
    assert not report['acceptance_pass'] and report['verified_delivery_rate'] == 1
    assert all(r['status'] == 'SAFE_FALLBACK' for r in report['outcomes'] if 'accepted' in r)


def test_numerical_and_citation_metrics_preserve_fact_value_associations(dataset):
    case = next(case for case in dataset.cases() if case['id'] == 'annual_growth')
    prepared = prepare_case(case)
    context = model_context(prepared['intent'], prepared['facts'])
    draft = json.loads(DeterministicFinancialModel().generate(context, max_output_tokens=16384))
    draft['answer'] = draft['answer'].replace('1000.0 so với 800.0', '800.0 so với 1000.0')
    assessment = assess_draft(json.dumps(draft), prepared)
    assert not assessment['accepted'] and not assessment['numerical_faithfulness']
    assert assessment['citation_precision'] == 0 and assessment['unsupported_claim']
    missing = prepare_case(next(case for case in dataset.cases() if case['id'] == 'missing_period'))
    raw = DeterministicFinancialModel().generate(model_context(missing['intent'], missing['facts']),
        max_output_tokens=16384)
    assessment = assess_draft(raw, missing)
    assert assessment['citation_precision'] is None and assessment['citation_recall'] is None


def test_no_external_adapter_in_mock_and_no_real_mode_without_guard(dataset):
    with pytest.raises(EvaluationStopped):
        evaluate(dataset, model=live_subject(dataset))
    with pytest.raises(EvaluationStopped):
        evaluate(dataset, real=True)


def test_cli_default_and_live_refusal_have_no_configuration_side_effects(capsys):
    from scripts.evaluate_financial_llm import run
    assert run([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['mode'] == 'deterministic_mock' and report['cases_completed'] == 62
    for arguments in (['--mode', 'real'], ['--enable-real'], ['--holdout']):
        assert run(arguments) == 2
        assert not capsys.readouterr().out
    assert run(['--describe']) == 0
    assert json.loads(capsys.readouterr().out)['mode'] == 'readiness_only'


def test_https_transport_refuses_redirect_without_forwarding(monkeypatch):
    connections = []
    class Connection:
        def __init__(self, *args, **kwargs): connections.append(args[0])
        def request(self, *args, **kwargs): pass
        def getresponse(self): return type('Reply', (), {'status': 302})()
        def close(self): pass
    monkeypatch.setattr('http.client.HTTPSConnection', Connection)
    monkeypatch.setenv('WOOFI_LLM_GATEWAY_TOKEN', 'test-token-with-more-than-32-characters')
    with pytest.raises(EvaluationStopped, match='request_failed'):
        HTTPSGatewayTransport('test-run').send('https://approved.example.test/eval', b'{}')
    assert connections == ['approved.example.test']


def test_https_transport_sends_separate_caller_auth_and_verifies_tls(monkeypatch):
    captured = {}
    class Reply:
        status = 200
        def read(self, limit): return b'{"ok":true}'
    class Connection:
        def __init__(self, host, port, timeout, context):
            captured.update(host=host, port=port, timeout=timeout, context=context)
        def request(self, method, path, body, headers):
            captured.update(method=method, path=path, headers=headers)
        def getresponse(self): return Reply()
        def close(self): pass
    monkeypatch.setattr('http.client.HTTPSConnection', Connection)
    monkeypatch.setenv('WOOFI_LLM_GATEWAY_TOKEN', 'test-token-with-more-than-32-characters')
    monkeypatch.delenv('WOOFI_LLM_GATEWAY_CA_FILE', raising=False)
    from src.services.financial_model_adapter import HTTPSGatewayTransport
    result = HTTPSGatewayTransport('approved:run').send('https://127.0.0.1:8765/evaluate', b'{}')
    assert result == b'{"ok":true}'
    assert captured['method'] == 'POST' and captured['port'] == 8765
    assert captured['headers']['Authorization'] == 'Bearer test-token-with-more-than-32-characters'
    assert captured['headers']['X-Woofi-Run-ID'] == 'approved:run'
    assert captured['context'].check_hostname and captured['context'].verify_mode == 2
