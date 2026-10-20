"""Activation classifications and saved canonical boundaries, without live access."""
import hashlib
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_personal_financials import source
from src.services.personal_financials import personal_projection, saved_packet, validated_canonical_packet
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response


def test_verification_and_permission_are_independent_and_never_promote_source_amounts():
    packet = source()
    personal = personal_projection(packet, authorization_reference='synthetic-boundary-test')
    verification = personal['verification']
    assert verification['audience'] == 'personal_research'
    latest = verification['periods'][-1]['metrics']
    revenue = latest['revenue']
    assert revenue['status'] == 'PARTIALLY_VERIFIED' and revenue['display_eligible']
    assert not revenue['public_display_eligible']
    assert {'reporting_scope', 'original_unit', 'qualified_publication_timestamp',
        'public_display_permission', 'original_document_verification'} <= set(revenue['missing_evidence'])
    assert not latest['roe']['display_eligible']
    public = display_financial_response(financial_engine(packet))
    assert public.rows[-1]['revenue'] is None
    assert not public.verification['periods'][-1]['metrics']['revenue']['display_eligible']
    assert public.verification['statuses']['VERIFIED'] == 0


def test_synthetic_and_invalid_computations_cannot_become_verified():
    packet = source()
    packet.is_fixture = True
    view = display_financial_response(financial_engine(packet))
    assert view.verification['statuses']['PARTIALLY_VERIFIED'] == 0
    assert view.verification['statuses']['VERIFIED'] == 0


@pytest.mark.parametrize('mutation', ['owner', 'amount', 'line_unit', 'profile', 'rights', 'boundaries', 'duplicate', 'naive_fetch', 'publication', 'flow_basis', 'currency'])
def test_canonical_saved_capture_rejects_promoted_or_inconsistent_evidence(mutation):
    packet = source()
    if mutation == 'owner':
        packet.reports['income'].observations[-1].ticker = 'WRONG'
    elif mutation == 'amount':
        packet.reports['income'].observations[-1].fields['revenue'] = 999
    elif mutation == 'line_unit':
        for line in packet.reports['income'].observations[-1].items:
            if line.code == 'isa3': line.unit = 'VND/share'
    elif mutation == 'profile':
        packet.profile = 'bank'
    elif mutation == 'rights':
        packet.reports['income'].observations[-1].source_context.display_rights = 'permitted'
    elif mutation == 'boundaries':
        packet.reports['income'].observations[-1].source_context.period_end = '2025-12-31'
    elif mutation == 'duplicate':
        packet.reports['income'].observations.append(packet.reports['income'].observations[-1])
    elif mutation == 'naive_fetch':
        packet.reports['income'].observed_at = packet.reports['income'].observed_at.replace(tzinfo=None)
    elif mutation == 'publication':
        packet.reports['income'].observations[-1].source_dates['publicDate'] = '2020-01-01'
    elif mutation == 'flow_basis':
        packet.reports['income'].observations[-1].basis = 'ytd'
    else:
        packet.reports['income'].observations[-1].source_context.original_currency = 'USD'
    with pytest.raises(ValueError):
        validated_canonical_packet(packet.model_dump_json().encode())


def test_canonical_bundle_is_hash_pinned_and_loopback_api_uses_it_without_provider(tmp_path, monkeypatch):
    packet = source()
    data = packet.model_dump_json().encode()
    assert validated_canonical_packet(data).ticker == 'ABC'
    (tmp_path / 'packet.json').write_bytes(data)
    (tmp_path / 'index.json').write_text(json.dumps({
        'contract': 'personal-saved-captures-v1',
        'captures': {'ABC': {'file': 'packet.json', 'sha256': hashlib.sha256(data).hexdigest(),
            'format': 'canonical-financial-packet-v1'}}}))
    loaded, _ = saved_packet(tmp_path, 'ABC')
    assert loaded.model_dump() == packet.model_dump()
    from routers.personal_research import router
    for key, value in dict(WOOFI_PERSONAL_RESEARCH='1', APP_ENV='development',
            WOOFI_PERSONAL_BIND='127.0.0.1', WOOFI_PERSONAL_CAPTURES=str(tmp_path)).items():
        monkeypatch.setenv(key, value)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app, client=('127.0.0.1', 1234), base_url='http://127.0.0.1')
    response = client.get('/personal-research/financials/ABC?frequency=annual')
    assert response.status_code == 200 and response.json()['rows'][-1]['revenue'] == 120
    assert response.json()['verification']['audience'] == 'personal_research'
    assert response.headers['cache-control'] == 'private, no-store'
    (tmp_path / 'packet.json').write_bytes(data + b' ')
    assert client.get('/personal-research/financials/ABC').status_code == 503


