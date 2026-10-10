"""Additive operational state; provisional rows never enter benchmark tables."""
from datetime import date, datetime
from sqlalchemy import JSON, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class TechnicalEODJob(SQLModel, table=True):
    id: str = Field(primary_key=True)
    ticker: str = Field(index=True)
    trading_session: date = Field(index=True)
    definition: dict = Field(sa_type=JSON)
    definition_hash: str
    definition_revision: int = 1
    first_receipt: dict | None = Field(default=None, sa_type=JSON)
    active_snapshot_id: str | None = None
    version: int = 0
    status: str = 'INCOMPLETE_EVIDENCE'
    reason_codes: list[str] = Field(default_factory=list, sa_type=JSON)
    next_due_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    last_attempt_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_checked_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class TechnicalEODSnapshot(SQLModel, table=True):
    __table_args__ = (UniqueConstraint('job_id','version',name='technical_eod_snapshot_version'),)
    id: str = Field(primary_key=True)
    job_id: str = Field(index=True)
    ticker: str = Field(index=True)
    trading_session: date
    version: int
    assurance: str = 'PROVISIONAL'
    state: str = 'ACTIVE'
    definition_hash: str
    source_version: str
    accepted_at: datetime = Field(sa_type=DateTime(timezone=True))
    evidence: dict = Field(sa_type=JSON)
    packet: dict = Field(sa_type=JSON)
    content_sha256: str
    retracted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    retraction_reason: str | None = None

    def packet_model(self):
        from src.services.provisional_eod import ProvisionalTechnicalDailyPacket
        return ProvisionalTechnicalDailyPacket.model_validate(self.packet)


class TechnicalEODWorkerLease(SQLModel, table=True):
    id: str = Field(default='ssi-eod', primary_key=True)
    token: str | None = None
    expires_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class TechnicalEODRetrievalReceipt(SQLModel, table=True):
    """Append-only metadata audit, including unchanged source rechecks."""
    id: str = Field(primary_key=True)
    job_id: str = Field(index=True)
    received_at: datetime = Field(sa_type=DateTime(timezone=True))
    payload: dict = Field(sa_type=JSON)
