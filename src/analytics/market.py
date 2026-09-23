"""Pure daily analytics. Returns/volatility are fractions, prices are VND."""
import numpy as np
import pandas as pd
from src.schemas.data import MarketBar, MarketSnapshot


def market_snapshot(ticker: str, bars: list[MarketBar], source: str) -> MarketSnapshot:
    if not bars:
        return MarketSnapshot(ticker=ticker, source=source)
    if any(bar.ticker != ticker or bar.source != source for bar in bars):
        raise ValueError("Mixed ticker or source")
    ordered = sorted(bars, key=lambda bar: bar.date)
    if len({bar.date for bar in ordered}) != len(ordered):
        raise ValueError("Duplicate daily bars")
    close = pd.Series([bar.close for bar in ordered], dtype=float)
    volume = pd.Series([bar.volume for bar in ordered], dtype=float)
    high = pd.Series([bar.high for bar in ordered], dtype=float)
    changes = close.diff()
    rsi = None
    if len(close) >= 15:
        gain = changes.clip(lower=0).iloc[1:15].mean()
        loss = (-changes.clip(upper=0)).iloc[1:15].mean()
        for delta in changes.iloc[15:]:
            gain = (gain * 13 + max(delta, 0)) / 14
            loss = (loss * 13 + max(-delta, 0)) / 14
        rsi = 50.0 if gain == loss == 0 else (100.0 if loss == 0 else 100 - 100 / (1 + gain / loss))
    def ret(days):
        return float(close.iloc[-1] / close.iloc[-days - 1] - 1) if len(close) > days else None
    def mean(series, count):
        return float(series.iloc[-count:].mean()) if len(series) >= count else None
    avg_volume = mean(volume, 20)
    return MarketSnapshot(
        ticker=ticker, as_of=ordered[-1].date, close=float(close.iloc[-1]), source=source,
        daily_return=ret(1), return_5d=ret(5), return_20d=ret(20),
        ma20=mean(close, 20), ma50=mean(close, 50), rsi14=rsi,
        avg_volume_20d=avg_volume,
        relative_volume_20d=float(volume.iloc[-1] / avg_volume) if avg_volume else None,
        volatility_20d=float(close.pct_change(fill_method=None).iloc[-20:].std(ddof=1) * np.sqrt(252)) if len(close) >= 21 else None,
        drawdown_from_20d_high=float(close.iloc[-1] / high.iloc[-20:].max() - 1) if len(close) >= 20 else None,
    )
