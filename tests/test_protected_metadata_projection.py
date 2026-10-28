"""Synthetic only: never read protected study files in tests."""
from copy import deepcopy
import json
from hashlib import sha256

import pytest

from scripts.project_technical_protected_metadata import (
    STUDIES, ALLOWED, build, canonical, fields, selected, cases,
    safe_path, project, admission_ledger,
)
from src.evaluation.benchmark.admission import (
    validate_real_data_admission, request_real_payload, AdmissionBlocked, RealDataLoaderDisabled,
)
from tests.test_benchmark_admission import certified_metadata


STAMP = '2026-10-04T00:00:00+00:00'


def fixtures(root):
    for number, (_, _, count, manifest, folder, review, lh, mh) in enumerate(STUDIES):
        records = [{'case_id': f'{number * 1000 + i:024x}', 'ticker': 'SYN', 'date': '2020-03-01',
                    'evidence': {'not_for_export': 'synthetic secret'}, 'scores': [99]} for i in range(count)]
        mb = canonical({'cases': records})
        rb = b''.join(canonical({'case_id': r['case_id'], 'annotation': 'synthetic secret'}) for r in records)
        fb = canonical({'version': 'synthetic', 'count': count, 'integrity_passed': True,
                        lh: sha256(rb).hexdigest(), mh: sha256(mb).hexdigest(), 'distribution': {'secret': 99}})
        for ref, data in ((manifest, mb), (folder + '/' + review, rb), (folder + '/label_freeze.json', fb)):
            p = root / ref
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)


def test_skip_unauthorized_values_without_decoding(monkeypatch):
    original = json.loads
    def guarded(text, *a, **kw):
        assert 'synthetic secret' not in text
        return original(text, *a, **kw)
    monkeypatch.setattr(json, 'loads', guarded)
    text = '{"cases":[{"case_id":"abc","ticker":"SYN","date":"2020-03-01","evidence":{"text":"synthetic secret \\\" } ]"}}]}'
    assert list(cases(text)) == [{'case_id': 'abc', 'ticker': 'SYN', 'date': '2020-03-01'}]


def test_complete_projection_and_determinism(tmp_path):
    fixtures(tmp_path)
    studies = project(tmp_path)
    a, b = build(studies, STAMP), build(deepcopy(studies), STAMP)
    assert a == b
    assert b'synthetic secret' not in a[0] + a[1]
    assert b'annotation' not in a[0] + a[1]
    assert sum(s['exported_case_count'] for s in studies) == 288
    assert all(s['completeness_status'] == 'COMPLETE' for s in studies)
    union = json.loads(a[1])
    assert union['unique_stock_day_count'] == 1
    assert len(union['records'][0]['protected_cases']) == 288
    assert union['ledger_sha256'] == sha256(a[0]).hexdigest()


@pytest.mark.parametrize('ref', ['data/holdout/2025.json', 'data/fresh_validation/manifest.json',
                               'data/future_validation_reservations.json', '../escape',
                               'data/evaluation/unrelated/reviews.jsonl'])
def test_denied_paths_never_open(tmp_path, ref, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('Opened denied source'))
    with pytest.raises(ValueError, match='DENIED'):
        safe_path(tmp_path, ref)


def test_source_hash_mismatch_fails(tmp_path):
    fixtures(tmp_path)
    p = tmp_path / STUDIES[0][3]
    p.write_bytes(p.read_bytes() + b' ')
    with pytest.raises(ValueError, match='hash mismatch'):
        project(tmp_path)


@pytest.mark.parametrize('mutation', ['duplicate', 'different_id'])
def test_counts_alone_do_not_certify(tmp_path, mutation):
    fixtures(tmp_path)
    _, _, _, manifest, folder, _, _, mh = STUDIES[0]
    p = tmp_path / manifest
    obj = json.loads(p.read_bytes())
    obj['cases'][0]['case_id'] = obj['cases'][1]['case_id'] if mutation == 'duplicate' else 'f' * 24
    p.write_bytes(canonical(obj))
    f = tmp_path / folder / 'label_freeze.json'
    freeze = json.loads(f.read_bytes()); freeze[mh] = sha256(p.read_bytes()).hexdigest()
    f.write_bytes(canonical(freeze))
    with pytest.raises(ValueError, match='duplicate|sets differ'):
        project(tmp_path)


def test_duplicate_json_identity_key_fails():
    with pytest.raises(ValueError, match='Duplicate'):
        fields('{"case_id":"a","case_id":"b"}')


def test_duplicate_case_in_ledger_fails(tmp_path):
    fixtures(tmp_path)
    studies = project(tmp_path)
    studies[0]['records'].append(studies[0]['records'][0])
    with pytest.raises(ValueError, match='Duplicate case'):
        build(studies, STAMP)


def test_adapter_excludes_before_loading_and_leaves_episode_unknown(tmp_path):
    fixtures(tmp_path)
    ledger = json.loads(build(project(tmp_path), STAMP)[0])
    meta = certified_metadata()
    meta['ledger'] = admission_ledger(ledger, meta['manifest']['scope'])
    meta['manifest']['protected_ledger_version'] = ledger['ledger_version']
    assert all(r['episode_id'] is None and r['episode_start'] is None and r['episode_end'] is None
               for r in meta['ledger']['records'])
    result = validate_real_data_admission(meta)
    assert 'B6_PROTECTED_STOCKDAY_IN_SOURCE' in result['reasons']
    with pytest.raises(AdmissionBlocked):
        request_real_payload(meta, payload_loader=lambda *a: pytest.fail('Payload opened'))


def test_complete_coverage_satisfies_b6_but_loader_stays_disabled(tmp_path):
    fixtures(tmp_path)
    ledger = json.loads(build(project(tmp_path), STAMP)[0])
    for study in ledger['studies']:
        for r in study['records']:
            r['ticker'] = 'OTHER'
    meta = certified_metadata()
    meta['manifest']['protected_ledger_version'] = ledger['ledger_version']
    meta['ledger'] = admission_ledger(ledger, meta['manifest']['scope'])
    assert validate_real_data_admission(meta)['decision'] == 'PASS'
    with pytest.raises(RealDataLoaderDisabled):
        request_real_payload(meta, payload_loader=lambda *a: pytest.fail('Payload opened'))
    for state in ('INCOMPLETE', 'UNRESOLVED'):
        ledger['studies'][0]['completeness_status'] = state
        meta['ledger'] = admission_ledger(ledger, meta['manifest']['scope'])
        result = validate_real_data_admission(meta)
        assert result['decision'] == 'BLOCKED'
        assert 'B6_STUDY_COVERAGE_INCOMPLETE' in result['reasons']
    ledger['studies'].pop()
    meta['ledger'] = admission_ledger(ledger, meta['manifest']['scope'])
    assert validate_real_data_admission(meta)['decision'] == 'BLOCKED'
