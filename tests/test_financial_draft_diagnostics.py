"""Private diagnostics exercise only pinned synthetic development cases."""
from dataclasses import replace
import json
import socket

import pytest

from src.services.financial_evaluation import load_dataset, prepare_case, evaluate
from src.services.financial_assistant import DeterministicFinancialModel, model_context
from src.services.financial_model_adapter import EvaluationStopped
from src.services.financial_draft_diagnostics import SyntheticDraftDiagnostics


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail('diagnostics must not access a network')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)


def draft():
    dataset = load_dataset(); case = next(c for c in dataset.cases() if c['id'] == 'performance')
    p = prepare_case(case)
    raw = DeterministicFinancialModel().generate(model_context(p['intent'],p['facts']),max_output_tokens=2048)
    return json.loads(raw), p


def store(path, **kwargs):
    return SyntheticDraftDiagnostics(load_dataset(),path,enabled=True,**kwargs)


def test_explicit_opt_in_and_pinned_dataset_required_before_storage(tmp_path):
    with pytest.raises(EvaluationStopped):
        SyntheticDraftDiagnostics(load_dataset(),tmp_path/'not-created')
    altered = replace(load_dataset(),data=load_dataset().data+b' ')
    with pytest.raises(EvaluationStopped):
        SyntheticDraftDiagnostics(altered,tmp_path/'not-created',enabled=True)
    with pytest.raises(EvaluationStopped):
        SyntheticDraftDiagnostics(object(),tmp_path/'not-created',enabled=True)
    with pytest.raises(EvaluationStopped):
        SyntheticDraftDiagnostics(replace(load_dataset(),split='holdout'),tmp_path/'not-created',enabled=True)
    assert not (tmp_path/'not-created').exists()


@pytest.mark.parametrize('mutation', ['whitespace','citation','missing_warning','unsupported_text'])
def test_exact_private_diff_can_reconstruct_rejected_synthetic_answer(tmp_path,mutation):
    writer = store(tmp_path/'private',prompt_variant='candidate-c-v1')
    value,p = draft(); expected=value['answer']; lines=expected.splitlines(keepends=True)
    if mutation=='whitespace': value['answer']=value['answer'].replace('Trạng thái',' Trạng thái',1)
    elif mutation=='citation': value['evidence_ids'][0]='synthetic-unknown-evidence'
    elif mutation=='missing_warning': value['answer']=value['answer'].replace(' Còn thiếu bằng chứng; xem missing_information.','',1)
    elif mutation=='unsupported_text': value['answer']+='\nSynthetic unsupported narrative.'
    filename=writer.record_rejection('performance',json.dumps(value,ensure_ascii=False))
    item=writer.read_artifact(filename)
    rebuilt=lines[:]
    for edit in reversed(item['answer_edits']):
        rebuilt[edit['expected_start']:edit['expected_end']]=edit['actual_lines']
    assert ''.join(rebuilt)==value['answer']
    assert item['citations']['submitted']==value['evidence_ids']
    assert item['assessment']['accepted'] is False
    assert item['classification']=='synthetic_non_sensitive'
    assert set(item) == writer.ARTIFACT_FIELDS
    assert item['expires_at']-item['created_at']<=3600
    if mutation=='citation': assert item['citations']['unexpected']==['synthetic-unknown-evidence']
    if mutation=='missing_warning': assert item['missing_warning_bindings'][0]['warning_omitted']


def test_foreign_files_and_repository_paths_fail_closed(tmp_path):
    root=tmp_path/'private'; writer=store(root)
    foreign=root/'keep.txt'; foreign.write_text('unrelated owner file')
    with pytest.raises(EvaluationStopped): writer.record_rejection('performance','{}')
    assert foreign.read_text()=='unrelated owner file'
    with pytest.raises(EvaluationStopped): store(__import__('pathlib').Path(__file__).resolve().parent/'must-not-create')


def test_expiry_is_enforced_and_purge_only_removes_owned_artifacts(tmp_path,monkeypatch):
    import src.services.financial_draft_diagnostics as module
    clock=[1000000.0]; monkeypatch.setattr(module.time,'time',lambda:clock[0])
    writer=store(tmp_path/'private',retention_seconds=2)
    value,_=draft(); value['answer']+=' '
    filename=writer.record_rejection('performance',json.dumps(value))
    clock[0]+=3
    with pytest.raises(EvaluationStopped): writer.read_artifact(filename)
    assert list((tmp_path/'private').iterdir())==[]
    with pytest.raises(EvaluationStopped): store(tmp_path/'bad-retention',retention_seconds=3601)


