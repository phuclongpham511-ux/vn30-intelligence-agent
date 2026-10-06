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
