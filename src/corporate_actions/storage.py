"""Additive tables; immutable source observations, original events and later updates."""
from datetime import datetime
from sqlalchemy import JSON, DateTime
from sqlmodel import Field, SQLModel


class CorporateActionRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    action_id: str = Field(index=True)
    observed_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    content_hash: str
    payload: dict = Field(sa_type=JSON)


class TechnicalContextEvent(SQLModel, table=True):
    id: str = Field(primary_key=True)
    generated_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    payload: dict = Field(sa_type=JSON)


class TechnicalContextUpdate(SQLModel, table=True):
    id: str = Field(primary_key=True)
    event_id: str = Field(foreign_key='technicalcontextevent.id', index=True)
    enriched_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    payload: dict = Field(sa_type=JSON)
