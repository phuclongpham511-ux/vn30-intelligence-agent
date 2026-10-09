"""Public prospective runtime tests, using only synthetic source snapshots."""
from copy import deepcopy
from dataclasses import asdict
from datetime import date, timedelta

import pytest

from test_d1_runtime import NOW, snapshot, bb_snapshot
from src.materiality import ScoringContext
from src.materiality.service import evaluate_d1_market_events, evaluate_d4_market_events


def data_with_tail(returns, volumes=None):
    volumes = volumes or [200] * len(returns)
    return snapshot(60, returns=[.01] * 60 + returns,
                    volumes=[100] * 60 + [50] + volumes)


def run(data, index=-1, **kwargs):
    return evaluate_d4_market_events(data, 'XYZ', data['calendar'][index], generated_at=NOW, **kwargs)


def state(result, family):
    return next(s for s in result.episode_states if s.family == family)


def event(result, family):
    return next(e for e in result.events if e.event_type == family)


def test_price_start_continue_close_reversal_reentry():
    data = data_with_tail([.1, .1, 0, -.1, .1])
    results = [run(data, i) for i in range(61, 66)]
    states = [state(r, 'abnormal_price_move') for r in results]
    assert [s.lifecycle for s in states] == ['ANCHOR', 'CONTINUATION', 'CLOSED', 'ANCHOR', 'ANCHOR']
    assert states[0].episode_id == states[1].episode_id == states[2].closed_episode_id
    assert states[3].episode_id != states[0].episode_id
    assert states[4].closed_episode_id == states[3].episode_id
    assert states[4].episode_id != states[3].episode_id
    assert event(results[0], 'abnormal_price_move').event_id != event(results[1], 'abnormal_price_move').event_id
    assert states[0].anchor_session == data['calendar'][61]


def test_volume_start_continue_close_reentry_and_independent_family_identity():
    data = data_with_tail([.1, .1, 0, .1], [200, 200, 50, 200])
    results = [run(data, i) for i in range(61, 65)]
    states = [state(r, 'unusual_volume') for r in results]
    assert [s.lifecycle for s in states] == ['ANCHOR', 'CONTINUATION', 'CLOSED', 'ANCHOR']
    assert states[0].episode_id == states[1].episode_id == states[2].closed_episode_id
    assert states[0].episode_id != states[3].episode_id
    assert states[0].episode_id != state(results[0], 'abnormal_price_move').episode_id
    assert event(results[0], 'unusual_volume').result.candidate.evidence != event(results[1], 'unusual_volume').result.candidate.evidence


@pytest.mark.parametrize('family', ['abnormal_price_move', 'unusual_volume'])
@pytest.mark.parametrize('bad', ['missing', 'invalid'])
def test_gap_cannot_bridge_or_close_an_episode(family, bad):
    data = data_with_tail([.1, .1, .1, .1])
    original = run(data, 61)
    if bad == 'missing': data['bars'].pop(62)
    else: data['bars'][62]['price_comparable' if family == 'abnormal_price_move' else 'volume_comparable'] = False
    gap = run(data, 62); later = run(data, 64)
    for result in (gap, later):
        s = state(result, family)
        assert s.lifecycle == 'UNRESOLVED' and s.relationship == 'UNRESOLVED'
        assert s.episode_id is None and s.closed_episode_id is None
        assert s.prior_unresolved_episode_id == state(original, family).episode_id
        assert s.reason and s.evidence_refs
    e = event(later, family)
    assert e.episode_id is None and e.episode_relationship == 'UNRESOLVED'


def test_valid_zero_price_fact_retains_neutral_without_directional_episode():
    data = snapshot(60, returns=[0] * 61)
    result = run(data)
    assert result.factual_decisions['abnormal_price_move']['predicate_result'] == 'EXISTS'
    e = event(result, 'abnormal_price_move')
    assert e.result.candidate.direction == 'neutral' and e.episode_id is None
    assert state(result, 'abnormal_price_move').lifecycle == 'UNRESOLVED'


