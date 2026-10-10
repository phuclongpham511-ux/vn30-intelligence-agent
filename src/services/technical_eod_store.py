"""Durable, fenced provisional producer. HTTP never calls the acquisition seam."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Literal
from uuid import uuid4

from pydantic import model_validator
from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.models import Security
from src.models.technical_eod import (TechnicalEODJob, TechnicalEODSnapshot,
    TechnicalEODWorkerLease, TechnicalEODRetrievalReceipt)
from src.providers.base import ProviderError
from src.schemas.stocks import SymbolRequest
from src.materiality.delivery import TechnicalDailySignalPacket
from .session_evidence import CalendarEvidence, aware, bar_fingerprint
from .provisional_eod import (POLICY_VERSION, AuthenticatedSsiReadReceipt,
    AuthenticatedSsiHistoryRead, HosePublicationEvidence, ProvisionalTechnicalDailyPacket,
    capture_fresh_ssi_read, compact_ssi_receipt, assess_provisional_eod,
    evaluate_provisional_technical_eod_packet)
from .technical_eod import EODModel, MAX_HISTORY_DAYS
from .technical_api import MAX_LOCAL_BYTES, BoundedCorporateActionReader, diagnostic, public_payload

LEASE_TIME = timedelta(minutes=10)
RECHECK_TIME = timedelta(hours=24)
MAX_JOBS = 128


class ProvisionalEODDefinition(EODModel):
    history_start: date
    calendar: CalendarEvidence | None = None
    publication: HosePublicationEvidence | None = None


class AcceptedProvisionalEvidence(ProvisionalEODDefinition):
    first: AuthenticatedSsiReadReceipt
    second: AuthenticatedSsiHistoryRead


class TechnicalOperationalAPIPacket(EODModel):
    kind: Literal['provisional_packet'] = 'provisional_packet'
    assurance: Literal['PROVISIONAL'] = 'PROVISIONAL'
    safe_to_display_as_verified: Literal[False] = False
    snapshot_id: str
    snapshot_version: int
    persisted_at: datetime
    last_checked_at: datetime
    next_check_due_at: datetime
    freshness: Literal['FRESH', 'STALE']
    packet: TechnicalDailySignalPacket

    @model_validator(mode='after')
    def require_provisional(self):
        if self.packet.data_provenance.get('completion_assurance') != 'PROVISIONAL':
            raise ValueError('Provisional API requires provisional assurance')
        return self


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(value):
    return sha256(_json(value).encode()).hexdigest()


def _dbtime(value):
    # SQLite removes timezone information from UTC database columns.
    return aware(value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value)


def _bounded(value):
    if len(_json(value).encode()) > MAX_LOCAL_BYTES or not public_payload(value):
        raise ValueError('Unsafe or oversized operational evidence')


def _job_id(ticker, target):
    symbol=SymbolRequest(symbol=ticker).symbol
    if type(target) is not date:
        raise ValueError('Explicit session date required')
    return symbol, symbol+':'+target.isoformat()


def _retract(session, job, now, reason):
    if job.active_snapshot_id:
        row=session.get(TechnicalEODSnapshot,job.active_snapshot_id)
        if row and row.state=='ACTIVE':
            row.state='RETRACTED'
            row.retracted_at=now
            row.retraction_reason=reason
            session.add(row)
    job.active_snapshot_id=None
    job.status='INCOMPLETE_EVIDENCE'
    job.reason_codes=[reason]
    session.add(job)


def enqueue_provisional_eod(session, ticker, target, *, history_start,
        calendar=None, publication=None, first=None, now=None, resume=False):
    """Operator-qualified evidence ingress; no acquisition, schedule inference or bars."""
    now=aware(now or datetime.now(timezone.utc))
    symbol, key=_job_id(ticker,target)
    if type(history_start) is not date or not 0 <= (target-history_start).days <= MAX_HISTORY_DAYS:
        raise ValueError('Bounded history required')
    definition=ProvisionalEODDefinition(history_start=history_start,calendar=calendar,publication=publication)
    payload=definition.model_dump(mode='json')
    _bounded(payload)
    if first is not None:
        first=AuthenticatedSsiReadReceipt.model_validate(first)
        if (first.requested_ticker,first.range_start,first.range_end)!=(symbol,history_start,target):
            raise ValueError('First receipt scope mismatch')
        _bounded(first.model_dump(mode='json'))
    job=session.get(TechnicalEODJob,key)
    if job is None:
        if len(session.exec(select(TechnicalEODJob.id).limit(MAX_JOBS)).all()) >= MAX_JOBS:
            raise ValueError('Operational job capacity exceeded')
        job=TechnicalEODJob(id=key,ticker=symbol,trading_session=target,
            definition=payload,definition_hash=_hash(payload),next_due_at=now)
    elif job.definition_hash != _hash(payload):
        _retract(session,job,now,'evidence_definition_changed')
        job.first_receipt=None
        job.next_due_at=now
        job.definition_revision+=1
    elif job.status=='STOPPED' and not resume:
        return job.id
    job.definition=payload
    job.definition_hash=_hash(payload)
    if first is not None and job.first_receipt is None:
        job.first_receipt=first.model_dump(mode='json')
    if resume:
        job.status='INCOMPLETE_EVIDENCE'
        job.reason_codes=[]
        job.next_due_at=now
    session.add(job)
    session.commit()
    return key


def _claim(engine, now):
    """One shared SSI slot; network work runs outside the transaction."""
    with Session(engine) as session:
        if session.get(TechnicalEODWorkerLease,'ssi-eod') is None:
            session.add(TechnicalEODWorkerLease())
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
        token=uuid4().hex
        changed=session.exec(update(TechnicalEODWorkerLease).where(
            TechnicalEODWorkerLease.id=='ssi-eod',or_(TechnicalEODWorkerLease.token.is_(None),
            TechnicalEODWorkerLease.expires_at <= now)).values(token=token,expires_at=now+LEASE_TIME))
        if not changed.rowcount:
            session.rollback()
            return None
        job=session.exec(select(TechnicalEODJob).where(TechnicalEODJob.status!='STOPPED',
            TechnicalEODJob.next_due_at <= now).order_by(TechnicalEODJob.next_due_at,TechnicalEODJob.id).limit(1)).first()
        if job is None:
            session.rollback()
            return None
        job.last_attempt_at=now
        session.add(job)
        session.commit()
        session.refresh(job)
        return token,job


def _finish(engine, token, original, now, operation):
    """Fence stale workers and changed job definitions before any publication."""
    with Session(engine) as session:
        # Conditional write locks the fence for this entire publication transaction.
        changed=session.exec(update(TechnicalEODWorkerLease).where(
            TechnicalEODWorkerLease.id=='ssi-eod',TechnicalEODWorkerLease.token==token,
            TechnicalEODWorkerLease.expires_at > now).values(token=None,expires_at=None))
        if not changed.rowcount:
            session.rollback()
            return {'status':'LEASE_LOST'}
        job=session.get(TechnicalEODJob,original.id)
        if (job.definition_hash != original.definition_hash or job.definition_revision != original.definition_revision
                or job.first_receipt != original.first_receipt):
            session.commit()
            return {'status':'EVIDENCE_CHANGED'}
        result=operation(session,job)
        session.add(job)
        session.commit()
        return result


def _revise_overlaps(session, incoming, now):
    """Compare actual overlapping bars; one revision retracts every affected output."""
    rows=session.exec(select(TechnicalEODSnapshot).where(TechnicalEODSnapshot.ticker==incoming.requested_ticker,
        TechnicalEODSnapshot.state=='ACTIVE').limit(MAX_JOBS+1)).all()
    if len(rows)>MAX_JOBS:
        raise ValueError('Revision check capacity exceeded')
    latest={o.payload.date:bar_fingerprint(o.payload) for o in incoming.history.observations}
    retracted=[]
    for row in rows:
        old=AcceptedProvisionalEvidence.model_validate(row.evidence)
        prior={o.payload.date:bar_fingerprint(o.payload) for o in old.second.history.observations}
        overlap=set(prior) & set(latest)
        # Missing previously observed bars within the new scope also constitutes revision.
        removed={d for d in prior if incoming.range_start<=d<=incoming.range_end} - set(latest)
        added={d for d in latest if old.second.range_start<=d<=old.second.range_end} - set(prior)
        if removed or added or any(prior[d]!=latest[d] for d in overlap):
            job=session.get(TechnicalEODJob,row.job_id)
            _retract(session,job,now,'ssi_history_revision_detected')
            job.first_receipt=None
            job.next_due_at=now
            retracted.append(row.id)
    return retracted


def _audit_receipt(session, job, receipt):
    payload=receipt.model_dump(mode='json')
    _bounded(payload)
    key=_hash(payload)
    if session.get(TechnicalEODRetrievalReceipt,key) is None:
        session.add(TechnicalEODRetrievalReceipt(id=key,job_id=job.id,
            received_at=receipt.received_at,payload=payload))


def run_technical_eod_cycle(engine, *, clock=None, acquire=None):
    """At most one fresh bounded read; persisted cache/timing decide whether it is due."""
    clock=clock or (lambda:datetime.now(timezone.utc))
    acquire=acquire or capture_fresh_ssi_read
    now=aware(clock())
    claimed=_claim(engine,now)
    if claimed is None:
        return {'status':'IDLE'}
    token,original=claimed
    def end(status,reasons=(),delay=RECHECK_TIME,first=None,read=None):
        at=aware(clock())
        def operation(session,job):
            retracted=_revise_overlaps(session,read,at) if read else []
            if read:
                _audit_receipt(session,job,compact_ssi_receipt(read))
            if first is not None:
                job.first_receipt=first.model_dump(mode='json')
            job.status=status
            job.reason_codes=list(reasons)
            job.next_due_at=(max(first.received_at+timedelta(hours=6),
                definition.publication.published_at+timedelta(hours=24)) if first else at+delay)
            return {'status':status,'reason_codes':list(reasons),'next_due_at':aware(job.next_due_at).isoformat(),
                'retracted_snapshot_count':len(retracted)}
        return _finish(engine,token,original,at,operation)
    try:
        _bounded(original.definition)
        if _hash(original.definition)!=original.definition_hash:
            return end('INCOMPLETE_EVIDENCE',('invalid_evidence_definition',))
        definition=ProvisionalEODDefinition.model_validate(original.definition)
        first=AuthenticatedSsiReadReceipt.model_validate(original.first_receipt) if original.first_receipt else None
        with Session(engine) as session:
            security=session.get(Security,original.ticker)
            if (security is None or not security.is_active or security.exchange!='HOSE'
                    or security.instrument_type!='Stock' or security.source!='SSI:FastConnect'
                    or aware(security.last_synced_at.replace(tzinfo=timezone.utc) if security.last_synced_at.tzinfo is None
                        else security.last_synced_at)>now):
                return end('INCOMPLETE_EVIDENCE',('active_security_metadata_unavailable',))
        preflight=assess_provisional_eod(original.ticker,original.trading_session,
            history_start=definition.history_start,calendar=definition.calendar,publication=definition.publication,
            first=first,second=None,evaluation_as_of=now)
        if preflight.reason_codes != ('authenticated_fresh_read_unavailable',):
            return end('INCOMPLETE_EVIDENCE',preflight.reason_codes)
        if first:
            if first.request_started_at < definition.publication.published_at:
                return end('INCOMPLETE_EVIDENCE',('first_read_before_publication',))
            eligible=max(first.received_at+timedelta(hours=6),definition.publication.published_at+timedelta(hours=24))
            if now<eligible:
                return end('WAITING_FOR_TIME',first=first)
        read=acquire(original.ticker,definition.history_start,original.trading_session)
        if (not isinstance(read,AuthenticatedSsiHistoryRead) or
                (read.requested_ticker,read.range_start,read.range_end)!=(original.ticker,definition.history_start,original.trading_session)):
            return end('INCOMPLETE_EVIDENCE',('read_request_scope_mismatch',))
        receipt=compact_ssi_receipt(read)
        if first is None:
            return end('WAITING_FOR_TIME',first=receipt,read=read)
        at=aware(clock())
        assessment=assess_provisional_eod(original.ticker,original.trading_session,
            history_start=definition.history_start,calendar=definition.calendar,publication=definition.publication,
            first=first,second=read,evaluation_as_of=at)
        if assessment.status!='PROVISIONAL':
            if 'ssi_history_revision_detected' in assessment.reason_codes:
                return end('INCOMPLETE_EVIDENCE',assessment.reason_codes,first=receipt,read=read)
            return end('INCOMPLETE_EVIDENCE',assessment.reason_codes,read=read)
        def publish(session,job):
            retracted=_revise_overlaps(session,read,at)
            _audit_receipt(session,job,first)
            _audit_receipt(session,job,receipt)
            current=session.get(TechnicalEODSnapshot,job.active_snapshot_id) if job.active_snapshot_id else None
            if current and current.source_version==read.history.source_version:
                # Keep original accepted receipts and packet; append audit metadata only.
                job.last_checked_at=read.received_at
                job.status='PROVISIONAL'
                job.reason_codes=[]
                job.next_due_at=at+RECHECK_TIME
                return {'status':'PROVISIONAL','cache_reused':True,'snapshot_id':current.id,
                    'snapshot_version':current.version,'retracted_snapshot_count':len(retracted)}
            result=evaluate_provisional_technical_eod_packet(job.ticker,job.trading_session,
                history_start=definition.history_start,calendar=definition.calendar,publication=definition.publication,
                first=first,second=read,evaluation_as_of=at,generated_at=at,db_session=session,
                corporate_actions=BoundedCorporateActionReader(session,job.ticker,at))
            if not isinstance(result,ProvisionalTechnicalDailyPacket):
                job.status='INCOMPLETE_EVIDENCE'
                job.reason_codes=list(result.reason_codes)
                job.next_due_at=at+RECHECK_TIME
                return {'status':job.status,'reason_codes':job.reason_codes}
            evidence=AcceptedProvisionalEvidence(**definition.model_dump(),first=first,second=read).model_dump(mode='json')
            packet=result.model_dump(mode='json')
            _bounded(evidence)
            _bounded(packet)
            if result.packet.data_provenance.get('completion_assurance')!='PROVISIONAL':
                raise ValueError('Invalid persisted assurance')
            if current:
                _retract(session,job,at,'superseded_snapshot')
            job.version+=1
            row=TechnicalEODSnapshot(id=uuid4().hex,job_id=job.id,ticker=job.ticker,
                trading_session=job.trading_session,version=job.version,definition_hash=job.definition_hash,
                source_version=read.history.source_version,accepted_at=at,evidence=evidence,packet=packet,
                content_sha256=_hash({'evidence':evidence,'packet':packet}))
            session.add(row)
            job.active_snapshot_id=row.id
            job.status='PROVISIONAL'
            job.reason_codes=[]
            job.last_checked_at=read.received_at
            job.next_due_at=at+RECHECK_TIME
            return {'status':'PROVISIONAL','cache_reused':False,'snapshot_id':row.id,
                'snapshot_version':row.version,'retracted_snapshot_count':len(retracted)}
        return _finish(engine,token,original,at,publish)
    except ProviderError:
        return end('STOPPED',('ssi_acquisition_failed_operator_resume_required',))
    except Exception:
        # A failed publication rolls back; lease release and diagnostic form a new transaction.
        return end('INCOMPLETE_EVIDENCE',('technical_eod_worker_failure',),delay=timedelta(hours=1))


def read_operational_packet(session, ticker, target, cutoff):
    """Bounded SELECT-only projection, no SSI or Technical scoring in HTTP."""
    cutoff=aware(cutoff)
    symbol,key=_job_id(ticker,target)
    job=session.get(TechnicalEODJob,key)
    if job is None:
        return diagnostic(symbol,target,cutoff,'missing_persisted_eod_snapshot')
    if not job.active_snapshot_id:
        return diagnostic(symbol,target,cutoff,*(job.reason_codes or ['provisional_evidence_not_yet_accepted']))
    row=session.get(TechnicalEODSnapshot,job.active_snapshot_id)
    try:
        if (not row or row.state!='ACTIVE' or row.assurance!='PROVISIONAL' or row.job_id!=key
                or row.definition_hash!=job.definition_hash or row.ticker!=symbol or row.trading_session!=target):
            raise ValueError('Invalid active snapshot')
        _bounded(row.evidence)
        _bounded(row.packet)
        if _hash({'evidence':row.evidence,'packet':row.packet})!=row.content_sha256:
            raise ValueError('Snapshot checksum mismatch')
        evidence=AcceptedProvisionalEvidence.model_validate(row.evidence)
        assessment=assess_provisional_eod(symbol,target,history_start=evidence.history_start,
            calendar=evidence.calendar,publication=evidence.publication,first=evidence.first,
            second=evidence.second,evaluation_as_of=cutoff)
        packet=row.packet_model()
        if (assessment.status!='PROVISIONAL' or packet.packet.ticker!=symbol
                or packet.packet.trading_session!=target.isoformat() or packet.source_version!=row.source_version
                or packet.source_version!=evidence.second.history.source_version
                or packet.first_received_at!=evidence.first.received_at or packet.second_received_at!=evidence.second.received_at
                or _dbtime(row.accepted_at)>cutoff or aware(packet.packet.generated_at)>cutoff):
            raise ValueError('Snapshot evidence mismatch')
        checked=_dbtime(job.last_checked_at)
        due=_dbtime(job.next_due_at)
        if checked>cutoff:
            raise ValueError('Snapshot check after cutoff')
        return TechnicalOperationalAPIPacket(snapshot_id=row.id,snapshot_version=row.version,
            persisted_at=_dbtime(row.accepted_at),last_checked_at=checked,next_check_due_at=due,
            freshness='STALE' if cutoff>=due or job.status!='PROVISIONAL' else 'FRESH',packet=packet.packet)
    except (ValueError,TypeError,AttributeError):
        return diagnostic(symbol,target,cutoff,'invalid_persisted_eod_evidence')
