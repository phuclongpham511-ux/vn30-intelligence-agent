"""Versioned prospective episode reconstruction; no ranking or delivery policy."""
from dataclasses import asdict, dataclass, field
from copy import deepcopy
from datetime import datetime
from typing import Literal

from src.analytics.episodes import link_episodes
from src.analytics.factual import FAMILIES
from src.evaluation.benchmark.facts import transition_inputs
from src.evaluation.benchmark.inputs import eod
from .factual import _hash, prepare_d1_evidence
from .models import MaterialityResult

D4_POLICY = 'd4-episode-policy-v1'


@dataclass(frozen=True)
class EpisodeState:
    family: str
    session: str
    factual_result: str
    factual_decision_ref: str
    lifecycle: Literal['NONE', 'ANCHOR', 'CONTINUATION', 'CLOSED', 'UNRESOLVED']
    relationship: str
    episode_id: str | None
    anchor_session: str | None
    closed_episode_id: str | None
    prior_unresolved_episode_id: str | None
    previous_session: str | None
    continuous: bool
    reason: str | None
    evidence_refs: tuple[str, ...]
    policy_version: str = D4_POLICY


@dataclass(frozen=True)
class TechnicalEventObservation:
    event_id: str
    event_type: str
    ticker: str
    session: str
    factual_decision_ref: str
    episode_id: str | None
    episode_family: str | None
    episode_relationship: str
    episode_status: str
    anchor_session: str | None
    continuity_reason: str | None
    evidence_refs: tuple[str, ...]
    provenance: dict
    result: MaterialityResult
    policy_version: str = D4_POLICY


@dataclass(frozen=True)
class EpisodeRevision:
    family: str
    session: str
    reason: str
    before: EpisodeState | None
    after: EpisodeState | None


@dataclass(frozen=True)
class D4MarketEvaluation:
    ticker: str
    session: str
    evaluation_id: str
    factual_decisions: dict
    events: tuple[TechnicalEventObservation, ...]
    episode_states: tuple[EpisodeState, ...]
    episode_history: tuple[EpisodeState, ...]
    supersedes_evaluation_id: str | None = None
    revisions: tuple[EpisodeRevision, ...] = ()
    runtime_version: str = 'technical-d4-runtime-v1'
    policy_version: str = D4_POLICY
    # Additive delivery evidence; event/lifecycle identities and scoring stay intact.
    evaluation_as_of: datetime | None = None
    pattern_decisions: dict = field(default_factory=dict)
    data_provenance: dict = field(default_factory=dict)
    is_fixture: bool = False
    indicator_check_reasons: dict = field(default_factory=dict)

    @property
    def results(self):
        return tuple(e.result for e in self.events)


def _pattern_checks(prepared, candidates, volume_ref, session):
    """Record resolved negatives/insufficient inputs at the existing detector seam.

    EXISTS comes only from the unchanged detector. A known negative volume gate
    resolves the conjunction without inventing indicator values. Otherwise all
    three potential touch sessions need usable bands before claiming no pattern.
    No D1 recomputation or independent positive-pattern detector is introduced.
    """
    from src.analytics.factual import finite
    decisions, _, technicals, _ = prepared
    volume = decisions['unusual_volume']
    recent = technicals[-3:]
    current = recent[-1] if recent else None
    prior = recent[-2] if len(recent) > 1 else None
    emitted = {c.event_type.value for c in candidates}
    checks = {}
    for kind, band in (('bollinger_lower_reversal_volume', 'bb50_lower'),
                       ('bollinger_upper_reversal_volume', 'bb50_upper')):
        if kind in emitted:
            state, reason = 'EXISTS', None
        elif volume['predicate_result'] == 'DOES_NOT_EXIST':
            state, reason = 'DOES_NOT_EXIST', 'volume_confirmation_not_met'
        elif volume['predicate_result'] == 'UNRESOLVED':
            state, reason = 'UNRESOLVED', 'volume_confirmation_unresolved'
        elif volume['comparison_value'] == 0:
            state, reason = 'DOES_NOT_EXIST', 'positive_volume_not_met'
        elif not prior or not current:
            state, reason = 'UNRESOLVED', 'missing_consecutive_indicator_pair'
        elif not all(finite(v) for v in (current.bb50_std, getattr(current, band))):
            state, reason = 'UNRESOLVED', 'insufficient_bollinger_warmup_or_missing_indicator'
        elif current.bb50_std == 0:
            state, reason = 'DOES_NOT_EXIST', 'zero_width_bands'
        elif len(recent) < 3 or any(not all(finite(v) for v in (row.bb50_std, getattr(row, band))) for row in recent):
            state, reason = 'UNRESOLVED', 'incomplete_bollinger_touch_window'
        else:
            state, reason = 'DOES_NOT_EXIST', 'pattern_not_confirmed'
        raw = {'predicate_result': state, 'reason': reason, 'session': session,
               'predicate_version': 'technical-bollinger-pattern-check-v1',
               'volume_decision_ref': volume_ref,
               'indicator_observations': [r.model_dump(mode='json') for r in recent]}
        raw['evidence_refs'] = (volume_ref, _hash([kind, raw]))
        checks[kind] = raw
    return checks


