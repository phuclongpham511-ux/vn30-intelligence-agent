from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
from src.db.session import get_session
from src.community.service import pulse

router = APIRouter(prefix='/community', tags=['community'])


@router.get('/pulse')
def community_pulse(session: Annotated[Session, Depends(get_session)], ticker: str | None = None, topic: str | None = None):
    return pulse(session, ticker=ticker, topic=topic)
