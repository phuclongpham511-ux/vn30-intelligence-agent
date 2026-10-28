from datetime import date, timedelta

import pytest

from src.analytics.market import technical_history
from src.schemas.data import MarketBar
from src.materiality import ScoringContext, detect_and_score_market_events


def pattern(side='lower', delay=0):
    rows = technical_history('XYZ', bars([100+(i % 2)*2 for i in range(65)]), 'synthetic')
    touch = rows[-1-delay]
    if side == 'lower':
        touch.low = touch.bb50_lower
    else:
        touch.high = touch.bb50_upper
    prior, current = rows[-2:]
    current.close = prior.close + (1 if side == 'lower' else -1)
    current.open = current.close
    current.high = max(current.high, current.close)
    current.low = min(current.low, current.close)
    current.volume = 300
    return rows


def score(rows, rank=1, days=None):
    contexts = {'unusual_volume': ScoringContext(own_history_abnormality=rank),
        'bollinger_lower_reversal_volume': ScoringContext(own_history_abnormality=.4, days_since_similar_event=days),
        'bollinger_upper_reversal_volume': ScoringContext(own_history_abnormality=.4, days_since_similar_event=days)}
    return [r for r in detect_and_score_market_events(rows[-2], rows[-1], contexts,
        recent_bars=rows[-4:], relative_volume=3) if r.candidate.event_type.value.startswith('bollinger')]


def bars(closes):
    return [MarketBar(ticker='XYZ', date=date(2001, 1, 1)+timedelta(days=i),
        open=p, high=p+1, low=max(.01, p-1), close=p, volume=100,
        source='synthetic') for i, p in enumerate(closes)]


def test_bb50_sample_std_known_window_and_warmup():
    rows = technical_history('XYZ', bars(list(range(1, 52))), 'synthetic')
    assert all(r.bb50_upper is None and r.bb50_lower is None and r.bb50_std is None for r in rows[:49])
    # Worked reference: 1..50 has mean 25.5 and sample variance 212.5.
    assert rows[49].ma50 == 25.5
    assert rows[49].bb50_std == pytest.approx(14.577379737113251)
    assert rows[49].bb50_upper == pytest.approx(54.6547594742265)
    assert rows[49].bb50_lower == pytest.approx(-3.654759474226502)
    assert rows[50].ma50 == 26.5


def test_lower_reversal_is_scored_without_counting_volume_twice_and_exposes_evidence():
    rows = pattern()
    results = score(rows, days=1)
    assert len(results) == 1
    result = results[0]
    assert result.candidate.event_type == 'bollinger_lower_reversal_volume'
    assert result.candidate.observed_at == rows[-1].date
    assert result.components.significance == .4
    assert result.components.novelty == .25
    evidence = {e.metric: e for e in result.candidate.evidence}
    assert evidence['touch_session'].value == rows[-1].date.isoformat()
    assert evidence['volume_percentile'].value == 1
    assert evidence['relative_volume'].value == 3
    assert all(e.source == 'synthetic' for e in evidence.values())


@pytest.mark.parametrize('side', ['lower', 'upper'])
@pytest.mark.parametrize('delay', [0, 1, 2])
@pytest.mark.parametrize('penetration', [0, .1])
def test_inclusive_touch_penetration_and_short_confirmation(side, delay, penetration):
    rows = pattern(side, delay)
    row = rows[-1-delay]
    if side == 'lower': row.low -= penetration
    else: row.high += penetration
    events = score(rows, rank=.95)
    assert len(events) == 1
    assert events[0].candidate.event_type == f'bollinger_{side}_reversal_volume'
    assert next(e.value for e in events[0].candidate.evidence if e.metric == 'touch_session') == row.date.isoformat()


@pytest.mark.parametrize('side', ['lower', 'upper'])
@pytest.mark.parametrize('failure', ['no_touch', 'no_move', 'not_recovered', 'weak_volume', 'no_volume_context', 'zero_volume', 'expired', 'missing_band', 'flat'])
def test_partial_conditions_never_emit(side, failure):
    rows = pattern(side, 3 if failure == 'expired' else 0)
    current, prior = rows[-1], rows[-2]
    rank = 1
    if failure == 'no_touch':
        for r in rows[-3:]:
            r.low, r.high = r.bb50_lower+.2, r.bb50_upper-.2
    if failure == 'no_move': current.close = prior.close
    if failure == 'not_recovered': current.close = current.bb50_lower if side == 'lower' else current.bb50_upper
    if failure == 'weak_volume': rank = .949999
    if failure == 'no_volume_context': rank = None
    if failure == 'zero_volume': current.volume = 0
    if failure == 'missing_band': current.bb50_lower = current.bb50_upper = None
    if failure == 'flat': current.bb50_std = 0
    assert score(rows, rank=rank) == []


def test_touch_day_volume_does_not_confirm_next_day_reversal():
    rows = pattern(delay=1)
    rows[-2].volume = 10000
    assert score(rows, rank=.5) == []


