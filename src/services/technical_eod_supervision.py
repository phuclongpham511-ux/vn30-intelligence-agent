"""One leased pilot coordinator around the existing durable EOD producer."""
from datetime import datetime,timedelta,timezone
from uuid import uuid4
from sqlalchemy import or_,update
from sqlmodel import Session,select

from src.models.technical_eod import TechnicalEODSupervision,TechnicalEODJob
from src.schemas.stocks import SymbolRequest
from src.evaluation.benchmark.inputs import ZONE
from .session_evidence import CalendarEvidence,aware
from .provisional_eod import HosePublicationEvidence
from .hose_eod_discovery import extend_calendar,qualified_definition
from .technical_eod_store import (enqueue_provisional_eod,run_technical_eod_cycle,
    read_latest_operational_packet,_dbtime,_bounded,_hash,LEASE_TIME)

MIN_CYCLE=timedelta(minutes=10)
DISCOVERY_CADENCE=timedelta(hours=1)
MAX_FAILURES=3


def supervision_status(session,now):
    """Read-only operational metadata, never bars or authentication values."""
    now=aware(now)
    row=session.get(TechnicalEODSupervision,'pilot')
    if not row:return {'status':'UNCONFIGURED'}
    jobs=session.exec(select(TechnicalEODJob).where(TechnicalEODJob.ticker==row.ticker)
        .order_by(TechnicalEODJob.trading_session.desc()).limit(128)).all()
    pending=[]
    for job in jobs:
        first=job.first_receipt
        pending.append({'session':job.trading_session.isoformat(),'status':job.status,
            'next_due_at':_dbtime(job.next_due_at).isoformat(),
            'first_received_at':first['received_at'] if first else None,
            'first_receipt_sha256':_hash(first) if first else None,
            'canonical_sha256':first['source_version'] if first else None,
            'observation_count':first['observation_count'] if first else None,
            'snapshot_version':job.version,'reason_codes':job.reason_codes})
    packet=read_latest_operational_packet(session,row.ticker,now)
    return {'status':'HALTED' if row.halted else 'SUPERVISED','ticker':row.ticker,
        'calendar_through':row.calendar['coverage_end'],
        'next_cycle_at':_dbtime(row.next_cycle_at).isoformat(),
        'next_discovery_at':_dbtime(row.next_discovery_at).isoformat(),
        'failures':row.failures,'jobs':pending,
        'api_kind':packet.kind,'ssi_requests':0,'writes':0}


def initialize_supervision(session,ticker,calendar,now):
    symbol=SymbolRequest(symbol=ticker).symbol
    now=aware(now)
    if not isinstance(calendar,CalendarEvidence) or calendar.venue!='HOSE':
        raise ValueError('Qualified seed calendar required')
    _bounded(calendar.model_dump(mode='json'))
    old=session.get(TechnicalEODSupervision,'pilot')
    if old:
        if old.ticker!=symbol: raise ValueError('Pilot scope already configured')
        return old
    row=TechnicalEODSupervision(ticker=symbol,calendar=calendar.model_dump(mode='json'),
        next_cycle_at=now,next_discovery_at=now)
    session.add(row);session.commit()
    return row


def resume_supervision(session,now):
    row=session.get(TechnicalEODSupervision,'pilot')
    if not row: raise ValueError('Pilot unavailable')
    if row.lease_token and _dbtime(row.lease_until)>now: raise ValueError('Pilot lease active')
    row.halted=False;row.failures=0;row.next_cycle_at=aware(now)
    # Only explicit operator resume may resume stopped jobs for this pilot.
    for job in session.exec(select(TechnicalEODJob).where(
            TechnicalEODJob.ticker==row.ticker,TechnicalEODJob.status=='STOPPED').limit(128)).all():
        job.status='INCOMPLETE_EVIDENCE';job.next_due_at=now;job.reason_codes=[]
        session.add(job)
    session.add(row);session.commit()


