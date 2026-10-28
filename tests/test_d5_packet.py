"""Public D1 -> D4 -> D5 seam, synthetic observations only."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json

import pytest

from test_d1_runtime import NOW, snapshot, bb_snapshot
from test_d4_runtime import override_indicators, data_with_tail
from src.materiality import ScoringContext, build_technical_daily_packet
from src.materiality.service import evaluate_d4_market_events


def evaluate(data=None, **kwargs):
    data = deepcopy(data if data is not None else snapshot())
    # Synthetic ordinary evidence exercises delivery; fixture exclusion is separate.
    data['is_fixture'] = False
    return evaluate_d4_market_events(data, 'XYZ', data['calendar'][-1], generated_at=NOW, **kwargs)


def packet(data=None, **kwargs):
    return build_technical_daily_packet(evaluate(data, **kwargs), generated_at=NOW)


def check(result, family):
    return next(c for c in result.family_checks if c.family == family)


def test_real_events_missing_scores_remain_rankable_and_inspectable():
    upstream = evaluate()
    result = build_technical_daily_packet(upstream, generated_at=NOW)
    assert result.packet_state == 'HAS_INSIGHTS'
    assert len(result.top_insights) == 2
    assert {e.event_type for e in result.top_insights} == {'abnormal_price_move', 'unusual_volume'}
    for insight in result.top_insights:
        event = next(e for e in upstream.events if e.event_id == insight.event_id)
        assert insight.base_v0 is None and insight.significance_v0 is None
        assert insight.novelty_v0 == event.result.components.novelty
        assert insight.confidence_v0 == event.result.components.confidence
        assert insight.factual_decision_ref == event.factual_decision_ref
        assert insight.episode_id != insight.event_id != result.packet_id
        assert insight.required_delivery == 'no'
    assert any('ranking_score_unavailable' in reason for reason in result.limitations)


@pytest.mark.parametrize('current,status', [(0, 'DOES_NOT_EXIST'), (None, 'UNRESOLVED')])
def test_price_negative_or_unresolved_is_never_an_eligible_event(current, status):
    data = snapshot(returns=[.01] * 60 + [0])
    if current is None:
        data['bars'][-1]['price_comparable'] = False
    result = packet(data)
    assert check(result, 'abnormal_price_move').state == status
    assert all(e.event_type != 'abnormal_price_move' for e in result.top_insights)


def test_complete_no_change_is_distinct_from_insufficient_history():
    data = snapshot(returns=[.01] * 60 + [0], volumes=[100] * 61 + [50])
    complete = packet(data)
    assert complete.packet_state == 'NO_MEANINGFUL_TECHNICAL_CHANGE'
    assert not complete.top_insights and not complete.unresolved_checks
    assert all(c.state == 'DOES_NOT_EXIST' for c in complete.family_checks)
    insufficient = packet(snapshot(15, volumes=[100] * 17))
    assert insufficient.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
    assert not insufficient.top_insights
    assert check(insufficient, 'abnormal_price_move').state == 'UNRESOLVED'
    assert check(insufficient, 'ma_cross').state == 'UNRESOLVED'


def test_valid_volume_with_unresolved_other_families_has_insights_and_diagnostics():
    data = snapshot()
    data['bars'][-1]['price_comparable'] = False
    result = packet(data)
    assert result.packet_state == 'HAS_INSIGHTS'
    assert [e.event_type for e in result.top_insights] == ['unusual_volume']
    assert 'abnormal_price_move' in result.unresolved_checks


def test_calendar_failure_is_incomplete_not_no_change():
    data = snapshot()
    data['provenance'].pop('calendar_evidence')
    result = packet(data)
    assert result.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
    assert not result.top_insights
    assert 'source_or_calendar_provenance_unavailable' in check(result, 'abnormal_price_move').reason_codes


def test_verified_cross_and_entry_then_persistence_never_duplicate(monkeypatch):
    data = data_with_tail([0, 0])
    override_indicators(monkeypatch, data, ma=[-1, 1], rsi=[70, 71])
    result = packet(data)
    assert {'ma_cross', 'rsi_regime_entry'} <= {e.event_type for e in result.top_insights}
    data = data_with_tail([0, 0, 0])
    override_indicators(monkeypatch, data, ma=[-1, 1, 1], rsi=[70, 71, 72])
    result = packet(data)
    assert check(result, 'ma_cross').state == 'DOES_NOT_EXIST'
    assert check(result, 'rsi_regime_entry').state == 'DOES_NOT_EXIST'
    assert not {'ma_cross', 'rsi_regime_entry'} & {e.event_type for e in result.all_current_session_events}


def test_bollinger_and_volume_retain_shared_evidence_and_distinct_identities():
    upstream = evaluate(bb_snapshot())
    result = build_technical_daily_packet(upstream, generated_at=NOW)
    volume = next(e for e in result.all_current_session_events if e.event_type == 'unusual_volume')
    bb = next(e for e in result.all_current_session_events if e.event_type == 'bollinger_lower_reversal_volume')
    assert bb.eligible and volume.eligible
    assert bb.event_id != volume.event_id
    assert bb.factual_decision_ref == volume.factual_decision_ref
    assert bb.episode_id is None and bb.episode_relationship == 'NOT_APPLICABLE'
    assert check(result, bb.event_type).state == 'EXISTS'
    assert volume.factual_decision_ref in check(result, bb.event_type).evidence_refs
    assert any(e['metric'] == 'touch_session' for e in bb.evidence)


def test_current_event_continuation_and_unresolved_episode_are_both_eligible():
    data = data_with_tail([.1, .1, .1, .1])
    upstream = evaluate(data)
    result = build_technical_daily_packet(upstream, generated_at=NOW)
    price = next(e for e in result.top_insights if e.event_type == 'abnormal_price_move')
    assert price.episode_status == 'CONTINUATION' and price.anchor_session
    data['bars'].pop(62)
    result = packet(data)
    price = next(e for e in result.top_insights if e.event_type == 'abnormal_price_move')
    assert price.episode_status == 'UNRESOLVED' and price.episode_id is None
    assert price.continuity_reason


def test_prior_session_and_other_ticker_events_are_excluded_without_mutation():
    upstream = evaluate()
    stale = replace(upstream.events[0], session='2019-12-01')
    other = replace(upstream.events[0], ticker='OTHER')
    mixed = replace(upstream, events=upstream.events + (stale, other))
    result = build_technical_daily_packet(mixed, generated_at=NOW)
    assert len(result.all_current_session_events) == len(upstream.events)
    assert mixed.events[-2:] == (stale, other)


@pytest.mark.parametrize('size', range(6))
def test_attention_budget_and_inventory(size, monkeypatch):
    data = bb_snapshot()
    data['bars'][-1].update(open=106, close=106, high=106.1)
    # Ensure actual MA and RSI events as well as price/volume/Bollinger.
    import src.materiality.factual as factual
    original = factual.technical_history
    def indicators(ticker, bars, source):
        rows = original(ticker, bars, source)
        for row in rows[-2:]:
            final = row.date.isoformat() == data['calendar'][-1]
            row.ma20 = row.ma50 + (1 if final else -1) if row.ma50 is not None else None
            row.rsi14 = 71 if final else 70
        return rows
    monkeypatch.setattr(factual, 'technical_history', indicators)
    upstream = evaluate(data)
    assert len(upstream.events) == 5
    upstream = replace(upstream, events=upstream.events[:size])
    result = build_technical_daily_packet(upstream, generated_at=NOW)
    assert len(result.top_insights) == min(size, 3)
    assert len(result.all_current_session_events) == size
    assert len(result.ranked_eligible_event_ids) == size
    assert result.overflow_event_ids == result.ranked_eligible_event_ids[3:]
    assert tuple(e.event_id for e in result.top_insights) == result.ranked_eligible_event_ids[:3]
    assert [e.ranking_position for e in result.top_insights] == list(range(1, min(size, 3) + 1))
    if size == 0:
        # Removing positive upstream events is incomplete delivery, not a normal day.
        assert result.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
        assert any(c.state == 'EXISTS' and not c.delivery_complete for c in result.family_checks)


def test_score_sort_and_order_invariance_without_new_threshold():
    contexts = {'abnormal_price_move': ScoringContext(own_history_abnormality=.01, days_since_similar_event=1),
                'unusual_volume': ScoringContext(own_history_abnormality=.02)}
    upstream = evaluate(contexts=contexts)
    result = build_technical_daily_packet(upstream, generated_at=NOW)
    assert [e.event_type for e in result.top_insights] == ['unusual_volume', 'abnormal_price_move']
    assert len(result.top_insights) == 2  # No unofficial significance/display threshold.
    for event in upstream.events:
        insight = next(e for e in result.top_insights if e.event_id == event.event_id)
        assert insight.base_v0 == event.result.base_score
        assert insight.significance_v0 == event.result.components.significance
        assert insight.novelty_v0 == event.result.components.novelty
        assert insight.confidence_v0 == event.result.components.confidence
    reversed_result = build_technical_daily_packet(replace(upstream, events=upstream.events[::-1]), generated_at=NOW)
    assert result.to_json() == reversed_result.to_json()


def test_numeric_scores_sort_before_missing_and_exact_ties_use_identifiers():
    result = packet(contexts={'unusual_volume': ScoringContext(own_history_abnormality=0)})
    assert result.top_insights[0].event_type == 'unusual_volume'
    assert result.top_insights[0].base_v0 is not None
    result = packet(contexts={family: ScoringContext(own_history_abnormality=.5)
                             for family in ('abnormal_price_move', 'unusual_volume')})
    assert [e.event_type for e in result.top_insights] == ['abnormal_price_move', 'unusual_volume']


def test_timestamps_identity_versions_and_stable_explicit_json():
    upstream = evaluate()
    first = build_technical_daily_packet(upstream, generated_at=NOW)
    second = build_technical_daily_packet(upstream, generated_at=NOW + timedelta(days=1))
    assert first.packet_id == second.packet_id
    assert first.generated_at != second.generated_at and first.evaluation_as_of == second.evaluation_as_of == NOW
    parsed = json.loads(first.to_json())
    assert parsed['factual_policy_version'] == 'd1-empirical-q95-nearest-rank-v1'
    assert parsed['episode_policy_version'] == 'd4-episode-policy-v1'
    assert parsed['score_version'] == 'v0'
    assert parsed['data_provenance']['source'] == 'SSI:FastConnect'
    assert parsed['ranking_policy_version'] and parsed['delivery_policy_version']
    assert parsed['top_insights'][0]['corporate_action_context']['status'] == 'UNKNOWN'
    assert first.to_json() == build_technical_daily_packet(upstream, generated_at=NOW).to_json()


@pytest.mark.parametrize('mode', ['naive', 'earlier', 'legacy', 'unfinished'])
def test_refuses_unbound_future_or_legacy_runtime(mode):
    upstream = evaluate()
    now = NOW
    if mode == 'naive': now = NOW.replace(tzinfo=None)
    if mode == 'earlier': now = NOW - timedelta(seconds=1)
    if mode == 'legacy': upstream = replace(upstream, runtime_version='legacy-v0')
    if mode == 'unfinished': upstream = replace(upstream, session=NOW.date().isoformat())
    with pytest.raises(ValueError): build_technical_daily_packet(upstream, generated_at=now)


def test_prefix_invariance_and_input_alias_isolation():
    data = data_with_tail([.1, .1, .1])
    data['is_fixture'] = False
    earlier = data['calendar'][61]
    full = evaluate_d4_market_events(data, 'XYZ', earlier, generated_at=NOW)
    prefix = deepcopy(data)
    prefix['bars'] = prefix['bars'][:62]
    prefix['calendar'] = prefix['calendar'][:62]
    truncated = evaluate_d4_market_events(prefix, 'XYZ', earlier, generated_at=NOW)
    result = build_technical_daily_packet(full, generated_at=NOW)
    assert result.to_json() == build_technical_daily_packet(truncated, generated_at=NOW).to_json()
    before = result.to_json()
    full.factual_decisions['unusual_volume']['n'] = -1
    full.events[0].provenance['version'] = 'mutated'
    assert result.to_json() == before


def test_fixture_events_retained_but_not_delivered():
    data = snapshot()
    upstream = evaluate_d4_market_events(data, 'XYZ', data['calendar'][-1], generated_at=NOW)
    result = build_technical_daily_packet(upstream, generated_at=NOW)
    assert not result.top_insights and result.all_current_session_events
    assert all(not e.eligible and e.is_fixture for e in result.all_current_session_events)
    assert result.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'


@pytest.mark.parametrize('left,right,winner', [
    ((.8, .1, .1, .1), (.7, 1, 1, 1), 'a'),
    ((.5, .8, .1, .1), (.5, .7, 1, 1), 'a'),
    ((.5, .5, .8, .1), (.5, .5, .7, 1), 'a'),
    ((.5, .5, .5, .8), (.5, .5, .5, .7), 'a'),
    ((None, .5, .5, .5), (0, 0, 0, 0), 'b'),
    ((None, None, .5, .5), (None, 0, 0, 0), 'b'),
    ((None, None, None, .5), (None, None, 0, 0), 'b'),
    ((None, None, None, None), (None, None, None, 0), 'b'),
    ((.5, .5, .5, .5), (.5, .5, .5, .5), 'a'),
    ((.5, .5, .5, .5), (.5000000000000001, .5, .5, .5), 'b'),
])
def test_full_lexicographic_comparator_at_public_seam(left, right, winner):
    from src.materiality.models import MaterialityComponents
    upstream = evaluate()
    original = upstream.events[0]
    events = tuple(replace(original, event_id=name, result=replace(original.result,
        base_score=values[0], components=MaterialityComponents(*values[1:])))
        for name, values in (('b', right), ('a', left)))
    result = build_technical_daily_packet(replace(upstream, events=events), generated_at=NOW)
    assert result.ranked_eligible_event_ids[0] == winner
    repeated = build_technical_daily_packet(replace(upstream, events=events[::-1]), generated_at=NOW)
    assert repeated.to_json() == result.to_json()


def test_corporate_action_real_enrichment_cannot_change_ranking_or_scores(session):
    from src.corporate_actions.models import CorporateActionNotice
    from src.corporate_actions.repository import CorporateActionRepository
    repo = CorporateActionRepository(session)
    data = snapshot()
    repo.ingest(CorporateActionNotice(symbol='XYZ', action_type='cash_dividend',
        effective_date=data['calendar'][-1], source='curated_verified', source_id='synthetic-1',
        verified=True), received_at=NOW - timedelta(hours=1))
    plain = packet(data)
    enriched = packet(data, corporate_actions=repo)
    assert enriched.ranked_eligible_event_ids == plain.ranked_eligible_event_ids
    for before, after in zip(plain.top_insights, enriched.top_insights):
        assert (before.base_v0, before.significance_v0, before.novelty_v0, before.confidence_v0) == (
            after.base_v0, after.significance_v0, after.novelty_v0, after.confidence_v0)
        assert before.episode_id == after.episode_id and before.event_id == after.event_id
        assert after.corporate_action_context.status == 'KNOWN_MATCH'
        assert after.corporate_action_context.actions[0].source_id == 'synthetic-1'
    # A later source observation cannot backfill the prior evaluation.
    repo.ingest(CorporateActionNotice(symbol='XYZ', action_type='stock_dividend',
        effective_date=data['calendar'][-1], source='curated_verified', source_id='synthetic-2',
        verified=True), received_at=NOW + timedelta(hours=1))
    assert packet(data, corporate_actions=repo).to_json() == enriched.to_json()


def test_missing_indicator_warmup_and_missing_source_have_distinct_reasons():
    warmup = packet(snapshot(15, volumes=[100] * 17))
    assert 'insufficient_indicator_warmup' in check(warmup, 'ma_cross').reason_codes
    data = snapshot()
    data['bars'].pop()
    missing = packet(data)
    assert check(missing, 'ma_cross').state == 'UNRESOLVED'
    assert 'insufficient_indicator_warmup' not in check(missing, 'ma_cross').reason_codes
    assert check(missing, 'ma_cross').reason_codes != check(warmup, 'ma_cross').reason_codes


@pytest.mark.parametrize('mode', ['unknown_positive_volume', 'zero_volume', 'missing_patterns'])
def test_bollinger_completeness_is_based_on_inputs_not_absent_emissions(mode):
    data = bb_snapshot()
    if mode == 'unknown_positive_volume':
        data['bars'][-1]['volume_comparable'] = False
    if mode == 'zero_volume':
        for row in data['bars']: row['volume'] = 0
    upstream = evaluate(data)
    if mode == 'missing_patterns': upstream = replace(upstream, pattern_decisions={})
    result = build_technical_daily_packet(upstream, generated_at=NOW)
    bb = check(result, 'bollinger_lower_reversal_volume')
    assert bb.state == ('DOES_NOT_EXIST' if mode == 'zero_volume' else 'UNRESOLVED')
    assert all(e.event_type != bb.family for e in result.top_insights)


def test_duplicate_identity_rejected_and_ineligible_inventory_not_erased():
    upstream = evaluate()
    with pytest.raises(ValueError, match='Duplicate'):
        build_technical_daily_packet(replace(upstream, events=upstream.events + (upstream.events[0],)), generated_at=NOW)
    false_event = replace(upstream.events[0], event_type='ma_cross')
    bad = replace(upstream, events=(false_event,))
    result = build_technical_daily_packet(bad, generated_at=NOW)
    assert len(result.all_current_session_events) == 1 and not result.top_insights
    assert not result.all_current_session_events[0].eligible
    assert result.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'


def test_fixture_provenance_and_revisions_change_packet_identity_not_event_identity():
    data = data_with_tail([.1, .1])
    original = evaluate(data)
    first = build_technical_daily_packet(original, generated_at=NOW)
    data['bars'][-1]['volume'] = 1000
    revised = evaluate(data, previous_evaluation=original)
    second = build_technical_daily_packet(revised, generated_at=NOW)
    assert first.packet_id != second.packet_id
    assert {e.event_id for e in first.all_current_session_events} == {e.event_id for e in second.all_current_session_events}
    assert first.to_json() != second.to_json()


def test_missing_indicator_with_resolved_d1_negatives_is_not_false_no_change():
    # An older expected source session is lost; own-history still has >=60
    # valid observations if sufficient authorized history is supplied.
    data = snapshot(110, returns=[.01] * 110 + [0], volumes=[100] * 111 + [50])
    data['bars'].pop(100)
    result = packet(data)
    assert check(result, 'abnormal_price_move').state == 'DOES_NOT_EXIST'
    assert check(result, 'unusual_volume').state == 'DOES_NOT_EXIST'
    assert check(result, 'ma_cross').state == 'UNRESOLVED'
    assert result.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'


def test_no_calls_to_detector_scoring_or_memory_from_packet_builder(monkeypatch):
    upstream = evaluate()
    import src.materiality.service as service
    import src.materiality.factual as factual
    def forbidden(*args, **kwargs): raise AssertionError('D5 must consume existing results')
    monkeypatch.setattr(service, 'evaluate_candidate', forbidden)
    monkeypatch.setattr(factual, 'prepare_d1_evidence', forbidden)
    assert build_technical_daily_packet(upstream, generated_at=NOW).top_insights


def test_json_deterministic_across_process_restart_and_hash_seeds():
    import os
    import subprocess
    import sys
    code = '''
import sys
sys.path.insert(0, 'tests')
from test_d1_runtime import snapshot, NOW
from src.materiality import evaluate_d4_market_events, build_technical_daily_packet
data = snapshot()
data['is_fixture'] = False
evaluation = evaluate_d4_market_events(data, 'XYZ', data['calendar'][-1], generated_at=NOW)
print(build_technical_daily_packet(evaluation, generated_at=NOW).to_json())
'''
    results = [subprocess.check_output([sys.executable, '-c', code],
        env=dict(os.environ, PYTHONHASHSEED=seed), text=True) for seed in ('1', '789')]
    assert results[0] == results[1]


def test_source_input_iteration_order_does_not_change_packet():
    data = snapshot()
    target = data['calendar'][-1]
    first = packet(data)
    data['bars'].reverse()
    data['calendar'].reverse()
    data['is_fixture'] = False
    reversed_evaluation = evaluate_d4_market_events(data, 'XYZ', target, generated_at=NOW)
    assert build_technical_daily_packet(reversed_evaluation, generated_at=NOW).to_json() == first.to_json()


def test_future_audited_current_observation_does_not_create_insights():
    data = snapshot()
    data['bars'][-1]['available_at'] = (NOW + timedelta(days=1)).isoformat()
    data['bars'][-1]['availability_basis'] = 'audited'
    result = packet(data)
    assert not result.top_insights
    assert result.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'


def test_future_event_evidence_and_ca_cutoff_are_not_consumed():
    from src.materiality.models import EvidenceItem
    from src.corporate_actions.models import CorporateActionContext
    upstream = evaluate()
    event = upstream.events[0]
    future_candidate = replace(event.result.candidate, evidence=event.result.candidate.evidence + (
        EvidenceItem('future', 1, 'synthetic', as_of=NOW.date()),))
    altered = replace(upstream, events=(replace(event, result=replace(event.result, candidate=future_candidate)),))
    result = build_technical_daily_packet(altered, generated_at=NOW)
    assert not result.top_insights
    assert 'future_event_evidence' in result.all_current_session_events[0].eligibility_reasons
    future_context = CorporateActionContext(as_of=NOW + timedelta(hours=1))
    altered = replace(upstream, events=(replace(event, result=replace(event.result,
                      corporate_action_context=future_context)),))
    with pytest.raises(ValueError, match='Corporate-action knowledge'):
        build_technical_daily_packet(altered, generated_at=NOW + timedelta(days=1))
