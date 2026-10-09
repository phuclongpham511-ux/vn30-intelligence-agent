"""Read-only HTTP boundary over operational evidence and the existing EOD engine.

This module never acquires evidence. The server-owned snapshot is an input
contract, not vendor authentication or certification of historical SSI vintages.
"""
from collections import deque
from datetime import date, datetime
from math import ceil
from pathlib import Path
import re
from threading import Lock
from time import monotonic
from typing import Annotated, Literal
from urllib.parse import urlsplit, parse_qsl

from pydantic import Field, ValidationError
from sqlalchemy import func
from sqlmodel import select

from src.analytics.factual import FAMILIES
from src.corporate_actions.models import CorporateActionObservation
from src.corporate_actions.repository import CorporateActionRepository
from src.corporate_actions.storage import CorporateActionRecord
from src.materiality.delivery import TechnicalDailySignalPacket
from src.providers.base import ProviderError
from .session_evidence import CalendarEvidence
from .technical_eod import (EODModel, EODHistoryRead, MAX_HISTORY_DAYS,
    MAX_SESSION_RECORDS, TechnicalEODDiagnostic, evaluate_technical_eod_packet)

MAX_LOCAL_BYTES = 4 * 1024 * 1024
LIMITATIONS = ('source_receipt_not_certified_historical_vendor_vintage',
              'local_operational_evidence_required_not_acquired_by_api')
OPAQUE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}$')
PRIVATE = re.compile(r'(?i)([a-z]:[\\/]|\\\\|(?:^|\s)/(?:home|users|tmp|etc|var)/|'
                     r'\b(?:api[_-]?key|api[_-]?secret|token|password|authorization)\s*[=:])')
SECRET_KEYS = {'token', 'access_token', 'api_key', 'apikey', 'secret', 'password', 'authorization'}


def public_reference(value):
    if OPAQUE.fullmatch(value) and not PRIVATE.search(value):
        return True
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return (parts.scheme in ('http', 'https') and bool(parts.hostname)
        and not parts.username and not parts.password and not PRIVATE.search(value)
        and not any(k.lower() in SECRET_KEYS for k, _ in parse_qsl(parts.query)))


def public_payload(value):
    """Fail closed on private references; do not redact or rewrite engine evidence."""
    if isinstance(value, str):
        return not PRIVATE.search(value) and (public_reference(value)
            if value.startswith(('http://', 'https://')) else True)
    if isinstance(value, dict):
        return all(str(k).lower() not in SECRET_KEYS and public_payload(v) for k, v in value.items())
    if isinstance(value, (tuple, list)):
        return all(public_payload(v) for v in value)
    return True


class LocalTechnicalEvidence(EODModel):
    schema_version: Literal['operational-technical-evidence-v1']
    history_start: date
    history: EODHistoryRead
    calendar: CalendarEvidence | None = None


class LocalEvidenceInvalid(ValueError):
    pass


class LocalEvidenceReader:
    """One deterministic, size-bounded file. No directory scan or write fallback."""
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def read(self, ticker: str, target: date):
        if not re.fullmatch(r'[A-Z0-9]{1,20}', ticker) or type(target) is not date:
            raise LocalEvidenceInvalid()
        base = self.directory.resolve()
        path = self.directory / ticker / f'{target.isoformat()}.json'
        if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(base):
            raise LocalEvidenceInvalid()
        try:
            with path.open('rb') as stream:
                raw = stream.read(MAX_LOCAL_BYTES + 1)
        except FileNotFoundError:
            return None
        if len(raw) > MAX_LOCAL_BYTES:
            raise LocalEvidenceInvalid()
        try:
            evidence = LocalTechnicalEvidence.model_validate_json(raw)
        except ValidationError:
            raise LocalEvidenceInvalid() from None
        read, calendar = evidence.history, evidence.calendar
        if (len(read.observations) > MAX_SESSION_RECORDS
                or not 0 <= (target-evidence.history_start).days <= MAX_HISTORY_DAYS):
            raise LocalEvidenceInvalid()
        refs = [read.source_version] + [p.source_ref for p in read.completion_evidence]
        refs += [p.source_version for p in read.completion_evidence]
        if calendar:
            refs += [calendar.version] + [r.source_ref for r in calendar.records]
        if not all(public_reference(ref) for ref in refs) or not public_payload(evidence.model_dump(mode='json')):
            raise LocalEvidenceInvalid()
        return evidence


