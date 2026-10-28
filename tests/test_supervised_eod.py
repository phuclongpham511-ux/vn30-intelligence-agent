"""Controlled pilot lifecycle; no network or live market data in tests."""
from datetime import datetime,timedelta
import json
import pytest
from sqlmodel import Session,select
from test_technical_eod_persistence import setup,fresh
from src.models.technical_eod import TechnicalEODSupervision,TechnicalEODJob,TechnicalEODSnapshot
from src.services.technical_eod_supervision import initialize_supervision,supervised_eod_cycle,resume_supervision
from src.services.technical_eod_store import read_latest_operational_packet


def pilot(session):
    target,cal,pub,first,second,now=setup(session,import_first=False)
    session.delete(session.get(TechnicalEODJob,'XYZ:'+target.isoformat()));session.commit()
    seed=cal.model_copy(update={'coverage_end':target-timedelta(days=1),
        'records':tuple(r for r in cal.records if r.session<target)})
    initialize_supervision(session,'XYZ',seed,now)
    qualified={'record':cal.records[-1].model_dump(mode='json'),
        'publication':pub.model_dump(mode='json'),'receipt':{'metadata_sha256':'a'*64}}
    class Source:
        calls=0
        def qualify_day(self,day):
            self.calls+=1
            return qualified if day==target else None
    return target,cal,pub,second,now,Source()


def test_dry_run_has_no_writes_or_ssi_and_reports_publication_gate(session):
    from sqlalchemy import event
    target,cal,pub,read,now,source=pilot(session)
    sql=[]
    def capture(conn,cursor,statement,parameters,context,executemany):sql.append(statement)
    event.listen(session.get_bind(),'before_cursor_execute',capture)
    try: result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:now,
        acquire=lambda *a:pytest.fail('dry SSI'),dry_run=True)
    finally:event.remove(session.get_bind(),'before_cursor_execute',capture)
    assert result['status']=='DRY_RUN' and result['writes']==result['ssi_requests']==0
    assert result['candidates'][0]['session']==target.isoformat()
    assert result['candidates'][0]['second_read_due_at'] is None
    assert sql and all(s.lstrip().upper().startswith('SELECT') for s in sql)


def test_operator_status_is_metadata_only_and_read_only(session):
    from sqlalchemy import event
    from src.services.technical_eod_supervision import supervision_status
    target,cal,pub,read,now,source=pilot(session)
    engine=session.get_bind()
    supervised_eod_cycle(engine,source,clock=lambda:now,acquire=lambda *a:fresh(read,now))
    sql=[]
    def capture(conn,cursor,statement,parameters,context,executemany):sql.append(statement)
    event.listen(engine,'before_cursor_execute',capture)
    try:
        with Session(engine) as reopened:status=supervision_status(reopened,now)
    finally:event.remove(engine,'before_cursor_execute',capture)
    assert status['jobs'][0]['canonical_sha256']
    assert status['jobs'][0]['first_received_at']
    assert status['ssi_requests']==status['writes']==0
    assert 'observations' not in json.dumps(status)
    assert sql and all(s.lstrip().upper().startswith('SELECT') for s in sql)


def test_first_second_read_and_restart_use_durable_receipt_and_delayed_packet(session):
    target,cal,pub,read,now,source=pilot(session)
    engine=session.get_bind()
    first=supervised_eod_cycle(engine,source,clock=lambda:now,acquire=lambda *a:fresh(read,now))
    assert first['status']=='WAITING_FOR_TIME'
    with Session(engine) as reopened:
        job=reopened.get(TechnicalEODJob,'XYZ:'+target.isoformat())
        assert job.first_receipt and 'observations' not in json.dumps(job.first_receipt)
        due=datetime.fromisoformat(job.first_receipt['received_at'])+timedelta(hours=6)
    early=now+timedelta(hours=5)
    assert supervised_eod_cycle(engine,source,clock=lambda:early,
        acquire=lambda *a:pytest.fail('early SSI'))['status'] in ('IDLE','WAITING_FOR_TIME')
    later=due+timedelta(seconds=2)
    accepted=supervised_eod_cycle(engine,source,clock=lambda:later,acquire=lambda *a:fresh(read,later))
    assert accepted['status']=='PROVISIONAL',accepted
    with Session(engine) as reopened:
        packet=read_latest_operational_packet(reopened,'XYZ',later)
        assert packet.assurance=='PROVISIONAL'
        assert packet.packet.trading_session==target.isoformat()
        assert len(reopened.exec(select(TechnicalEODSnapshot)).all())==1


