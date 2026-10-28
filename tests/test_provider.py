from datetime import date
from types import SimpleNamespace
import pandas as pd
import pytest
from src.providers import vnstock as adapter
from src.providers.base import ProviderError


def test_mock_sdk_history_and_validation(monkeypatch):
    frame = pd.DataFrame([{"time":"2025-01-02","open":10,"high":12,"low":9,"close":11,"volume":100},
                          {"time":"2024-12-31","open":10,"high":12,"low":9,"close":11,"volume":100}])
    fake = SimpleNamespace(
        Quote=lambda **kwargs: SimpleNamespace(history=lambda **kwargs: frame),
        Listing=lambda **kwargs: SimpleNamespace(all_symbols=lambda: pd.DataFrame([{"symbol":"XYZ","organ_name":"Example"}])))
    monkeypatch.setattr(adapter,"sdk",lambda:fake)
    provider = adapter.VnstockMarketDataProvider()
    assert provider.validate_symbol("XYZ")
    assert not provider.validate_symbol("BAD")
    rows = provider.get_history("XYZ",date(2025,1,1),date(2025,1,3))
    assert len(rows)==1
    assert rows[0].close == 11000
    assert rows[0].volume == 100
    assert rows[0].source == "vnstock:VCI"


def test_mock_sdk_fundamentals(monkeypatch):
    frame = pd.DataFrame([
        {"item_id":"isa3","2025":120,"2024":100},
        {"item_id":"isa20","2025":15,"2024":10},
        {"item_id":"isa5","2025":60,"2024":None},
    ])
    fake = SimpleNamespace(Finance=lambda **kwargs: SimpleNamespace(income_statement=lambda **kwargs: frame))
    monkeypatch.setattr(adapter,"sdk",lambda:fake)
    rows = adapter.VnstockFundamentalDataProvider().get_financials("XYZ")
    assert rows[-1].revenue == 120
    assert rows[-1].gross_margin == .5
    assert rows[-1].net_margin == .125
    assert rows[-1].roe is None
    assert rows[0].gross_margin is None


def test_bank_missing_revenue_stays_null():
    rows = adapter.normalize_financials(pd.DataFrame([{"item_id":"isa20","2025":20},{"item_id":"isb25","2025":100}]),"BANK")
    assert rows[0].revenue is None
    assert rows[0].net_profit == 20
    assert rows[0].net_margin is None


def test_provider_error_is_safe(monkeypatch,caplog):
    def fail(): raise RuntimeError("secret=do-not-log")
    monkeypatch.setattr(adapter,"sdk",fail)
    with pytest.raises(ProviderError) as exc:
        adapter.VnstockMarketDataProvider().get_history("XYZ",date(2025,1,1),date(2025,1,2))
    assert "secret" not in str(exc.value)
    assert "do-not-log" not in caplog.text
    assert "ticker=XYZ" in caplog.text
    assert "error_type=RuntimeError" in caplog.text


def test_invalid_provider_schema_rejected():
    with pytest.raises(ValueError):
        adapter.normalize_history(pd.DataFrame([{"close":10}]),"XYZ",date(2025,1,1),date(2025,1,2))
    with pytest.raises(ValueError):
        adapter.normalize_financials(pd.DataFrame([{"unknown":1}]),"XYZ")
