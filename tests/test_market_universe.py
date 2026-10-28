from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from src.schemas.stocks import SecurityMetadata, SecurityUniverse


def test_cached_universe_discovers_unadded_equities_without_network(session, client):
    from src.services.universe import sync_universe
    snapshot = SecurityUniverse(raw_count=4, exclusions={'Bond': 1}, securities=[
        SecurityMetadata(symbol='AAA', exchange='HOSE', display_name_en='Alpha issuer'),
        SecurityMetadata(symbol='BBB', exchange='HNX', company_name='Công ty Beta'),
        SecurityMetadata(symbol='CCC', exchange='UPCOM')])
    calls = []
    provider = SimpleNamespace(get_security_universe=lambda: calls.append(1) or snapshot)
    now = datetime.now(timezone.utc)
    assert sync_universe(session, provider=provider, now=now)['status'] == 'ok'
    assert sync_universe(session, provider=provider, now=now + timedelta(minutes=1))['status'] == 'skipped'
    response = client.get('/stocks/universe?q=beta&exchange=HNX').json()
    assert response['total'] == 1 and response['items'][0]['symbol'] == 'BBB'
    assert client.get('/stocks/universe?q=ccc').json()['items'][0]['exchange'] == 'UPCOM'
    assert client.get('/stocks/universe?limit=1&offset=1').json()['items'][0]['symbol'] == 'BBB'
    assert client.get('/stocks').json() == []
    monitored = client.post('/watchlists/monitoring', json={'symbols':['CCC']}).json()['stocks'][0]
    assert monitored['status'] == 'ready' and monitored['developments'] == []
    assert calls == [1]


def test_failed_refresh_preserves_cache_and_lazy_research_validates_only_opened_ticker(session, client):
    from src.services.universe import sync_universe
    from src.services.stocks import get_market_provider
    from main import app
    snapshot = SecurityUniverse(raw_count=1, exclusions={}, securities=[SecurityMetadata(symbol='ZZZ', exchange='HNX')])
    now = datetime.now(timezone.utc)
    sync_universe(session, provider=SimpleNamespace(get_security_universe=lambda: snapshot), now=now)
    def fail(): raise TimeoutError('private credentials')
    assert sync_universe(session, provider=SimpleNamespace(get_security_universe=fail), now=now + timedelta(days=1)) == {'status':'error', 'error':'TimeoutError'}
    assert client.get('/stocks/universe').json()['total'] == 1
    calls = []
    app.dependency_overrides[get_market_provider] = lambda: SimpleNamespace(validate_symbol=lambda symbol: calls.append(symbol) or True)
    assert client.get('/stocks/zzz').json()['exchange'] == 'HNX'
    assert calls == ['ZZZ']
    assert client.get('/stocks/ZZZ').status_code == 200 and calls == ['ZZZ']
    assert client.post('/stocks', json={'symbol':'NONSTOCK'}).status_code == 404


def test_index_membership_cache_composes_with_discovery_and_survives_refresh_failure(session,client):
    from src.services.universe import sync_universe,sync_index_groups
    now=datetime.now(timezone.utc)
    snapshot=SecurityUniverse(raw_count=2,exclusions={},securities=[SecurityMetadata(symbol='AAA',exchange='HOSE'),SecurityMetadata(symbol='BBB',exchange='HNX')])
    sync_universe(session,provider=SimpleNamespace(get_security_universe=lambda:snapshot),now=now)
    provider=SimpleNamespace(get_index_memberships=lambda:{'VN30':['AAA'],'VN100':['AAA'],'HNX30':['BBB']})
    assert sync_index_groups(session,provider=provider,now=now)['status']=='ok'
    groups=client.get('/stocks/universe').json()['index_groups']
    assert groups['groups']['HNX30']==['BBB'] and groups['status']=='healthy'
    assert sync_index_groups(session,provider=provider,now=now+timedelta(minutes=1))['status']=='skipped'
    def fail():raise TimeoutError('private request')
    assert sync_index_groups(session,provider=SimpleNamespace(get_index_memberships=fail),now=now+timedelta(days=1))['status']=='error'
    cached=client.get('/stocks/universe').json()['index_groups']
    assert cached['groups']['VN100']==['AAA'] and cached['status']=='error'


def test_bounded_discovery_composes_index_exchange_search_and_recent_identities(session, client):
    from src.services.universe import sync_universe, sync_index_groups
    now = datetime.now(timezone.utc)
    rows = [SecurityMetadata(symbol=f'X{n:02}', exchange='HNX' if n % 2 else 'HOSE',
                             company_name='Công ty Alpha') for n in range(32)]
    rows += [SecurityMetadata(symbol='AAA', exchange='UPCOM', company_name='X01 issuer')]
    sync_universe(session, provider=SimpleNamespace(get_security_universe=lambda:
        SecurityUniverse(raw_count=len(rows), exclusions={}, securities=rows)), now=now)
    sync_index_groups(session, provider=SimpleNamespace(get_index_memberships=lambda:
        {'VN30': [f'X{n:02}' for n in range(20)], 'VN100': [r.symbol for r in rows]}), now=now)
    page = client.get('/stocks/universe?limit=10&offset=10&index_group=VN30').json()
    assert len(page['items']) == 10 and page['total'] == 20 and page['total_universe'] == 33
    assert page['items'][0]['symbol'] == 'X10'
    filtered = client.get('/stocks/universe?limit=10&index_group=VN30&exchange=HNX&q=cong%20ty').json()
    assert filtered['total'] == 10 and all(r['exchange'] == 'HNX' for r in filtered['items'])
    assert client.get('/stocks/universe?q=X01&limit=6').json()['items'][0]['symbol'] == 'X01'
    assert client.get('/stocks/universe?q=???').json()['total'] == 0
    recent = client.get('/stocks/universe?symbols=X01,X02,MISSING&limit=8').json()
    assert [r['symbol'] for r in recent['items']] == ['X01', 'X02']
    assert client.get('/stocks/universe?symbols=bad%20ticker').status_code == 422
    assert client.get('/stocks/universe?symbols=' + ','.join(f'X{n}' for n in range(51))).status_code == 422
    assert client.get('/stocks/universe?index_group=FAKE').status_code == 422
    assert client.get('/stocks/universe?index_group=HNX30').json()['total'] == 0


def test_index_filter_retains_dated_cache_after_failure_without_inventing_members(session, client):
    from src.services.universe import sync_universe, sync_index_groups
    from src.models import Security
    now = datetime.now(timezone.utc)
    sync_universe(session, provider=SimpleNamespace(get_security_universe=lambda:
        SecurityUniverse(raw_count=1, exclusions={}, securities=[SecurityMetadata(symbol='AAA', exchange='HOSE')])), now=now)
    assert client.get('/stocks/universe?index_group=VN30').json()['items'] == []
    provider = SimpleNamespace(get_index_memberships=lambda: {'VN30': ['AAA']})
    sync_index_groups(session, provider=provider, now=now)
    def fail(): raise TimeoutError()
    sync_index_groups(session, provider=SimpleNamespace(get_index_memberships=fail), now=now+timedelta(days=1))
    cached = client.get('/stocks/universe?index_group=VN30').json()
    assert cached['items'][0]['symbol'] == 'AAA'
    assert cached['index_groups']['status'] == 'error' and cached['index_groups']['last_synced_at']
    record = session.get(Security, 'AAA'); record.is_active = False
    session.add(record); session.commit()
    assert client.get('/stocks/universe?index_group=VN30').json()['total'] == 0
