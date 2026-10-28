"""Opt-in real network smoke: uv run python -m scripts.smoke_vnstock FPT TCB HPG."""
import argparse
import json
from datetime import date, timedelta
from src.providers.vnstock import VnstockMarketDataProvider, VnstockFundamentalDataProvider
from src.analytics.market import market_snapshot
from src.analytics.fundamentals import fundamental_snapshot


def run():
    parser=argparse.ArgumentParser()
    parser.add_argument("symbols",nargs="+")
    args=parser.parse_args()
    market=VnstockMarketDataProvider()
    financial=VnstockFundamentalDataProvider()
    for value in args.symbols:
        symbol=value.strip().upper()
        if not market.validate_symbol(symbol):
            raise SystemExit(f"FAIL {symbol}: invalid ticker")
        bars=market.get_history(symbol,date.today()-timedelta(days=180),date.today())
        metrics=market_snapshot(symbol,bars,market.source)
        fundamentals=fundamental_snapshot(symbol,financial.get_financials(symbol),financial.source)
        if not bars or metrics.ma50 is None or fundamentals.period is None or fundamentals.net_profit is None:
            raise SystemExit(f"FAIL {symbol}: incomplete data path")
        print(json.dumps({"ticker":symbol,"bars":len(bars),"as_of":str(metrics.as_of),
            "close_vnd":metrics.close,"ma50":metrics.ma50,"period":fundamentals.period,
            "net_profit_vnd":fundamentals.net_profit,"source":metrics.source,"status":"PASS"}))


if __name__=="__main__":
    run()
