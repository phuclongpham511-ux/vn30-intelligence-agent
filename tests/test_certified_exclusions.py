"""Pinned B6 boundary tests with synthetic sources/artifacts only."""
import json
from hashlib import sha256
from types import SimpleNamespace

import pytest

from src.evaluation.benchmark import exclusions
from src.evaluation.benchmark.admission import AdmissionBlocked, RealDataLoaderDisabled
from scripts.project_technical_protected_metadata import project, build
from tests.test_protected_metadata_projection import fixtures, STAMP
from tests.test_benchmark_admission import certified_metadata


def frozen(tmp_path, monkeypatch):
    fixtures(tmp_path)
    payloads = build(project(tmp_path), STAMP)
    hashes = {}
    for name, raw in zip(exclusions.HASHES, payloads):
        p = tmp_path / exclusions.DIRECTORY / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        hashes[name] = sha256(raw).hexdigest()
    monkeypatch.setattr(exclusions, 'HASHES', hashes)
    return hashes


def test_only_identity_artifacts_read_and_forged_caller_ledger_replaced(tmp_path, monkeypatch):
    from pathlib import Path
    hashes = frozen(tmp_path, monkeypatch)
    allowed = {tmp_path / exclusions.DIRECTORY / name for name in hashes}
    original = Path.read_bytes
    def guarded(path):
        assert path in allowed, 'Followed protected provenance or payload path'
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', guarded)
    meta = certified_metadata()
    meta['ledger']['records'] = []  # Caller cannot remove pinned exclusions.
    with pytest.raises(AdmissionBlocked) as err:
        exclusions.request_certified_payload(meta, root=tmp_path,
            payload_loader=lambda *a: pytest.fail('Payload loaded'))
    assert 'B6_PROTECTED_STOCKDAY_IN_SOURCE' in err.value.decision['reasons']
    assert meta['ledger']['records'] == []  # Caller data not mutated.


@pytest.mark.parametrize('which', [0, 1])
def test_mutation_blocks_before_payload(tmp_path, monkeypatch, which):
    hashes = frozen(tmp_path, monkeypatch)
    p = tmp_path / exclusions.DIRECTORY / list(hashes)[which]
    p.write_bytes(p.read_bytes() + b' ')
    with pytest.raises(ValueError, match='hash mismatch'):
        exclusions.request_certified_payload(certified_metadata(), root=tmp_path,
            payload_loader=lambda *a: pytest.fail('Payload loaded'))


def test_missing_artifact_blocks(tmp_path):
    with pytest.raises(FileNotFoundError):
        exclusions.request_certified_payload(certified_metadata(), root=tmp_path,
            payload_loader=lambda *a: pytest.fail('Payload loaded'))


def test_metadata_pass_still_cannot_enable_loader(tmp_path, monkeypatch):
    frozen(tmp_path, monkeypatch)
    meta = certified_metadata()
    meta['manifest']['scope']['instruments'][0]['ticker'] = 'OTHER'
    meta['request']['instruments'][0]['ticker'] = 'OTHER'
    for certificate in meta['manifest']['certificates'].values():
        certificate['scope']['instruments'][0]['ticker'] = 'OTHER'
    with pytest.raises(RealDataLoaderDisabled):
        exclusions.request_certified_payload(meta, root=tmp_path,
            payload_loader=lambda *a: pytest.fail('Payload loaded'))


def test_redirected_artifact_rejected_before_read(tmp_path, monkeypatch):
    from pathlib import Path
    frozen(tmp_path, monkeypatch)
    target = tmp_path / exclusions.DIRECTORY / next(iter(exclusions.HASHES))
    monkeypatch.setattr(Path, 'is_junction', lambda p: p == target.parent)
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('Redirected read'))
    with pytest.raises(ValueError, match='Redirected'):
        exclusions.load_certified_ledger(tmp_path)


def test_current_preflight_cannot_confuse_tests_or_b6_with_data_readiness(monkeypatch):
    from scripts import check_technical_data_readiness as preflight
    monkeypatch.setattr(preflight, 'verify_governance', lambda: {'synthetic': 'hash'})
    monkeypatch.setattr(preflight, 'load_cohort', lambda: SimpleNamespace(normalized_cohort_sha256='synthetic', tickers=('SYN',)))
    monkeypatch.setattr(preflight, 'load_certified_ledger', lambda: {'studies': [
        {'protected_study_id': name, 'exported_case_count': 1} for name in exclusions.REQUIRED_STUDIES]})
    result = preflight.check()
    assert result['status'] == 'BLOCKED_BY_DATA_OR_PROVENANCE'
    assert result['official_generation_enabled'] is False
    assert result['benchmark_payload_loaded'] is False
    assert result['real_data_PIT_prefix_check'] == 'NOT_RUN_NO_ADMITTED_DATA'
