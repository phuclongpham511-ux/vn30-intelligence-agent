"""Synthetic evidence contracts, never live-source qualification."""
from datetime import date, datetime, timedelta, timezone
import pytest
from test_technical_eod_consumer import inputs, metadata, run
from test_d4_runtime import data_with_tail
from src.services.session_evidence import (
    SessionEvidence, CalendarEvidence, EODCompletionEvidence, bar_fingerprint,
)
from src.services.technical_eod import evaluate_technical_eod_packet
from src.materiality.delivery import TechnicalDailySignalPacket


def modern(data=None):
    data, read, old = inputs(data)
    records=[]
    d=old.coverage_start
    while d<=old.coverage_end:
        records.append(SessionEvidence(session=d,
            status='OCCURRED' if d in old.sessions else 'CLOSED',
            source_ref='synthetic-venue-record', observed_at=old.observed_at))
        d+=timedelta(days=1)
    calendar=CalendarEvidence(venue='HOSE', coverage_start=old.coverage_start,
        coverage_end=old.coverage_end, version='synthetic-calendar-v2', records=tuple(records))
    return data,read,calendar


def call(session,data,read,calendar,cutoff=None):
    from test_d1_runtime import NOW
    cutoff=cutoff or NOW
    return evaluate_technical_eod_packet('XYZ', data['calendar'][-1], db_session=session,
        history_read=read, calendar=calendar, history_start=calendar.coverage_start,
        evaluation_as_of=cutoff,generated_at=cutoff)


def proof(read,bar,at):
    return EODCompletionEvidence(ticker='XYZ',venue='HOSE',session=bar.date,
        source=read.source, source_version=read.source_version,
        bar_sha256=bar_fingerprint(bar),status='COMPLETE',available_at=at,
        observed_at=read.observed_at,source_ref='synthetic-finalization-attestation')


def test_verified_calendar_provenance_and_repeat(session):
    metadata(session)
    data,read,cal=modern()
    result=call(session,data,read,cal)
    assert isinstance(result,TechnicalDailySignalPacket)
    assert result.to_json()==call(session,data,read,cal).to_json()
    assert result.data_provenance['calendar_contract']=='venue-session-evidence-v1'
    assert result.data_provenance['completion_assurance']=='VERIFIED'


def test_weekend_and_holiday_closures_keep_volume_episode(session):
    metadata(session)
    data=data_with_tail([.1,.1],[200,200])
    data['calendar'][-2:]=['2020-04-03','2020-04-07']
    for row,day in zip(data['bars'],data['calendar']): row['session']=day
    data,read,cal=modern(data)
    result=call(session,data,read,cal)
    volume=next(e for e in result.top_insights if e.event_type=='unusual_volume')
    assert volume.episode_relationship=='same_episode' and volume.episode_status=='CONTINUATION'


@pytest.mark.parametrize('status',['SCHEDULED','UNKNOWN','SUSPENDED','NO_TRADE','MISSING'])
def test_gap_never_bridges_volume_episode(session,status):
    metadata(session)
    data=data_with_tail([.1,.1,.1],[200,200,200])
    data,read,cal=modern(data)
    gap=cal.records[-2]
    changes={'status':status if status in ('SCHEDULED','UNKNOWN') else 'OCCURRED'}
    if status in ('SUSPENDED','NO_TRADE'):
        changes.update(ticker='XYZ',ticker_status=status)
    records=tuple(r.model_copy(update=changes) if r.session==gap.session else r for r in cal.records)
    if status=='MISSING': records=tuple(r for r in records if r.session!=gap.session)
    cal=cal.model_copy(update={'records':records})
    result=call(session,data,read,cal)
    volume=next(e for e in result.top_insights if e.event_type=='unusual_volume')
    assert volume.episode_status=='UNRESOLVED'
    assert volume.episode_id is None
    assert result.data_provenance['calendar_unresolved_sessions']


@pytest.mark.parametrize('problem',['duplicate','venue','future','coverage'])
def test_bad_calendar_is_explicit(session,problem):
    metadata(session)
    data,read,cal=modern()
    if problem=='duplicate': cal=cal.model_copy(update={'records':cal.records+(cal.records[-1].model_copy(update={'status':'CLOSED'}),)})
    if problem=='venue': cal=cal.model_copy(update={'venue':'HNX'})
    if problem=='future': cal=cal.model_copy(update={'records':cal.records[:-1]+(cal.records[-1].model_copy(update={'observed_at':read.observed_at+timedelta(days=3)}),)})
    if problem=='coverage': cal=cal.model_copy(update={'coverage_end':cal.coverage_end-timedelta(days=1)})
    result=call(session,data,read,cal)
    assert result.status=='INCOMPLETE_EVIDENCE'


