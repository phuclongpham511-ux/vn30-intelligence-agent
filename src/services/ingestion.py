"""HTTP records durable News intent; only the collector executes acquisition."""
from datetime import datetime, timezone
from src.db.session import get_engine


def request_refresh(*, now: datetime | None = None) -> str:
    """Signal due News work without starting a collector or bypassing any cadence."""
    now = now or datetime.now(timezone.utc)
    from sqlmodel import Session
    from src.news.registry import load_sources
    from src.news.scheduling import request_due_refresh
    with Session(get_engine()) as session:
        request_due_refresh(session, load_sources(), now=now)
    return 'pending_worker'