def test_supplied_exchange_sessions_bridge_weekend_and_closure_not_missing_bars():
    data = data_with_tail([.1, .1])
    # A supplied calendar declares no trading sessions over this closure interval.
    days = [(date(2019, 1, 1) + timedelta(days=i)).isoformat() for i in range(61)] + ['2020-01-03', '2020-01-08']
    data['calendar'] = days
    for row, day in zip(data['bars'], days): row['session'] = day
    first, later = run(data, 61), run(data, 62)
    for family in ('abnormal_price_move', 'unusual_volume'):
        assert state(later, family).lifecycle == 'CONTINUATION'
        assert state(first, family).episode_id == state(later, family).episode_id
        assert state(later, family).previous_session == '2020-01-03'


def override_indicators(monkeypatch, data, *, ma=None, rsi=None):
    """Exact boundary fixtures at the existing analytics seam, never source labels."""
    import src.materiality.factual as factual
    original = factual.technical_history
    days = data['calendar'][61:]
    def controlled(ticker, bars, source):
        rows = original(ticker, bars, source)
        for row in rows:
            i = days.index(row.date.isoformat()) if row.date.isoformat() in days else None
            difference = ma[i] if i is not None and ma is not None else 0
            row.ma20 = None if difference is None else 100 + difference
            row.ma50 = 100
            row.rsi14 = rsi[i] if i is not None and rsi is not None else 50
        return rows
    monkeypatch.setattr(factual, 'technical_history', controlled)


def test_ma_regime_entry_continuation_reverse_and_equality(monkeypatch):
    data = data_with_tail([0] * 5)
    override_indicators(monkeypatch, data, ma=[1, 2, 0, -1, -2])
    results = [run(data, i) for i in range(61, 66)]
    assert [state(r, 'ma_cross').lifecycle for r in results] == ['ANCHOR', 'CONTINUATION', 'UNRESOLVED', 'ANCHOR', 'CONTINUATION']
    assert len([e for e in results[1].events if e.event_type == 'ma_cross']) == 0
    assert state(results[2], 'ma_cross').closed_episode_id is None
    assert event(results[3], 'ma_cross').result.candidate.direction == 'negative'
    assert state(results[3], 'ma_cross').episode_id != state(results[0], 'ma_cross').episode_id


def test_ma_reverse_without_gap_closes_previous_regime(monkeypatch):
    data = data_with_tail([0] * 2)
    override_indicators(monkeypatch, data, ma=[1, -1])
    first, second = run(data, 61), run(data, 62)
    assert state(second, 'ma_cross').closed_episode_id == state(first, 'ma_cross').episode_id


@pytest.mark.parametrize('values', [[70, 71, 75, 70, 72], [30, 29, 25, 30, 28]])
def test_rsi_boundaries_entry_continuation_exit_reentry(monkeypatch, values):
    data = data_with_tail([0] * len(values))
    override_indicators(monkeypatch, data, rsi=values)
    results = [run(data, i) for i in range(61, 61 + len(values))]
    assert [state(r, 'rsi_regime_entry').lifecycle for r in results] == ['NONE', 'ANCHOR', 'CONTINUATION', 'CLOSED', 'ANCHOR']
    assert not any(e.event_type == 'rsi_regime_entry' for e in results[2].events)
    assert state(results[1], 'rsi_regime_entry').episode_id == state(results[3], 'rsi_regime_entry').closed_episode_id
    assert state(results[4], 'rsi_regime_entry').episode_id != state(results[1], 'rsi_regime_entry').episode_id


