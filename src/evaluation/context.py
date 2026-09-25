"""Trailing-only empirical mappings, version empirical-v0.1; no fitted weights."""
from math import sqrt
from statistics import mean, stdev
from src.materiality.detectors import ScoringContext


def percentile(current: float | None, prior: list[float | None], minimum: int, absolute=False):
    values = [abs(v) if absolute else v for v in prior if v is not None]
    if current is None or len(values) < minimum:
        return None
    value = abs(current) if absolute else current
    return (sum(v < value for v in values) + .5 * sum(v == value for v in values)) / len(values)


def zscore(value, prior):
    if value is None or len(prior) < 2:
        return None
    sd = stdev(prior)
    return (value - mean(prior)) / sd if sd > 0 else None


def build_context(snapshot, technical, prior_features, volume, excess_return, config):
    """prior_features excludes the current session and all future sessions.

    Return/MA-spread/excess are ranked by absolute magnitude; volume and RSI
    distance from 50 are upper-tail midranks. These are baseline mappings, not
    calibrated materiality thresholds. All channels remain independent.
    """
    prior = prior_features[-config.lookback_sessions:]
    returns = [r["daily_return"] for r in prior if r["daily_return"] is not None]
    volumes = [r["volume"] for r in prior if r["volume"] is not None]
    spread = (technical.ma20 / technical.ma50 - 1) if technical.ma20 is not None and technical.ma50 else None
    rsi_distance = abs(technical.rsi14 - 50) if technical.rsi14 is not None else None
    raw = {"daily_return": snapshot.daily_return, "volume": volume,
           "return_zscore": zscore(snapshot.daily_return, returns),
           "relative_volume": volume / mean(volumes) if volumes and mean(volumes) > 0 else None,
           "volume_zscore": zscore(volume, volumes),
           "volatility_regime": stdev(returns) * sqrt(252) if len(returns) >= 2 else None,
           "excess_return": excess_return, "ma_spread": spread, "rsi_distance": rsi_distance,
           "prior_sessions": len(prior), "prior_return_count": len(returns),
           "prior_excess_count": sum(r["excess_return"] is not None for r in prior)}
    market_rank = percentile(excess_return, [r["excess_return"] for r in prior], config.min_history, True)
    mapping = {"abnormal_price_move": ("daily_return", True), "unusual_volume": ("volume", False),
               "ma_cross": ("ma_spread", True), "rsi_regime_entry": ("rsi_distance", False)}
    contexts = {}
    for event, (feature, absolute) in mapping.items():
        own = percentile(raw[feature], [r[feature] for r in prior], config.min_history, absolute)
        # A return residual does not explain a volume anomaly.
        contexts[event] = ScoringContext(own_history_abnormality=own,
            market_relative_abnormality=market_rank if event != "unusual_volume" else None)
    return raw, contexts
