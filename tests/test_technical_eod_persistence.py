"""Durable worker/API contracts; synthetic reads are never live SSI evidence."""
from datetime import timedelta, timezone
import pytest
from sqlmodel import Session, select

from test_provisional_eod import evidence
from src.models import Security
from src.services.provisional_eod import compact_ssi_receipt
from src.services.technical_eod_store import (
    enqueue_provisional_eod, run_technical_eod_cycle, read_operational_packet,
)
from src.models.technical_eod import (TechnicalEODJob, TechnicalEODSnapshot,
    TechnicalEODRetrievalReceipt, TechnicalEODWorkerLease)


def setup(session, *, import_first=True, extra_history=False):
    target, calendar, publication, first, second = evidence()
    if extra_history:
        from src.services.technical_eod import fingerprint_eod_observations
        start=calendar.coverage_start-timedelta(days=1)
        row=second.history.observations[0]
        prior=row.model_copy(update={'observation_time':start.isoformat(),
            'available_at':row.available_at-timedelta(days=1),
            'payload':row.payload.model_copy(update={'date':start})})
        obs=(prior,)+second.history.observations
        version=fingerprint_eod_observations(obs)
        first=first.model_copy(update={'range_start':start,'history':first.history.model_copy(update={'observations':obs,'source_version':version})})
        second=second.model_copy(update={'range_start':start,'history':second.history.model_copy(update={'observations':obs,'source_version':version})})
        calendar=calendar.model_copy(update={'coverage_start':start,
            'records':(calendar.records[0].model_copy(update={'session':start}),)+calendar.records})
    session.add(Security(symbol='XYZ', exchange='HOSE',
        last_synced_at=first.request_started_at-timedelta(days=1)))
    session.commit()
    now=second.received_at+timedelta(minutes=1)
    enqueue_provisional_eod(session, 'XYZ', target, history_start=calendar.coverage_start,
        calendar=calendar, publication=publication,
        first=compact_ssi_receipt(first) if import_first else None, now=now)
    return target, calendar, publication, first, second, now


def run(session, second, now):
    return run_technical_eod_cycle(session.get_bind(), clock=lambda:now,
        acquire=lambda *args:second)


def test_matching_read_atomically_persists_only_provisional_packet(session):
    target, cal, pub, first, second, now=setup(session)
    assert run(session, second, now)['status']=='PROVISIONAL'
    session.expire_all()
    rows=session.exec(select(TechnicalEODSnapshot)).all()
    assert len(rows)==1 and rows[0].state=='ACTIVE'
    assert rows[0].evidence['second']['history']['source_version']==second.history.source_version
    response=read_operational_packet(session, 'XYZ', target, now)
    assert response.kind=='provisional_packet'
    assert response.assurance=='PROVISIONAL' and response.safe_to_display_as_verified is False
    assert response.packet.data_provenance['completion_assurance']=='PROVISIONAL'
    assert response.packet==rows[0].packet_model().packet


def test_cached_snapshot_does_not_acquire_or_append_duplicate(session):
    target, cal, pub, first, second, now=setup(session)
    run(session, second, now)
    result=run_technical_eod_cycle(session.get_bind(),clock=lambda:now+timedelta(hours=1),
        acquire=lambda *a:pytest.fail('unexpected SSI read'))
    assert result['status']=='IDLE'
    assert len(session.exec(select(TechnicalEODSnapshot)).all())==1


def test_first_read_stores_metadata_and_survives_restart(session):
    target, cal, pub, first, second, now=setup(session,import_first=False)
    result=run(session, first, now)
    assert result['status']=='WAITING_FOR_TIME'
    with Session(session.get_bind()) as restarted:
        job=restarted.get(TechnicalEODJob, 'XYZ:'+target.isoformat())
        assert job.first_receipt and 'history' not in job.first_receipt
        assert restarted.exec(select(TechnicalEODSnapshot)).all()==[]


def fresh(read, at, *, revision=False):
    from src.services.technical_eod import fingerprint_eod_observations
    observations=read.history.observations
    if revision:
        old=observations[-2]
        changed=old.model_copy(update={'payload':old.payload.model_copy(update={'close':old.payload.close+1})})
        observations=observations[:-2]+(changed,observations[-1])
    history=read.history.model_copy(update={'observations':observations,'observed_at':at,
        'source_version':fingerprint_eod_observations(observations)})
    return read.model_copy(update={'history':history,'request_started_at':at-timedelta(seconds=2),'received_at':at})