def test_missing_occurrence_never_creates_job_or_calls_ssi(session):
    target,cal,pub,read,now,source=pilot(session)
    source.qualify_day=lambda _:None
    result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:now,
        acquire=lambda *a:pytest.fail('unqualified SSI'))
    assert result['status']=='INCOMPLETE_EVIDENCE'
    assert result['discovery']['reason_codes']==['official_hose_session_unavailable']
    with Session(session.get_bind()) as reopened:
        assert reopened.get(TechnicalEODJob,'XYZ:'+target.isoformat()) is None
        assert reopened.exec(select(TechnicalEODSnapshot)).all()==[]


def test_source_failure_backoff_is_durable_capped_and_sanitized(session):
    target,cal,pub,read,now,source=pilot(session)
    source.qualify_day=lambda _:(_ for _ in ()).throw(RuntimeError('API_SECRET=SECRET'))
    for hours in (0,3,8):
        result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:now+timedelta(hours=hours))
    assert result['status']=='HALTED'
    assert 'SECRET' not in json.dumps(result)
    assert supervised_eod_cycle(session.get_bind(),source,clock=lambda:now+timedelta(days=1))['status']=='HALTED'
    with Session(session.get_bind()) as reopened:
        resume_supervision(reopened,now+timedelta(days=1))
        assert not reopened.get(TechnicalEODSupervision,'pilot').halted


def test_pilot_throttle_and_scope_do_not_process_other_ticker_jobs(session):
    target,cal,pub,read,now,source=pilot(session)
    session.add(TechnicalEODJob(id='OTHER:'+target.isoformat(),ticker='OTHER',trading_session=target,
        definition={},definition_hash='irrelevant',next_due_at=now-timedelta(days=1)))
    session.commit()
    calls=[]
    result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:now,
        acquire=lambda ticker,*a:(calls.append(ticker) or fresh(read,now)))
    assert result['status']=='WAITING_FOR_TIME' and calls==['XYZ']
    assert supervised_eod_cycle(session.get_bind(),source,clock=lambda:now+timedelta(minutes=1),
        acquire=lambda *a:pytest.fail('repeat SSI'))['status']=='IDLE'
    with Session(session.get_bind()) as reopened:
        assert reopened.get(TechnicalEODJob,'OTHER:'+target.isoformat()).last_attempt_at is None


def accept(session):
    target,cal,pub,read,now,source=pilot(session)
    engine=session.get_bind()
    supervised_eod_cycle(engine,source,clock=lambda:now,acquire=lambda *a:fresh(read,now))
    later=now+timedelta(hours=6,seconds=2)
    assert supervised_eod_cycle(engine,source,clock=lambda:later,
        acquire=lambda *a:fresh(read,later))['status']=='PROVISIONAL'
    return target,read,later,source


def test_revision_retracts_and_corrected_pair_publishes_next_version(session):
    target,read,accepted,source=accept(session)
    now=accepted+timedelta(hours=25)
    revised=supervised_eod_cycle(session.get_bind(),source,clock=lambda:now,
        acquire=lambda *a:fresh(read,now,revision=True))
    assert revised['status']=='INCOMPLETE_EVIDENCE'
    with Session(session.get_bind()) as reopened:
        assert read_latest_operational_packet(reopened,'XYZ',now).kind=='diagnostic'
        assert reopened.exec(select(TechnicalEODSnapshot)).one().state=='RETRACTED'
    corrected=now+timedelta(hours=6,seconds=2)
    result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:corrected,
        acquire=lambda *a:fresh(read,corrected,revision=True))
    assert result['status']=='PROVISIONAL',result
    with Session(session.get_bind()) as reopened:
        assert read_latest_operational_packet(reopened,'XYZ',corrected).snapshot_version==2
        assert len(reopened.exec(select(TechnicalEODSnapshot)).all())==2


def test_mismatched_second_read_never_persists_raw_data(session):
    target,cal,pub,read,now,source=pilot(session)
    supervised_eod_cycle(session.get_bind(),source,clock=lambda:now,acquire=lambda *a:fresh(read,now))
    later=now+timedelta(hours=6,seconds=2)
    result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:later,
        acquire=lambda *a:fresh(read,later,revision=True))
    assert result['status']=='INCOMPLETE_EVIDENCE'
    with Session(session.get_bind()) as reopened:
        assert reopened.exec(select(TechnicalEODSnapshot)).all()==[]
        assert 'observations' not in json.dumps(reopened.get(TechnicalEODJob,'XYZ:'+target.isoformat()).first_receipt)


def test_authentication_failure_halts_without_repeated_reads_or_canonical_bypass(session):
    from src.providers.base import ProviderError
    from src.services.technical_eod_store import run_technical_eod_cycle
    target,cal,pub,read,now,source=pilot(session)
    calls=[]
    def failed(*a):
        calls.append(a);raise ProviderError('sanitized authentication failure')
    assert supervised_eod_cycle(session.get_bind(),source,clock=lambda:now,acquire=failed)['status']=='HALTED'
    assert supervised_eod_cycle(session.get_bind(),source,clock=lambda:now+timedelta(days=1),acquire=failed)['status']=='HALTED'
    assert run_technical_eod_cycle(session.get_bind(),clock=lambda:now+timedelta(days=1),acquire=failed)['status']=='IDLE'
    assert len(calls)==1


