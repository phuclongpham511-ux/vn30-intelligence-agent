"""Bounded caller-attested venue and finalization evidence; no acquisition/inference."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SOURCE = 'SSI:FastConnect'


class EvidenceModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')


class SessionEvidence(EvidenceModel):
    session: date
    status: Literal['SCHEDULED', 'OCCURRED', 'CLOSED', 'UNKNOWN']
    source_ref: str = Field(min_length=1)
    evidence_kind: Literal['exchange_session_record','market_wide_observation','official_schedule'] = 'exchange_session_record'
    observed_at: datetime
    verified_at: datetime | None = None
    unresolved_reason: str | None = None
    ticker: str | None = None
    ticker_status: Literal['UNKNOWN', 'OBSERVED', 'SUSPENDED', 'NO_TRADE'] = 'UNKNOWN'


class CalendarEvidence(EvidenceModel):
    venue: Literal['HOSE', 'HNX', 'UPCOM']
    coverage_start: date
    coverage_end: date
    version: str = Field(min_length=1)
    records: tuple[SessionEvidence, ...] = Field(max_length=731)
    contract_version: str = 'venue-session-evidence-v1'


class EODCompletionEvidence(EvidenceModel):
    ticker: str
    venue: Literal['HOSE', 'HNX', 'UPCOM']
    session: date
    source: str
    source_version: str = Field(min_length=1)
    bar_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    status: Literal['COMPLETE', 'INCOMPLETE', 'UNKNOWN']
    available_at: datetime
    observed_at: datetime
    source_ref: str = Field(min_length=1)
    method: Literal['provider_finalization', 'verified_snapshot'] = 'provider_finalization'


def aware(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError('Evidence timestamps must be aware')
    return value.astimezone(timezone.utc)


def bar_fingerprint(bar):
    return sha256(json.dumps(bar.model_dump(mode='json'), sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def completion_visible(evidence, ticker, session, cutoff):
    """Validate operational attestation, not cryptographic source authenticity."""
    try:
        proof=EODCompletionEvidence.model_validate(evidence)
        from src.evaluation.benchmark.inputs import ZONE
        return (proof.status=='COMPLETE' and proof.ticker==ticker and proof.session==date.fromisoformat(session)
            and proof.source==SOURCE and aware(proof.available_at)<=aware(proof.observed_at)<=aware(cutoff)
            and proof.available_at.astimezone(ZONE).date()>=proof.session)
    except (ValueError, TypeError):
        return False


def resolve_calendar(calendar, start, target, cutoff, ticker):
    """Every intervening date needs evidence. Unknown slots break continuity.

    Only verified CLOSED dates are omitted. SCHEDULED does not mean OCCURRED.
    Ticker suspension/no-trade preserves the venue session, withholding its bar.
    """
    if calendar.contract_version!='venue-session-evidence-v1':
        raise ValueError('Unrecognized calendar contract')
    if not 0 <= (calendar.coverage_end-calendar.coverage_start).days <= 730:
        raise ValueError('Calendar exceeds bounded coverage')
    # Ignore later knowledge before checking contradictions or reading statuses.
    scoped=[r for r in calendar.records if start<=r.session<=target
        and aware(r.observed_at)<=aware(cutoff)
        and (r.verified_at is None or aware(r.verified_at)<=aware(cutoff))]
    if any(not calendar.coverage_start<=r.session<=calendar.coverage_end for r in scoped):
        raise ValueError('Evidence outside calendar coverage')
    if len(scoped)>731 or len({r.session for r in scoped})!=len(scoped):
        raise ValueError('Contradictory or duplicate calendar evidence')
    records={r.session:r for r in scoped}
    days,blocked,unresolved,visible=[],set(),[],[]
    day=start
    while day<=target:
        record=records.get(day)
        known=record is not None and aware(record.observed_at)<=aware(cutoff)
        if known and record.verified_at is not None:
            known=aware(record.observed_at)<=aware(record.verified_at)<=aware(cutoff)
        status=record.status if known else 'UNKNOWN'
        if known and status=='OCCURRED' and record.evidence_kind=='official_schedule':
            status='UNKNOWN'  # Schedule proves planned opening, not actual occurrence.
        ticker_blocked=bool(known and record.ticker==ticker and record.ticker_status in ('SUSPENDED','NO_TRADE'))
        if known: visible.append(record.model_dump(mode='json'))
        if status!='CLOSED':
            days.append(day)
            if status!='OCCURRED' or ticker_blocked:
                blocked.add(day)
                unresolved.append(dict(session=day.isoformat(),status=status,
                    ticker_status=record.ticker_status if known else 'UNKNOWN',
                    reason=(record.unresolved_reason if known else None) or
                        ('ticker_without_valid_observation' if ticker_blocked else 'exchange_occurrence_unverified')))
        day+=timedelta(days=1)
    target_record=records.get(target)
    if not target_record or target in blocked or target not in days:
        raise ValueError('Target exchange occurrence unverified')
    return days,blocked,dict(calendar_contract=calendar.contract_version,
        calendar_records=visible,calendar_unresolved_sessions=unresolved,
        calendar_knowledge_cutoff=aware(cutoff).isoformat(),
        calendar_adjacency_policy='all_intervening_dates_occurred_or_verified_closed')


def completion_matches_bar(evidence, bar, source_version, cutoff, venue=None):
    try:
        proof=EODCompletionEvidence.model_validate(evidence)
        return (completion_visible(proof,bar.ticker,bar.date.isoformat(),cutoff)
            and proof.source==bar.source and proof.source_version==source_version
            and proof.bar_sha256==bar_fingerprint(bar) and (venue is None or proof.venue==venue))
    except (ValueError, TypeError):
        return False