def test_revision_retracts_and_new_pair_appends_correction_version(session):
    target, cal, pub, first, second, now=setup(session)
    run(session,second,now)
    later=now+timedelta(hours=25)
    revised=fresh(second,later,revision=True)
    result=run(session,revised,later)
    assert result['status']=='INCOMPLETE_EVIDENCE' and result['retracted_snapshot_count']==1
    session.expire_all()
    old=session.exec(select(TechnicalEODSnapshot)).one()
    assert old.state=='RETRACTED' and old.retraction_reason=='ssi_history_revision_detected'
    assert read_operational_packet(session,'XYZ',target,later).kind=='diagnostic'
    assert session.get(TechnicalEODJob,'XYZ:'+target.isoformat()).first_receipt['source_version']==revised.history.source_version
    accepted_at=later+timedelta(hours=6,minutes=1)
    result=run(session,fresh(revised,accepted_at),accepted_at)
    assert result['status']=='PROVISIONAL' and result['snapshot_version']==2
    session.expire_all()
    rows=session.exec(select(TechnicalEODSnapshot).order_by(TechnicalEODSnapshot.version)).all()
    assert [r.state for r in rows]==['RETRACTED','ACTIVE']
    assert rows[0].packet==old.packet
    assert read_operational_packet(session,'XYZ',target,accepted_at).snapshot_version==2


def test_unchanged_due_recheck_is_audited_without_duplicate_packet(session):
    target, cal, pub, first, second, now=setup(session)
    run(session,second,now)
    later=now+timedelta(hours=25)
    result=run(session,fresh(second,later),later)
    assert result['cache_reused'] and result['snapshot_version']==1
    session.expire_all()
    assert len(session.exec(select(TechnicalEODSnapshot)).all())==1
    assert len(session.exec(select(TechnicalEODRetrievalReceipt)).all())==3
    response=read_operational_packet(session,'XYZ',target,later)
    assert response.last_checked_at==later and response.freshness=='FRESH'


@pytest.mark.parametrize('gap',['calendar','publication','calendar_hole','publication_late'])
def test_missing_evidence_never_acquires_or_persists_bars(session,gap):
    target, cal, pub, first, second, now=setup(session)
    if gap=='calendar':cal=None
    if gap=='publication':pub=None
    if gap=='calendar_hole':cal=cal.model_copy(update={'records':cal.records[:-1]})
    if gap=='publication_late':pub=pub.model_copy(update={'verified_at':now+timedelta(days=1)})
    enqueue_provisional_eod(session,'XYZ',target,history_start=first.range_start,
        calendar=cal,publication=pub,first=compact_ssi_receipt(first),now=now)
    result=run_technical_eod_cycle(session.get_bind(),clock=lambda:now,
        acquire=lambda *a:pytest.fail('read without qualified evidence'))
    assert result['status']=='INCOMPLETE_EVIDENCE'
    assert session.exec(select(TechnicalEODSnapshot)).all()==[]


@pytest.mark.parametrize('gate',['six_hours','publication_24_hours'])
def test_future_time_gate_never_requests_ssi(session,gate):
    target, cal, pub, first, second, now=setup(session)
    if gate=='six_hours':
        first=fresh(first,pub.published_at+timedelta(hours=18))
    early=first.received_at+timedelta(hours=5) if gate=='six_hours' else pub.published_at+timedelta(hours=23)
    job=session.get(TechnicalEODJob,'XYZ:'+target.isoformat())
    job.first_receipt=compact_ssi_receipt(first).model_dump(mode='json')
    job.next_due_at=early
    session.add(job);session.commit()
    result=run_technical_eod_cycle(session.get_bind(),clock=lambda:early,
        acquire=lambda *a:pytest.fail('premature read'))
    assert result['status']=='WAITING_FOR_TIME'
    assert session.exec(select(TechnicalEODSnapshot)).all()==[]


def test_authentication_failure_stops_without_automatic_retry(session):
    from src.providers.base import ProviderError
    target, cal, pub, first, second, now=setup(session)
    calls=[]
    def fail(*a):
        calls.append(1)
        raise ProviderError('API_SECRET=PRIVATE')
    assert run_technical_eod_cycle(session.get_bind(),clock=lambda:now,acquire=fail)['status']=='STOPPED'
    assert run_technical_eod_cycle(session.get_bind(),clock=lambda:now+timedelta(days=2),acquire=fail)['status']=='IDLE'
    assert calls==[1]
    assert 'PRIVATE' not in str(read_operational_packet(session,'XYZ',target,now).model_dump())