@pytest.mark.parametrize('family', ['ma_cross', 'rsi_regime_entry'])
def test_missing_indicator_is_not_an_exit_or_invented_anchor(monkeypatch, family):
    data = data_with_tail([0] * 3)
    override_indicators(monkeypatch, data, ma=[1, None, 2] if family == 'ma_cross' else None,
                        rsi=[71, None, 75] if family == 'rsi_regime_entry' else None)
    initial = run(data, 61)
    for i in (62, 63):
        s = state(run(data, i), family)
        assert s.lifecycle == 'UNRESOLVED' and s.closed_episode_id is None
        assert s.prior_unresolved_episode_id == state(initial, family).episode_id


def test_no_historical_regime_anchor_is_fabricated():
    result = run(data_with_tail([.01]))
    assert state(result, 'rsi_regime_entry').episode_id is None
    assert state(result, 'rsi_regime_entry').anchor_session is None


def test_repeat_restart_prefix_and_input_order_invariance():
    data = data_with_tail([.1, .1, 0, .1])
    original = run(data, 62)
    assert run(deepcopy(data), 62) == original
    prefix = deepcopy(data)
    prefix['calendar'] = prefix['calendar'][:63]; prefix['bars'] = prefix['bars'][:63]
    assert run(prefix) == original
    data['bars'].reverse()
    assert run(data, 62) == original
    assert len({e.event_id for e in original.events}) == len(original.events)
    for e in original.events:
        assert e.factual_decision_ref and e.policy_version and e.provenance
        assert e.episode_id != e.event_id


def test_bollinger_is_discrete_and_scoring_and_d1_stay_identical():
    data = bb_snapshot()
    context = {'unusual_volume': ScoringContext(own_history_abnormality=.5),
               'abnormal_price_move': ScoringContext(own_history_abnormality=.4)}
    before = evaluate_d1_market_events(data, 'XYZ', data['calendar'][-1], generated_at=NOW, contexts=context)
    after = run(data, contexts=context)
    assert after.factual_decisions['abnormal_price_move'] == before.factual_decisions['abnormal_price_move']
    assert after.factual_decisions['unusual_volume'] == before.factual_decisions['unusual_volume']
    assert after.results == before.results
    e = event(after, 'bollinger_lower_reversal_volume')
    assert e.episode_id is None and e.episode_family is None
    assert e.episode_relationship == 'NOT_APPLICABLE'


def test_corporate_action_enrichment_cannot_change_episode_relationships():
    from src.corporate_actions.models import CorporateActionContext
    class Repository:
        def context_for(self, *args, **kwargs):
            return CorporateActionContext(as_of=kwargs['as_of'], reason='pending_verification')
    data = data_with_tail([.1, .1])
    base, enriched = run(data), run(data, corporate_actions=Repository())
    assert enriched.episode_history == base.episode_history
    assert enriched.evaluation_id == base.evaluation_id
    assert [e.event_id for e in enriched.events] == [e.event_id for e in base.events]
    assert [r.components for r in enriched.results] == [r.components for r in base.results]


def test_correction_versions_evidence_and_reports_changed_relationships_without_mutating_original():
    data = data_with_tail([.1, 0, .1])
    before = run(data); preserved = deepcopy(asdict(before))
    revised = deepcopy(data)
    # Correct the middle close; this removes the verified normal interruption.
    previous = revised['bars'][61]['close']
    revised['bars'][62].update(close=previous * 1.1, open=previous * 1.1, low=previous * 1.1, high=previous * 1.1)
    revised['bars'][63].update(close=previous * 1.21, open=previous * 1.21, low=previous * 1.21, high=previous * 1.21)
    revised['provenance']['version'] = 'synthetic-source-v2'
    after = run(revised, previous_evaluation=before)
    assert asdict(before) == preserved
    assert after.evaluation_id != before.evaluation_id
    assert after.supersedes_evaluation_id == before.evaluation_id
    assert any(r.family == 'abnormal_price_move' and r.reason == 'episode_relationship_revised' for r in after.revisions)
    assert event(after, 'abnormal_price_move').event_id == event(before, 'abnormal_price_move').event_id
    assert run(data, previous_evaluation=before).supersedes_evaluation_id is None


