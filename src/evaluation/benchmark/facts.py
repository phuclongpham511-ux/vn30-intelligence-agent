"""D1 machine predicate inputs, kept separate from unannotated human truth."""
from datetime import date
from math import isfinite

FAMILIES = ("abnormal_price_move", "unusual_volume", "ma_cross", "rsi_regime_entry")


def finite(value):
    return type(value) in (int, float) and isfinite(value)


def factual_inputs(family, session, value, history, *, comparable=True):
    if family not in FAMILIES[:2]:
        raise ValueError("D1 applies to price and HIGH volume only")
    date.fromisoformat(session)
    price = family == "abnormal_price_move"
    prior = sorted((r for r in history if r["session"] < session), key=lambda r: r["session"])
    if len({r["session"] for r in prior}) != len(prior):
        raise ValueError("Duplicate reference sessions")
    valid, excluded = [], []
    for row in prior:
        if row.get("comparable") is not True or not finite(row["value"]) or (not price and row["value"] < 0):
            excluded.append({"session": row["session"], "reason": "missing_or_noncomparable"})
        else:
            valid.append({"session": row["session"], "value": abs(row["value"]) if price else row["value"]})
    valid = valid[-252:]
    n = len(valid)
    k = (95 * n + 99) // 100 if n >= 60 else None
    q95 = sorted(r["value"] for r in valid)[k - 1] if k else None
    usable = comparable is True and finite(value) and (price or value >= 0)
    comparison = (abs(value) if price else value) if usable else None
    reason = "invalid_current_evidence" if not usable else "insufficient_history" if n < 60 else None
    return {
        "predicate_version": "d1-nearest-rank-q95-v1", "family": family,
        "comparison_value": comparison, "unit": "fraction" if price else "shares",
        "direction": ("up" if value > 0 else "down" if value < 0 else "neutral")
        if price and usable else "HIGH" if usable else None,
        "history": valid, "excluded": excluded, "n": n, "order_index": k, "q95": q95,
        "predicate_result": "UNRESOLVED" if reason else "EXISTS" if comparison >= q95 else "DOES_NOT_EXIST",
        "reason": reason,
    }


def transition_inputs(family, prior, current, *, continuous=True):
    """Frozen MA difference / RSI transitions; current state is not a repeated event."""
    if family not in FAMILIES[2:]:
        raise ValueError("Unknown transition family")
    valid = continuous and finite(prior) and finite(current)
    if family == "rsi_regime_entry":
        valid = valid and 0 <= prior <= 100 and 0 <= current <= 100
    if not valid:
        return {"predicate_result": "UNRESOLVED", "direction": None, "regime": None,
                "reason": "missing_or_nonconsecutive_indicator_pair"}
    if family == "ma_cross":
        entry = prior <= 0 < current or prior >= 0 > current
        regime = "up" if current > 0 else "down" if current < 0 else None
    else:
        entry = prior <= 70 < current or prior >= 30 > current
        regime = "upper" if current > 70 else "lower" if current < 30 else None
    return {"predicate_result": "EXISTS" if entry else "DOES_NOT_EXIST",
            "direction": regime if entry else None, "regime": regime, "reason": None}