def test_flat_near_flat_and_49_session_boundaries():
    flat = technical_history('XYZ', bars([100]*50), 'synthetic')
    assert flat[-1].bb50_upper == flat[-1].bb50_lower == flat[-1].ma50 == 100
    assert flat[-1].bb50_std == 0
    assert score(flat) == []
    assert score(technical_history('XYZ', bars([100+i % 2 for i in range(49)]), 'synthetic')) == []
    near = technical_history('XYZ', bars([100+(i % 2)*.000001 for i in range(50)]), 'synthetic')
    assert 0 < near[-1].bb50_std < .000001


@pytest.mark.parametrize('missing', ['open', 'high', 'low', 'close', 'volume'])
def test_missing_required_evidence_is_rejected_without_zero_filling(missing):
    from pydantic import ValidationError
    payload = bars([100])[0].model_dump()
    payload[missing] = None
    with pytest.raises(ValidationError): MarketBar(**payload)


def test_duplicate_and_misaligned_history_is_rejected():
    rows = pattern()
    with pytest.raises(ValueError): technical_history('XYZ', [rows[0], rows[0]], 'synthetic')
    rows[-3].date = rows[-2].date
    with pytest.raises(ValueError): score(rows)
    rows = pattern()
    rows[-3].ticker = 'OTHER'
    with pytest.raises(ValueError): score(rows)


@pytest.mark.parametrize('side', ['lower', 'upper'])
@pytest.mark.parametrize('factor', [.25, .5, .75, 1.25, 1.5, 2])
def test_computed_bands_and_semantic_event_scale_together(side, factor):
    original = pattern(side, 1)
    touch = original[-2]
    if side == 'lower': touch.low *= .99
    else: touch.high *= 1.01
    original = technical_history('XYZ', [MarketBar(**r.model_dump()) for r in original], 'synthetic')
    scaled = []
    for r in original:
        values = r.model_dump()
        for field in ('open', 'high', 'low', 'close'): values[field] *= factor
        scaled.append(MarketBar(**values))
    scaled = technical_history('XYZ', scaled, 'synthetic')
    assert len(score(original)) == len(score(scaled)) == 1
    for field in ('ma50', 'bb50_lower', 'bb50_upper', 'bb50_std'):
        assert getattr(scaled[-1], field) == pytest.approx(factor*getattr(original[-1], field))
    assert score(original)[0].candidate.event_type == score(scaled)[0].candidate.event_type


def test_existing_technical_history_api_exposes_python_bands(client, session):
    from main import app
    from src.models import Stock
    from src.services.stocks import get_market_provider
    class Provider:
        source = 'synthetic'
        def get_history(self, symbol, start, end):
            return bars(list(range(1, 52)))
    session.add(Stock(symbol='XYZ')); session.commit()
    app.dependency_overrides[get_market_provider] = Provider
    response = client.get('/stocks/XYZ/technical-history?start=2001-01-01&end=2001-02-20')
    assert response.status_code == 200
    assert response.json()[48]['bb50_upper'] is None
    assert response.json()[49]['bb50_upper'] == pytest.approx(54.6547594742265)


def test_replay_confirmation_dates_recurrence_and_fixture_provenance():
    from datetime import datetime, time, timezone
    from src.evaluation.models import DatasetManifest, HistoricalObservation, Period, ReplayConfig
    from src.evaluation.replay import replay
    from src.evaluation.store import digest
    raw = bars([100+(i % 2)*2 for i in range(66)])
    calculated = technical_history('XYZ', raw, 'synthetic')
    for i in (61, 63):
        raw[i].low = calculated[i].bb50_lower-.1
        raw[i].volume = 300
    observations = [HistoricalObservation(ticker='XYZ', data_type='market', observation_time=str(r.date),
        available_at=datetime.combine(r.date, time(23), timezone.utc), availability_basis='published',
        source='synthetic', is_fixture=True, payload=r) for r in raw]
    manifest = DatasetManifest(dataset_version='bb-fixture', created_at=datetime(2001,1,1,tzinfo=timezone.utc),
        source=['synthetic'], tickers=['XYZ'], benchmark=None, known_limitations=['Synthetic fixture'],
        coverage={}, observation_count=len(raw),
        content_sha256=digest([r.model_dump(mode='json') for r in observations]))
    config = ReplayConfig(primary_start=date(2001,1,1), min_history=60, lookback_sessions=80,
        calibration_period=Period(start=date(2001,1,1),end=date(2001,12,31)),
        validation_period=Period(start=date(2002,1,1),end=date(2002,12,31)),
        holdout_period=Period(start=date(2003,1,1),end=date(2003,12,31)))
    cases = replay(observations, manifest, config)
    bb = [c for c in cases if c.event_type == 'bollinger_lower_reversal_volume']
    assert [c.replay_time.date() for c in bb] == [raw[61].date, raw[63].date]
    assert [c.novelty for c in bb] == [1, .5]
    assert all(c.excluded and c.confidence == 0 and c.base_score is None for c in bb)
    shorter = replay(observations[:62], manifest, config)
    assert next(c.candidate for c in shorter if c.event_type == bb[0].event_type) == bb[0].candidate
