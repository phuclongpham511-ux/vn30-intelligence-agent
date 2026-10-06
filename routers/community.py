from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from src.db.session import get_session
from src.community.service import pulse, source_status

router = APIRouter(prefix='/community', tags=['community'])


class CommunitySourceResponse(BaseModel):
    source_id: str
    name: str
    url: str
    status: Literal['healthy', 'stale', 'error', 'not_attempted']
    poll_interval_minutes: int
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    threads_received: int | None


@router.get('/sources', response_model=list[CommunitySourceResponse])
def community_sources(session: Annotated[Session, Depends(get_session)]):
    return [source_status(session)]


@router.get('/pulse')
def community_pulse(session: Annotated[Session, Depends(get_session)], ticker: str | None = None, topic: str | None = None):
    return pulse(session, ticker=ticker, topic=topic)
