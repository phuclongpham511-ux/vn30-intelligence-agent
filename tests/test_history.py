from datetime import date, timedelta
import pytest
from main import app
from src.models import Stock
from src.schemas.data import MarketBar, FundamentalRecord
from src.analytics.market import market_snapshot, technical_history
from src.analytics.fundamentals import fundamental_history, fundamental_snapshot
from src.services.stocks import get_market_provider
from src.services.data import get_fundamental_provider
from src.providers.base import ProviderError


def bars(n=70):
    closes = [100 + i * .3 + (i % 7) * 2 for i in range(n)]
    return [MarketBar(ticker="FPT", date=date(2025, 1, 1) + timedelta(days=i),
        open=c, high=c + 1, low=c - 1, close=c, volume=i, source="test") for i, c in enumerate(closes)]


def test_rolling_values_and_every_prefix_matches_snapshot():
    rows = bars()
    series = technical_history("FPT", list(reversed(rows)), "test")
    assert all(row.ma20 is None for row in series[:19])
    assert all(row.ma50 is None for row in series[:49])
    assert all(row.rsi14 is None for row in series[:14])
    assert series[19].ma20 == pytest.approx(sum(row.close for row in rows[:20]) / 20)
    assert series[49].ma50 == pytest.approx(sum(row.close for row in rows[:50]) / 50)
    for i, row in enumerate(series):
        snap = market_snapshot("FPT", rows[:i + 1], "test")
        for field in ("ma20", "ma50", "rsi14"):
            assert getattr(row, field) == pytest.approx(getattr(snap, field)) if getattr(snap, field) is not None else getattr(row, field) is None
    assert technical_history("FPT", [], "test") == []


def test_series_reference_rsi():
    values = [44.34,44.09,44.15,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46,46.03,46.41,46.22,45.64]
    rows = bars(len(values))
    for row, value in zip(rows, values):
        row.open = row.high = row.low = row.close = value
    result = technical_history("FPT", rows, "test")
    assert result[14].rsi14 == pytest.approx(70.4641, abs=.0001)
    assert result[-1].rsi14 == pytest.approx(57.9150, abs=.0001)


def records():
    return [FundamentalRecord(ticker="FPT", period=str(year), revenue=revenue,
        net_profit=profit, gross_margin=margin, source="test")
        for year, revenue, profit, margin in [(2025,120,15,.4),(2022,80,-2,.2),(2024,100,10,.3)]]


def test_annual_order_gaps_nulls_and_limit():
    result = fundamental_history("FPT", records(), "test")
    assert [r.period for r in result] == ["2022", "2024", "2025"]
    assert result[1].revenue_growth_yoy is None
    assert result[2].revenue_growth_yoy == pytest.approx(.2)
    assert result[2].gross_margin_change == pytest.approx(.1)
    assert all(r.roe is None and r.roe_change is None for r in result)
    assert fundamental_history("FPT", records(), "test", 1)[0] == result[-1]
    assert result[-1].model_dump() == fundamental_snapshot("FPT", records(), "test").model_dump()
    assert fundamental_history("FPT", [], "test") == []


@pytest.mark.parametrize("base", [None, 0, -5])
def test_invalid_growth_bases_and_bank_fields(base):
    rows = [FundamentalRecord(ticker="FPT",period="2024",net_profit=base,source="test"),
            FundamentalRecord(ticker="FPT",period="2025",net_profit=10,source="test")]
    current = fundamental_history("FPT",rows,"test")[-1]
    assert current.net_profit_growth_yoy is None
    assert current.revenue is None and current.gross_margin is None and current.roe is None


class Market:
    source = "test"
    def get_history(self, symbol, start, end):
        return [r for r in bars() if start <= r.date <= end]


class Financial:
    source = "test"
    def get_financials(self, symbol):
        return records()


@pytest.fixture
def api(client, session):
    session.add(Stock(symbol="FPT")); session.commit()
    app.dependency_overrides[get_market_provider] = Market
    app.dependency_overrides[get_fundamental_provider] = Financial
    return client


def test_technical_api_range_and_warmup(api):
    response = api.get("/stocks/FPT/technical-history?start=2025-01-01&end=2025-01-20")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 20 and rows[0]["date"] == "2025-01-01" and rows[-1]["date"] == "2025-01-20"
    assert rows[0]["ma20"] is None and rows[-1]["ma20"] is not None and rows[-1]["ma50"] is None
    assert rows[-1]["currency"] == "VND"
    assert api.get("/stocks/FPT/technical-history").status_code == 200
    assert api.get("/stocks/UNKNOWN/technical-history").status_code == 404


@pytest.mark.parametrize("query", ["start=bad", "start=2025-02-01&end=2025-01-01",
    "start=2020-01-01&end=2025-01-01", "end=2999-01-01"])
def test_invalid_ranges(api, query):
    assert api.get("/stocks/FPT/technical-history?" + query).status_code == 422


def test_fundamental_api(api):
    response = api.get("/stocks/FPT/fundamentals/history?limit=1")
    assert response.status_code == 200
    assert response.json()[0]["period"] == "2025"
    assert response.json()[0]["revenue_growth_yoy"] == pytest.approx(.2)
    assert len(api.get("/stocks/FPT/fundamentals/history").json()) == 3
    assert api.get("/stocks/FPT/fundamentals/history?limit=0").status_code == 422
    assert api.get("/stocks/UNKNOWN/fundamentals/history").status_code == 404


@pytest.mark.parametrize("endpoint", ["technical-history", "fundamentals/history"])
def test_sanitized_errors(api, endpoint):
    class Broken:
        source = "test"
        def get_history(self, *args): raise ProviderError("secret upstream traceback")
        def get_financials(self, *args): raise ProviderError("secret upstream traceback")
    app.dependency_overrides[get_market_provider] = Broken
    app.dependency_overrides[get_fundamental_provider] = Broken
    response = api.get("/stocks/FPT/" + endpoint)
    assert response.status_code == 502
    assert "secret" not in response.text and "traceback" not in response.text