def test_worker_interruption_expires_lease_and_fences_old_result(session):
    from src.services.technical_eod_store import _claim,_finish,LEASE_TIME
    target, cal, pub, first, second, now=setup(session)
    token,job=_claim(session.get_bind(),now)
    assert run(session,second,now)['status']=='IDLE'
    later=now+LEASE_TIME+timedelta(seconds=1)
    assert run(session,fresh(second,later),later)['status']=='PROVISIONAL'
    result=_finish(session.get_bind(),token,job,later,
        lambda *a:pytest.fail('stale worker published'))
    assert result['status']=='LEASE_LOST'
    assert len(session.exec(select(TechnicalEODSnapshot)).all())==1


def test_interruption_during_publish_rolls_back_and_recovers(session,monkeypatch):
    target, cal, pub, first, second, now=setup(session)
    original=Session.add
    def interrupted(self,row,*a,**kw):
        if isinstance(row,TechnicalEODSnapshot):raise KeyboardInterrupt()
        return original(self,row,*a,**kw)
    with monkeypatch.context() as m:
        m.setattr(Session,'add',interrupted)
        with pytest.raises(KeyboardInterrupt):run(session,second,now)
    session.expire_all()
    assert session.exec(select(TechnicalEODSnapshot)).all()==[]
    assert session.get(TechnicalEODJob,'XYZ:'+target.isoformat()).active_snapshot_id is None
    later=now+timedelta(minutes=11)
    assert run(session,fresh(second,later),later)['status']=='PROVISIONAL'


def test_changed_definition_during_read_fences_publication(session):
    target, cal, pub, first, second, now=setup(session)
    def change(*a):
        with Session(session.get_bind()) as editor:
            enqueue_provisional_eod(editor,'XYZ',target,history_start=cal.coverage_start,
                calendar=None,publication=pub,now=now)
        return second
    result=run_technical_eod_cycle(session.get_bind(),clock=lambda:now,acquire=change)
    assert result['status']=='EVIDENCE_CHANGED'
    assert session.exec(select(TechnicalEODSnapshot)).all()==[]


def test_corrupted_snapshot_and_private_provenance_fail_closed(session):
    target, cal, pub, first, second, now=setup(session)
    run(session,second,now)
    row=session.exec(select(TechnicalEODSnapshot)).one()
    row.packet={**row.packet,'publication_source':'https://public.example?token=SECRET'}
    session.add(row);session.commit()
    result=read_operational_packet(session,'XYZ',target,now)
    assert result.kind=='diagnostic' and 'SECRET' not in str(result.model_dump())


def test_operational_api_is_select_only_and_never_calls_provider_or_scoring(session,client,monkeypatch):
    from sqlalchemy import event
    from main import app
    from routers.technical import get_evaluation_clock
    target, cal, pub, first, second, now=setup(session)
    run(session,second,now)
    app.dependency_overrides[get_evaluation_clock]=lambda:now
    monkeypatch.setattr('src.services.technical_eod_store.capture_fresh_ssi_read',lambda *a:pytest.fail('HTTP SSI'))
    monkeypatch.setattr('src.services.technical_eod_store.evaluate_provisional_technical_eod_packet',lambda *a,**kw:pytest.fail('HTTP scoring'))
    statements=[]
    def capture(conn,cursor,statement,parameters,context,executemany):statements.append(statement)
    event.listen(session.get_bind(),'before_cursor_execute',capture)
    try:
        response=client.get('/technical/XYZ/daily/operational',params={'session':target.isoformat()})
        assert response.status_code==200
        assert response.json()['kind']=='provisional_packet'
        assert response.json()['assurance']=='PROVISIONAL'
        assert response.json()['safe_to_display_as_verified'] is False
    finally:event.remove(session.get_bind(),'before_cursor_execute',capture)
    assert statements and all(s.lstrip().upper().startswith('SELECT') for s in statements)
    # Existing verified endpoint cannot read a provisional database snapshot.
    verified=client.get('/technical/XYZ/daily',params={'session':target.isoformat()})
    assert verified.json()['kind']=='diagnostic' and not verified.json()['safe_to_display_as_verified']


def test_public_hose_urls_are_safe_but_private_paths_and_tokens_are_rejected():
    from src.services.technical_api import public_payload
    assert public_payload('https://www.hsx.vn/vi/tin-tuc/official/123')
    assert not public_payload(r'C:\private\receipt.json')
    assert not public_payload('https://public.example?access_token=secret')


