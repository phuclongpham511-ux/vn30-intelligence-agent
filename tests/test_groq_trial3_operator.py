"""Explicit Trial #3 profile; all provider replies and approvals are synthetic."""
from decimal import Decimal

import pytest

from scripts import groq_trial_operator as operator
from src.services.financial_model_adapter import EvaluationStopped
from test_groq_operator_setup import one_request_config
from test_financial_groq_gateway import setup, run_through


def trial3_config():
    config = one_request_config()
    budget = config.budget
    budget.max_input_tokens = budget.per_request_input_tokens = 5888
    budget.max_output_tokens = budget.per_request_output_tokens = 2048
    budget.max_cost_usd = Decimal('.002112')
    return config


def test_trial3_profile_requires_explicit_selection_without_changing_default(tmp_path):
    path = tmp_path / 'config.json'
    baseline = one_request_config()
    path.write_text(baseline.model_dump_json(), encoding='utf-8')
    assert operator.load_approved_config(path).budget.per_request_output_tokens == 1280
    with pytest.raises(EvaluationStopped):
        operator.load_approved_config(path, trial_profile='trial3-completion')
    path.write_text(trial3_config().model_dump_json(), encoding='utf-8')
    with pytest.raises(EvaluationStopped):
        operator.load_approved_config(path)
    config = operator.load_approved_config(path, trial_profile='trial3-completion')
    assert config.budget.max_requests == 1
    assert config.budget.max_input_tokens + config.budget.max_output_tokens == 7936
    with pytest.raises(EvaluationStopped):
        operator.load_approved_config(path, trial_profile='arbitrary')


@pytest.mark.parametrize('field,value', [
    ('max_requests', 2), ('max_input_tokens', 5889), ('per_request_input_tokens', 5889),
    ('max_output_tokens', 2049), ('per_request_output_tokens', 2049),
    ('max_cost_usd', Decimal('.002113')),
])
def test_trial3_rejects_any_unapproved_budget(tmp_path, field, value):
    config = trial3_config()
    setattr(config.budget, field, value)
    path = tmp_path / 'config.json'
    path.write_text(config.model_dump_json(), encoding='utf-8')
    with pytest.raises(EvaluationStopped, match='one_request_trial'):
        operator.load_approved_config(path, trial_profile='trial3-completion')


def test_trial3_first_case_admission_and_one_request_stop_with_fake_provider(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Trial #3 tests must not access external network')
    monkeypatch.setattr('socket.socket.connect', forbidden)
    monkeypatch.setattr('socket.create_connection', forbidden)
    gateway, http, _ = setup(tmp_path, monkeypatch, config=trial3_config(),
        review_changes={'limits': dict(rpm=30, rpd=1000, tpm=8000, tpd=200000)})
    report = run_through(gateway)
    assert len(http.requests) == 1
    assert http.requests[0]['body']['max_completion_tokens'] == 2048
    assert report['outcomes'][0]['case_id'] == 'performance'
    assert report['outcomes'][0]['accepted'] is True
    assert report['stopped_reason'] == 'run_budget_exhausted'
    assert gateway.ledger.state['requests'] == 1
    assert Decimal(gateway.ledger.state['cost_reserved']) == Decimal('.002112')


def test_trial3_cli_explicitly_passes_profile(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(operator, 'run', lambda path, **kwargs: seen.append((path, kwargs)) or 0)
    monkeypatch.setattr('sys.argv', ['groq_trial_operator', '--trial-directory', str(tmp_path),
        '--trial-profile', 'trial3-completion'])
    assert operator.main() == 0
    assert seen == [(tmp_path, {'trial_profile': 'trial3-completion'})]
