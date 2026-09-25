"""Offline tests of time integrity, persistence, and human/engine separation."""
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
import json
import pytest
from pydantic import ValidationError
from src.schemas.data import MarketBar, FundamentalPeriod, NewsItem
from src.evaluation.models import HistoricalObservation, DatasetManifest, ReplayConfig, Period, HumanReview, ReplayCase
from src.evaluation.store import digest, validate_observations, save_dataset, load_dataset, read_jsonl, write_jsonl, save_reviews
from src.evaluation.replay import replay
from src.evaluation.event_memory import EventMemory
from src.evaluation.context import percentile
from src.evaluation.triage import build_review_queue
from src.evaluation.metrics import report
from src.materiality.service import evaluate_candidate

UTC = timezone.utc


def config(**updates):
    base = dict(primary_start=date(2020,1,1),
        calibration_period=Period(start=date(2020,1,1),end=date(2020,3,31)),
        validation_period=Period(start=date(2020,4,1),end=date(2020,5,31)),
        holdout_period=Period(start=date(2020,6,1),end=date(2020,12,31)),
        stress_period=Period(start=date(2019,1,1),end=date(2019,12,31)),
        min_history=3, lookback_sessions=20)
    return ReplayConfig(**(base | updates))


def observations(n=70, ticker="ABC", benchmark=False, start=date(2020,1,1), fixture=False):
    rows=[]
    for i in range(n):
        day=start+timedelta(days=i)
        price=100+(i%9)*2+i*.1
        bar=MarketBar(ticker=ticker,date=day,open=price,high=price+1,low=price-1,
                      close=price,volume=100+i%11,source="test")
        rows.append(HistoricalObservation(ticker=ticker,data_type="benchmark" if benchmark else "market",
                    observation_time=str(day),available_at=datetime.combine(day,time(23),UTC),
                    availability_basis="published",source="test",is_fixture=fixture,payload=bar))
    return rows


def manifest(rows, benchmark=None):
    return DatasetManifest(dataset_version="test-v1",created_at=datetime(2026,1,1,tzinfo=UTC),
        source=["test"],tickers=sorted({r.ticker for r in rows if r.data_type=="market"}),benchmark=benchmark,
        coverage={},adjustment_basis="unknown",known_limitations=["test input"],
        observation_count=len(rows),content_sha256=digest([r.model_dump(mode="json") for r in validate_observations(rows)]))


def test_chronological_replay_and_determinism():
    rows=observations()
    m=manifest(rows)
    result=replay(rows,m,config())
    assert result == replay(list(reversed(rows)),m,config())
    assert [c.replay_time for c in result] == sorted(c.replay_time for c in result)
    assert result
    for case in result:
        scored=evaluate_candidate(case.candidate)
        assert scored.base_score == case.base_score
        assert scored.components.novelty == case.novelty
        assert case.source_provenance["adjustment_basis"] == "unknown"
        assert "adjustment_semantics_unknown" in case.reason_codes


def test_no_future_features_or_case_changes():
    rows=observations(75)
    m=manifest(rows)
    prefix=replay(rows[:60],m,config())
    full=replay(rows,m,config())
    assert prefix == [c for c in full if c.replay_time<=rows[59].available_at]
    altered=rows[:60]+[r.model_copy(update={"payload":r.payload.model_copy(update={"volume":1e12})}) for r in rows[60:]]
    assert prefix == [c for c in replay(altered,m,config()) if c.replay_time<=rows[59].available_at]


def test_empirical_rank_uses_only_trailing_observations():
    rows=observations(30)
    cases=replay(rows,manifest(rows),config())
    case=next(c for c in cases if c.event_type=="unusual_volume" and c.raw_context_features["prior_sessions"]==20)
    day=case.candidate.observed_at
    prior=[r.payload.volume for r in rows if r.payload.date<day][-20:]
    assert case.normalized_context_features["own_history_abnormality"] == percentile(case.raw_context_features["volume"],prior,3)
    assert case.raw_context_features["prior_sessions"] == 20
    assert percentile(5,[5,5,5],3)==.5
    assert percentile(10,[1,2],3) is None


