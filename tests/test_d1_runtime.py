"""Synthetic public-seam coverage; no provider calls or protected datasets."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone

import pytest

from src.materiality import ScoringContext
from src.materiality.service import evaluate_d1_market_events


NOW = datetime(2021, 1, 1, tzinfo=timezone.utc)


def snapshot(n=60, *, volumes=None, returns=None):
    volumes = volumes if volumes is not None else [100] * (n + 2)
    returns = returns if returns is not None else [.01] * (n + 1)
    rows, close = [], 100.0
    for i in range(len(volumes)):
        if i:
            close *= 1 + returns[i - 1]
        day = (date(2020, 1, 1) + timedelta(days=i)).isoformat()
        rows.append(dict(ticker='XYZ', session=day, open=close, high=close + 1,
                         low=close - 1, close=close, volume=volumes[i], source='SSI:FastConnect',
                         currency='VND', price_comparable=True, volume_comparable=True,
                         availability_basis='end_of_day_assumption', timeframe='1d'))
    return dict(is_fixture=True, calendar=[r['session'] for r in rows], bars=rows,
                provenance=dict(source='SSI:FastConnect', version='synthetic-source-v1',
                                calendar_version='synthetic-calendar-v1', calendar_evidence='fixture',
                                adjustment_semantics='adjusted', volume_unit='shares',
                                downloaded_at='2020-12-31T00:00:00+00:00'))


def run(data, session=None, **kwargs):
    return evaluate_d1_market_events(data, 'XYZ', session or data['calendar'][-1],
                                    generated_at=NOW, **kwargs)


def fact(result, family):
    return result.factual_decisions[family]


def types(result):
    return [r.candidate.event_type.value for r in result.results]


@pytest.mark.parametrize('n,status', [(59, 'UNRESOLVED'), (60, 'EXISTS'), (280, 'EXISTS')])
def test_history_minimum_and_cap_at_runtime(n, status):
    result = run(snapshot(n, returns=[0] * (n + 1)))
    assert fact(result, 'abnormal_price_move')['predicate_result'] == status
    assert fact(result, 'abnormal_price_move')['n'] == min(n, 252)
    assert fact(result, 'unusual_volume')['predicate_result'] == 'EXISTS'
    assert fact(result, 'abnormal_price_move')['predicate_version'] == 'd1-empirical-q95-nearest-rank-v1'


@pytest.mark.parametrize('value,status', [(100, 'EXISTS'), (99.999, 'DOES_NOT_EXIST'), (0, 'DOES_NOT_EXIST'),
                                        (None, 'UNRESOLVED'), (-1, 'UNRESOLVED'), (float('inf'), 'UNRESOLVED')])
def test_volume_equality_negative_and_missing(value, status):
    data = snapshot()
    data['bars'][-1]['volume'] = value
    result = run(data, contexts={'unusual_volume': ScoringContext(own_history_abnormality=1)})
    decision = fact(result, 'unusual_volume')
    assert decision['predicate_result'] == status
    assert ('unusual_volume' in types(result)) == (status == 'EXISTS')
    assert decision['n'] == 61  # Current is excluded, even when it would change q95.


@pytest.mark.parametrize('n,status', [(59, 'UNRESOLVED'), (60, 'EXISTS'), (252, 'EXISTS')])
def test_volume_own_history_minimum(n, status):
    result = run(snapshot(n - 1, returns=[0] * n))
    assert fact(result, 'unusual_volume')['n'] == n
    assert fact(result, 'unusual_volume')['predicate_result'] == status


def test_valid_zero_returns_and_volume_are_not_missing():
    result = run(snapshot(60, volumes=[0] * 62, returns=[0] * 61))
    assert set(types(result)) == {'abnormal_price_move', 'unusual_volume'}
    for decision in result.factual_decisions.values():
        assert decision['predicate_result'] == 'EXISTS' and decision['q95'] == 0
    price = next(r for r in result.results if r.candidate.event_type == 'abnormal_price_move')
    assert price.candidate.direction == 'neutral'


def test_price_exact_equality_and_below_without_scoring_gate():
    data = snapshot(60, returns=[1] * 61)
    positive = run(data)
    assert fact(positive, 'abnormal_price_move')['q95'] == 1
    assert 'abnormal_price_move' in types(positive)
    data['bars'][-1]['close'] = data['bars'][-2]['close'] * 1.999
    data['bars'][-1].update(open=data['bars'][-1]['close'], high=data['bars'][-1]['close'], low=data['bars'][-1]['close'])
    negative = run(data, contexts={'abnormal_price_move': ScoringContext(own_history_abnormality=1)})
    assert fact(negative, 'abnormal_price_move')['predicate_result'] == 'DOES_NOT_EXIST'
    assert 'abnormal_price_move' not in types(negative)


@pytest.mark.parametrize('change', ['missing_prior', 'missing_calendar', 'source', 'intraday', 'incomplete',
                                  'adjustment', 'currency', 'late', 'duplicate', 'invalid_ohlc'])
def test_bad_required_evidence_is_unresolved(change):
    data = snapshot()
    if change == 'missing_prior': data['bars'].pop(-2)
    if change == 'missing_calendar': data['provenance']['calendar_evidence'] = None
    if change == 'source': data['bars'][-1]['source'] = 'other'
    if change == 'intraday': data['bars'][-1]['timeframe'] = '1m'
    if change == 'incomplete': data['bars'][-1]['is_complete'] = False
    if change == 'adjustment': data['provenance']['adjustment_semantics'] = 'unadjusted'
    if change == 'currency': data['bars'][-1]['currency'] = 'USD'
    if change == 'late': data['bars'][-1]['available_at'] = '2022-01-01T00:00:00+00:00'
    if change == 'duplicate': data['bars'].append(deepcopy(data['bars'][-1]))
    if change == 'invalid_ohlc': data['bars'][-1]['close'] = float('nan')
    result = run(data)
    assert fact(result, 'abnormal_price_move')['predicate_result'] == 'UNRESOLVED'
    assert 'abnormal_price_move' not in types(result)


def test_wrong_volume_units_do_not_invalidate_price():
    data = snapshot(60, returns=[0] * 61)
    data['provenance']['volume_unit'] = 'lots'
    result = run(data)
    assert fact(result, 'unusual_volume')['predicate_result'] == 'UNRESOLVED'
    assert fact(result, 'abnormal_price_move')['predicate_result'] == 'EXISTS'
    assert types(result) == ['abnormal_price_move']


def test_last_valid_observations_and_future_prefix_invariance():
    data = snapshot(280, volumes=[999] * 20 + [100] * 262, returns=[0] * 281)
    for row in data['bars'][-5:-1]: row['volume_comparable'] = False
    day = data['calendar'][-1]
    expected = run(data, day)
    volume = fact(expected, 'unusual_volume')
    assert volume['n'] == 252 and volume['q95'] == 100
    assert len(volume['excluded']) == 4
    assert volume['order_index'] == 240
    future = deepcopy(data['bars'][-1]); future.update(session='2022-01-01', volume=1e12, close=1e12)
    data['bars'].append(future); data['calendar'].append(future['session'])
    assert run(data, day) == expected
    assert run(data, day) == run(data, day)


def bb_snapshot(delay=0, volume=100):
    data = snapshot(65, returns=[0] * 66)
    for i, row in enumerate(data['bars']):
        close = 100 + (i % 2) * 2
        row.update(open=close, close=close, low=close - .1, high=close + .1)
    current, prior = data['bars'][-1], data['bars'][-2]
    current.update(open=103, close=103, low=102.9, high=103.1, volume=volume)
    data['bars'][-1-delay]['low'] = 90
    return data


@pytest.mark.parametrize('delay', [0, 1, 2])
def test_bollinger_uses_shared_tied_q95_despite_low_significance_midrank(delay):
    result = run(bb_snapshot(delay), contexts={'unusual_volume': ScoringContext(own_history_abnormality=.5),
        'abnormal_price_move': ScoringContext(own_history_abnormality=.4)})
    assert fact(result, 'unusual_volume')['predicate_result'] == 'EXISTS'
    bb = next(r for r in result.results if r.candidate.event_type == 'bollinger_lower_reversal_volume')
    assert bb.components.significance == .4
    assert next(e.value for e in bb.candidate.evidence if e.metric == 'd1_volume_q95') == 100


@pytest.mark.parametrize('volume,comparability', [(99, True), (100, False), (None, True)])
def test_bollinger_absent_or_unresolved_volume_cannot_confirm(volume, comparability):
    data = bb_snapshot(volume=volume); data['bars'][-1]['volume_comparable'] = comparability
    result = run(data, contexts={'unusual_volume': ScoringContext(own_history_abnormality=1)})
    assert 'bollinger_lower_reversal_volume' not in types(result)


def test_bollinger_positive_volume_is_separate_from_zero_q95_fact():
    data = bb_snapshot(volume=0)
    for row in data['bars']: row['volume'] = 0
    result = run(data)
    assert fact(result, 'unusual_volume')['predicate_result'] == 'EXISTS'
    assert 'unusual_volume' in types(result)
    assert 'bollinger_lower_reversal_volume' not in types(result)


def test_approved_fact_reaches_unchanged_scoring_and_post_score_context():
    contexts = {'unusual_volume': ScoringContext(own_history_abnormality=.5)}
    data = snapshot(); data['is_fixture'] = False
    base = run(data, contexts=contexts)
    scored = next(r for r in base.results if r.candidate.event_type == 'unusual_volume')
    assert scored.components.significance == .5 and scored.base_score == pytest.approx(2.5 / 3)
    class Repository:
        def context_for(self, *args, **kwargs):
            from src.corporate_actions.models import CorporateActionContext
            return CorporateActionContext(as_of=kwargs['as_of'], reason='not_observed')
    enriched = run(data, contexts=contexts, corporate_actions=Repository())
    assert types(enriched) == types(base)
    assert [r.components for r in enriched.results] == [r.components for r in base.results]
    assert [r.candidate for r in enriched.results] == [r.candidate for r in base.results]


def test_today_not_admitted_even_after_close():
    data = snapshot()
    day = data['calendar'][-1]
    result = evaluate_d1_market_events(data, 'XYZ', day,
                                     generated_at=datetime.fromisoformat(day + 'T23:00:00+07:00'))
    assert all(d['predicate_result'] == 'UNRESOLVED' for d in result.factual_decisions.values())
    assert not result.results


def test_ordinary_movements_do_not_reappear_with_high_scoring_context():
    data = snapshot(60, returns=[1] * 60 + [0])
    data['bars'][-1]['volume'] = 90
    result = run(data, contexts={family: ScoringContext(own_history_abnormality=1,
        market_relative_abnormality=1, economic_magnitude=1) for family in ('abnormal_price_move', 'unusual_volume')})
    assert all(d['predicate_result'] == 'DOES_NOT_EXIST' for d in result.factual_decisions.values())
    assert not set(types(result)) & {'abnormal_price_move', 'unusual_volume'}


def test_signed_negative_price_is_separate_from_magnitude():
    data = snapshot(60, returns=[0] * 60 + [-.5])
    result = run(data)
    decision = fact(result, 'abnormal_price_move')
    assert decision['signed_return'] == -.5 and decision['comparison_value'] == .5
    price = next(r for r in result.results if r.candidate.event_type == 'abnormal_price_move')
    assert price.candidate.direction == 'negative'


def test_invalid_volume_does_not_erase_an_evidenced_price_fact():
    data = snapshot(60, returns=[0] * 61)
    data['bars'][-1]['volume'] = None
    result = run(data)
    assert fact(result, 'unusual_volume')['predicate_result'] == 'UNRESOLVED'
    assert fact(result, 'abnormal_price_move')['predicate_result'] == 'EXISTS'
    assert types(result) == ['abnormal_price_move']


def test_runtime_ma_rsi_transitions_reuse_existing_analytics_and_detectors():
    from src.analytics.market import technical_history
    from src.schemas.data import MarketBar
    from src.materiality.service import detect_and_score_market_events
    data = snapshot(60, returns=[0] * 60 + [.03])
    rows = technical_history('XYZ', [MarketBar(ticker=r['ticker'], date=r['session'], source=r['source'],
        **{k: r[k] for k in ('open', 'high', 'low', 'close', 'volume')}) for r in data['bars']], 'SSI:FastConnect')
    expected = detect_and_score_market_events(rows[-2], rows[-1], is_fixture=True)
    actual = run(data)
    transitions = lambda results: [r for r in results if r.candidate.event_type in ('ma_cross', 'rsi_regime_entry')]
    assert transitions(actual.results) == transitions(expected)
    assert len(transitions(actual.results)) == 2


@pytest.mark.parametrize('failure', ['no_touch', 'expired', 'no_recovery', 'flat'])
def test_d1_does_not_relax_bollinger_price_conditions(failure):
    data = bb_snapshot(delay=3 if failure == 'expired' else 0)
    if failure == 'no_touch': data['bars'][-1]['low'] = 102.9
    if failure == 'no_recovery':
        data['bars'][-1].update(open=90, close=90, low=89, high=103)
    if failure == 'flat':
        for row in data['bars']: row.update(open=100, close=100, high=100, low=100)
    result = run(data)
    assert fact(result, 'unusual_volume')['predicate_result'] == 'EXISTS'
    assert 'bollinger_lower_reversal_volume' not in types(result)


def test_benchmark_legacy_metadata_keeps_identical_numerical_contract():
    from src.analytics.factual import factual_inputs as shared
    from src.evaluation.benchmark.facts import factual_inputs as benchmark
    history = [dict(session=r['session'], value=r['volume'], comparable=True) for r in snapshot()['bars']]
    old = benchmark('unusual_volume', '2020-12-01', 100, history)
    new = shared('unusual_volume', '2020-12-01', 100, history)
    assert old.pop('predicate_version') == 'd1-nearest-rank-q95-v1'
    assert new.pop('predicate_version') == 'd1-empirical-q95-nearest-rank-v1'
    assert old == new


def test_source_receipt_in_future_and_unknown_calendar_are_not_guessed():
    data = snapshot()
    data['provenance']['downloaded_at'] = '2022-01-01T00:00:00+00:00'
    assert all(d['predicate_result'] == 'UNRESOLVED' for d in run(data).factual_decisions.values())
    data = snapshot(); data['calendar'].pop()
    assert not run(data, data['bars'][-1]['session']).results


def test_selected_evidence_is_versioned_and_row_fixture_contaminates_scoring():
    data = snapshot(); data['is_fixture'] = False; data['bars'][10]['is_fixture'] = True
    result = run(data, contexts={'unusual_volume': ScoringContext(own_history_abnormality=1)})
    assert all(r.excluded and r.base_score is None and r.candidate.is_fixture for r in result.results)
    for decision in result.factual_decisions.values():
        assert len(decision['calculation_sha256']) == len(decision['source_subset_sha256']) == 64
        assert len(decision['selected_evidence']) == decision['n']
        assert all(h['session'] < data['calendar'][-1] for h in decision['selected_evidence'])
