from datetime import date, timedelta
import math
import pytest
from pydantic import ValidationError
from src.schemas.data import MarketBar, FundamentalRecord
from src.analytics.market import market_snapshot
from src.analytics.fundamentals import fundamental_snapshot


def bars(count=60, flat=False, volume=100):
    return [MarketBar(ticker="XYZ", date=date(2025,1,1)+timedelta(days=i),
        open=100 if flat else 100+i, close=100 if flat else 100+i,
        high=101 if flat else 101+i, low=99 if flat else 99+i,
        volume=volume, source="test") for i in range(count)]


def test_market_known_values():
    rows = bars()
    rows[-1].volume = 200
    result = market_snapshot("XYZ", rows, "test")
    assert result.daily_return == pytest.approx(159/158-1)
    assert result.return_5d == pytest.approx(159/154-1)
    assert result.return_20d == pytest.approx(159/139-1)
    assert result.ma20 == pytest.approx(149.5)
    assert result.ma50 == pytest.approx(134.5)
    assert result.rsi14 == 100
    assert result.avg_volume_20d == 105
    assert result.relative_volume_20d == pytest.approx(200/105)
    returns = [1/i for i in range(139,159)]
    mean = sum(returns)/20
    expected = math.sqrt(sum((value-mean)**2 for value in returns)/19)*math.sqrt(252)
    assert result.volatility_20d == pytest.approx(expected)
    assert result.drawdown_from_20d_high == pytest.approx(159/160-1)


def test_empty_and_warmup():
    assert market_snapshot("XYZ", [], "test").as_of is None
    result = market_snapshot("XYZ", bars(1), "test")
    for key in ("daily_return","return_20d","ma20","ma50","rsi14","avg_volume_20d","relative_volume_20d","volatility_20d","drawdown_from_20d_high"):
        assert getattr(result,key) is None
    assert market_snapshot("XYZ", bars(20), "test").ma20 is not None
    assert market_snapshot("XYZ", bars(20), "test").return_20d is None


def test_flat_and_zero_volume():
    result = market_snapshot("XYZ", bars(flat=True,volume=0), "test")
    assert result.rsi14 == 50
    assert result.relative_volume_20d is None
    assert result.volatility_20d == 0


def test_wilder_rsi_reference():
    values = [44.34,44.09,44.15,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46,46.03,46.41,46.22,45.64]
    rows = [MarketBar(ticker="XYZ",date=date(2025,1,1)+timedelta(days=i),open=c,high=c,low=c,close=c,volume=1,source="test") for i,c in enumerate(values)]
    assert market_snapshot("XYZ", rows[:15], "test").rsi14 == pytest.approx(70.4641,abs=.0001)
    assert market_snapshot("XYZ", rows, "test").rsi14 == pytest.approx(57.9150,abs=.0001)


def test_invalid_and_duplicate_bars():
    with pytest.raises(ValidationError):
        MarketBar(ticker="X", date="2025-01-01",open=2,high=1,low=1,close=2,volume=0,source="test")
    with pytest.raises(ValidationError):
        MarketBar(ticker="X", date="2025-01-01",open=2,high=2,low=1,close=float("nan"),volume=0,source="test")
    with pytest.raises(ValueError):
        market_snapshot("XYZ", bars(1)*2, "test")
    assert market_snapshot("XYZ", list(reversed(bars())), "test") == market_snapshot("XYZ", bars(), "test")


def test_fundamental_yoy_exact_period():
    records = [FundamentalRecord(ticker="XYZ",period="2024",revenue=100,net_profit=10,gross_margin=.4,net_margin=.1,roe=.2,source="test"),
               FundamentalRecord(ticker="XYZ",period="2025",revenue=120,net_profit=15,gross_margin=.5,net_margin=.125,roe=.25,source="test")]
    result = fundamental_snapshot("XYZ",records,"test")
    assert result.revenue_growth_yoy == pytest.approx(.2)
    assert result.net_profit_growth_yoy == pytest.approx(.5)
    assert result.gross_margin_change == pytest.approx(.1)
    assert result.net_margin_change == pytest.approx(.025)
    assert result.roe_change == pytest.approx(.05)
    records[0].period = "2023"
    assert fundamental_snapshot("XYZ",records,"test").revenue_growth_yoy is None


@pytest.mark.parametrize("profit", [None, 0, -10])
def test_noncomparable_profit_growth(profit):
    records = [FundamentalRecord(ticker="XYZ",period="2024",net_profit=profit,source="test"),
               FundamentalRecord(ticker="XYZ",period="2025",net_profit=15,source="test")]
    assert fundamental_snapshot("XYZ",records,"test").net_profit_growth_yoy is None
