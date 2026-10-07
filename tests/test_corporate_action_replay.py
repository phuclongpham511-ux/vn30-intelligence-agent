"""Context tests use synthetic price fixtures; no protected historical prices."""
from datetime import date, datetime, timedelta, timezone

from src.corporate_actions.models import CorporateActionNotice
from src.corporate_actions.repository import CorporateActionRepository
from src.evaluation.models import DatasetManifest, HistoricalObservation, Period, ReplayConfig
from src.evaluation.replay import replay
from src.evaluation.store import digest
from src.schemas.data import MarketBar


def test_replay_filters_future_notice_and_keeps_existing_case_ids(session):
    start = date(2001, 1, 1)
    rows = []
    for i in range(12):
        day = start + timedelta(days=i)
        bar = MarketBar(ticker='SIM', date=day, source='synthetic_fixture', open=100+i,
                        high=100+i, low=100+i, close=100+i, volume=1000+i)
        rows.append(HistoricalObservation(ticker='SIM', data_type='market', payload=bar,
            source=bar.source, observation_time=str(day), available_at=datetime.combine(day, datetime.min.time(), timezone.utc),
            availability_basis='published', is_fixture=True))
    manifest = DatasetManifest(dataset_version='context-test-v1', created_at=rows[-1].available_at,
        source=['synthetic_fixture'], tickers=['SIM'], benchmark=None, coverage={}, adjustment_basis='adjusted',
        known_limitations=['synthetic test'], observation_count=len(rows), content_sha256=digest([r.model_dump(mode='json') for r in rows]))
    config = ReplayConfig(primary_start=start, min_history=3, lookback_sessions=10,
        calibration_period=Period(start=start,end=date(2001,1,31)),
        validation_period=Period(start=date(2001,2,1),end=date(2001,2,28)),
        holdout_period=Period(start=date(2001,3,1),end=date(2001,3,31)))
    repo = CorporateActionRepository(session)
    action_day = rows[8].payload.date
    repo.ingest(CorporateActionNotice(symbol='SIM', action_type='cash_dividend', effective_date=action_day,
        source='synthetic', source_id='one', verified=True, is_fixture=True), received_at=rows[7].available_at)
    repo.ingest(CorporateActionNotice(symbol='SIM', action_type='bonus_shares', effective_date=action_day,
        source='synthetic', source_id='two', verified=True, is_fixture=True), received_at=rows[9].available_at)
    plain = replay(rows, manifest, config)
    result = replay(rows, manifest, config, corporate_actions=repo)
    assert [c.case_id for c in result] == [c.case_id for c in plain]
    for c, original in zip(result, plain):
        assert c.candidate == original.candidate
        assert c.base_score == original.base_score
        if c.candidate.observed_at == action_day:
            assert c.corporate_action_context.status == 'KNOWN_MATCH'
            assert [a.source_id for a in c.corporate_action_context.actions] == ['one']
        else:
            assert c.corporate_action_context.status == 'UNKNOWN'
    prefix = replay(rows[:9], manifest, config, corporate_actions=repo)
    assert prefix == result[:len(prefix)]
