from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine
import main
from src.db.session import get_session


def test_development_startup_initializes_news_without_ingesting(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    original = main.create_tables
    monkeypatch.setattr(main, 'get_settings', lambda: SimpleNamespace(app_env='development'))
    monkeypatch.setattr(main, 'create_tables', lambda: original(engine))
    def database():
        with Session(engine) as session:
            yield session
    main.app.dependency_overrides[get_session] = database
    try:
        for _ in range(2):
            with TestClient(main.app) as client:
                assert client.get('/news/latest').json() == []
                assert all(row['status'] == 'not_attempted' for row in client.get('/news/sources').json())
                assert client.get('/stocks').json() == []
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()


def test_production_startup_does_not_apply_schema_changes(monkeypatch):
    monkeypatch.setattr(main, 'get_settings', lambda: SimpleNamespace(app_env='production'))
    def unexpected():
        raise AssertionError('Production schema changes must remain explicit')
    monkeypatch.setattr(main, 'create_tables', unexpected)
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200
