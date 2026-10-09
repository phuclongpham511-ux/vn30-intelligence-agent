"""D1 machine predicate inputs, kept separate from unannotated human truth."""
from src.analytics.factual import (FAMILIES, LEGACY_BENCHMARK_VERSION, finite,
                                   factual_inputs as _shared_factual_inputs)


def factual_inputs(family, session, value, history, *, comparable=True):
    """Preserve the existing benchmark spelling and byte-stable evidence contract.

    Both identifiers use the same mechanics. Runtime uses the canonical D1 name;
    existing benchmark packets keep their original version, without migration.
    """
    return _shared_factual_inputs(family, session, value, history, comparable=comparable,
                                 predicate_version=LEGACY_BENCHMARK_VERSION)


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