class TechnicalRequestBudget:
    """Bounded per-process sliding window, one calculation, no waiting queue."""
    def __init__(self, max_requests=12, window_seconds=60):
        if max_requests < 1 or window_seconds <= 0:
            raise ValueError('Positive request budget required')
        self.max_requests, self.window_seconds = max_requests, window_seconds
        self._requests = deque(maxlen=max_requests)
        self._active, self._lock = False, Lock()

    def enter(self):
        with self._lock:
            now = monotonic()
            while self._requests and now-self._requests[0] >= self.window_seconds:
                self._requests.popleft()
            if self._active:
                return 1
            if len(self._requests) >= self.max_requests:
                return max(1, ceil(self.window_seconds-(now-self._requests[0])))
            self._requests.append(now)
            self._active = True
            return 0

    def exit(self):
        with self._lock:
            self._active = False


class AvailableEvidenceSummary(EODModel):
    local_history_present: bool = False
    observation_count: int = Field(default=0, ge=0, le=MAX_SESSION_RECORDS)
    calendar_present: bool = False
    completion_count: int = Field(default=0, ge=0, le=MAX_SESSION_RECORDS)
    source: Literal['SSI:FastConnect'] | None = None
    venue: Literal['HOSE', 'HNX', 'UPCOM'] | None = None


class TechnicalAPIDiagnostic(EODModel):
    kind: Literal['diagnostic'] = 'diagnostic'
    ticker: str
    requested_session: date
    evaluation_as_of: datetime
    readiness_status: Literal['INVALID_REQUEST', 'INCOMPLETE_EVIDENCE',
                             'SOURCE_UNAVAILABLE', 'INFRASTRUCTURE_FAILURE', 'RESOURCE_LIMITED']
    reason_codes: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    available_evidence_summary: AvailableEvidenceSummary = Field(default_factory=AvailableEvidenceSummary)
    source_last_observed_at: datetime | None = None
    limitations: tuple[str, ...] = LIMITATIONS
    safe_to_display_as_verified: Literal[False] = False


class TechnicalAPIPacket(EODModel):
    kind: Literal['packet'] = 'packet'
    safe_to_display_as_verified: Literal[True] = True
    packet: TechnicalDailySignalPacket


TechnicalAPIResponse = Annotated[TechnicalAPIPacket | TechnicalAPIDiagnostic, Field(discriminator='kind')]


def diagnostic(ticker, target, cutoff, *reasons, status='INCOMPLETE_EVIDENCE', evidence=None):
    read = evidence.history if evidence else None
    summary = AvailableEvidenceSummary(local_history_present=read is not None,
        observation_count=len(read.observations) if read else 0,
        calendar_present=bool(evidence and evidence.calendar),
        completion_count=len(read.completion_evidence) if read else 0,
        source='SSI:FastConnect' if read and read.source=='SSI:FastConnect' else None,
        venue=evidence.calendar.venue if evidence and evidence.calendar else None)
    missing = tuple(dict.fromkeys('local_history' if r=='missing_local_history'
        else 'source_provenance' if 'provenance' in r else 'calendar_session_evidence' if 'calendar' in r
        else 'eod_completion' if 'completion' in r else 'd1_lookback' if 'history' in r
        else 'as_of_evidence' if 'cutoff' in r else 'compatible_data_basis' if 'basis' in r
        else 'verified_evaluation' for r in reasons))
    receipt = read.observed_at if read and read.observed_at.utcoffset() is not None and read.observed_at <= cutoff else None
    return TechnicalAPIDiagnostic(ticker=ticker, requested_session=target, evaluation_as_of=cutoff,
        readiness_status=status, reason_codes=reasons, missing_evidence=missing,
        available_evidence_summary=summary, source_last_observed_at=receipt)