def test_prepare_bundle_keeps_original_bytes_and_rejects_replacement(tmp_path):
    from scripts.prepare_financial_activation import prepare
    source_dir = tmp_path / 'source'
    source_dir.mkdir()
    data = source().model_dump_json().encode()
    (source_dir / 'capture.json').write_bytes(data)
    index = {'contract': 'personal-saved-captures-v1', 'captures': {
        'ABC': {'file': 'capture.json', 'sha256': hashlib.sha256(data).hexdigest(),
            'format': 'canonical-financial-packet-v1'}}}
    (source_dir / 'index.json').write_text(json.dumps(index))
    target = tmp_path / 'private'
    assert prepare(source_dir, target)['tickers'] == ['ABC']
    assert prepare(source_dir, target)['provider_requests'] == 0
    copied = json.loads((target / 'index.json').read_text())
    assert (target / copied['captures']['ABC']['file']).read_bytes() == data
    with pytest.raises(ValueError): prepare(source_dir, source_dir)
    with pytest.raises(ValueError): prepare(source_dir, tmp_path / 'Public')
    copied['captures']['ABC']['sha256'] = 'a' * 64
    (target / 'index.json').write_text(json.dumps(copied))
    with pytest.raises(ValueError): prepare(source_dir, target)


def test_observed_industry_pairs_are_reviewed_without_creating_historical_memberships():
    from src.services.industry_membership_review import review_memberships
    from src.schemas.financial_intelligence import IndustryTaxonomy
    record = dict(symbol='ABC', board='HOSE', stockType='Stock', icbCode='0012', icbName='Provider category')
    result = review_memberships([record, record], receipt=dict(fetched_at='2026-10-17T00:00:00Z',
        document_sha256='a' * 64), review_reference='synthetic-review')
    assert result['duplicate_rows'] == 1 and len(result['entries']) == 1
    member = result['entries'][0]
    assert member['provider_code'] == '0012' and member['verification_status'] == 'PARTIALLY_VERIFIED'
    assert member['classification_effective_at'] is None and member['financial_model'] is None
    assert not member['eligible_for_industry_aggregation']
    with pytest.raises(ValueError): IndustryTaxonomy.model_validate(result)
    conflict = {**record, 'icbCode': 'OTHER'}
    reviewed = review_memberships([record, conflict], receipt=result['receipt'], review_reference='synthetic-review')
    assert reviewed['entries'][0]['verification_status'] == 'UNAVAILABLE'


def test_a_missing_canonical_statement_does_not_erase_other_reported_observations():
    packet = source()
    receipt = packet.reports['cash']
    receipt.observations = []
    receipt.status = 'error'
    receipt.content_sha256 = None
    receipt.error_type = 'ProviderError'
    loaded = validated_canonical_packet(packet.model_dump_json().encode())
    view = personal_projection(loaded, authorization_reference='synthetic-boundary')
    assert view['rows'][-1]['revenue'] == 120
    assert view['rows'][-1]['cash_operating'] is None
    assert next(p for p in view['research_panels'] if p['key'] == 'cashflow')['status'] == 'UNAVAILABLE'


@pytest.mark.parametrize('value', [True, '120'])
def test_canonical_financial_numbers_are_not_coerced_from_flags_or_text(value):
    raw = source().model_dump(mode='json')
    obs = raw['reports']['income']['observations'][-1]
    obs['fields']['revenue'] = value
    line = next(l for l in obs['items'] if l['code'] == 'isa3')
    line['value'] = line['raw_value'] = value
    with pytest.raises(ValueError):
        validated_canonical_packet(json.dumps(raw).encode())