def test_sensitive_text_is_not_written_and_capacity_is_bounded(tmp_path,monkeypatch):
    writer=store(tmp_path/'private')
    value,_=draft(); value['answer']='Authorization: Bearer synthetic-secret'
    with pytest.raises(EvaluationStopped): writer.record_rejection('performance',json.dumps(value))
    assert list((tmp_path/'private').iterdir())==[]
    value,_=draft(); value['answer']+=' '
    monkeypatch.setattr(writer,'MAX_ARTIFACTS',1)
    writer.record_rejection('performance',json.dumps(value))
    with pytest.raises(EvaluationStopped): writer.record_rejection('performance',json.dumps(value))
    assert len(list((tmp_path/'private').iterdir()))==1


def test_diagnostics_integrates_only_when_explicitly_passed_to_evaluation(tmp_path):
    writer=store(tmp_path/'private')
    result=evaluate(load_dataset(),diagnostics=writer)
    assert result['diagnostics']['artifacts_written']>0
    assert all('actual_lines' not in json.dumps(outcome) for outcome in result['outcomes'])
    with pytest.raises(EvaluationStopped): evaluate(load_dataset(),diagnostics=object())


def test_storage_failure_stops_before_any_model_generation(tmp_path,monkeypatch):
    writer=store(tmp_path/'private')
    def refused(): raise EvaluationStopped('diagnostic_storage_unsafe')
    monkeypatch.setattr(writer,'preflight',refused)
    class NoModel:
        external_io=False
        def generate(self,*args,**kwargs): pytest.fail('unsafe diagnostics must stop before generation')
    with pytest.raises(EvaluationStopped): evaluate(load_dataset(),model=NoModel(),diagnostics=writer)


def test_inherited_or_broad_directory_permissions_are_not_silently_repaired(tmp_path):
    import os
    path=tmp_path/'unsafe'; path.mkdir(mode=0o755)
    if os.name!='nt': path.chmod(0o755)
    with pytest.raises(EvaluationStopped): store(path)
    assert list(path.iterdir())==[]


def test_hardlinked_artifact_is_rejected_without_deleting_either_link(tmp_path):
    import os
    writer=store(tmp_path/'private'); value,_=draft(); value['answer']+=' '
    name=writer.record_rejection('performance',json.dumps(value))
    linked=tmp_path/'other-link.json'
    os.link(tmp_path/'private'/name,linked)
    with pytest.raises(EvaluationStopped): writer.read_artifact(name)
    assert linked.exists() and (tmp_path/'private'/name).exists()


def test_unicode_escaped_sensitive_content_is_rejected_before_write(tmp_path):
    writer=store(tmp_path/'private'); value,_=draft()
    marker='Authorization: Bearer synthetic-secret'
    encoded=''.join('\\u%04x'%ord(c) for c in marker)
    value['answer']='PLACEHOLDER'
    raw=json.dumps(value).replace('PLACEHOLDER',encoded)
    with pytest.raises(EvaluationStopped): writer.record_rejection('performance',raw)
    assert list((tmp_path/'private').iterdir())==[]


def test_relative_and_unc_storage_are_rejected_without_creation(tmp_path):
    from pathlib import Path
    for path in (Path('relative-diagnostic-path'),Path('//unavailable-server/share/diagnostics')):
        with pytest.raises(EvaluationStopped): store(path)


def test_cli_purge_removes_expired_artifacts_without_evaluation(tmp_path,monkeypatch,capsys):
    import src.services.financial_draft_diagnostics as module
    from scripts import evaluate_financial_llm as cli
    clock=[1000000.0]; monkeypatch.setattr(module.time,'time',lambda:clock[0])
    root=tmp_path/'private'; writer=store(root,retention_seconds=2)
    value,_=draft(); value['answer']+=' '
    writer.record_rejection('performance',json.dumps(value))
    clock[0]+=3
    def forbidden(*args,**kwargs): pytest.fail('purge must not run evaluation')
    monkeypatch.setattr(cli,'evaluate',forbidden)
    assert cli.run(['--enable-rejected-draft-diagnostics','--diagnostics-directory',str(root),
        '--purge-expired-diagnostics'])==0
    assert json.loads(capsys.readouterr().out)=={'expired_artifacts_removed':1}
    assert list(root.iterdir())==[]
