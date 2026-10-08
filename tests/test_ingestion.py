from threading import Event

from src.services import ingestion


def test_web_refresh_starts_background_ingestion(client, session, monkeypatch):
    monkeypatch.setattr(ingestion, 'get_engine', lambda: session.get_bind())
    completed = Event()
    monkeypatch.setattr(ingestion, 'run_cycle', lambda engine, **kw: completed.set() or {})
    ingestion._running = False
    ingestion._last_started = None
    response = client.post('/ingestion/refresh')
    assert response.status_code == 202
    assert response.json() == {'status': 'started'}
    assert completed.wait(2)


def test_web_refresh_coalesces_active_or_recent_requests(client, session, monkeypatch):
    monkeypatch.setattr(ingestion, 'get_engine', lambda: session.get_bind())
    started = Event()
    release = Event()
    monkeypatch.setattr(ingestion, 'run_cycle', lambda engine, **kw: (started.set(), release.wait(2)))
    ingestion._running = False
    ingestion._last_started = None
    first = client.post('/ingestion/refresh')
    assert first.status_code == 202
    assert started.wait(2)
    assert client.post('/ingestion/refresh').json() == {'status': 'already_running'}
    release.set()
    assert client.post('/ingestion/refresh').json() == {'status': 'cooldown'}
