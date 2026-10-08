"""Coalesce one background data refresh triggered by a web session."""
from datetime import datetime, timedelta, timezone
from threading import Lock, Thread

from scripts.ingest_data import run_cycle
from src.db.session import get_engine


REFRESH_COOLDOWN = timedelta(minutes=5)
_lock = Lock()
_running = False
_last_started: datetime | None = None


def _run_cycle() -> None:
    global _running
    try:
        run_cycle(get_engine(), include_news=False)
    finally:
        with _lock:
            _running = False


def request_refresh(*, now: datetime | None = None) -> str:
    """Start one non-blocking all-domain refresh when no recent refresh exists."""
    global _running, _last_started
    now = now or datetime.now(timezone.utc)
    # News refresh is durable and worker-owned; this convenience thread serves
    # the other existing domains and never promises News acquisition completion.
    from sqlmodel import Session
    from src.news.registry import load_sources
    from src.news.scheduling import request_due_refresh
    with Session(get_engine()) as session:
        request_due_refresh(session, load_sources(), now=now)
    with _lock:
        if _running:
            return 'already_running'
        if _last_started and now - _last_started < REFRESH_COOLDOWN:
            return 'cooldown'
        _running = True
        _last_started = now
        Thread(target=_run_cycle, name='web-ingestion-refresh', daemon=True).start()
        return 'started'
