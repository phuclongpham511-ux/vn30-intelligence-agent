from datetime import datetime
from sqlalchemy import JSON, DateTime
from sqlmodel import Field, SQLModel


class CommunityThread(SQLModel, table=True):
    id: str = Field(primary_key=True)  # source + public thread ID
    source_id: str = Field(index=True)
    title: str
    url: str
    author: str | None = None
    published_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    activity_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    first_seen_at: datetime = Field(sa_type=DateTime(timezone=True))
    last_seen_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    tickers: list[str] = Field(default_factory=list, sa_type=JSON)
    topics: list[str] = Field(default_factory=list, sa_type=JSON)
    replies: int | None = None
    views: int | None = None


class CommunitySourceState(SQLModel, table=True):
    source_id: str = Field(primary_key=True)
    last_attempt_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_success_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_error: str | None = None
    threads_received: int | None = None
    items_received: int | None = None


class CommunityThreadObservation(SQLModel, table=True):
    """Raw successful listing observations; never backfilled or updated."""
    thread_id: str = Field(foreign_key='communitythread.id', primary_key=True)
    observed_at: datetime = Field(sa_type=DateTime(timezone=True), primary_key=True)
    replies: int | None = None
    views: int | None = None


class CommunityEvidenceItem(SQLModel, table=True):
    """Latest bounded public discussion, independent of legacy thread metadata."""
    id: str = Field(primary_key=True)
    source_id: str = Field(index=True)
    source_item_id: str
    item_type: str
    title: str | None = None
    excerpt: str
    context_text: str = ''
    author: str | None = None
    url: str
    published_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    first_seen_at: datetime = Field(sa_type=DateTime(timezone=True))
    last_seen_at: datetime = Field(sa_type=DateTime(timezone=True))
    tickers: list[str] = Field(default_factory=list, sa_type=JSON)
    provenance: dict = Field(default_factory=dict, sa_type=JSON)
    is_fixture: bool = False
    replies: int | None = None
    views: int | None = None
    revision_id: str


class CommunityEvidenceRevision(SQLModel, table=True):
    """Immutable bounded text/attribution version; no raw HTML archive."""
    item_id: str = Field(foreign_key='communityevidenceitem.id', primary_key=True)
    revision_id: str = Field(primary_key=True)
    observed_at: datetime = Field(sa_type=DateTime(timezone=True))
    evidence: dict = Field(sa_type=JSON)
