from src.services import ingestion


def test_web_refresh_records_durable_intent_without_executing_collector(client, session, monkeypatch):
    monkeypatch.setattr(ingestion, 'get_engine', lambda: session.get_bind())
    executed = []
    monkeypatch.setattr(ingestion, 'run_cycle', lambda *a, **kw: executed.append(True), raising=False)
    response = client.post('/ingestion/refresh')
    assert response.status_code == 202
    assert response.json() == {'status': 'pending_worker'}
    assert not executed
    assert client.post('/ingestion/refresh').json() == {'status': 'pending_worker'}
    assert not executed
