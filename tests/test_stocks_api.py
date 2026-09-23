import pytest
from scripts.seed_stocks import seed_stocks
from src.models import Stock
from src.services.stocks import get_market_provider
from main import app


def test_database_driven_stock_routes(client, session):
    seed_stocks(session)
    session.add(Stock(symbol="VNM"))
    session.commit()
    assert len(client.get("/stocks").json()) == 4
    assert client.get("/stocks/vnm").json()["symbol"] == "VNM"
    assert client.get("/stocks/UNKNOWN").status_code == 404


def test_validation_scaffold_is_honest(client):
    response = client.post("/stocks/validate", json={"symbol": " vnm "})
    assert response.status_code == 200
    assert response.json()["symbol"] == "VNM"
    assert response.json()["valid"] is None
    assert response.json()["status"] == "not_implemented"


@pytest.mark.parametrize("symbol", ["", " ", "BAD!", "A" * 21, 123])
def test_invalid_symbol(client, symbol):
    assert client.post("/stocks/validate", json={"symbol": symbol}).status_code == 422


def test_provider_can_be_replaced(client):
    class FakeProvider:
        def validate_symbol(self, symbol):
            return symbol == "VNM"
    app.dependency_overrides[get_market_provider] = lambda: FakeProvider()
    response = client.post("/stocks/validate", json={"symbol": "vnm"})
    assert response.json()["valid"] is True
    assert response.json()["status"] == "validated"


def test_watchlist_scaffolds(client):
    responses = [
        client.get("/watchlists"),
        client.post("/watchlists", json={"user_id": 1, "name": "Research"}),
        client.post("/watchlists/1/stocks", json={"symbol": "VNM"}),
        client.delete("/watchlists/1/stocks/VNM"),
    ]
    assert all(response.status_code == 501 for response in responses)