def test_benchmark_same_dates_and_available_time():
    rows=observations(30)
    bench=observations(30,ticker="VN30",benchmark=True)
    m=manifest(rows+bench,"VN30")
    cases=replay(rows+bench,m,config())
    price=[c for c in cases if c.event_type=="abnormal_price_move"]
    assert price[-1].raw_context_features["excess_return"] == pytest.approx(0)
    assert price[-1].normalized_context_features["market_relative_abnormality"] == .5
    target=bench[-1]
    late=target.model_copy(update={"available_at":target.available_at+timedelta(days=1)})
    cases=replay(rows+bench[:-1]+[late],m,config())
    last=[c for c in cases if c.replay_time==rows[-1].available_at]
    assert all(c.normalized_context_features["market_relative_abnormality"] is None for c in last)
    assert all(c.raw_context_features["excess_return"] is None for c in last)
    # A missing prior benchmark day cannot be bridged with an earlier return.
    cases=replay(rows+bench[:-2]+bench[-1:],m,config())
    assert all(c.raw_context_features["excess_return"] is None for c in cases if c.replay_time==rows[-1].available_at)


def test_missing_benchmark_sector_and_economic_channels_are_null():
    rows=observations(25)
    for case in replay(rows,manifest(rows),config()):
        assert case.normalized_context_features["market_relative_abnormality"] is None
        assert case.normalized_context_features["sector_relative_abnormality"] is None
        assert case.normalized_context_features["economic_magnitude"] is None


def test_event_memory_cannot_see_future_and_preserves_calendar_days():
    memory=EventMemory()
    now=datetime(2020,1,1,tzinfo=UTC)
    assert memory.days_since("A","ma_cross",now) is None
    memory.record("A","ma_cross",now)
    assert memory.days_since("A","ma_cross",now+timedelta(days=3))==3
    with pytest.raises(ValueError): memory.days_since("A","ma_cross",now)
    with pytest.raises(ValueError): memory.record("A","ma_cross",now-timedelta(days=1))
    rows=observations(30)
    prices=[c for c in replay(rows,manifest(rows),config()) if c.event_type=="abnormal_price_move"]
    assert prices[0].candidate.days_since_similar_event is None
    assert prices[1].candidate.days_since_similar_event==1
    assert prices[1].novelty==.25


def test_fixture_prefix_contamination_and_benchmark_exclusion():
    rows=observations(30,fixture=True)
    cases=replay(rows,manifest(rows),config())
    assert cases and all(c.excluded and c.confidence==0 for c in cases)
    normal=observations(30)
    bench=observations(30,ticker="VN30",benchmark=True,fixture=True)
    cases=replay(normal+bench,manifest(normal+bench,"VN30"),config())
    assert all(c.normalized_context_features["market_relative_abnormality"] is None for c in cases)


def test_holdout_does_not_affect_calibration_or_enter_queue():
    rows=observations(30)
    holdout=observations(5,start=date(2020,6,1))
    m=manifest(rows+holdout)
    before=replay(rows,m,config())
    after=replay(rows+holdout,m,config())
    assert before==[c for c in after if c.split=="calibration"]
    queue=build_review_queue(after,1000)
    assert queue and all(q["case"]["split"]!="holdout" for q in queue)
    with pytest.raises(ValueError): build_review_queue(after,splits=("holdout",))


def test_stress_data_does_not_enter_primary_distribution():
    old=observations(20,start=date(2019,12,1))
    rows=observations(25)
    m=manifest(old+rows)
    assert replay(rows,m,config()) == [c for c in replay(old+rows,m,config()) if c.split=="calibration"]


def test_duplicate_invalid_and_late_observations():
    rows=observations(5)
    with pytest.raises(ValueError,match="Duplicate"): replay(rows+[rows[0]],manifest(rows),config())
    with pytest.raises(ValidationError): HistoricalObservation(**(rows[0].model_dump() | {"ticker":"WRONG"}))
    with pytest.raises(ValidationError): HistoricalObservation(**(rows[0].model_dump() | {"available_at":datetime(2020,1,1)}))
    late=rows[0].model_copy(update={"available_at":rows[-1].available_at+timedelta(days=1)})
    with pytest.raises(ValueError,match="Out-of-order"): replay(rows[1:]+[late],manifest(rows),config())