def discovery_plan(ticker,calendar,publications,source,now):
    """Source reads only; no SSI, DB writes or inferred missing dates."""
    now=aware(now)
    next_day=calendar.coverage_end+timedelta(days=1)
    qualified=None
    if next_day<now.astimezone(ZONE).date():
        if next_day.weekday()<5:
            qualified=source.qualify_day(next_day)
            if qualified is None:
                return {'status':'INCOMPLETE_EVIDENCE','reason_codes':['official_hose_session_unavailable'],
                    'calendar':calendar,'publications':publications,'qualified':None}
        calendar=extend_calendar(calendar,next_day,qualified,now)
        if qualified:
            publications={**publications,next_day.isoformat():qualified['publication']}
    return {'status':'READY' if qualified else 'NO_NEW_ELIGIBLE_SESSION',
        'calendar':calendar,'publications':publications,'qualified':qualified}


def _claim(engine,now):
    with Session(engine) as session:
        token=uuid4().hex
        changed=session.exec(update(TechnicalEODSupervision).where(
            TechnicalEODSupervision.id=='pilot',TechnicalEODSupervision.halted.is_(False),
            TechnicalEODSupervision.next_cycle_at<=now,
            or_(TechnicalEODSupervision.lease_token.is_(None),TechnicalEODSupervision.lease_until<=now))
            .values(lease_token=token,lease_until=now+LEASE_TIME,next_cycle_at=now+MIN_CYCLE))
        if not changed.rowcount: session.rollback();return None
        session.commit()
        return token


def _save(engine,token,now,operation,release=False):
    with Session(engine) as session:
        changed=session.exec(update(TechnicalEODSupervision).where(
            TechnicalEODSupervision.id=='pilot',TechnicalEODSupervision.lease_token==token,
            TechnicalEODSupervision.lease_until>now).values(
                lease_token=None if release else token))
        if not changed.rowcount: session.rollback();return {'status':'LEASE_LOST'}
        row=session.get(TechnicalEODSupervision,'pilot')
        result=operation(session,row)
        _bounded(row.calendar);_bounded(row.publications);_bounded(row.source_receipts);_bounded(result)
        session.add(row);session.commit()
        return result