def same_day(session):
    metadata(session)
    data,read,cal=modern()
    target=read.observations[-1].payload.date
    cutoff=datetime.combine(target,datetime.min.time(),timezone(timedelta(hours=7)))+timedelta(hours=16)
    receipt=cutoff-timedelta(minutes=1)
    read=read.model_copy(update={'observed_at':receipt})
    final=read.observations[-1].model_copy(update={'availability_basis':'published','available_at':receipt})
    read=read.model_copy(update={'observations':read.observations[:-1]+(final,),
        'completion_evidence':(proof(read,final.payload,receipt),)})
    cal=cal.model_copy(update={'records':tuple(r.model_copy(update={'observed_at':receipt}) for r in cal.records)})
    security=session.get(__import__('src.models',fromlist=['Security']).Security,'XYZ')
    security.last_synced_at=receipt-timedelta(days=1)
    session.commit()
    return data,read,cal,cutoff


def test_verified_same_day_is_allowed_and_asof_preserved(session):
    data,read,cal,cutoff=same_day(session)
    result=call(session,data,read,cal,cutoff)
    assert isinstance(result,TechnicalDailySignalPacket) and result.top_insights
    assert result.evaluation_as_of==cutoff.astimezone(timezone.utc)
    price=next(c for c in result.family_checks if c.family=='abnormal_price_move')
    assert datetime.fromisoformat(price.evidence['cutoff'])==cutoff


@pytest.mark.parametrize('problem',['missing','incomplete','late','wrong_hash','wrong_source','late_receipt'])
def test_completion_requires_actual_proof_even_after_close(session,problem):
    data,read,cal,cutoff=same_day(session)
    proofs=read.completion_evidence
    if problem=='missing': proofs=()
    else:
        changes={'incomplete':{'status':'INCOMPLETE'},'late':{'available_at':cutoff+timedelta(minutes=1)},
            'wrong_hash':{'bar_sha256':'0'*64},'wrong_source':{'source':'other'},
            'late_receipt':{'observed_at':cutoff+timedelta(minutes=1)}}[problem]
        proofs=(proofs[0].model_copy(update=changes),)
    result=call(session,data,read.model_copy(update={'completion_evidence':proofs}),cal,cutoff)
    assert result.status=='INCOMPLETE_EVIDENCE'
    assert 'completion' in ' '.join(result.reason_codes)


def test_historical_missing_proof_is_not_certified_no_change(session):
    metadata(session)
    data,read,cal=modern()
    result=call(session,data,read.model_copy(update={'completion_evidence':()}),cal)
    assert result.status=='INCOMPLETE_EVIDENCE'


def test_completion_is_bound_to_current_bar_revision(session):
    metadata(session)
    data,read,cal=modern()
    final=read.observations[-1]
    bar=final.payload.model_copy(update={'volume':123})
    read=read.model_copy(update={'observations':read.observations[:-1]+(final.model_copy(update={'payload':bar}),)})
    assert call(session,data,read,cal).status=='INCOMPLETE_EVIDENCE'


def test_scheduled_open_is_not_actual_venue_occurrence(session):
    metadata(session)
    data,read,cal=modern()
    cal=cal.model_copy(update={'records':cal.records[:-1]+(
        cal.records[-1].model_copy(update={'evidence_kind':'official_schedule'}),)})
    assert call(session,data,read,cal).status=='INCOMPLETE_EVIDENCE'


def test_incomplete_calendar_never_becomes_complete_no_change(session):
    from test_d1_runtime import snapshot
    metadata(session)
    data,read,cal=modern(snapshot(returns=[.01]*60+[0],volumes=[100]*61+[50]))
    cal=cal.model_copy(update={'records':tuple(r for r in cal.records if r!=cal.records[1])})
    result=call(session,data,read,cal)
    assert result.packet_state=='TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
    assert not result.top_insights
    assert 'calendar_continuity_unresolved' in result.limitations


def test_future_calendar_evidence_and_future_bars_do_not_change_prefix(session):
    metadata(session)
    data,read,cal=modern()
    initial=call(session,data,read,cal)
    future_day=cal.coverage_end+timedelta(days=1)
    later=cal.records[-1].model_copy(update={'session':future_day,'status':'UNKNOWN'})
    cal=cal.model_copy(update={'records':cal.records+(later,)})
    final=read.observations[-1]
    future=final.model_copy(update={'observation_time':future_day.isoformat(),
        'payload':final.payload.model_copy(update={'date':future_day,'volume':999999})})
    read=read.model_copy(update={'observations':read.observations+(future,)})
    assert call(session,data,read,cal).to_json()==initial.to_json()


