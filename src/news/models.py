from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel
from pydantic import field_serializer
from src.models import utc_now
from src.news.normalization import utc


class NewsSourceState(SQLModel, table=True):
    source_id: str = Field(primary_key=True)
    last_success_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_attempt_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_error: str | None = None
    articles_received: int = 0
    priority: str | None = None
    next_due_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    consecutive_failures: int = 0
    fetch_duration_seconds: float | None = None
    newly_inserted_articles: int = 0
    lease_token: str | None = None
    lease_until: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    refresh_requested_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_refresh_request_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    refresh_requests: int = 0
    fetch_attempts: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0


class NewsReadCache(SQLModel, table=True):
    """Worker-built research rows. Evidence remains in NewsArticle/NewsStory."""
    id: str = Field(primary_key=True)
    updated_at: datetime = Field(sa_type=DateTime(timezone=True))
    rows: list[dict] = Field(default_factory=list, sa_type=JSON)
    refresh_count: int = 0


class NewsFetchSlot(SQLModel, table=True):
    id: int = Field(primary_key=True)
    lease_token: str | None = None
    lease_until: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class NewsStory(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    representative_title: str
    first_seen_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), index=True)
    last_updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), index=True)
    article_count: int = 0
    source_count: int = 0
    topics: list[str] = Field(default_factory=list, sa_type=JSON)
    tickers: list[str] = Field(default_factory=list, sa_type=JSON)
    sectors: list[str] = Field(default_factory=list, sa_type=JSON)
    trend_score: float = 0
    read_cache_dirty: bool = True

    @field_serializer('first_seen_at', 'last_updated_at', when_used='json')
    def serialize_time(self, value):
        return utc(value).isoformat().replace('+00:00', 'Z')


class NewsArticle(SQLModel, table=True):
    __table_args__ = (UniqueConstraint('source_id', 'title_hash'),)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    source_id: str = Field(index=True)
    source_name: str
    publisher_group: str
    title: str
    url: str
    canonical_url: str
    url_hash: str = Field(unique=True, index=True)
    title_hash: str = Field(index=True)
    published_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), index=True)
    first_seen_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), index=True)
    last_seen_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    country: str = Field(index=True)
    language: str
    category: str = Field(index=True)
    scope: str
    topics: list[str] = Field(default_factory=list, sa_type=JSON)
    tickers: list[str] = Field(default_factory=list, sa_type=JSON)
    sectors: list[str] = Field(default_factory=list, sa_type=JSON)
    story_id: str = Field(foreign_key='newsstory.id', index=True)
    thumbnail_url: str | None = None
    thumbnail_provenance: str | None = None

    @field_serializer('published_at', 'first_seen_at', 'last_seen_at', when_used='json')
    def serialize_time(self, value):
        # SQLite returns naive UTC; never let a browser interpret it as local time.
        return utc(value).isoformat().replace('+00:00', 'Z') if value is not None else None
