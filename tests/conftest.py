import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine
from main import app
from src.db.session import create_tables, get_session
from src.services.stocks import get_market_provider
from src.providers.base import ProviderNotReadyError


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def enable_fk(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    create_tables(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(session):
    class UnconfiguredProvider:
        def validate_symbol(self, symbol):
            raise ProviderNotReadyError("Test provider is not configured")
    def override_session():
        yield session
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_market_provider] = lambda: UnconfiguredProvider()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
