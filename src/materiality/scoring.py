"""Provisional equal-weight V0 scoring. All functions are pure."""

from .models import MaterialEventCandidate, SIGNIFICANCE_CHANNELS


def significance(candidate: MaterialEventCandidate) -> float | None:
    available = [getattr(candidate, name) for name in SIGNIFICANCE_CHANNELS
                 if getattr(candidate, name) is not None]
    return sum(available) / len(available) if available else None


def novelty(candidate: MaterialEventCandidate) -> float:
    days = candidate.days_since_similar_event
    if candidate.is_state_transition or days is None:
        return 1.0
    if days <= 1:
        return 0.25
    if days <= 5:
        return 0.5
    if days <= 20:
        return 0.75
    return 1.0


def confidence(candidate: MaterialEventCandidate) -> float:
    return 0.0 if candidate.is_fixture else candidate.source_quality * candidate.data_completeness


def base_materiality(s: float, n: float, c: float) -> float:
    return (s + n + c) / 3.0