def _daily_facts(prepared, session, previous_session, previous_volume_valid):
    """D1 facts plus the existing MA/RSI transition evidence, never V0 guesses."""
    decisions, _, technicals, _ = prepared
    current = technicals[-1] if technicals else None
    prior = technicals[-2] if len(technicals) > 1 else None
    indicator_pair = (prior is not None and current is not None
                      and prior.date.isoformat() == previous_session)
    def spread(row):
        return row.ma20 - row.ma50 if row is not None and row.ma20 is not None and row.ma50 is not None else None
    transitions = {
        'ma_cross': transition_inputs('ma_cross', spread(prior), spread(current), continuous=indicator_pair),
        'rsi_regime_entry': transition_inputs('rsi_regime_entry', prior.rsi14 if prior else None,
                                             current.rsi14 if current else None, continuous=indicator_pair),
    }
    for family, decision in transitions.items():
        decision.update(session=session, cutoff=decisions['abnormal_price_move'].get('cutoff',eod(session).isoformat()),
                        predicate_version='technical-ma-rsi-transitions-v1',
                        source=decisions['abnormal_price_move']['source'],
                        source_subset_sha256=decisions['abnormal_price_move'].get('source_subset_sha256'),
                        prior_value=spread(prior) if family == 'ma_cross' else prior.rsi14 if prior else None,
                        current_value=spread(current) if family == 'ma_cross' else current.rsi14 if current else None)
    facts = {**decisions, **transitions}
    volume_valid = decisions['unusual_volume']['comparison_value'] is not None
    continuity = {
        'abnormal_price_move': decisions['abnormal_price_move'].get('signed_return') is not None,
        'unusual_volume': volume_valid and previous_volume_valid,
        'ma_cross': bool(indicator_pair), 'rsi_regime_entry': bool(indicator_pair),
    }
    return facts, continuity, volume_valid


def _indicator_check_reasons(prepared):
    """Additive completeness diagnostics; do not alter frozen transition facts."""
    decisions, current, technicals, _ = prepared
    reasons = {}
    for family, metrics in (('ma_cross', ('ma20', 'ma50')), ('rsi_regime_entry', ('rsi14',))):
        if not current or not technicals:
            reasons[family] = decisions['abnormal_price_move'].get('reason') or 'missing_native_source_observation'
        elif len(technicals) < 2:
            reasons[family] = 'missing_consecutive_indicator_pair'
        elif any(getattr(row, metric) is None for row in technicals[-2:] for metric in metrics):
            reasons[family] = 'insufficient_indicator_warmup'
    return reasons


