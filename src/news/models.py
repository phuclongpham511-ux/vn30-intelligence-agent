from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel
from src.models import utc_now


class NewsSourceState(SQLModel, table=True):
    source_id: str = Field(primary_key=True)
    last_success_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_attempt_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_error: str | None = None
    articles_received: int = 0


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