def test_financial_news_unknown_availability_do_not_replay():
    financial=FundamentalPeriod(ticker="ABC",period="2020",source="test",revenue_growth_yoy=.2)
    article=NewsItem(id="x",ticker="ABC",published_at=datetime(2020,1,1,tzinfo=UTC),title="sample",source="test",is_fixture=True)
    rows=[HistoricalObservation(ticker="ABC",data_type="fundamental",observation_time="2020",available_at=None,source="test",payload=financial),
          HistoricalObservation(ticker="ABC",data_type="news",observation_time=article.published_at.isoformat(),available_at=None,
                                source="test",payload=article,is_fixture=True)]
    assert replay(rows,manifest(rows),config())==[]
    summary=report(rows,[])
    assert summary["unknown_available_at"]==2
    assert summary["unsupported_nonmarket_records"]==2
    with pytest.raises(ValidationError): HistoricalObservation(**(rows[1].model_dump() | {"is_fixture":False}))


def test_dataset_roundtrip_and_integrity(tmp_path):
    rows=observations(4)
    m=manifest(rows)
    directory=save_dataset(tmp_path,rows,m)
    actual,loaded=load_dataset(directory)
    assert actual==m and loaded==rows
    assert type(loaded[0].payload) is MarketBar
    path=directory/'observations.jsonl'
    path.write_text(path.read_text().replace('"volume":100.0','"volume":999.0'))
    with pytest.raises(ValueError,match="integrity"): load_dataset(directory)


def test_case_roundtrip_and_append_only_human_labels(tmp_path):
    rows=observations(20)
    cases=replay(rows,manifest(rows),config())
    case_path=tmp_path/'cases.jsonl'
    write_jsonl(case_path,cases)
    before=case_path.read_bytes()
    loaded=read_jsonl(case_path,ReplayCase)
    assert [c.model_dump(mode="json") for c in loaded]==[c.model_dump(mode="json") for c in cases]
    review=HumanReview(case_id=cases[0].case_id,verdict="uncertain",attention_level=1,
                      reviewed_at=datetime(2026,1,1,tzinfo=UTC),review_version="human-v1")
    path=tmp_path/'human_reviews.jsonl'
    save_reviews(path,[review],cases)
    assert case_path.read_bytes()==before
    with pytest.raises(ValueError): save_reviews(path,[review],cases)
    with pytest.raises(ValueError): save_reviews(path,[review.model_copy(update={"case_id":"bad"})],cases)
    assert report(rows,cases,reviews=[review])["review_verdicts"]=={"uncertain":1}
    with pytest.raises(ValidationError): HumanReview(**(review.model_dump() | {"attention_level":5}))


def test_triage_broad_deterministic_and_descriptive_only():
    rows=observations(70)
    cases=replay(rows,manifest(rows),config())
    queue=build_review_queue(cases,24)
    assert queue==build_review_queue(list(reversed(cases)),24)
    assert len(queue)==24 and len({q['case_id'] for q in queue})==24
    assert {'high_base','low_or_borderline_base','hash_control','rare_event_type','repeated_event'} <= {q['selection_reason'] for q in queue}
    summary=report(rows,cases,queue)
    assert summary['status']=='descriptive_only'
    assert summary['human_reviewed_cases']==0
    assert 'accuracy' not in summary


@pytest.mark.parametrize("updates", [
    {"validation_period":Period(start=date(2020,3,1),end=date(2020,4,1))},
    {"min_history":30,"lookback_sessions":20},
    {"stress_period":Period(start=date(2019,1,1),end=date(2020,1,1))},
])
def test_invalid_splits_rejected(updates):
    with pytest.raises(ValidationError): config(**updates)


