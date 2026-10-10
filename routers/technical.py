"""One public, bounded, read-only Technical Daily Signal endpoint."""
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlmodel import Session

from src.db.session import get_session
from src.evaluation.benchmark.inputs import ZONE
from src.models import Security
from src.schemas.stocks import SymbolRequest
from src.services.technical_api import (LocalEvidenceReader, LocalEvidenceInvalid,
    TechnicalRequestBudget, TechnicalAPIResponse, TechnicalAPIDiagnostic,
    diagnostic, evaluate_local_packet)
from src.services.technical_eod_store import (TechnicalOperationalAPIPacket, TechnicalOperationalLatestDiagnostic,
    read_operational_packet, read_latest_operational_packet)

router = APIRouter(prefix='/technical', tags=['technical'])


def get_evaluation_clock():
    return datetime.now(timezone.utc)


@router.get('/{ticker}/daily/operational/latest',
    response_model=TechnicalOperationalAPIPacket | TechnicalOperationalLatestDiagnostic)
def latest_operational_daily(ticker: str, request: Request, response: Response,
        db: Session = Depends(get_session), cutoff: datetime = Depends(get_evaluation_clock)):
    response.headers['Cache-Control'] = 'no-store'
    if request.query_params:
        raise HTTPException(422, 'Latest accepted lookup supports no query parameters')
    try:
        symbol = SymbolRequest(symbol=ticker).symbol
    except ValueError:
        raise HTTPException(422, 'Invalid ticker') from None
    try:
        return read_latest_operational_packet(db,symbol,cutoff)
    except Exception:
        response.status_code = 503
        return TechnicalOperationalLatestDiagnostic(ticker=symbol,
            evaluation_as_of=datetime.now(timezone.utc), readiness_status='INFRASTRUCTURE_FAILURE',
            reason_codes=('technical_eod_infrastructure_failure',),
            missing_evidence=('accepted_operational_snapshot',))


@router.get('/{ticker}/daily/operational', response_model=TechnicalOperationalAPIPacket | TechnicalAPIDiagnostic)
def operational_daily(ticker: str, request: Request, response: Response,
          requested_session: date = Query(alias='session'), db: Session = Depends(get_session),
          cutoff: datetime = Depends(get_evaluation_clock)):
    if (set(request.query_params) != {'session'} or len(request.query_params.getlist('session')) != 1
            or request.query_params['session'] != requested_session.isoformat()):
        raise HTTPException(422, 'Only one YYYY-MM-DD session parameter is supported')
    try:
        symbol=SymbolRequest(symbol=ticker).symbol
    except ValueError:
        raise HTTPException(422, 'Invalid ticker') from None
    try:
        if cutoff.utcoffset() is None:
            raise ValueError('Aware server clock required')
        cutoff=cutoff.astimezone(timezone.utc)
        if requested_session >= cutoff.astimezone(ZONE).date():
            response.status_code=422
            return diagnostic(symbol,requested_session,cutoff,'session_not_completed_or_invalid_generation_time',status='INVALID_REQUEST')
        return read_operational_packet(db,symbol,requested_session,cutoff)
    except Exception:
        response.status_code=503
        return diagnostic(symbol,requested_session,datetime.now(timezone.utc),
            'technical_eod_infrastructure_failure',status='INFRASTRUCTURE_FAILURE')


@lru_cache
def get_local_evidence_reader():
    return LocalEvidenceReader(Path(__file__).resolve().parents[1] / 'runtime' / 'technical_eod_evidence')


@lru_cache
def get_request_budget():
    return TechnicalRequestBudget()


@router.get('/{ticker}/daily', response_model=TechnicalAPIResponse)
def daily(ticker: str, request: Request, response: Response,
          requested_session: date = Query(alias='session'),
          db: Session = Depends(get_session), reader: LocalEvidenceReader = Depends(get_local_evidence_reader),
          cutoff: datetime = Depends(get_evaluation_clock),
          budget: TechnicalRequestBudget = Depends(get_request_budget)):
    if set(request.query_params) != {'session'} or len(request.query_params.getlist('session')) != 1:
        raise HTTPException(422, 'Only one session parameter is supported')
    # Date syntax must be literal YYYY-MM-DD, not Pydantic's numeric timestamp coercion.
    if request.query_params['session'] != requested_session.isoformat():
        raise HTTPException(422, 'Session must use YYYY-MM-DD')
    try:
        symbol = SymbolRequest(ticker=ticker).symbol
    except ValueError:
        raise HTTPException(422, 'Invalid ticker') from None
    if cutoff.utcoffset() is None:
        response.status_code = 503
        return diagnostic(symbol, requested_session, datetime.now(timezone.utc),
            'technical_eod_infrastructure_failure', status='INFRASTRUCTURE_FAILURE')
    cutoff = cutoff.astimezone(timezone.utc)
    if requested_session > cutoff.astimezone(ZONE).date():
        response.status_code = 422
        return diagnostic(symbol, requested_session, cutoff, 'session_not_completed_or_invalid_generation_time', status='INVALID_REQUEST')
    retry = budget.enter()
    if retry:
        response.status_code = 429
        response.headers['Retry-After'] = str(retry)
        return diagnostic(symbol, requested_session, cutoff, 'technical_request_budget_exceeded', status='RESOURCE_LIMITED')
    try:
        security = db.get(Security, symbol)
        if security is None:
            response.status_code = 404
            return diagnostic(symbol, requested_session, cutoff, 'active_security_metadata_unavailable')
        if (not security.is_active or security.exchange not in ('HOSE','HNX','UPCOM')
                or security.instrument_type != 'Stock' or security.source != 'SSI:FastConnect'):
            response.status_code = 422
            return diagnostic(symbol, requested_session, cutoff, 'incompatible_security_metadata')
        evidence = reader.read(symbol, requested_session)
        if evidence is None:
            return diagnostic(symbol, requested_session, cutoff, 'missing_local_history')
        result = evaluate_local_packet(symbol, requested_session, cutoff, db, evidence)
        if isinstance(result, TechnicalAPIDiagnostic):
            response.status_code = {'INVALID_REQUEST':422, 'SOURCE_UNAVAILABLE':502,
                'INFRASTRUCTURE_FAILURE':503}.get(result.readiness_status, 200)
        return result
    except LocalEvidenceInvalid:
        return diagnostic(symbol, requested_session, cutoff, 'invalid_provenance')
    except Exception:
        response.status_code = 503
        return diagnostic(symbol, requested_session, cutoff,
            'technical_eod_infrastructure_failure', status='INFRASTRUCTURE_FAILURE')
    finally:
        budget.exit()
