"""Pure D5-A delivery over validated D4 V1 evidence, never another detector."""
from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from src.analytics.factual import D1_VERSION, FAMILIES
from src.corporate_actions.models import CorporateActionContext
from src.evaluation.benchmark.inputs import ZONE
from .episodes import D4MarketEvaluation, D4_POLICY

RANKING_POLICY = 'd5-a-base-s-n-c-type-id-v1'
DELIVERY_POLICY = 'd5-attention-budget-3-v1'
ENGINE_VERSION = 'technical-daily-signal-packet-v1'
BB_TYPES = ('bollinger_lower_reversal_volume', 'bollinger_upper_reversal_volume')
REQUIRED_FAMILIES = FAMILIES + BB_TYPES
Truth = Literal['EXISTS', 'DOES_NOT_EXIST', 'UNRESOLVED']


class PacketModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid', allow_inf_nan=False)


class TechnicalFamilyCheck(PacketModel):
    family: str
    state: Truth
    applicable: bool = True
    required: bool = True
    delivery_complete: bool = True
    is_fixture: bool = False
    reason_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    evidence: dict[str, Any]


class TechnicalPacketEvent(PacketModel):
    event_id: str
    event_type: str
    ticker: str
    trading_session: str
    direction: str
    regime: str | None
    episode_id: str | None
    episode_family: str | None
    episode_relationship: str
    episode_status: str
    anchor_session: str | None
    continuity_reason: str | None
    episode_continuous: bool | None
    prior_unresolved_episode_id: str | None
    closed_episode_id: str | None
    factual_decision_ref: str
    evidence_refs: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]
    provenance: dict[str, Any]
    is_fixture: bool
    significance_v0: float | None
    novelty_v0: float | None
    confidence_v0: float | None
    base_v0: float | None
    score_version: str
    score_excluded: bool
    score_exclusion_reason: str | None
    score_reason_codes: tuple[str, ...]
    scoring_inputs: dict[str, Any]
    corporate_action_context: CorporateActionContext
    eligible: bool
    eligibility_reasons: tuple[str, ...]
    ranking_position: int | None = None
    required_delivery: Literal['no'] = 'no'
    required_delivery_policy: str = DELIVERY_POLICY


class TechnicalDailySignalPacket(PacketModel):
    ticker: str
    trading_session: str
    generated_at: datetime
    evaluation_as_of: datetime
    packet_id: str
    upstream_evaluation_id: str
    engine_version: str = ENGINE_VERSION
    factual_policy_version: str = D1_VERSION
    factual_runtime_version: str = 'technical-d1-runtime-v1'
    episode_policy_version: str = D4_POLICY
    episode_runtime_version: str = 'technical-d4-runtime-v1'
    score_version: str = 'v0'
    ranking_policy_version: str = RANKING_POLICY
    delivery_policy_version: str = DELIVERY_POLICY
    packet_state: Literal['HAS_INSIGHTS', 'NO_MEANINGFUL_TECHNICAL_CHANGE',
                          'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE']
    family_checks: tuple[TechnicalFamilyCheck, ...]
    all_current_session_events: tuple[TechnicalPacketEvent, ...]
    ranked_eligible_event_ids: tuple[str, ...]
    top_insights: tuple[TechnicalPacketEvent, ...]
    overflow_event_ids: tuple[str, ...]
    unresolved_checks: tuple[str, ...]
    data_provenance: dict[str, Any]
    limitations: tuple[str, ...]

    def to_json(self) -> str:
        """Explicit JSON dates/enums/nulls; stable key order and finite numbers."""
        return _canonical(self.model_dump(mode='json'))


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':'))


def _aware(value, name):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError(f'{name} must be timezone-aware')
    return value.astimezone(timezone.utc)


