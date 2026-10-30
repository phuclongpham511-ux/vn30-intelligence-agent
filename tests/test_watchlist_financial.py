"""Private Watchlist HTTP seam over synthetic saved original reports."""
import hashlib
import socket
import pytest
from fastapi.testclient import TestClient
from main import app
from src.services.financial_journal import MetricJournal
from src.providers.reviewed_reports import report_packet
from test_free_financial_sources import reviewed


@pytest.fixture(autouse=True)
def no_provider_network(monkeypatch):
    original = socket.socket.connect
    def guarded(sock, address):
        # Windows asyncio builds its internal socketpair over loopback. Preserve
        # that test infrastructure while refusing every external destination.
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1', 'localhost'):
            pytest.fail('Financial Watchlist must not contact providers')
        return original(sock, address)
    monkeypatch.setattr(socket.socket, 'connect', guarded)


@pytest.fixture
def financial_store(tmp_path, monkeypatch):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    journal = MetricJournal(tmp_path/'financial.sqlite'); journal.initialize()
    journal.import_packet(packet, 'a'*64)
    for key, value in dict(APP_ENV='development', WOOFI_PERSONAL_RESEARCH='1',
        WOOFI_PERSONAL_BIND='127.0.0.1', WOOFI_PERSONAL_FINANCIAL_READS='sqlite',
        WOOFI_PERSONAL_SQLITE=str(journal.path), WOOFI_PERSONAL_CAPTURES=str(tmp_path),
        WOOFI_WATCHLIST_FINANCIALS='1').items(): monkeypatch.setenv(key, value)
    return journal, packet


def private_client():
    return TestClient(app, client=('127.0.0.1', 1234), base_url='http://127.0.0.1')