def test_unknown_calendar_keeps_explicit_unresolved_lifecycle():
    data = data_with_tail([.1]); data['provenance']['calendar_evidence'] = None
    result = run(data)
    assert not result.events
    assert all(s.lifecycle == 'UNRESOLVED' and s.episode_id is None for s in result.episode_states)


def test_valid_zero_volume_can_anchor_a_high_volume_episode():
    data = snapshot(60, returns=[0] * 61, volumes=[0] * 62)
    first, later = run(data, 60), run(data, 61)
    assert state(first, 'unusual_volume').lifecycle == 'ANCHOR'
    assert state(later, 'unusual_volume').lifecycle == 'CONTINUATION'
    assert state(first, 'unusual_volume').episode_id == state(later, 'unusual_volume').episode_id


def test_verified_negative_after_gap_allows_later_new_anchor_without_backdated_close():
    data = data_with_tail([.1, .1, 0, 0, .1], [200, 200, 50, 50, 200])
    initial = run(data, 61)
    data['bars'].pop(62)
    later = run(data, 65)
    for family in ('abnormal_price_move', 'unusual_volume'):
        s = state(later, family)
        assert s.lifecycle == 'ANCHOR' and s.episode_id != state(initial, family).episode_id
        gap = next(s for s in later.episode_history if s.family == family and s.session == data['calendar'][62])
        assert gap.lifecycle == 'UNRESOLVED' and gap.closed_episode_id is None


def test_verified_transition_after_missing_indicator_records_unresolved_prior_close(monkeypatch):
    data = data_with_tail([0] * 4)
    override_indicators(monkeypatch, data, rsi=[71, None, 50, 72])
    first, later = run(data, 61), run(data, 64)
    s = state(later, 'rsi_regime_entry')
    assert s.lifecycle == 'ANCHOR' and s.episode_id != state(first, 'rsi_regime_entry').episode_id
    # The new entry is verified; never invent a dated exit inside the earlier gap.
    assert s.closed_episode_id is None
    assert not any(s.closed_episode_id for s in later.episode_history if s.family == 'rsi_regime_entry')


def test_correction_scope_mismatch_is_rejected():
    data = data_with_tail([.1, .1])
    earlier = run(data, 61)
    with pytest.raises(ValueError, match='same ticker/session'):
        run(data, 62, previous_evaluation=earlier)


def test_correction_without_vendor_version_change_still_gets_distinct_evaluation_identity():
    data = data_with_tail([.1, 0, .1]); before = run(data)
    data['bars'][62]['volume'] = 250
    after = run(data, previous_evaluation=before)
    assert after.evaluation_id != before.evaluation_id
    assert after.supersedes_evaluation_id == before.evaluation_id and after.revisions


def test_result_does_not_alias_mutable_source_provenance():
    data = data_with_tail([.1]); data['provenance']['extra_evidence'] = {'reference': 'original'}
    before = run(data); saved = deepcopy(asdict(before))
    data['provenance']['extra_evidence']['reference'] = 'corrected'
    assert asdict(before) == saved


def test_restart_in_fresh_process_reconstructs_identical_episode_and_event_ids():
    import json
    import subprocess
    import sys
    data = data_with_tail([.1, .1]); expected = run(data)
    code = '''import json,sys
from datetime import datetime,timezone
from src.materiality import evaluate_d4_market_events
data=json.load(sys.stdin)
r=evaluate_d4_market_events(data,'XYZ',data['calendar'][-1],generated_at=datetime(2021,1,1,tzinfo=timezone.utc))
print(json.dumps([r.evaluation_id,[e.event_id for e in r.events],[s.episode_id for s in r.episode_states]]))
'''
    result = subprocess.run([sys.executable, '-B', '-c', code], input=json.dumps(data),
                            text=True, capture_output=True, check=True, timeout=30)
    assert json.loads(result.stdout) == [expected.evaluation_id, [e.event_id for e in expected.events],
                                       [s.episode_id for s in expected.episode_states]]
