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