def test_eligible_change_reuses_financial_engine_and_private_evidence(financial_store):
    journal, _ = financial_store
    before = hashlib.sha256(journal.path.read_bytes()).hexdigest()
    response = private_client().post('/personal-research/watchlist-financials', json={'symbols':['ABC']})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'private, no-store'
    page = response.json()['stocks'][0]['financial']
    assert page['status'] == 'READY' and len(page['items']) == 1
    item = page['items'][0]; insight = item['evidence']['insight']
    assert insight['current_value'] == 1000 and insight['comparison_value'] == 800
    assert insight['absolute_change'] == 200 and insight['percentage_change'] == .25
    assert insight['attention_reason']['criteria'] == ['RELATIVE_MOVEMENT']
    assert insight['qualification_status'] == 'COMPARABLE'
    assert 'public_display_permission' in insight['missing_information']
    assert item['id'] == 'financial:'+item['entity_id']
    assert item['evidence']['capture_id'] and insight['evidence_references']
    again = private_client().post('/personal-research/watchlist-financials', json={'symbols':['ABC']}).json()
    assert again['stocks'][0]['financial']['items'][0]['revision'] == item['revision']
    assert hashlib.sha256(journal.path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize('mode,status', [('scope','INSUFFICIENT_COMPARISON'),('missing','MISSING_DATA')])
def test_insufficient_or_missing_never_becomes_a_financial_update(financial_store, tmp_path, mode, status):
    import json
    journal, packet = financial_store
    revised = packet.model_copy(deep=True)
    if mode == 'scope':
        for observation in revised.reports['income'].observations: observation.consolidation = None
    else:
        for observation in revised.reports['income'].observations:
            observation.fields['revenue'] = None
            for line in observation.items:
                if line.code == observation.field_codes['revenue']: line.value = line.raw_value = None
    journal.import_packet(revised, 'b'*64)
    (tmp_path/'index.json').write_text(json.dumps(dict(contract='personal-saved-captures-v1',
        reviewed_reports={'ABC':{'sha256':'b'*64}})))
    page = private_client().post('/personal-research/watchlist-financials',json={'symbols':['ABC']}).json()['stocks'][0]['financial']
    assert page['status'] == status and page['items'] == [] and page['reasons']


def test_duplicate_and_explicit_revision_preserve_identity(financial_store, tmp_path):
    import json
    journal, packet = financial_store
    client = private_client()
    read = lambda: client.post('/personal-research/watchlist-financials',json={'symbols':['ABC']}).json()['stocks'][0]['financial']
    original = read()['items'][0]
    assert journal.import_packet(packet,'a'*64)['inserted_captures'] == 0
    assert read()['items'][0] == original
    journal.import_packet(packet,'b'*64)
    assert read()['status'] == 'UNAVAILABLE'  # Never pick an arbitrary newer revision.
    (tmp_path/'index.json').write_text(json.dumps(dict(contract='personal-saved-captures-v1',
        reviewed_reports={'ABC':{'sha256':'b'*64}})))
    correction = read()['items'][0]
    assert correction['id'] == original['id'] and correction['revision'] != original['revision']


@pytest.mark.parametrize('flag,value', [('WOOFI_WATCHLIST_FINANCIALS','0'),('WOOFI_PERSONAL_RESEARCH','0'),
    ('WOOFI_PERSONAL_BIND','0.0.0.0'),('APP_ENV','production'),('WOOFI_PERSONAL_FINANCIAL_READS','captures')])
@pytest.mark.parametrize('profile', ['revenue-v1','qualified-v58'])
def test_default_off_and_production_access_are_denied(financial_store, monkeypatch, flag, value, profile):
    monkeypatch.setenv('WOOFI_WATCHLIST_FINANCIAL_PROFILE',profile)
    monkeypatch.setenv(flag,value)
    assert private_client().post('/personal-research/watchlist-financials',json={'symbols':['ABC']}).status_code == 404


def test_socket_host_spoof_bounds_and_missing_coverage(financial_store):
    for peer,host in [('198.51.100.1','127.0.0.1'),('127.0.0.1','example.test')]:
        c=TestClient(app,client=(peer,1234),base_url='http://'+host)
        assert c.post('/personal-research/watchlist-financials',json={'symbols':['ABC']},
            headers={'X-Forwarded-For':'127.0.0.1'}).status_code == 404
    c=private_client()
    assert c.post('/personal-research/watchlist-financials',json={'symbols':['ABC']*6}).status_code == 422
    page=c.post('/personal-research/watchlist-financials',json={'symbols':['UNKNOWN']}).json()['stocks'][0]['financial']
    assert page['status']=='MISSING_DATA' and not page['items']


@pytest.mark.parametrize('profile', ['revenue-v1','qualified-v58'])
def test_public_watchlist_never_invokes_private_financial_reader(financial_store, client, monkeypatch, profile):
    monkeypatch.setenv('WOOFI_WATCHLIST_FINANCIAL_PROFILE',profile)
    def forbidden(*a,**kw): pytest.fail('Public read must not touch private financials')
    monkeypatch.setattr('src.services.watchlist_intelligence.financial_updates',forbidden)
    body=client.post('/watchlists/intelligence',json={'symbols':['ABC']}).json()
    assert 'financial' not in body['stocks'][0]


def test_qualified_profile_is_explicit_and_reuses_revenue_identity(financial_store, monkeypatch):
    client = private_client()
    read = lambda: client.post('/personal-research/watchlist-financials',json={'symbols':['ABC']}).json()['stocks'][0]['financial']
    baseline = read()
    assert [i['evidence']['insight']['metric'] for i in baseline['items']] == ['revenue']
    monkeypatch.setenv('WOOFI_WATCHLIST_FINANCIAL_PROFILE','qualified-v58')
    expanded = read()
    assert expanded['profile'] == 'qualified-v58'
    assert [i['evidence']['insight']['metric'] for i in expanded['items']] == ['revenue','net_profit']
    assert expanded['items'][0] == baseline['items'][0]
    assert len({i['id'] for i in expanded['items']}) == len(expanded['items'])
    assert {c['metric'] for c in expanded['checks']} == {'revenue','net_profit'}
    monkeypatch.delenv('WOOFI_WATCHLIST_FINANCIAL_PROFILE')
    assert read() == baseline
