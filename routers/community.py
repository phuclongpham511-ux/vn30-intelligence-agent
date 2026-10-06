from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from src.db.session import get_session
from src.community.daily import pulse, source_statuses

router = APIRouter(prefix='/community', tags=['community'])


class CommunitySourceResponse(BaseModel):
    source_id: str
    name: str
    url: str
    status: Literal['healthy', 'stale', 'error', 'not_attempted', 'disabled']
    enabled: bool
    qualification: Literal['INTEGRATED', 'DEFERRED']
    reason: str | None
    poll_interval_minutes: int
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    threads_received: int | None
    items_received: int | None


@router.get('/sources', response_model=list[CommunitySourceResponse])
def community_sources(session: Annotated[Session, Depends(get_session)]):
    return source_statuses(session)


@router.get('/pulse')
def community_pulse(session: Annotated[Session, Depends(get_session)], ticker: str | None = None, topic: str | None = None, window: Literal['today', 'last24h'] = 'today'):
    return pulse(session, ticker=ticker, topic=topic, window=window)
