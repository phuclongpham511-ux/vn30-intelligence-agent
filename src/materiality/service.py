"""Side-effect-free evaluation entry points."""

from src.schemas.data import TechnicalBar, FundamentalPeriod
from .detectors import ScoringContext, detect_fundamental_events, detect_market_events
from .models import MaterialEventCandidate, MaterialityCategory, MaterialityComponents, MaterialityResult, SIGNIFICANCE_CHANNELS
from .scoring import base_materiality, confidence, novelty, significance


def evaluate_candidate(candidate: MaterialEventCandidate) -> MaterialityResult:
    s, n, c = significance(candidate), novelty(candidate), confidence(candidate)
    reasons = list(candidate.reason_codes)
    reasons.extend(f"unavailable:{name}" for name in SIGNIFICANCE_CHANNELS if getattr(candidate, name) is None)
    if candidate.data_completeness < 1:
        reasons.append("incomplete_evidence")
    if not candidate.evidence:
        reasons.append("missing_evidence")
    if candidate.days_since_similar_event is None and not candidate.is_state_transition:
        reasons.append("similar_event_history_unavailable")
    exclusion = ("fixture_evidence" if candidate.is_fixture else
                 "news_not_supported_v0" if candidate.category == MaterialityCategory.NEWS else
                 "missing_evidence" if not candidate.evidence else
                 "no_significance_channels" if s is None else None)
    if exclusion:
        reasons.append(exclusion)
    return MaterialityResult(candidate, MaterialityComponents(s, n, c),
                             None if exclusion else base_materiality(s, n, c),
                             excluded=exclusion is not None, exclusion_reason=exclusion,
                             reason_codes=tuple(dict.fromkeys(reasons)))


def detect_and_score_market_events(prior: TechnicalBar | None, current: TechnicalBar,
                                   contexts: dict[str, ScoringContext] | None = None, *,
                                   is_fixture: bool = False) -> tuple[MaterialityResult, ...]:
    return tuple(map(evaluate_candidate, detect_market_events(prior, current, contexts, is_fixture=is_fixture)))


def detect_and_score_fundamental_events(prior: FundamentalPeriod | None, current: FundamentalPeriod,
                                        contexts: dict[str, ScoringContext] | None = None, *,
                                        is_fixture: bool = False) -> tuple[MaterialityResult, ...]:
    return tuple(map(evaluate_candidate, detect_fundamental_events(prior, current, contexts, is_fixture=is_fixture)))