def _validate_runtime(evaluation, generated_at):
    from src.services.session_evidence import completion_visible
    if not isinstance(evaluation, D4MarketEvaluation):
        raise ValueError('D5 requires typed D4 V1 runtime results')
    if evaluation.runtime_version != 'technical-d4-runtime-v1' or evaluation.policy_version != D4_POLICY:
        raise ValueError('D5 cannot consume legacy or unrecognized runtime versions')
    generated = _aware(generated_at, 'generated_at')
    as_of = _aware(evaluation.evaluation_as_of, 'evaluation_as_of')
    if generated < as_of:
        raise ValueError('Packet generation cannot precede upstream evaluation knowledge')
    session_day=date.fromisoformat(evaluation.session)
    if session_day > as_of.astimezone(ZONE).date() or (session_day==as_of.astimezone(ZONE).date()
            and not completion_visible(evaluation.data_provenance.get('completion_evidence'),
                evaluation.ticker,evaluation.session,as_of)):
        raise ValueError('D5 requires a completed EOD session')
    for family in FAMILIES[:2]:
        fact = evaluation.factual_decisions.get(family, {})
        if fact.get('predicate_version') != D1_VERSION:
            raise ValueError('D5 requires canonical D1 factual evidence')
    for family, fact in {**evaluation.factual_decisions, **evaluation.pattern_decisions}.items():
        if family in FAMILIES[2:] and fact.get('predicate_version') != 'technical-ma-rsi-transitions-v1':
            raise ValueError('D5 requires versioned MA/RSI transition evidence')
        if family in BB_TYPES and fact.get('predicate_version') != 'technical-bollinger-pattern-check-v1':
            raise ValueError('D5 requires versioned Bollinger evaluation evidence')
        if fact.get('session') is not None and fact['session'] != evaluation.session:
            raise ValueError('Family evidence belongs to a different session')
        if fact.get('cutoff') is not None:
            cutoff = _aware(datetime.fromisoformat(fact['cutoff']), 'factual cutoff')
            if cutoff > as_of:
                raise ValueError('Factual evidence is after the evaluation cutoff')
    return generated, as_of


def _family_checks(evaluation):
    states = {s.family: s for s in evaluation.episode_states if s.session == evaluation.session}
    checks = []
    for family in REQUIRED_FAMILIES:
        fact = deepcopy((evaluation.factual_decisions if family in FAMILIES else
                         evaluation.pattern_decisions).get(family, {}))
        state = fact.get('predicate_result', 'UNRESOLVED')
        reasons = (fact['reason'],) if fact.get('reason') else ()
        if state == 'UNRESOLVED' and family in evaluation.indicator_check_reasons:
            reasons += (evaluation.indicator_check_reasons[family],)
        refs = tuple(fact.get('evidence_refs', ())) if family in BB_TYPES else (
            states[family].factual_decision_ref,) if family in states else ()
        if not fact:
            reasons = ('family_evaluation_evidence_unavailable',)
        if family in FAMILIES and not refs:
            state, reasons = 'UNRESOLVED', reasons + ('factual_reference_unavailable',)
        calendar_incomplete=bool(evaluation.data_provenance.get('calendar_unresolved_sessions'))
        if calendar_incomplete:
            reasons += ('calendar_continuity_unresolved',)
        if evaluation.is_fixture:
            reasons += ('fixture_evidence',)
        checks.append(TechnicalFamilyCheck(family=family, state=state,
                      delivery_complete=not evaluation.is_fixture and not calendar_incomplete, is_fixture=evaluation.is_fixture,
                      reason_codes=tuple(dict.fromkeys(reasons)), evidence_refs=refs, evidence=fact))
    return checks


