from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SAEnum, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now():
    return datetime.now(timezone.utc)


class Timestamped(SQLModel):
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))


class User(Timestamped, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=320)


class Stock(Timestamped, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(unique=True, index=True, max_length=20)
    exchange: str | None = Field(default=None, max_length=30)
    company_name: str | None = Field(default=None, max_length=255)
    sector: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class Watchlist(Timestamped, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)


class WatchlistItem(Timestamped, table=True):
    __table_args__ = (UniqueConstraint("watchlist_id", "stock_id"),)
    id: int | None = Field(default=None, primary_key=True)
    watchlist_id: int = Field(foreign_key="watchlist.id", index=True)
    stock_id: int = Field(foreign_key="stock.id", index=True)


class Dimension(str, Enum):
    fundamentals = "fundamentals"
    technical = "technical"
    news = "news"


class Priority(str, Enum):
    primary = "primary"
    secondary = "secondary"
    low = "low"


class MonitoringPreference(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "stock_id", "dimension"),)
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    stock_id: int = Field(foreign_key="stock.id", index=True)
    dimension: Dimension = Field(sa_column=Column(SAEnum(Dimension, name="monitoring_dimension", create_constraint=True), nullable=False))
    priority: Priority = Field(sa_column=Column(SAEnum(Priority, name="monitoring_priority", create_constraint=True), nullable=False))
