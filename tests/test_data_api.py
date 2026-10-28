from datetime import date, timedelta
import pytest
from main import app
from src.models import Stock
from src.providers.base import ProviderError
from src.schemas.data import MarketBar, FundamentalRecord
from src.services.stocks import get_market_provider
from src.services.data import get_fundamental_provider


class Market:
    source = "test"
    def validate_symbol(self, symbol): return symbol in {"XYZ","NEW"}
    def company_name(self, symbol): return "Example company"
    def get_history(self,symbol,start,end):
        return [MarketBar(ticker=symbol,date=end-timedelta(days=60-i),open=100+i,high=101+i,low=99+i,close=100+i,volume=100,source=self.source) for i in range(60)]


class Financial:
    source = "test"
    def get_financials(self,symbol):
        return [FundamentalRecord(ticker=symbol,period="2025",revenue=100,net_profit=20,source=self.source)]


@pytest.fixture
def data_client(client,session):
    session.add(Stock(symbol="XYZ")); session.commit()
    app.dependency_overrides[get_market_provider] = Market
    app.dependency_overrides[get_fundamental_provider] = Financial
    return client


@pytest.mark.parametrize("endpoint",["market","history","fundamentals","news","overview"])
def test_data_routes(data_client,endpoint):
    response=data_client.get("/stocks/XYZ/"+endpoint)
    assert response.status_code==200
    assert data_client.get("/stocks/UNKNOWN/"+endpoint).status_code==404
    body=response.json()
    if endpoint=="market": assert body["ma50"] == pytest.approx(134.5)
    if endpoint=="fundamentals": assert body["revenue"]==100 and body["roe"] is None
    if endpoint=="news": assert body[0]["is_fixture"] is True
    if endpoint=="overview": assert body["market"]["source"]=="test"


def test_dynamic_add_idempotent(data_client):
    first=data_client.post("/stocks",json={"ticker":" new "})
    assert first.status_code==201 and first.json()["symbol"]=="NEW"
    second=data_client.post("/stocks",json={"symbol":"new"})
    assert second.json()["id"]==first.json()["id"]
    assert len(data_client.get("/stocks").json())==2
    assert data_client.post("/stocks",json={"ticker":"INVALID"}).status_code==404


def test_provider_unavailable(data_client):
    class Broken(Market):
        def get_history(self,*args): raise ProviderError("upstream secret")
    app.dependency_overrides[get_market_provider]=Broken
    response=data_client.get("/stocks/XYZ/market")
    assert response.status_code==502
    assert "secret" not in response.text


def test_empty_history_is_200(data_client):
    class Empty(Market):
        def get_history(self,*args): return []
    app.dependency_overrides[get_market_provider]=Empty
    response=data_client.get("/stocks/XYZ/market")
    assert response.status_code==200 and response.json()["ma20"] is None


def test_history_range(data_client):
    assert data_client.get("/stocks/XYZ/history?start=2025-02-01&end=2025-01-01").status_code==422