def test_provider_missing_scheduled_ticker_bar_remains_unknown(session):
    metadata(session)
    data,read,cal=modern(data_with_tail([.1,.1,.1],[200,200,200]))
    read=read.model_copy(update={'observations':read.observations[:-2]+read.observations[-1:]})
    result=call(session,data,read,cal)
    volume=next(e for e in result.top_insights if e.event_type=='unusual_volume')
    assert volume.episode_status=='UNRESOLVED'
    assert volume.episode_id is None


@pytest.mark.parametrize('problem',['duplicate','wrong_venue','naive','wrong_version'])
def test_invalid_completion_contract_does_not_emit(session,problem):
    data,read,cal,cutoff=same_day(session)
    proofs=read.completion_evidence
    if problem=='duplicate': proofs=proofs+proofs
    else:
        changes={'wrong_venue':{'venue':'HNX'},'naive':{'observed_at':cutoff.replace(tzinfo=None)},
            'wrong_version':{'source_version':'other-revision'}}[problem]
        proofs=(proofs[0].model_copy(update=changes),)
    result=call(session,data,read.model_copy(update={'completion_evidence':proofs}),cal,cutoff)
    assert result.status=='INCOMPLETE_EVIDENCE'
    assert not hasattr(result,'top_insights')


def test_same_day_assumed_availability_cannot_replace_publication(session):
    from src.evaluation.benchmark.inputs import eod
    data,read,cal,cutoff=same_day(session)
    final=read.observations[-1].model_copy(update={'availability_basis':'end_of_day_assumption',
        'available_at':eod(data['calendar'][-1])})
    read=read.model_copy(update={'observations':read.observations[:-1]+(final,)})
    assert call(session,data,read,cal,cutoff).reason_codes==('eod_completion_availability_unverified',)


def test_same_day_direct_d1_rejects_attestation_for_different_bar(session):
    from src.materiality import evaluate_d1_market_events
    data,read,cal,cutoff=same_day(session)
    data['is_fixture']=False
    data['provenance'].update(downloaded_at=read.observed_at.isoformat(),
        version=read.source_version,venue='HOSE',completion_evidence=read.completion_evidence[0].model_dump(mode='json'))
    data['bars'][-1].update(available_at=read.observations[-1].available_at.isoformat(),volume=999999)
    result=evaluate_d1_market_events(data,'XYZ',data['calendar'][-1],generated_at=cutoff)
    assert all(f['predicate_result']=='UNRESOLVED' and f['reason']=='session_not_completed'
        for f in result.factual_decisions.values())


def test_prior_incomplete_proof_overrides_daily_assumption(session):
    metadata(session)
    data,read,cal=modern(data_with_tail([.1,.1,.1],[200,200,200]))
    read=read.model_copy(update={'completion_evidence':tuple(
        p.model_copy(update={'status':'INCOMPLETE'}) if p.session==read.observations[-2].payload.date else p
        for p in read.completion_evidence)})
    result=call(session,data,read,cal)
    volume=next(e for e in result.top_insights if e.event_type=='unusual_volume')
    assert volume.episode_status=='UNRESOLVED' and volume.episode_id is None


def test_known_post_eod_completion_cannot_hide_under_daily_assumption(session):
    metadata(session)
    data,read,cal=modern()
    target=read.observations[-1].payload.date
    proofs=tuple(p.model_copy(update={'available_at':datetime.combine(target,datetime.min.time(),timezone.utc)+timedelta(days=1)})
        if p.session==target else p for p in read.completion_evidence)
    result=call(session,data,read.model_copy(update={'completion_evidence':proofs}),cal)
    assert result.packet_state=='TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
    assert not result.top_insights


def test_late_prior_completion_correction_is_not_visible_at_earlier_cutoff(session):
    metadata(session)
    data,read,cal=modern(data_with_tail([.1,.1,.1],[200,200,200]))
    original=call(session,data,read,cal)
    prior=read.completion_evidence[-2].model_copy(update={'status':'INCOMPLETE',
        'observed_at':read.observed_at+timedelta(days=3)})
    # A later source attestation is not knowledge available to this preserved read.
    read=read.model_copy(update={'completion_evidence':read.completion_evidence+(prior,)})
    assert call(session,data,read,cal).to_json()==original.to_json()


def test_future_calendar_correction_does_not_change_earlier_evidence(session):
    metadata(session)
    data,read,cal=modern()
    original=call(session,data,read,cal)
    future=cal.records[-2].model_copy(update={'status':'CLOSED',
        'observed_at':read.observed_at+timedelta(days=3)})
    cal=cal.model_copy(update={'records':cal.records+(future,)})
    assert call(session,data,read,cal).to_json()==original.to_json()