def evaluate_episodes(snapshot, ticker, session, *, generated_at, contexts=None,
                      corporate_actions=None, previous_evaluation=None):
    from .service import _d1_market_candidates, evaluate_candidate
    from src.corporate_actions.context import enrich_result

    prepared = prepare_d1_evidence(snapshot, ticker, session, generated_at)
    # D1 validates source/calendar first. Invalid global metadata cannot acquire
    # lifecycle certainty by replaying otherwise plausible raw rows.
    try:
        days = sorted(d for d in snapshot.get('calendar', []) if d <= session)
    except TypeError:
        days = []
    global_failure = not days or len(set(days)) != len(days) or days[-1] != session or all(
        'source_subset_sha256' not in decision for decision in prepared[0].values())
    if global_failure:
        days = [session]
    streams = {family: [] for family in FAMILIES}
    references, facts_by_day = {}, {}
    previous_day, previous_volume_valid = None, False
    for day in days:
        inputs = prepared if day == session else prepare_d1_evidence(snapshot, ticker, day, generated_at)
        facts, continuity, previous_volume_valid = _daily_facts(inputs, day, previous_day, previous_volume_valid)
        facts_by_day[day] = facts
        for family, fact in facts.items():
            reference = _hash([D4_POLICY, ticker, family, day, fact])
            references[(family, day)] = reference
            streams[family].append({'session': day, **fact, 'continuous': continuity[family]})
        previous_day = day

    history = []
    for family in FAMILIES:
        # Bounded operational reads cannot prove a pre-window anchor. Preserve
        # the original runtime default for existing callers; an explicit unknown
        # left boundary uses the helper's conservative unresolved warm-up mode.
        links = link_episodes(ticker, family, streams[family],
                              runtime_initial_anchor=snapshot.get('episode_history_boundary') != 'unknown')
        anchors, previous_link = {}, None
        for index, link in enumerate(links):
            if link['lifecycle'] == 'ANCHOR':
                anchors[link['episode_id']] = link['session']
            previous = days[index - 1] if index else None
            refs = (references[(family, link['session'])],)
            if previous:
                refs += (references[(family, previous)],)
            unresolved_prior = link['prior_unresolved_episode_id']
            reason = link['reason']
            # A verified new regime entry may anchor after a gap, but never
            # claim a dated close for the earlier unresolved episode.
            if (link['lifecycle'] == 'ANCHOR' and previous_link
                    and previous_link['prior_unresolved_episode_id']):
                unresolved_prior = previous_link['prior_unresolved_episode_id']
                reason = 'prior_episode_close_unresolved'
            history.append(EpisodeState(family=family, session=link['session'],
                factual_result=streams[family][index]['predicate_result'], factual_decision_ref=refs[0],
                lifecycle=link['lifecycle'], relationship=link['relationship'], episode_id=link['episode_id'],
                anchor_session=anchors.get(link['episode_id']), closed_episode_id=link['closed_episode_id'],
                prior_unresolved_episode_id=unresolved_prior, previous_session=previous,
                continuous=streams[family][index]['continuous'],
                reason=reason or streams[family][index].get('reason'), evidence_refs=refs))
            previous_link = link
    # Chronological evidence inventory, not attention ranking.
    history.sort(key=lambda s: (s.session, FAMILIES.index(s.family)))
    states = tuple(s for s in history if s.session == session)
    current_states = {s.family: s for s in states}
    evaluation_id = _hash([D4_POLICY, ticker, session, [asdict(s) for s in history]])
    revisions, supersedes = [], None
    if previous_evaluation is not None:
        if previous_evaluation.ticker != ticker or previous_evaluation.session != session:
            raise ValueError('Correction comparison requires the same ticker/session')
        if previous_evaluation.evaluation_id != evaluation_id:
            supersedes = previous_evaluation.evaluation_id
            old = {(s.family, s.session): s for s in previous_evaluation.episode_history}
            new = {(s.family, s.session): s for s in history}
            for key in sorted(old.keys() | new.keys()):
                if old.get(key) != new.get(key):
                    relationship_fields = ('lifecycle', 'relationship', 'episode_id', 'anchor_session',
                                           'closed_episode_id', 'prior_unresolved_episode_id')
                    before, after = old.get(key), new.get(key)
                    relationship_changed = before is None or after is None or any(
                        getattr(before, field) != getattr(after, field) for field in relationship_fields)
                    reason = 'episode_relationship_revised' if relationship_changed else 'factual_evidence_revised'
                    revisions.append(EpisodeRevision(*key, reason,
                                                     old.get(key), new.get(key)))

    # Factual candidates and lifecycle are established before unchanged scoring.
    events = []
    candidates = _d1_market_candidates(prepared, contexts)
    patterns = _pattern_checks(prepared, candidates, references[('unusual_volume', session)], session)
    for candidate in candidates:
        family = candidate.event_type.value
        is_bollinger = family not in FAMILIES
        episode = None if is_bollinger else current_states[family]
        fact_family = 'unusual_volume' if is_bollinger else family
        fact_ref = references[(fact_family, session)]
        result = evaluate_candidate(candidate)
        if corporate_actions is not None:
            result = enrich_result(result, corporate_actions, generated_at=generated_at)
        events.append(TechnicalEventObservation(
            event_id=_hash(['technical-event-v1', ticker, family, session])[:24],
            event_type=family, ticker=ticker, session=session, factual_decision_ref=fact_ref,
            episode_id=episode.episode_id if episode else None,
            episode_family=family if episode else None,
            episode_relationship=episode.relationship if episode else 'NOT_APPLICABLE',
            episode_status=episode.lifecycle if episode else 'NOT_APPLICABLE',
            anchor_session=episode.anchor_session if episode else None,
            continuity_reason=episode.reason if episode else 'bollinger_episode_policy_not_approved',
            evidence_refs=episode.evidence_refs if episode else (fact_ref,),
            provenance=deepcopy(snapshot.get('provenance', {})), result=result))
    return D4MarketEvaluation(ticker, session, evaluation_id, deepcopy(facts_by_day[session]), tuple(events),
                              states, tuple(history), supersedes, tuple(revisions),
                              evaluation_as_of=generated_at, pattern_decisions=patterns,
                              data_provenance=deepcopy(snapshot.get('provenance', {})), is_fixture=prepared[3],
                              indicator_check_reasons=_indicator_check_reasons(prepared))