def supervised_eod_cycle(engine,source,*,clock=None,acquire=None,dry_run=False):
    clock=clock or (lambda:datetime.now(timezone.utc))
    now=aware(clock())
    with Session(engine) as session:
        row=session.get(TechnicalEODSupervision,'pilot')
        if not row: return {'status':'UNCONFIGURED'}
        calendar=CalendarEvidence.model_validate(row.calendar)
        ticker=row.ticker
        publications=dict(row.publications)
        due=_dbtime(row.next_discovery_at)<=now
        if dry_run:
            plan=discovery_plan(ticker,calendar,publications,source,now) if due else {
                'status':'CACHED_DISCOVERY','calendar':calendar,'publications':publications,'qualified':None}
            candidates=[]
            for payload in plan['publications'].values():
                pub=HosePublicationEvidence.model_validate(payload)
                definition=qualified_definition(ticker,plan['calendar'],pub,now)
                job=session.get(TechnicalEODJob,ticker+':'+pub.session.isoformat())
                receipt=job.first_receipt if job else None
                eligible=max(datetime.fromisoformat(receipt['received_at'])+timedelta(hours=6),
                    pub.published_at+timedelta(hours=24)) if receipt else None
                candidates.append({'session':pub.session.isoformat(),
                    'history_start':definition['history_start'].isoformat(),
                    'second_read_due_at':eligible.isoformat() if eligible else None,
                    'publication_gate_at':(pub.published_at+timedelta(hours=24)).isoformat()})
            return {'status':'DRY_RUN','discovery_status':plan['status'],
                'ticker':ticker,'calendar_through':plan['calendar'].coverage_end.isoformat(),
                'candidates':candidates,'ssi_requests':0,'writes':0}
        if row.halted: return {'status':'HALTED','last_result':row.last_result}
    token=_claim(engine,now)
    if not token: return {'status':'IDLE'}
    try:
        discovery_result=None
        if due:
            plan=discovery_plan(ticker,calendar,publications,source,now)
            at=aware(clock())
            def discovered(session,row):
                row.calendar=plan['calendar'].model_dump(mode='json')
                row.publications=plan['publications']
                if plan['qualified']:
                    day=plan['qualified']['publication']['session']
                    row.source_receipts={**row.source_receipts,day:plan['qualified']['receipt']}
                row.next_discovery_at=at+DISCOVERY_CADENCE
                return {'status':plan['status'],'calendar_through':plan['calendar'].coverage_end.isoformat()}
            result=_save(engine,token,at,discovered)
            if result['status']=='LEASE_LOST':return result
            discovery_result={'status':plan['status'],'reason_codes':plan.get('reason_codes',[])}
            calendar,publications=plan['calendar'],plan['publications']
        # Queue at most one new, independently qualified session. Durable source
        # state commits first; restart recovers any interrupted enqueue.
        with Session(engine) as session:
            if not session.get(TechnicalEODSupervision,'pilot').lease_token==token:
                return {'status':'LEASE_LOST'}
            for day,payload in sorted(publications.items()):
                if session.get(TechnicalEODJob,ticker+':'+day) is None:
                    pub=HosePublicationEvidence.model_validate(payload)
                    definition=qualified_definition(ticker,calendar,pub,aware(clock()))
                    enqueue_provisional_eod(session,ticker,pub.session,**definition,now=aware(clock()))
                    break
        result=run_technical_eod_cycle(engine,clock=clock,acquire=acquire,tickers=(ticker,),supervision_token=token)
        at=aware(clock())
        def finished(session,row):
            failure=result['status'] in ('STOPPED','INCOMPLETE_EVIDENCE','LEASE_LOST')
            # Revisions intentionally establish a new pair; they are not retries.
            revision='ssi_history_revision_detected' in result.get('reason_codes',[])
            row.failures=(row.failures+1) if failure and not revision else 0
            row.halted=result['status']=='STOPPED' or row.failures>=MAX_FAILURES
            if failure and not revision: row.next_cycle_at=at+timedelta(hours=min(24,2**row.failures))
            if row.halted:
                for job in session.exec(select(TechnicalEODJob).where(
                        TechnicalEODJob.ticker==ticker).limit(128)).all():
                    job.status='STOPPED';session.add(job)
            status=('INCOMPLETE_EVIDENCE' if result['status']=='IDLE' and discovery_result
                and discovery_result['status']=='INCOMPLETE_EVIDENCE' else result['status'])
            row.last_result={'producer':result,'discovery':discovery_result}
            return {'status':'HALTED' if row.halted else status,'ticker':ticker,'producer':result,
                'discovery':discovery_result,
                'next_cycle_at':_dbtime(row.next_cycle_at).isoformat(),'calendar_through':calendar.coverage_end.isoformat()}
        return _save(engine,token,at,finished,release=True)
    except Exception:
        # No traceback/upstream body in persisted state or public logs.
        at=aware(clock())
        def failed(session,row):
            row.failures+=1;row.halted=row.failures>=MAX_FAILURES
            row.next_cycle_at=at+timedelta(hours=min(24,2**row.failures))
            row.last_result={'status':'INCOMPLETE_EVIDENCE','reason_codes':['supervised_source_or_runtime_failure']}
            if row.halted:
                for job in session.exec(select(TechnicalEODJob).where(
                        TechnicalEODJob.ticker==ticker).limit(128)).all():
                    job.status='STOPPED';session.add(job)
            return {'status':'HALTED' if row.halted else 'INCOMPLETE_EVIDENCE',
                'reason_codes':row.last_result['reason_codes']}
        return _save(engine,token,at,failed,release=True)