def test_transient_transport_retries_are_backed_off_and_capped(session):
    from src.providers.base import ProviderTransientError
    target,cal,pub,read,now,source=pilot(session)
    calls=[]
    def failed(*a):
        calls.append(a);raise ProviderTransientError('sanitized timeout')
    for hours in (0,3,8):
        result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:now+timedelta(hours=hours),acquire=failed)
    assert result['status']=='HALTED'
    assert len(calls)==3
    assert supervised_eod_cycle(session.get_bind(),source,clock=lambda:now+timedelta(days=1),acquire=failed)['status']=='HALTED'
    assert len(calls)==3


def test_missing_ssi_target_is_incomplete_and_never_stored(session):
    target,cal,pub,read,now,source=pilot(session)
    invalid=fresh(read,now).model_copy(update={'history':read.history.model_copy(update={'observations':()})})
    result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:now,acquire=lambda *a:invalid)
    assert result['status']=='INCOMPLETE_EVIDENCE'
    with Session(session.get_bind()) as reopened:
        assert reopened.exec(select(TechnicalEODSnapshot)).all()==[]
        assert reopened.get(TechnicalEODJob,'XYZ:'+target.isoformat()).first_receipt is None


def test_expired_coordinator_cannot_publish_and_new_worker_recovers(session):
    from src.services.technical_eod_supervision import _claim,_save
    target,cal,pub,read,now,source=pilot(session)
    engine=session.get_bind()
    old=_claim(engine,now)
    assert supervised_eod_cycle(engine,source,clock=lambda:now,acquire=lambda *a:pytest.fail('busy SSI'))['status']=='IDLE'
    recovered=now+timedelta(minutes=11)
    assert _save(engine,old,recovered,lambda *a:pytest.fail('expired publication'))['status']=='LEASE_LOST'
    assert supervised_eod_cycle(engine,source,clock=lambda:recovered,
        acquire=lambda *a:fresh(read,recovered))['status']=='WAITING_FOR_TIME'


def test_no_current_day_discovery_or_other_pilot_activation(session):
    target,cal,pub,read,now,source=pilot(session)
    early=pub.published_at
    with Session(session.get_bind()) as reopened:
        row=reopened.get(TechnicalEODSupervision,'pilot')
        row.next_cycle_at=row.next_discovery_at=early;reopened.add(row);reopened.commit()
    result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:early,acquire=lambda *a:pytest.fail('ineligible SSI'))
    assert result['status']=='IDLE'
    assert source.calls==0
    with pytest.raises(ValueError):initialize_supervision(session,'OTHER',cal,now)


def test_unchanged_checks_reuse_snapshot_and_api_staleness_is_truthful(session,client,monkeypatch):
    from main import app
    from routers.technical import get_evaluation_clock
    target,read,accepted,source=accept(session)
    later=accepted+timedelta(hours=25)
    app.dependency_overrides[get_evaluation_clock]=lambda:later
    monkeypatch.setattr('src.services.technical_eod_store.capture_fresh_ssi_read',lambda *a:pytest.fail('HTTP SSI'))
    assert client.get('/technical/XYZ/daily/operational/latest').json()['freshness']=='STALE'
    result=supervised_eod_cycle(session.get_bind(),source,clock=lambda:later,acquire=lambda *a:fresh(read,later))
    assert result['producer']['cache_reused']
    assert client.get('/technical/XYZ/daily/operational/latest').json()['freshness']=='FRESH'
    with Session(session.get_bind()) as reopened:
        assert len(reopened.exec(select(TechnicalEODSnapshot)).all())==1


def test_file_reconnect_recovers_between_reads(tmp_path):
    from sqlmodel import create_engine
    from src.db.session import create_tables
    path=tmp_path/'pilot.db'
    engine=create_engine('sqlite:///'+path.as_posix())
    create_tables(engine)
    with Session(engine) as session:
        target,cal,pub,read,now,source=pilot(session)
    supervised_eod_cycle(engine,source,clock=lambda:now,acquire=lambda *a:fresh(read,now))
    engine.dispose()
    engine=create_engine('sqlite:///'+path.as_posix())
    later=now+timedelta(hours=6,seconds=2)
    result=supervised_eod_cycle(engine,source,clock=lambda:later,acquire=lambda *a:fresh(read,later))
    assert result['status']=='PROVISIONAL'
    engine.dispose()
    engine=create_engine('sqlite:///'+path.as_posix())
    with Session(engine) as session:
        assert read_latest_operational_packet(session,'XYZ',later).assurance=='PROVISIONAL'
    engine.dispose()