def _event_view(event, evaluation, checks):
    result, candidate = event.result, event.result.candidate
    family = event.event_type
    check = checks.get(family)
    reasons = []
    if family not in REQUIRED_FAMILIES:
        reasons.append('unsupported_event_family')
    if candidate.ticker != evaluation.ticker or str(candidate.observed_at) != evaluation.session:
        reasons.append('candidate_scope_mismatch')
    if candidate.event_type.value != family or event.policy_version != D4_POLICY:
        reasons.append('event_contract_mismatch')
    if not check or check.state != 'EXISTS':
        reasons.append('current_factual_event_not_verified')
    if check and event.factual_decision_ref not in check.evidence_refs:
        reasons.append('factual_reference_mismatch')
    if family in FAMILIES[2:] and not candidate.is_state_transition:
        reasons.append('verified_transition_required')
    if event.episode_status == 'CLOSED':
        reasons.append('episode_closure_is_not_an_event')
    if family in BB_TYPES:
        volume = evaluation.factual_decisions.get('unusual_volume', {})
        evidence = {item.metric: item.value for item in candidate.evidence}
        if (volume.get('predicate_result') != 'EXISTS' or
                not isinstance(evidence.get('volume'), (int, float)) or evidence['volume'] <= 0 or
                evidence.get('confirmation_session') != evaluation.session):
            reasons.append('bollinger_confirmation_not_verified')
    if candidate.is_fixture or evaluation.is_fixture:
        reasons.append('fixture_evidence')
    if not candidate.evidence:
        reasons.append('missing_event_evidence')
    for item in candidate.evidence:
        if item.as_of is not None:
            # Technical evidence dates are source session dates, not receipt time.
            value = item.as_of.isoformat() if isinstance(item.as_of, (date, datetime)) else item.as_of
            if str(value)[:10] > evaluation.session:
                reasons.append('future_event_evidence')
    context = result.corporate_action_context
    if context.as_of is not None and context.as_of > evaluation.evaluation_as_of:
        raise ValueError('Corporate-action knowledge exceeds upstream evaluation as-of')
    # Scoring availability is not factual eligibility. V0 can exclude an EXISTS
    # event solely because significance channels are unavailable; retain/rank it.
    if result.excluded and result.exclusion_reason != 'no_significance_channels':
        reasons.append(result.exclusion_reason or 'score_exclusion_unexplained')
    if result.score_version != 'v0':
        raise ValueError('D5-A ranking requires existing V0 score outputs')
    values = (result.base_score, result.components.significance,
              result.components.novelty, result.components.confidence)
    if any(value is not None and (type(value) not in (int, float) or not isfinite(value)
                                 or not 0 <= value <= 1) for value in values):
        raise ValueError('Ranking scores must be normalized finite V0 evidence or None')
    fact = evaluation.factual_decisions.get(family, {})
    regime = fact.get('regime') or fact.get('direction')
    episode = next((s for s in evaluation.episode_states if s.family == family
                    and s.session == evaluation.session), None)
    scoring_inputs = {name: getattr(candidate, name) for name in (
        'own_history_abnormality', 'market_relative_abnormality', 'sector_relative_abnormality',
        'economic_magnitude', 'days_since_similar_event', 'is_state_transition',
        'source_quality', 'data_completeness')}
    return TechnicalPacketEvent(event_id=event.event_id, event_type=family, ticker=event.ticker,
        trading_session=event.session, direction=candidate.direction.value, regime=regime,
        episode_id=event.episode_id, episode_family=event.episode_family,
        episode_relationship=event.episode_relationship, episode_status=event.episode_status,
        anchor_session=event.anchor_session, continuity_reason=event.continuity_reason,
        episode_continuous=episode.continuous if episode else None,
        prior_unresolved_episode_id=episode.prior_unresolved_episode_id if episode else None,
        closed_episode_id=episode.closed_episode_id if episode else None,
        factual_decision_ref=event.factual_decision_ref, evidence_refs=tuple(event.evidence_refs),
        evidence=tuple(deepcopy(asdict(item)) for item in candidate.evidence),
        provenance=deepcopy(event.provenance), is_fixture=candidate.is_fixture or evaluation.is_fixture,
        significance_v0=result.components.significance, novelty_v0=result.components.novelty,
        confidence_v0=result.components.confidence, base_v0=result.base_score,
        score_version=result.score_version, score_excluded=result.excluded,
        score_exclusion_reason=result.exclusion_reason, score_reason_codes=result.reason_codes,
        scoring_inputs=scoring_inputs,
        corporate_action_context=result.corporate_action_context.model_copy(deep=True),
        eligible=not reasons, eligibility_reasons=tuple(dict.fromkeys(reasons)))


def _ranking_key(event):
    # Missing sorts after every observed value, including genuine zero, at EACH
    # lexicographic component. No tolerance, rounding, scoring or fallback zero.
    def descending(value):
        return (True, None) if value is None else (False, -value)
    return (descending(event.base_v0), descending(event.significance_v0),
            descending(event.novelty_v0), descending(event.confidence_v0),
            event.event_type, event.event_id)


