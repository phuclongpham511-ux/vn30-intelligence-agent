"""Candidate C is explicitly selected; all transport responses are manufactured."""
import json
import socket

import pytest

from src.services.financial_evaluation import load_dataset, evaluate
from src.services.financial_model_adapter import (
    EvaluationStopped, SyntheticEgressGate, SyntheticGatewayModel, config_digest,
    prompt_contract, prompt_digest,
)
from src.services.financial_llm_gateway import RealLLMGateway
from test_groq_trial3_operator import trial3_config
from test_financial_groq_gateway import KEY, FakeGroqHTTP, GatewayWire, review
from test_financial_llm_gateway import TOKEN

CANDIDATE = 'candidate-c-v1'


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail('Trial #4 preparation must remain offline')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)


def test_candidate_is_explicit_and_preserves_default_schema_and_dataset():
    assert prompt_digest() == '69a55678664e5d40f9fd52e886f7520adbfa2a264825abec2b16a6838f3b9a87'
    candidate = prompt_contract(CANDIDATE)
    assert candidate['output_schema'] == prompt_contract()['output_schema']
    assert candidate['introduction'] == prompt_contract()['introduction']
    assert prompt_digest(CANDIDATE) != prompt_digest()
    assert prompt_digest(CANDIDATE) == 'ae26989e80bd9bdb21724efd7b9e8238548b696d7a2a9a330001856fcd429c22'
    assert load_dataset().sha256 == '40638a706ecaf922e6e7d2646a969b0a6e61331532854696146c33cbc2e01e6a'
    for selection in ('arbitrary', None):
        with pytest.raises(EvaluationStopped): prompt_contract(selection)


def test_old_approval_cannot_enable_candidate_and_default_refuses_candidate_approval():
    c = trial3_config()
    gate = SyntheticEgressGate(load_dataset())
    with pytest.raises(EvaluationStopped):
        SyntheticGatewayModel(c, gate, operator_enabled=True, egress_authorized=True, prompt_variant=CANDIDATE)
    c.approval.prompt_sha256 = prompt_digest(CANDIDATE)
    with pytest.raises(EvaluationStopped):
        SyntheticGatewayModel(c, gate, operator_enabled=True, egress_authorized=True)


def test_candidate_first_case_passes_real_admission_with_fake_groq_and_stops_once(tmp_path, monkeypatch):
    c = trial3_config()
    c.approval.reference = 'trial4-offline-synthetic-fixture'
    c.approval.prompt_sha256 = prompt_digest(CANDIDATE)
    review_path = tmp_path / 'synthetic-review.json'
    review_path.write_text(json.dumps(review(c)), encoding='utf-8')
    monkeypatch.setenv('WOOFI_GROQ_API_KEY', KEY)
    monkeypatch.setenv('WOOFI_GROQ_FREE_PLAN_REVIEW', str(review_path))
    http = FakeGroqHTTP()
    monkeypatch.setattr('http.client.HTTPSConnection', http.connection)
    gateway = RealLLMGateway(c, TOKEN, str(tmp_path/'synthetic-usage.json'), prompt_variant=CANDIDATE)
    model = SyntheticGatewayModel(c, SyntheticEgressGate(load_dataset()), operator_enabled=True,
        egress_authorized=True, transport=GatewayWire(gateway), prompt_variant=CANDIDATE)
    result = evaluate(load_dataset(), model=model, real=True, output_tokens=2048, prompt_variant=CANDIDATE)
    assert len(http.requests) == 1
    wire = http.requests[0]['body']
    assert json.loads(wire['messages'][0]['content']) == prompt_contract(CANDIDATE)
    assert wire['max_completion_tokens'] == 2048
    assert wire['response_format']['json_schema']['strict'] is True
    assert result['outcomes'][0]['case_id'] == 'performance' and result['outcomes'][0]['accepted']
    assert result['prompt_sha256'] == prompt_digest(CANDIDATE)
    assert result['stopped_reason'] == 'run_budget_exhausted'
    assert gateway.ledger.state['input_reserved'] + gateway.ledger.state['output_reserved'] == 7936


def test_gateway_also_requires_explicit_candidate_selection(tmp_path):
    c = trial3_config(); c.approval.prompt_sha256 = prompt_digest(CANDIDATE)
    with pytest.raises(EvaluationStopped, match='approval_invalid'):
        RealLLMGateway(c, TOKEN, str(tmp_path/'never-used.json'))


def test_cli_describes_candidate_without_creating_approval(tmp_path,capsys):
    from scripts.evaluate_financial_llm import run
    assert run(['--describe','--prompt-variant',CANDIDATE])==0
    assert json.loads(capsys.readouterr().out)['prompt_sha256']==prompt_digest(CANDIDATE)
    assert list(tmp_path.iterdir())==[]


def test_cli_diagnostics_requires_opt_in_and_never_reads_holdout(tmp_path,monkeypatch,capsys):
    from scripts import evaluate_financial_llm as cli
    def forbidden(*args,**kwargs): pytest.fail('invalid diagnostics options must fail before loading data')
    monkeypatch.setattr(cli,'load_dataset',forbidden)
    assert cli.run(['--diagnostics-directory',str(tmp_path/'private')])==2
    assert cli.run(['--enable-rejected-draft-diagnostics','--diagnostics-directory',str(tmp_path/'private'),
        '--holdout','--release-holdout'])==2
    assert not (tmp_path/'private').exists()
    assert not capsys.readouterr().out


def test_operator_candidate_and_diagnostic_flags_are_explicit(tmp_path,monkeypatch):
    from scripts import groq_trial_operator as operator
    c=trial3_config(); c.approval.prompt_sha256=prompt_digest(CANDIDATE)
    path=tmp_path/'synthetic-config.json'; path.write_text(c.model_dump_json(),encoding='utf-8')
    with pytest.raises(EvaluationStopped): operator.load_approved_config(path,trial_profile='trial3-completion')
    assert operator.load_approved_config(path,trial_profile='trial3-completion',prompt_variant=CANDIDATE)
    calls=[]
    monkeypatch.setattr(operator,'run',lambda path,**kwargs: calls.append(kwargs) or 0)
    monkeypatch.setattr('sys.argv',['operator','--trial-directory',str(tmp_path),
        '--trial-profile','trial3-completion','--prompt-variant',CANDIDATE,
        '--enable-rejected-draft-diagnostics','--diagnostics-directory',str(tmp_path/'diagnostics')])
    assert operator.main()==0
    assert calls==[dict(trial_profile='trial3-completion',prompt_variant=CANDIDATE,diagnostics_directory=tmp_path/'diagnostics')]
