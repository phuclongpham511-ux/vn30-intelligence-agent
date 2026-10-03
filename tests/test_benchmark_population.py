"""Cohort provenance plus synthetic eligibility metadata; no market payloads."""
import json
import socket
from pathlib import Path
from datetime import date, timedelta

import pytest

from src.evaluation.benchmark.population import COHORT_PATH, load_cohort


def test_certified_cohort_loads_without_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Live lookup forbidden')
    monkeypatch.setattr(socket, 'socket', forbidden)
    cohort = load_cohort()
    assert cohort.cohort_id == 'BENCHMARK_COHORT_V1'
    assert len(cohort.tickers) == 30
    assert cohort.tickers == tuple(sorted(set(cohort.tickers)))


@pytest.mark.parametrize('change', [
    {'normalized_cohort_sha256': '0' * 64}, {'cohort_id': 'other'},
    {'cohort_version': '2'}, {'index_name': 'VN100'}, {'effective_from': '2026-08-04'},
    {'certification_status': 'UNVERIFIED'}, {'tickers': ['AAA'] * 30},
    {'tickers': None}, {'tickers': 'ABC'},
])
def test_invalid_cohort_fails_closed(tmp_path, change):
    data = json.loads(COHORT_PATH.read_text(encoding='utf-8'))
    data.update(change)
    path = tmp_path / 'cohort.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError):
        load_cohort(path)


@pytest.mark.parametrize('mutation', ['29', '31', 'reversed', 'lowercase', 'duplicate', 'tampered_source'])
def test_bad_cohort_content_fails(tmp_path, mutation):
    data = json.loads(COHORT_PATH.read_text(encoding='utf-8'))
    if mutation == '29': data['tickers'].pop()
    elif mutation == '31': data['tickers'].append('ZZZ')
    elif mutation == 'reversed': data['tickers'].reverse()
    elif mutation == 'lowercase': data['tickers'][0] = 'acb'
    elif mutation == 'duplicate': data['tickers'][1] = data['tickers'][0]
    else: data['constituent_source']['raw_sha256'] = '0' * 64
    path = tmp_path / 'cohort.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError): load_cohort(path)


def test_missing_malformed_or_duplicate_json_keys_fail(tmp_path):
    path = tmp_path / 'missing.json'
    with pytest.raises(FileNotFoundError): load_cohort(path)
    for content in ('{', '[]', '{"tickers":[],"tickers":[]}'):
        path.write_text(content, encoding='utf-8')
        with pytest.raises(ValueError): load_cohort(path)


def candidate(count=60, **changes):
    days, day = [], date(2020, 1, 1)
    while len(days) < count:
        if day.weekday() < 5:
            days.append({'session': day.isoformat(), 'valid': True, 'comparable': True,
                         'is_trading_session': True})
        day += timedelta(days=1)
    return {'ticker': 'ACB', 'session': '2020-06-01', 'component': 'REPRESENTATIVE',
            'listing': {'status': 'LISTED_AND_TRADING', 'ticker': 'ACB', 'session': '2020-06-01',
                        'first_trading_session': '2019-01-01', 'source_kind': 'EXCHANGE_NOTICE',
                        'source': 'synthetic-custodian', 'version': 'fixture-v1',
                        'evidence_reference': 'fixture:listing', 'certification_status': 'CERTIFIED'},
            'prior_sessions': days, **changes}


def decide(value):
    from src.evaluation.benchmark.population import evaluate_eligibility
    return evaluate_eligibility(load_cohort(), value)


@pytest.mark.parametrize('count,expected', [(59, 'INELIGIBLE'), (60, 'ELIGIBLE'), (80, 'ELIGIBLE')])
def test_representative_history_boundary(count, expected):
    result = decide(candidate(count))
    assert result['decision'] == expected
    assert result['prior_valid_sessions'] == count
    assert result['official_sampling_enabled'] is False


@pytest.mark.parametrize('status,expected', [('PRE_LISTING','INELIGIBLE'), ('LISTING_STATUS_UNKNOWN','UNRESOLVED')])
def test_listing_status_fails_closed(status, expected):
    row = candidate()
    row['listing']['status'] = status
    assert decide(row)['decision'] == expected


@pytest.mark.parametrize('field,value', [('evidence_reference',None), ('certification_status','UNVERIFIED'),
    ('source_kind','FIRST_PROVIDER_ROW'), ('ticker','OTHER'), ('session','2020-05-31'),
    ('first_trading_session','2020-07-01')])
def test_missing_or_conflicting_listing_provenance(field, value):
    row = candidate(); row['listing'][field] = value
    assert decide(row)['decision'] == 'UNRESOLVED'


def test_only_prior_valid_comparable_trading_sessions_count():
    row = candidate(59)
    row['prior_sessions'] += [
        {'session': '2020-06-01', 'valid': True, 'comparable': True, 'is_trading_session': True},
        {'session': '2020-06-02', 'valid': True, 'comparable': True, 'is_trading_session': True},
        {'session': '2020-05-26', 'valid': False, 'comparable': True, 'is_trading_session': True},
        {'session': '2020-05-27', 'valid': True, 'comparable': False, 'is_trading_session': True},
        {'session': '2020-05-28', 'valid': True, 'comparable': True, 'is_trading_session': False}]
    assert decide(row)['prior_valid_sessions'] == 59
    assert decide(row)['decision'] == 'INELIGIBLE'