def build_technical_daily_packet(evaluation: D4MarketEvaluation, *,
                                 generated_at: datetime) -> TechnicalDailySignalPacket:
    """Build one completed stock-day without fetching, recomputing or persisting.

    Caller supplies the V1 D4 evaluation bound to its explicit knowledge timestamp,
    including additive negative Bollinger checks. Generation may be later but
    cannot relabel that knowledge cutoff. Preserve the upstream evidence/versions;
    no inference of an audited delivery ledger or corporate-action absence.
    """
    generated, as_of = _validate_runtime(evaluation, generated_at)
    checks = _family_checks(evaluation)
    checks_by_family = {c.family: c for c in checks}
    current = sorted((e for e in evaluation.events if e.ticker == evaluation.ticker
                      and e.session == evaluation.session), key=lambda e: (e.event_type, e.event_id))
    if len({e.event_id for e in current}) != len(current):
        raise ValueError('Duplicate current-session event identity')
    inventory = tuple(_event_view(e, evaluation, checks_by_family) for e in current)
    ranked = tuple(e.model_copy(update={'ranking_position': index})
                   for index, e in enumerate(sorted((e for e in inventory if e.eligible),
                                                   key=_ranking_key), start=1))
    positions = {e.event_id: e.ranking_position for e in ranked}
    inventory = tuple(e.model_copy(update={'ranking_position': positions.get(e.event_id)}) for e in inventory)
    # A positive check missing its valid emitted event is a delivery discrepancy,
    # never evidence that nothing happened. Keep the original factual truth inside
    # evidence, and expose unresolved delivery completeness separately from truth.
    for index, check in enumerate(checks):
        if check.state == 'EXISTS' and not any(e.eligible and e.event_type == check.family for e in inventory):
            checks[index] = check.model_copy(update={'delivery_complete': False,
                'reason_codes': check.reason_codes + ('factual_event_missing_from_runtime',)})
    unresolved = tuple(c.family for c in checks if c.state == 'UNRESOLVED' or not c.delivery_complete)
    limitations = ['provisional_v0_scores_not_official_calibration',
                   'source_receipt_not_certified_historical_vendor_vintage',
                   'corporate_action_coverage_incomplete']
    limitations.extend(value for value in evaluation.data_provenance.get('limitations', ())
                       if isinstance(value, str))
    for check in checks:
        if check.state == 'UNRESOLVED' or not check.delivery_complete:
            limitations.append('unresolved_family:' + check.family)
    for event in inventory:
        if any(v is None for v in (event.base_v0, event.significance_v0, event.novelty_v0, event.confidence_v0)):
            limitations.append('ranking_score_unavailable:' + event.event_id)
        if event.episode_status == 'UNRESOLVED':
            limitations.append('episode_continuity_unresolved:' + event.event_id)
        if not event.eligible:
            limitations.append('ineligible_event:' + event.event_id)
    state = ('HAS_INSIGHTS' if ranked else 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE' if unresolved
             else 'NO_MEANINGFUL_TECHNICAL_CHANGE')
    result = TechnicalDailySignalPacket(ticker=evaluation.ticker, trading_session=evaluation.session,
        generated_at=generated, evaluation_as_of=as_of, packet_id='',
        upstream_evaluation_id=evaluation.evaluation_id, packet_state=state,
        family_checks=tuple(checks), all_current_session_events=inventory,
        ranked_eligible_event_ids=tuple(e.event_id for e in ranked), top_insights=ranked[:3],
        overflow_event_ids=tuple(e.event_id for e in ranked[3:]), unresolved_checks=unresolved,
        data_provenance=deepcopy(evaluation.data_provenance), limitations=tuple(sorted(set(limitations))))
    identity = result.model_dump(mode='json', exclude={'generated_at', 'packet_id'})
    packet_id = sha256(_canonical(['technical-packet-evaluation-v1', identity]).encode()).hexdigest()
    return result.model_copy(update={'packet_id': packet_id})
