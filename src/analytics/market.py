"""Pure daily analytics. Returns/volatility are fractions, prices are VND."""
import numpy as np
import pandas as pd
from src.schemas.data import MarketBar, MarketSnapshot, TechnicalBar


def ordered_bars(ticker: str, bars: list[MarketBar], source: str) -> list[MarketBar]:
    if any(bar.ticker != ticker or bar.source != source for bar in bars):
        raise ValueError("Mixed ticker or source")
    ordered = sorted(bars, key=lambda bar: bar.date)
    if len({bar.date for bar in ordered}) != len(ordered):
        raise ValueError("Duplicate daily bars")
    return ordered


def rolling_indicators(closes: list[float]) -> tuple[list, list, list]:
    """One Wilder implementation for both snapshots and historical series."""
    close = pd.Series(closes, dtype=float)
    def sma(window):
        return [None if pd.isna(value) else float(value) for value in close.rolling(window).mean()]
    rsi = [None] * len(closes)
    if len(closes) >= 15:
        changes = close.diff()
        gain = changes.clip(lower=0).iloc[1:15].mean()
        loss = (-changes.clip(upper=0)).iloc[1:15].mean()
        def value():
            return float(50 if gain == loss == 0 else (100 if loss == 0 else 100 - 100 / (1 + gain / loss)))
        rsi[14] = value()
        for i in range(15, len(closes)):
            delta = closes[i] - closes[i - 1]
            gain = (gain * 13 + max(delta, 0)) / 14
            loss = (loss * 13 + max(-delta, 0)) / 14
            rsi[i] = value()
    return sma(20), sma(50), rsi


def technical_history(ticker: str, bars: list[MarketBar], source: str) -> list[TechnicalBar]:
    ordered = ordered_bars(ticker, bars, source)
    ma20, ma50, rsi = rolling_indicators([bar.close for bar in ordered])
    return [TechnicalBar(**bar.model_dump(), ma20=ma20[i], ma50=ma50[i], rsi14=rsi[i])
            for i, bar in enumerate(ordered)]


def market_snapshot(ticker: str, bars: list[MarketBar], source: str) -> MarketSnapshot:
    if not bars:
        return MarketSnapshot(ticker=ticker, source=source)
    ordered = ordered_bars(ticker, bars, source)
    close = pd.Series([bar.close for bar in ordered], dtype=float)
    volume = pd.Series([bar.volume for bar in ordered], dtype=float)
    high = pd.Series([bar.high for bar in ordered], dtype=float)
    ma20, ma50, rsi = rolling_indicators(close.tolist())
    def ret(days):
        return float(close.iloc[-1] / close.iloc[-days - 1] - 1) if len(close) > days else None
    avg_volume = float(volume.iloc[-20:].mean()) if len(volume) >= 20 else None
    return MarketSnapshot(
        ticker=ticker, as_of=ordered[-1].date, close=float(close.iloc[-1]), source=source,
        daily_return=ret(1), return_5d=ret(5), return_20d=ret(20),
        ma20=ma20[-1], ma50=ma50[-1], rsi14=rsi[-1],
        avg_volume_20d=avg_volume,
        relative_volume_20d=float(volume.iloc[-1] / avg_volume) if avg_volume else None,
        volatility_20d=float(close.pct_change(fill_method=None).iloc[-20:].std(ddof=1) * np.sqrt(252)) if len(close) >= 21 else None,
        drawdown_from_20d_high=float(close.iloc[-1] / high.iloc[-20:].max() - 1) if len(close) >= 20 else None,
    )