class _NoAcquisitionProvider:
    source = 'SSI:FastConnect'

    def get_history(self, *args, **kwargs):
        raise ProviderError('Local evidence required')


class BoundedCorporateActionReader(CorporateActionRepository):
    """Reuse CA revision/context rules with bounded, once-per-request SQL reads.

    Find identities EVER assigned this symbol before cutoff, then select their
    latest revisions before filtering symbol/date. Corrections away from the
    symbol or target date therefore remain effective.
    """
    def __init__(self, session, ticker, cutoff):
        super().__init__(session)
        self.ticker, self.cutoff, self._known = ticker, cutoff, None
        self._attempted = False

    def get_known_actions_as_of(self, *, as_of):
        if as_of != self.cutoff:
            raise ValueError('Request-scoped knowledge cutoff required')
        if self._known is None:
            if self._attempted:
                raise ValueError('Corporate action snapshot unavailable')
            self._attempted = True
            record = CorporateActionRecord
            ids = self.session.exec(select(record.action_id).where(record.observed_at <= as_of,
                record.payload['symbol'].as_string() == self.ticker).distinct().limit(MAX_SESSION_RECORDS+1)).all()
            if len(ids) > MAX_SESSION_RECORDS:
                raise ValueError('Corporate action read bound exceeded')
            if not ids:
                self._known = ()
            else:
                latest = select(record.action_id.label('action_id'), func.max(record.observed_at).label('observed_at')).where(
                    record.action_id.in_(ids), record.observed_at <= as_of).group_by(record.action_id).subquery()
                rows = self.session.exec(select(record).join(latest,
                    (record.action_id==latest.c.action_id) & (record.observed_at==latest.c.observed_at))
                    .order_by(record.action_id, record.id).limit(MAX_SESSION_RECORDS+1)).all()
                if len(rows)>MAX_SESSION_RECORDS or len({r.action_id for r in rows}) != len(rows):
                    raise ValueError('Corporate action revision evidence ambiguous or oversized')
                self._known = tuple(CorporateActionObservation.model_validate(r.payload) for r in rows)
        return self._known


def evaluate_local_packet(ticker, target, cutoff, session, evidence):
    result = evaluate_technical_eod_packet(ticker, target, evaluation_as_of=cutoff,
        generated_at=cutoff, db_session=session, provider=_NoAcquisitionProvider(),
        history_read=evidence.history, calendar=evidence.calendar, history_start=evidence.history_start,
        corporate_actions=BoundedCorporateActionReader(session, ticker, cutoff))
    if isinstance(result, TechnicalEODDiagnostic):
        return diagnostic(ticker, target, cutoff, *result.reason_codes, status=result.status, evidence=evidence)
    reasons = []
    if evidence.history.is_fixture or any(o.is_fixture for o in evidence.history.observations):
        reasons.append('fixture_evidence')
    if result.data_provenance.get('calendar_unresolved_sessions'):
        reasons.append('calendar_continuity_unresolved')
    for check in result.family_checks:
        if check.family in FAMILIES[:2] and (check.state=='UNRESOLVED' or not check.delivery_complete):
            reasons.extend(check.reason_codes or ('invalid_current_evidence',))
    if result.packet_state=='TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE':
        reasons.append('invalid_or_incomplete_eod_evidence')
    if not public_payload(result.model_dump(mode='json')):
        reasons.append('invalid_provenance')
    if reasons:
        return diagnostic(ticker, target, cutoff, *dict.fromkeys(reasons), evidence=evidence)
    return TechnicalAPIPacket(packet=result)
