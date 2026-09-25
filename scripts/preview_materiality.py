"""Offline engineering preview: python -m scripts.preview_materiality [TICKER]."""
import argparse
import json
from dataclasses import asdict
from datetime import date, timedelta

from src.analytics.market import technical_history
from src.analytics.fundamentals import fundamental_history
from src.schemas.data import MarketBar, FundamentalRecord
from src.schemas.stocks import SymbolRequest
from src.materiality import ScoringContext, detect_and_score_market_events, detect_and_score_fundamental_events


def preview(ticker: str) -> dict:
    ticker = SymbolRequest(ticker=ticker).symbol
    source = "deterministic_demo_fixture"
    # A flat warm-up followed by a price change gives real analytics transitions.
    closes = [100_000.0] * 59 + [103_000.0]
    bars = [MarketBar(ticker=ticker, date=date(2026, 1, 1) + timedelta(days=i),
                      open=close, high=close, low=close, close=close,
                      volume=100_000, source=source) for i, close in enumerate(closes)]
    technicals = technical_history(ticker, bars, source)
    records = [FundamentalRecord(ticker=ticker, period=str(year), source=source,
                revenue=revenue, net_profit=profit, gross_margin=margin, net_margin=profit / revenue)
               for year, revenue, profit, margin in
               ((2023, 100_000_000, 10_000_000, .20),
                (2024, 110_000_000, 12_000_000, .22),
                (2025, 132_000_000, 18_000_000, .25))]
    annual = fundamental_history(ticker, records, source)
    market_contexts = {kind: ScoringContext(own_history_abnormality=.8) for kind in
                       ("ma_cross", "rsi_regime_entry", "abnormal_price_move", "unusual_volume")}
    fundamental_contexts = {kind: ScoringContext(economic_magnitude=.6) for kind in
                            ("revenue_growth_change", "net_profit_growth_change", "margin_change")}
    results = (detect_and_score_market_events(technicals[-2], technicals[-1], market_contexts, is_fixture=True) +
               detect_and_score_fundamental_events(annual[-2], annual[-1], fundamental_contexts, is_fixture=True))
    return {"notice": "Engineering preview only; synthetic fixtures are excluded. V0 is not calibrated or production-ready.",
            "results": [asdict(result) for result in results]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", default="FPT")
    args = parser.parse_args()
    print(json.dumps(preview(args.ticker), indent=2, ensure_ascii=False, default=str, allow_nan=False))


if __name__ == "__main__":
    main()
