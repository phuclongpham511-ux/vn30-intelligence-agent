"""Small persisted News scheduler; Vietnam weekday sessions are a heuristic."""
from datetime import datetime, timedelta, timezone, time
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from sqlalchemy import update, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from src.news.models import NewsSourceState, NewsFetchSlot
from src.news.normalization import utc


class NewsSchedule(BaseModel):
    priority_minutes: int = Field(default=30, ge=15, le=1440)
    standard_minutes: int = Field(default=120, ge=15, le=1440)
    off_hours_minutes: int = Field(default=240, ge=15, le=1440)
    weekend_minutes: int = Field(default=360, ge=15, le=1440)
    max_concurrent: int = Field(default=2, ge=1, le=4)
    max_sources_per_cycle: int = Field(default=6, ge=1, le=20)
    timeout_seconds: int = Field(default=20, ge=1, le=60)
    failure_backoff_minutes: int = Field(default=30, ge=1, le=240)
    stale_refresh_min_minutes: int = Field(default=5, ge=1, le=60)


def load_schedule():
    return NewsSchedule.model_validate_json(Path(__file__).with_name('schedule.json').read_text(encoding='utf-8'))


def cadence_minutes(source, now, config=None):
    config = config or load_schedule()
    # Older alternate registries keep their explicit fixed cadence.
    if source.scheduling_priority is None:
        return source.poll_interval_minutes
    local = utc(now).astimezone(ZoneInfo('Asia/Ho_Chi_Minh'))
    if local.weekday() >= 5:
        return config.weekend_minutes
    if time(9) <= local.time() < time(11, 30) or time(13) <= local.time() < time(15):
        return config.priority_minutes if source.scheduling_priority == 'priority' else config.standard_minutes
    return config.off_hours_minutes


def next_due(source, state, now, config):
    if state is None or state.last_attempt_at is None:
        return utc(now)
    if state.lease_token and state.lease_until and utc(state.lease_until) <= now:
        return utc(now)  # crashed worker: expired ownership is retried safely
    if state.consecutive_failures and state.next_due_at:
        return utc(state.next_due_at)
    # Derive on session transitions so an off-hours timer cannot delay opening.
    return utc(state.last_attempt_at) + timedelta(minutes=cadence_minutes(source, now, config))


def ensure_state(session, source):
    if session.get(NewsSourceState, source.source_id) is None:
        session.add(NewsSourceState(source_id=source.source_id, priority=source.scheduling_priority))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()  # another process inserted the same source


def claim(session, source, now, config, *, force=False):
    ensure_state(session, source)
    session.expire_all()
    state = session.get(NewsSourceState, source.source_id)
    due = next_due(source, state, now, config)
    if not force and due > now:
        return None
    token = str(uuid4())
    # Shared slots bound acquisition across multiple worker processes, not just
    # the thread pool within one process. Slot and source claims commit together.
    for slot_id in range(config.max_concurrent):
        if session.get(NewsFetchSlot, slot_id) is None:
            session.add(NewsFetchSlot(id=slot_id))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
    acquired_slot = False
    for slot_id in range(config.max_concurrent):
        slot = session.execute(update(NewsFetchSlot).where(NewsFetchSlot.id == slot_id,
            or_(NewsFetchSlot.lease_until.is_(None), NewsFetchSlot.lease_until <= now))
            .values(lease_token=token, lease_until=now+timedelta(minutes=10))
            .execution_options(synchronize_session=False))
        if slot.rowcount:
            acquired_slot = True
            break
    if not acquired_slot:
        session.rollback()
        return None
    # Compare the observed attempt as well as lease: prevents a stale scheduler
    # snapshot claiming again after another worker already completed its fetch.
    observed = state.last_attempt_at
    result = session.execute(update(NewsSourceState).where(
        NewsSourceState.source_id == source.source_id,
        NewsSourceState.last_attempt_at == observed if observed is not None else NewsSourceState.last_attempt_at.is_(None),
        or_(NewsSourceState.lease_until.is_(None), NewsSourceState.lease_until <= now)
    ).values(last_attempt_at=now, lease_token=token,
             lease_until=now + timedelta(minutes=10),
             priority=source.scheduling_priority,
             fetch_attempts=NewsSourceState.fetch_attempts+1).execution_options(synchronize_session=False))
    if result.rowcount:
        session.commit()
        return token
    session.rollback()
    return None


def release_slot(session, token):
    session.execute(update(NewsFetchSlot).where(NewsFetchSlot.lease_token == token)
                    .values(lease_token=None, lease_until=None).execution_options(synchronize_session=False))


def request_due_refresh(session, sources, *, now=None, config=None):
    """Durable intent only. No upstream calls or request-process fetch tasks."""
    now = utc(now or datetime.now(timezone.utc))
    config = config or load_schedule()
    requested = deduplicated = 0
    states = {s.source_id: s for s in session.exec(select(NewsSourceState)).all()}
    for source in sources:
        if not source.enabled or source.country != 'VN' or source.category != 'VN':
            continue
        state = states.get(source.source_id)
        if next_due(source, state, now, config) > now:
            continue
        ensure_state(session, source)
        result = session.execute(update(NewsSourceState).where(
            NewsSourceState.source_id == source.source_id,
            NewsSourceState.refresh_requested_at.is_(None),
            or_(NewsSourceState.last_refresh_request_at.is_(None),
                NewsSourceState.last_refresh_request_at <= now-timedelta(minutes=config.stale_refresh_min_minutes)),
            or_(NewsSourceState.lease_until.is_(None), NewsSourceState.lease_until <= now)
        ).values(refresh_requested_at=now, last_refresh_request_at=now,
                 refresh_requests=NewsSourceState.refresh_requests+1).execution_options(synchronize_session=False))
        if result.rowcount:
            requested += 1
        else:
            deduplicated += 1
    session.commit()
    import logging
    logging.getLogger(__name__).info('news_refresh_request %s', {'requested': requested, 'deduplicated': deduplicated})
    return {'status': 'pending_worker' if requested or deduplicated else 'not_due',
            'requested': requested, 'deduplicated': deduplicated,
            'execution': 'scripts.ingest_data --watch; this request does not start a worker'}
