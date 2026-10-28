"""Opt-in SSI smoke: uv run python -m scripts.smoke_ssi FPT HPG TCB VNM."""
import argparse
from datetime import timedelta
import json

from src.analytics.market import market_snapshot
from src.providers.base import ProviderError
from src.providers.ssi import SsiMarketDataProvider, vietnam_today


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="+")
    args = parser.parse_args()
    today = vietnam_today()
    with SsiMarketDataProvider() as provider:
        for value in args.symbols:
            symbol = value.strip().upper()
            try:
                if not provider.validate_symbol(symbol):
                    raise ProviderError("Invalid ticker.")
                bars = provider.get_history(symbol, today - timedelta(days=180), today)
                latest = provider.get_latest(symbol)
                metrics = market_snapshot(symbol, bars, provider.source)
                if (not bars or latest is None or latest != bars[-1]
                    or metrics.ma50 is None or metrics.rsi14 is None
                    or any(bar.date >= today for bar in bars)
                    or [bar.date for bar in bars] != sorted({bar.date for bar in bars})):
                    raise ProviderError("Incomplete SSI data path.")
                print(json.dumps({"ticker": symbol, "bar_count": len(bars),
                    "first_date": str(bars[0].date), "last_completed_date": str(latest.date),
                    "close_vnd": latest.close, "volume_shares": latest.volume,
                    "ma50": metrics.ma50, "rsi14": metrics.rsi14,
                    "source": provider.source, "status": "PASS"}))
            except ProviderError as exc:
                raise SystemExit(f"FAIL {symbol}: {exc}") from None


if __name__ == "__main__":
    run()
