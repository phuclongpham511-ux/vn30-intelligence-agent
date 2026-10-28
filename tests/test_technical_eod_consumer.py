"""Actual normalized reader/provider contracts with synthetic SSI payloads."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone

import httpx
import pytest

from test_d1_runtime import snapshot, bb_snapshot, NOW
from test_d4_runtime import data_with_tail
from src.models import Security
from src.services.session_evidence import EODCompletionEvidence, bar_fingerprint
from src.schemas.data import MarketBar
from src.evaluation.models import HistoricalObservation
from src.materiality.delivery import TechnicalDailySignalPacket
from src.services.technical_eod import (
    EODHistoryRead, VerifiedSessionCalendar, TechnicalEODDiagnostic,
    read_eod_history, evaluate_technical_eod_packet, summarize_eod_result,
)


def inputs(data=None):
    data = deepcopy(data or snapshot())
    records = tuple(HistoricalObservation(ticker='XYZ', data_type='market',
        observation_time=row['session'], source=row['source'],
        available_at=datetime.fromisoformat(row['session'] + 'T23:59:59+07:00'),
        availability_basis='end_of_day_assumption', payload=MarketBar(
            ticker='XYZ', date=row['session'], source=row['source'],
            **{key: row[key] for key in ('open', 'high', 'low', 'close', 'volume')})) for row in data['bars'])
    read = EODHistoryRead(observations=records, observed_at=NOW - timedelta(hours=1),
        source_version='synthetic-read-v1')
    calendar = VerifiedSessionCalendar(venue='HOSE', sessions=tuple(date.fromisoformat(d) for d in data['calendar']),
        coverage_start=date.fromisoformat(data['calendar'][0]), coverage_end=date.fromisoformat(data['calendar'][-1]),
        source_ref='synthetic-declared-calendar', version='synthetic-calendar-v1', observed_at=NOW-timedelta(days=1))
    read = attest_fixture(read)
    return data, read, calendar


def attest_fixture(read):
    return read.model_copy(update={'completion_evidence':tuple(EODCompletionEvidence(
        ticker=o.ticker,venue='HOSE',session=o.payload.date,source=read.source,
        source_version=read.source_version,bar_sha256=bar_fingerprint(o.payload),
        status='COMPLETE',available_at=o.available_at,observed_at=read.observed_at,
        source_ref='synthetic-finalization-attestation') for o in read.observations)})


def metadata(session):
    session.add(Security(symbol='XYZ', exchange='HOSE', last_synced_at=NOW-timedelta(days=1)))
    session.commit()


def run(session, data=None, **changes):
    data, read, calendar = inputs(data)
    kwargs = dict(db_session=session, history_read=read, calendar=calendar,
        history_start=calendar.coverage_start, evaluation_as_of=NOW, generated_at=NOW)
    kwargs.update(changes)
    return evaluate_technical_eod_packet('XYZ', data['calendar'][-1], **kwargs)


def test_completed_reader_contract_flows_through_real_d1_d4_d5(session):
    metadata(session)
    result = run(session)
    assert isinstance(result, TechnicalDailySignalPacket)
    assert result.packet_state == 'HAS_INSIGHTS'
    assert {e.event_type for e in result.top_insights} == {'abnormal_price_move', 'unusual_volume'}
    assert all(e.base_v0 is not None for e in result.top_insights)
    assert result.data_provenance['venue'] == 'HOSE'
    assert result.data_provenance['volume_unit'] == 'shares'
    assert result.data_provenance['price_unit'] == 'VND'
    assert result.data_provenance['source_observed_at'] < NOW.isoformat()
    assert 'market_relative_context_unavailable' in result.limitations
    assert 'recurrence_history_unavailable' in result.limitations


@pytest.mark.parametrize('ticker', ['', None, '!', 'not supported'])
def test_invalid_ticker_is_diagnostic_without_reader_calls(session, ticker):
    result = evaluate_technical_eod_packet(ticker, '2020-03-02', db_session=session,
        evaluation_as_of=NOW, generated_at=NOW)
    assert isinstance(result, TechnicalEODDiagnostic) and result.status == 'INVALID_REQUEST'


@pytest.mark.parametrize('mode', ['unfinished', 'invalid_date', 'generation_before_cutoff', 'naive'])
def test_invalid_session_and_timestamps(session, mode):
    metadata(session)
    target = '2021-01-02' if mode == 'unfinished' else 'bad-date' if mode == 'invalid_date' else '2020-03-02'
    result = evaluate_technical_eod_packet('XYZ', target, db_session=session,
        evaluation_as_of=NOW.replace(tzinfo=None) if mode == 'naive' else NOW,
        generated_at=NOW-timedelta(seconds=1) if mode == 'generation_before_cutoff' else NOW)
    assert result.status == 'INVALID_REQUEST'


@pytest.mark.parametrize('field,value', [('adjustment_semantics', 'raw'), ('price_unit', 'USD'), ('volume_unit', 'lots')])
def test_incompatible_basis_and_units_are_not_admitted(session, field, value):
    metadata(session)
    _, read, _ = inputs()
    result = run(session, history_read=read.model_copy(update={field:value}))
    assert isinstance(result, TechnicalEODDiagnostic) and result.status == 'INCOMPLETE_EVIDENCE'
    assert not hasattr(result, 'top_insights')


def test_missing_calendar_preserves_observations_without_fake_packet(session):
    metadata(session)
    result = run(session, calendar=None)
    assert isinstance(result, TechnicalEODDiagnostic)
    assert 'verified_session_calendar_unavailable' in result.reason_codes
    assert len(result.available_observations) == 62
    assert result.source_summary['source'] == 'SSI:FastConnect'


def test_duplicate_session_and_wrong_ticker_reader_data_are_diagnostics(session):
    metadata(session)
    _, read, _ = inputs()
    duplicate = read.model_copy(update={'observations':read.observations+(read.observations[-1],)})
    assert 'duplicate_source_session' in run(session, history_read=duplicate).reason_codes
    other_payload = read.observations[-1].payload.model_copy(update={'ticker':'OTHER'})
    other = read.observations[-1].model_copy(update={'ticker':'OTHER','payload':other_payload})
    assert 'history_identity_mismatch' in run(session, history_read=read.model_copy(update={'observations':(other,)})).reason_codes


def test_wrong_venue_and_future_metadata_fail_closed(session):
    metadata(session)
    _, _, calendar = inputs()
    assert 'calendar_venue_mismatch' in run(session, calendar=calendar.model_copy(update={'venue':'HNX'})).reason_codes
    security = session.get(Security, 'XYZ')
    security.last_synced_at = NOW + timedelta(days=1)
    session.add(security); session.commit()
    assert 'security_metadata_after_cutoff' in run(session).reason_codes


@pytest.mark.parametrize('n,state', [(59, 'UNRESOLVED'), (60, 'EXISTS'), (270, 'EXISTS')])
def test_prior_return_count_additional_close_and_current_exclusion(session, n, state):
    metadata(session)
    data = snapshot(n, returns=[0] * (n+1))
    result = run(session, data)
    price = next(c for c in result.family_checks if c.family == 'abnormal_price_move')
    assert price.state == state
    assert price.evidence['n'] == min(n, 252)
    assert all(h['session'] < result.trading_session for h in price.evidence['history'])


def test_current_missing_and_indicator_warmup_remain_incomplete(session):
    metadata(session)
    _, read, _ = inputs()
    result = run(session, history_read=read.model_copy(update={'observations':read.observations[:-1]}))
    assert result.packet_state == 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
    warmup = run(session, snapshot(15, volumes=[100]*17))
    assert 'ma_cross' in warmup.unresolved_checks


def test_complete_no_change(session):
    metadata(session)
    result = run(session, snapshot(returns=[.01]*60+[0], volumes=[100]*61+[50]))
    assert result.packet_state == 'NO_MEANINGFUL_TECHNICAL_CHANGE'
    assert not result.top_insights


def test_missing_session_breaks_continuity_without_fabricating_anchor(session):
    metadata(session)
    data = data_with_tail([.1,.1,.1,.1])
    _, read, _ = inputs(data)
    read = read.model_copy(update={'observations':read.observations[:62]+read.observations[63:]})
    result = run(session, data, history_read=read)
    price = next(e for e in result.top_insights if e.event_type == 'abnormal_price_move')
    assert price.episode_status == 'UNRESOLVED' and price.episode_id is None
    assert price.scoring_inputs['own_history_abnormality'] is not None


def test_bounded_history_does_not_claim_initial_known_volume_anchor(session):
    metadata(session)
    result = run(session)
    volume = next(e for e in result.top_insights if e.event_type == 'unusual_volume')
    assert volume.episode_id is None and volume.episode_status == 'UNRESOLVED'


def test_verified_closure_then_reentry_can_anchor_and_continue_across_weekend(session):
    metadata(session)
    data = data_with_tail([.1,.1], [200,200])
    data['calendar'][-2:] = ['2020-04-03','2020-04-06']
    for row, day in zip(data['bars'], data['calendar']): row['session'] = day
    result = run(session, data)
    volume = next(e for e in result.top_insights if e.event_type == 'unusual_volume')
    assert volume.episode_status == 'CONTINUATION' and volume.anchor_session == '2020-04-03'


def test_bollinger_and_transitions_top_three_overflow(session, monkeypatch):
    metadata(session)
    data = bb_snapshot()
    data['bars'][-1].update(open=106, close=106, high=106.1)
    import src.materiality.factual as factual
    original = factual.technical_history
    def controlled(ticker, bars, source):
        rows = original(ticker,bars,source)
        for row in rows[-2:]:
            final = row.date.isoformat() == data['calendar'][-1]
            if row.ma50 is not None: row.ma20 = row.ma50+(1 if final else -1)
            row.rsi14 = 71 if final else 70
        return rows
    monkeypatch.setattr(factual,'technical_history',controlled)
    result = run(session,data)
    assert len(result.all_current_session_events) == 5
    assert len(result.top_insights) == 3 and len(result.overflow_event_ids) == 2
    assert {'ma_cross','rsi_regime_entry','bollinger_lower_reversal_volume'} <= {e.event_type for e in result.all_current_session_events}


def test_future_data_and_iteration_order_do_not_change_context_or_packet(session):
    metadata(session)
    data, read, calendar = inputs()
    first = run(session, data)
    future = read.observations[-1].model_copy(update={'observation_time':'2020-12-01',
        'payload':read.observations[-1].payload.model_copy(update={'date':date(2020,12,1),'close':999})})
    read = read.model_copy(update={'observations':(future,)+read.observations[::-1]})
    repeated = run(session, data, history_read=read)
    assert repeated.to_json() == first.to_json()


def test_new_acquisition_cannot_be_backdated_to_historical_asof(session):
    metadata(session)
    _, read, _ = inputs()
    result = run(session, history_read=read.model_copy(update={'observed_at':NOW+timedelta(hours=1)}))
    assert 'history_observed_after_cutoff' in result.reason_codes


def test_ssi_payload_through_actual_provider_and_existing_service_reader(session, monkeypatch):
    from src.providers.ssi import SsiMarketDataProvider
    from src.config.settings import Settings
    metadata(session)
    data, _, calendar = inputs()
    requests=[]
    def transport(request):
        if request.url.path.endswith('/token'):
            return httpx.Response(200,json={'accessToken':'synthetic-token','expiresAt':4102444800000})
        requests.append(dict(request.url.params))
        rows=[{'symbol':'XYZ','tradingDate':row['session'].replace('-','/'),
               **{key:str(row[key]) for key in ('open','high','low','close','volume')}} for row in data['bars']]
        return httpx.Response(200,json={'data':rows if request.url.params['pageIndex']=='1' else []})
    monkeypatch.setattr('src.services.technical_eod._observation_time', lambda:NOW-timedelta(seconds=1))
    with SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='test',ssi_api_secret='test'),
            transport=httpx.MockTransport(transport),today=lambda:NOW.date()) as provider:
        read=read_eod_history('XYZ',provider,calendar.coverage_start,calendar.coverage_end)
    # Transport has no finalization flag: independently supplied synthetic attestation, not SSI proof.
    read=attest_fixture(read)
    result=run(session,data,history_read=read)
    assert isinstance(result,TechnicalDailySignalPacket) and result.top_insights
    assert len(requests)==2 and all(r['timeFrame']=='1d' for r in requests)
    assert result.data_provenance['fetched_at'] is None


@pytest.mark.parametrize('error,status', [(TimeoutError('secret'),'SOURCE_UNAVAILABLE'),
                                       (RuntimeError('secret'),'INFRASTRUCTURE_FAILURE')])
def test_provider_and_infrastructure_errors_sanitized(session, monkeypatch, error, status):
    metadata(session)
    class Provider:
        source='SSI:FastConnect'
        def get_history(self,*args): raise error
    result=run(session,history_read=None,provider=Provider())
    assert result.status==status and 'secret' not in result.model_dump_json()


def test_unavailable_ca_does_not_block_factual_events_or_change_scores(session):
    metadata(session)
    class MissingCA:
        def context_for(self,*args,**kwargs): raise RuntimeError('private-config')
    plain=run(session)
    unavailable=run(session,corporate_actions=MissingCA())
    assert unavailable.ranked_eligible_event_ids==plain.ranked_eligible_event_ids
    assert [e.base_v0 for e in unavailable.top_insights]==[e.base_v0 for e in plain.top_insights]
    assert all(e.corporate_action_context.status=='UNKNOWN' and
               e.corporate_action_context.reason=='source_unavailable' for e in unavailable.top_insights)
    assert 'corporate_action_source_unavailable' in unavailable.limitations
    assert 'private-config' not in unavailable.to_json()


def test_ca_real_repository_observation_cutoff_isolation(session):
    from src.corporate_actions.models import CorporateActionNotice
    from src.corporate_actions.repository import CorporateActionRepository
    metadata(session)
    repo=CorporateActionRepository(session)
    data=snapshot()
    repo.ingest(CorporateActionNotice(symbol='XYZ',action_type='cash_dividend',
        effective_date=data['calendar'][-1],source='curated_verified',source_id='early',verified=True),
        received_at=NOW-timedelta(hours=1))
    first=run(session,data,corporate_actions=repo)
    assert all(e.corporate_action_context.status=='KNOWN_MATCH' for e in first.top_insights)
    repo.ingest(CorporateActionNotice(symbol='XYZ',action_type='stock_dividend',
        effective_date=data['calendar'][-1],source='curated_verified',source_id='late',verified=True),
        received_at=NOW+timedelta(hours=1))
    assert run(session,data,corporate_actions=repo).to_json()==first.to_json()


def test_explicit_noncomparability_preserves_independent_volume_and_missing_price(session):
    metadata(session)
    data,read,_=inputs()
    read=read.model_copy(update={'noncomparable_price_sessions':(date.fromisoformat(data['calendar'][-1]),)})
    result=run(session,data,history_read=read)
    assert [e.event_type for e in result.top_insights]==['unusual_volume']
    assert 'abnormal_price_move' in result.unresolved_checks
    assert result.data_provenance['raw_context_features']['daily_return'] is None


def test_missing_volume_context_stays_null(session):
    metadata(session)
    data,read,_=inputs()
    read=read.model_copy(update={'noncomparable_volume_sessions':(date.fromisoformat(data['calendar'][-1]),)})
    result=run(session,data,history_read=read)
    assert result.data_provenance['raw_context_features']['relative_volume'] is None
    assert result.data_provenance['raw_context_features']['volume'] is None


def test_audited_late_observation_not_relabelled_as_assumed_eod(session):
    metadata(session)
    _,read,_=inputs()
    final=read.observations[-1].model_copy(update={'availability_basis':'published',
        'available_at':NOW+timedelta(hours=1)})
    read=read.model_copy(update={'observations':read.observations[:-1]+(final,)})
    result=run(session,history_read=read)
    assert result.packet_state=='TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
    assert not result.top_insights


def test_history_range_bound_prevents_loading_and_missing_metadata_is_explicit(session):
    metadata(session)
    assert run(session,history_start=date(2010,1,1)).status=='INVALID_REQUEST'
    assert evaluate_technical_eod_packet('NOSUCH','2020-03-02',db_session=session,
        evaluation_as_of=NOW,generated_at=NOW).reason_codes==('active_security_metadata_unavailable',)


def test_developer_invocation_summary_is_bounded_and_explicit(session):
    metadata(session)
    summary=summarize_eod_result(run(session))
    assert summary['event_count']==summary['selected_insight_count']==2
    assert summary['overflow_count']==0 and summary['packet_state']=='HAS_INSIGHTS'
    assert summary['source_summary']['fetched_at'] is None
    incomplete=summarize_eod_result(run(session,calendar=None))
    assert incomplete['status']=='INCOMPLETE_EVIDENCE' and 'event_count' not in incomplete
