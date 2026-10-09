"""Side-effect-free evaluation entry points."""

from src.schemas.data import TechnicalBar, FundamentalPeriod
from .detectors import ScoringContext, detect_fundamental_events, detect_market_events, detect_d1_factual_events
from .models import MaterialEventCandidate, MaterialityCategory, MaterialityComponents, MaterialityResult, SIGNIFICANCE_CHANNELS
from .scoring import base_materiality, confidence, novelty, significance
from src.corporate_actions.context import enrich_result


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
                                   is_fixture: bool = False, recent_bars: list[TechnicalBar] | None = None,
                                   relative_volume: float | None = None,
                                   corporate_actions=None, generated_at=None) -> tuple[MaterialityResult, ...]:
    if corporate_actions is not None and generated_at is None:
        raise ValueError('Corporate-action context requires an explicit generation timestamp')
    results = tuple(map(evaluate_candidate, detect_market_events(prior, current, contexts,
        is_fixture=is_fixture, recent_bars=recent_bars, relative_volume=relative_volume)))
    return tuple(enrich_result(r, corporate_actions, generated_at=generated_at) for r in results) if corporate_actions is not None else results


def detect_and_score_fundamental_events(prior: FundamentalPeriod | None, current: FundamentalPeriod,
                                        contexts: dict[str, ScoringContext] | None = None, *,
                                        is_fixture: bool = False) -> tuple[MaterialityResult, ...]:
    return tuple(map(evaluate_candidate, detect_fundamental_events(prior, current, contexts, is_fixture=is_fixture)))


def evaluate_d1_market_events(snapshot, ticker: str, session: str, *, generated_at,
                              contexts: dict[str, ScoringContext] | None = None,
                              corporate_actions=None):
    """Versioned D1 runtime; retain negative/unresolved facts even with no events.

    The legacy pair-based entry points and V0 replay stay unchanged. This seam
    requires source/calendar evidence and never fetches live or historical data.
    """
    from .factual import D1MarketEvaluation, prepare_d1_evidence
    prepared = prepare_d1_evidence(snapshot, ticker, session, generated_at)
    decisions = prepared[0]
    candidates = _d1_market_candidates(prepared, contexts)
    results = tuple(map(evaluate_candidate, candidates))
    if corporate_actions is not None:
        results = tuple(enrich_result(r, corporate_actions, generated_at=generated_at) for r in results)
    return D1MarketEvaluation(decisions, results)


def _d1_market_candidates(prepared, contexts):
    """The same factual candidate seam is consumed before scoring by D1 and D4."""
    decisions, current, technicals, fixture = prepared
    contexts = contexts or {}
    if technicals:
        prior = technicals[-2] if len(technicals) > 1 else None
        candidates = detect_market_events(prior, technicals[-1], contexts, is_fixture=fixture,
                                           recent_bars=technicals[-3:], factual_decisions=decisions)
    else:
        candidates = detect_d1_factual_events(current, decisions, contexts, is_fixture=fixture)
    return candidates


def evaluate_d4_market_events(snapshot, ticker: str, session: str, *, generated_at,
                              contexts: dict[str, ScoringContext] | None = None,
                              corporate_actions=None, previous_evaluation=None):
    """Reconstruct D4 from D1 facts; no mutable process memory or D5 delivery."""
    from .episodes import evaluate_episodes
    return evaluate_episodes(snapshot, ticker, session, generated_at=generated_at,
                             contexts=contexts, corporate_actions=corporate_actions,
                             previous_evaluation=previous_evaluation)