def test_source_basis_failure_keeps_raw_history_out_of_storage(session):
    target, cal, pub, first, second, now=setup(session)
    bad=second.model_copy(update={'history':second.history.model_copy(update={'volume_unit':'lots'})})
    result=run(session,bad,now)
    assert result['status']=='INCOMPLETE_EVIDENCE'
    assert session.exec(select(TechnicalEODSnapshot)).all()==[]
    assert session.exec(select(TechnicalEODRetrievalReceipt)).all()==[]


def test_evidence_change_retracts_without_another_ssi_call(session):
    target, cal, pub, first, second, now=setup(session)
    run(session,second,now)
    session.expire_all()
    enqueue_provisional_eod(session,'XYZ',target,history_start=cal.coverage_start,calendar=None,
        publication=pub,now=now+timedelta(minutes=1))
    result=read_operational_packet(session,'XYZ',target,now+timedelta(minutes=1))
    assert result.kind=='diagnostic' and result.reason_codes==('evidence_definition_changed',)
    assert session.exec(select(TechnicalEODSnapshot)).one().state=='RETRACTED'


def test_api_stale_receipt_is_labeled_and_infrastructure_failure_is_sanitized(session,client,monkeypatch):
    from main import app
    from routers.technical import get_evaluation_clock
    target, cal, pub, first, second, now=setup(session)
    run(session,second,now)
    later=now+timedelta(hours=25)
    app.dependency_overrides[get_evaluation_clock]=lambda:later
    result=client.get('/technical/XYZ/daily/operational',params={'session':target.isoformat()})
    assert result.json()['freshness']=='STALE'
    monkeypatch.setattr(session,'get',lambda *a:(_ for _ in ()).throw(RuntimeError('API_SECRET=SECRET')))
    response=client.get('/technical/XYZ/daily/operational',params={'session':target.isoformat()})
    assert response.status_code==503 and response.json()['kind']=='diagnostic'
    assert 'SECRET' not in response.text


def test_cross_session_history_revision_retracts_all_affected_snapshots(session):
    from src.services.technical_eod import fingerprint_eod_observations
    target, cal, pub, first, second, now=setup(session,extra_history=True)
    run(session,second,now)
    prior_target=second.history.observations[-2].payload.date
    prior_cal=cal.model_copy(update={'coverage_end':prior_target,
        'records':tuple(r for r in cal.records if r.session<=prior_target)})
    prior_pub=pub.model_copy(update={'session':prior_target})
    def trim(read):
        obs=tuple(o for o in read.history.observations if o.payload.date<=prior_target)
        history=read.history.model_copy(update={'observations':obs,'source_version':fingerprint_eod_observations(obs)})
        return read.model_copy(update={'range_end':prior_target,'history':history})
    enqueue_provisional_eod(session,'XYZ',prior_target,history_start=cal.coverage_start,
        calendar=prior_cal,publication=prior_pub,first=compact_ssi_receipt(trim(first)),now=now)
    prior_result=run(session,trim(second),now)
    assert prior_result['status']=='PROVISIONAL',prior_result
    later=now+timedelta(hours=25)
    result=run(session,trim(fresh(second,later,revision=True)),later)
    assert result['retracted_snapshot_count']==2
    session.expire_all()
    assert all(r.state=='RETRACTED' for r in session.exec(select(TechnicalEODSnapshot)).all())
    assert read_operational_packet(session,'XYZ',prior_target,later).kind=='diagnostic'


def test_durable_file_reopen_keeps_receipt_and_accepts_qualified_second_read(tmp_path):
    from sqlmodel import create_engine
    from src.db.session import create_tables
    url='sqlite:///'+str(tmp_path/'eod.db')
    engine=create_engine(url)
    create_tables(engine)
    with Session(engine) as session:
        target, cal, pub, first, second, now=setup(session,import_first=False)
        at=pub.published_at+timedelta(hours=18)
        first=fresh(first,at)
        job=session.get(TechnicalEODJob,'XYZ:'+target.isoformat())
        job.next_due_at=at
        session.add(job);session.commit()
        assert run(session,first,at)['status']=='WAITING_FOR_TIME'
    engine.dispose()
    engine=create_engine(url)
    with Session(engine) as session:
        early=at+timedelta(hours=5)
        assert run_technical_eod_cycle(engine,clock=lambda:early,acquire=lambda *a:pytest.fail('early after restart'))['status']=='IDLE'
        eligible=at+timedelta(hours=6,seconds=2)
        assert run(session,fresh(second,eligible),eligible)['status']=='PROVISIONAL'
    engine.dispose()
    engine=create_engine(url)
    with Session(engine) as session:
        assert read_operational_packet(session,'XYZ',target,eligible).kind=='provisional_packet'
    engine.dispose()