def test_duplicate_sessions_do_not_manufacture_history():
    row = candidate(59); row['prior_sessions'].append(row['prior_sessions'][0])
    assert decide(row)['decision'] == 'UNRESOLVED'


@pytest.mark.parametrize('purpose,reason,expected', [
    ('insufficient_history', 'predeclared history diagnostic', 'ELIGIBLE'),
    ('unavailable_evidence', 'predeclared missing evidence diagnostic', 'ELIGIBLE'),
    ('insufficient_history', None, 'INELIGIBLE'),
    ('price_move', 'large price move', 'INELIGIBLE'),
    (None, None, 'INELIGIBLE')])
def test_enriched_exception_requires_declared_purpose_and_reason(purpose, reason, expected):
    assert decide(candidate(59, component='ENRICHED_DIAGNOSTIC', diagnostic_purpose=purpose,
                            diagnostic_reason=reason))['decision'] == expected


def test_diagnostic_reason_cannot_admit_representative_short_history():
    assert decide(candidate(59, diagnostic_purpose='insufficient_history',
                            diagnostic_reason='diagnostic'))['decision'] == 'INELIGIBLE'


def test_eligibility_deterministic_and_membership_is_metadata_only():
    from src.materiality import EvidenceItem, MaterialEventCandidate, evaluate_candidate
    outputs = []
    for membership in ('YES', 'NO', 'UNKNOWN'):
        row = candidate(historical_membership_status=membership)
        result = decide(row)
        assert result == decide(row)
        assert result['decision'] == 'ELIGIBLE'
        assert result['historical_membership_status'] == membership
        # Only technical evidence crosses the engine boundary; never the eligibility record.
        event = MaterialEventCandidate(ticker=row['ticker'], event_type='abnormal_price_move',
            category='market', direction='positive', observed_at=row['session'],
            evidence=(EvidenceItem('return', .03, 'synthetic'),), own_history_abnormality=.8)
        outputs.append(evaluate_candidate(event))
    assert outputs[0] == outputs[1] == outputs[2]


def test_outside_cohort_or_frame_rejected():
    assert decide(candidate(ticker='OUTSIDE'))['decision'] == 'INELIGIBLE'
    assert decide(candidate(session='2025-01-01'))['decision'] == 'INELIGIBLE'


def admission_metadata():
    from test_benchmark_admission import certified_metadata
    metadata = json.loads(json.dumps(certified_metadata()).replace('"SYN"', '"ACB"'))
    metadata['request']['start'] = metadata['request']['end'] = '2020-06-01'
    metadata['manifest']['certificates']['historical_universe'] = None
    return metadata


@pytest.mark.parametrize('membership', ['YES', 'NO', 'UNKNOWN'])
def test_primary_admission_replaces_historical_gate_with_cohort(membership):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    result = validate_real_data_admission(admission_metadata(), stock_day=candidate(
        historical_membership_status=membership))
    assert result['decision'] == 'PASS'
    assert result['population_eligibility']['historical_membership_status'] == membership
    assert result['real_loader_enabled'] is False
    assert result['payload_loaded'] is False


@pytest.mark.parametrize('missing', ['comparability', 'provenance', 'exchange_calendar', 'ledger'])
def test_primary_admission_preserves_other_data_gates(missing):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    data = admission_metadata()
    if missing == 'ledger': data['ledger'] = None
    else: data['manifest']['certificates'][missing] = None
    assert validate_real_data_admission(data, stock_day=candidate())['decision'] == 'BLOCKED'


def test_primary_gate_fails_closed_for_mismatched_or_missing_inputs(tmp_path):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    for row in (candidate(59), {}, candidate(ticker='OUTSIDE')):
        assert validate_real_data_admission(admission_metadata(), stock_day=row)['decision'] == 'BLOCKED'
    data = admission_metadata(); data['request']['end'] = '2020-06-02'
    assert validate_real_data_admission(data, stock_day=candidate())['decision'] == 'BLOCKED'
    assert validate_real_data_admission(admission_metadata(), stock_day=candidate(),
        cohort_path=tmp_path / 'missing.json')['decision'] == 'BLOCKED'


def test_primary_metadata_pass_never_calls_payload_loader():
    from src.evaluation.benchmark.admission import request_real_payload, RealDataLoaderDisabled
    def forbidden():
        raise AssertionError('Real payload must remain sealed')
    with pytest.raises(RealDataLoaderDisabled):
        request_real_payload(admission_metadata(), stock_day=candidate(), payload_loader=forbidden)


def test_manifest_always_carries_claim_and_unrun_status(tmp_path):
    from test_technical_benchmark import synthetic_snapshot
    from src.evaluation.benchmark.builder import build_group
    from src.evaluation.benchmark.package import write_package
    from src.evaluation.benchmark.population import CLAIM_SCOPE
    snapshot = synthetic_snapshot()
    group = build_group(snapshot, 'SYN', snapshot['calendar'][-1])
    result = write_package(tmp_path, [group], source_inventory={'fixture': True})
    assert result['population_claim']['approved_claim'] == CLAIM_SCOPE
    assert result['population_claim']['claim_status'] == 'NOT_ESTABLISHED_SMOKE_ONLY'
    stored = json.loads((tmp_path / 'run_manifest.json').read_text(encoding='utf-8'))
    assert stored['population_claim'] == result['population_claim']


def test_smoke_receipt_covers_population_dependency(tmp_path):
    from scripts.build_technical_benchmark_smoke import run_phase1
    result = run_phase1(tmp_path)
    assert 'src/evaluation/benchmark/population.py' in result['code_hashes']