def test_audit_reuses_models_and_quarantines_invalid_benchmark(monkeypatch):
    import pandas as pd
    import src.evaluation.acquisition as acquisition
    class Market:
        source="test"
        def get_history(self, symbol, start, end):
            return [r.payload for r in observations(4,ticker=symbol)]
    class Financial:
        source="test"
        def get_financials(self, symbol):
            return []
    class Quote:
        def history(self, **kwargs):
            return pd.DataFrame([
                {"time":"2020-01-01","open":100,"high":101,"low":99,"close":100,"volume":1},
                {"time":"2020-01-02","open":200,"high":101,"low":99,"close":100,"volume":1}])
    class SDK:
        def Quote(self, **kwargs): return Quote()
    monkeypatch.setattr(acquisition,"VnstockMarketDataProvider",Market)
    monkeypatch.setattr(acquisition,"VnstockFundamentalDataProvider",Financial)
    monkeypatch.setattr(acquisition,"sdk",lambda:SDK())
    m,rows=acquisition.collect([" xyz "],date(2020,1,1),date(2020,1,4))
    assert m.tickers==["XYZ"] and m.coverage["tickers"]["XYZ"]["sessions"]==4
    assert len(m.coverage["quarantined_rows"]["VN30"])==1
    bench=next(r for r in rows if r.data_type=="benchmark")
    assert bench.payload.close==100 and bench.payload.currency=="points"
    assert bench.availability_basis=="end_of_day_assumption"
    assert bench.available_at.hour==23
    assert all(r.is_fixture for r in rows if r.data_type=="news")


def test_holdout_labels_cannot_be_saved(tmp_path):
    rows=observations(20,start=date(2020,6,1))
    cases=replay(rows,manifest(rows),config())
    label=HumanReview(case_id=cases[0].case_id,verdict="approve",attention_level=2,
        reviewed_at=datetime(2026,1,1,tzinfo=UTC),review_version="v1")
    with pytest.raises(ValueError,match="holdout"):
        save_reviews(tmp_path/'labels.jsonl',[label],cases)
    assert not (tmp_path/'labels.jsonl').exists()


def test_review_revisions_preserve_history_and_latest_metrics(tmp_path):
    rows=observations(20)
    cases=replay(rows,manifest(rows),config())
    a=HumanReview(case_id=cases[0].case_id,verdict="uncertain",attention_level=1,
        reviewed_at=datetime(2026,1,1,tzinfo=UTC),review_version="v1")
    b=a.model_copy(update={"verdict":"reject","attention_level":0,
                           "reviewed_at":datetime(2026,1,2,tzinfo=UTC),"review_version":"v2"})
    path=tmp_path/'labels.jsonl'
    save_reviews(path,[a],cases)
    save_reviews(path,[b],cases)
    assert read_jsonl(path,HumanReview)==[a,b]
    summary=report(rows,cases,reviews=[a,b])
    assert summary['human_reviewed_cases']==1 and summary['review_verdicts']=={'reject':1}


def test_cli_offline_pipeline(tmp_path,monkeypatch,capsys):
    import sys
    from scripts.replay_materiality import main as replay_main
    from scripts.build_review_queue import main as queue_main
    from scripts.import_human_reviews import main as import_main
    from scripts.report_evaluation import main as report_main
    rows=observations(25)
    directory=save_dataset(tmp_path,rows,manifest(rows))
    conf=tmp_path/'config.json'
    conf.write_text(config().model_dump_json())
    monkeypatch.setattr(sys,'argv',['replay',str(directory),'--config',str(conf)])
    replay_main()
    run=next((directory/'runs').iterdir())
    monkeypatch.setattr(sys,'argv',['queue',str(run),'--size','5'])
    queue_main()
    assert (run/'human_reviews.jsonl').read_text()==''
    cases=read_jsonl(run/'replay_cases.jsonl',ReplayCase)
    original=(run/'replay_cases.jsonl').read_bytes()
    # Synthetic test label only; never written to the real evaluation directory.
    label=HumanReview(case_id=cases[0].case_id,verdict='uncertain',attention_level=1,
        reviewed_at=datetime(2026,1,1,tzinfo=UTC),review_version='test-only')
    labels=tmp_path/'input-labels.jsonl'
    write_jsonl(labels,[label])
    monkeypatch.setattr(sys,'argv',['import',str(run),str(labels)])
    import_main()
    monkeypatch.setattr(sys,'argv',['report',str(run)])
    report_main()
    summary=json.loads((run/'summary.json').read_text())
    assert summary['review_queue_size']==5 and summary['human_reviewed_cases']==1
    assert (run/'replay_cases.jsonl').read_bytes()==original
    assert len((run/'reviewed_benchmark.jsonl').read_text().splitlines())==1
    assert json.loads((run/'run_manifest.json').read_text())['case_count']==len(cases)
