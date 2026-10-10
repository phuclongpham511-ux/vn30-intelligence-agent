"""Vietnam calendar-day discussion attention, computed from persisted public evidence."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from src.news.normalization import utc
from sqlmodel import Session, select
from sqlalchemy import func
from hashlib import sha256
import json
from collections import Counter
from src.community.models import CommunityEvidenceItem, CommunityEvidenceRevision, CommunitySourceState, CommunityThread, CommunityThreadObservation
from src.community.acquisition import SOURCES, acquire
from src.community.service import community_tags
from src.models import Stock
from src.services.universe import discovery_metadata
from src.services.ingestion_owner import collector_owned


def time_window(now, kind='today'):
    now = utc(now)
    if kind not in ('today', 'last24h'):
        raise ValueError('Unknown discussion window')
    start = now - timedelta(hours=24) if kind == 'last24h' else now.astimezone(
        ZoneInfo('Asia/Ho_Chi_Minh')).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    return dict(kind=kind, label='Today' if kind == 'today' else 'Last 24 hours',
        timezone='Asia/Ho_Chi_Minh', start=start, end=now)


def in_window(published, window):
    return published is not None and window['start'] <= utc(published) <= window['end']


@collector_owned
def ingest_source(session, source, *, fetch=acquire, now=None):
    supplied_now = now
    now = utc(now or datetime.now(timezone.utc))
    if not source.enabled:
        return {'status': 'disabled'}
    state = session.get(CommunitySourceState, source.id)
    if state and state.last_attempt_at and utc(state.last_attempt_at) > now - timedelta(minutes=source.interval):
        return {'status': 'skipped'}
    # Persist the attempt before network work: interruption cannot erase cooldown.
    state = state or CommunitySourceState(source_id=source.id)
    state.last_attempt_at = now
    session.add(state); session.commit()
    try:
        stocks = discovery_metadata(session)
        incoming, threads = fetch(source, stocks)
        observed_at = utc(supplied_now or datetime.now(timezone.utc))
        known = {s.symbol for s in stocks}
        received = set()
        for raw in incoming:
            row = dict(raw)
            if row['source_id'] != source.id or not row.get('published_at') or utc(row['published_at']) > observed_at:
                continue
            direct = row.pop('direct_tickers', [])
            contextual, _ = community_tags(' '.join(filter(None, [row.get('title'), row['excerpt'], row.get('context_text')])), stocks)
            row['tickers'] = sorted(set(contextual) | (set(direct) & known))
            row['published_at'] = utc(row['published_at'])
            evidence = dict(row, published_at=row['published_at'].isoformat())
            revision = sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            existing = session.get(CommunityEvidenceItem, row['id'])
            entry = existing or CommunityEvidenceItem(**row, revision_id=revision, first_seen_at=observed_at, last_seen_at=observed_at)
            for key, value in row.items():
                setattr(entry, key, value)
            entry.last_seen_at, entry.revision_id = observed_at, revision
            session.add(entry); session.flush()
            if not session.get(CommunityEvidenceRevision, (entry.id, revision)):
                session.add(CommunityEvidenceRevision(item_id=entry.id, revision_id=revision, observed_at=observed_at, evidence=evidence))
            received.add(entry.id)
        # Keep historical listing observations without promoting them into daily evidence.
        for row in threads:
            existing = session.get(CommunityThread, row['id'])
            thread = existing or CommunityThread(**row, first_seen_at=observed_at, last_seen_at=observed_at)
            for key, value in row.items():
                setattr(thread, key, value)
            thread.last_seen_at = observed_at
            thread.tickers, thread.topics = community_tags(thread.title, stocks)
            session.add(thread); session.flush()
            if not session.get(CommunityThreadObservation, (thread.id, observed_at)):
                session.add(CommunityThreadObservation(thread_id=thread.id, observed_at=observed_at, replies=thread.replies, views=thread.views))
        state = state or CommunitySourceState(source_id=source.id)
        state.last_attempt_at, state.last_success_at = now, observed_at
        state.last_error, state.items_received = None, len(received)
        if source.id == 'f319_public':
            state.threads_received = len(threads)
        session.add(state); session.commit()
        return {'status': 'ok', 'received': len(received)}
    except Exception as exc:
        session.rollback()
        state = session.get(CommunitySourceState, source.id) or CommunitySourceState(source_id=source.id)
        state.last_attempt_at, state.last_error = now, type(exc).__name__
        session.add(state); session.commit()
        return {'status': 'error', 'error': state.last_error}


@collector_owned
def ingest_cycle(engine, *, sources=SOURCES, fetch=acquire, now=None):
    results = {}
    for source in sources:
        # A transaction/session failure cannot poison another source.
        try:
            with Session(engine) as session:
                results[source.id] = ingest_source(session, source, fetch=fetch, now=now)
        except Exception as exc:
            results[source.id] = {'status': 'error', 'error': type(exc).__name__}
    return results


def source_statuses(session, *, now=None):
    now = utc(now or datetime.now(timezone.utc))
    output = []
    for source in SOURCES:
        state = session.get(CommunitySourceState, source.id)
        status = ('disabled' if not source.enabled else 'not_attempted' if not state or not state.last_attempt_at
            else 'error' if state.last_error else 'stale' if not state.last_success_at or utc(state.last_success_at) < now - timedelta(minutes=2*source.interval) else 'healthy')
        output.append(dict(source_id=source.id, name=source.name, url=source.url, enabled=source.enabled,
            qualification='INTEGRATED' if source.enabled else 'DEFERRED', reason=source.reason,
            status=status, poll_interval_minutes=source.interval,
            last_attempt_at=utc(state.last_attempt_at) if state and state.last_attempt_at else None,
            last_success_at=utc(state.last_success_at) if state and state.last_success_at else None,
            last_error=state.last_error if state else None, items_received=state.items_received if state else None,
            threads_received=state.threads_received if state else None))
    return output


def pulse(session, *, ticker=None, topic=None, now=None, window='today'):
    from src.community.themes import deduplicate, extract_themes
    now = utc(now or datetime.now(timezone.utc))
    bounds = time_window(now, window)
    ticker = ticker.strip().upper() if ticker else None
    # Exact array membership before the cap; unrelated chatter cannot hide a stock.
    values = (func.json_each(CommunityEvidenceItem.tickers) if session.get_bind().dialect.name == 'sqlite'
        else func.json_array_elements_text(CommunityEvidenceItem.tickers)).table_valued('value')
    if session.get_bind().dialect.name == 'postgresql':
        values = values.render_derived()
    eligibility = select(values.c.value).where(values.c.value == ticker).exists() if ticker else select(values.c.value).exists()
    rows = session.exec(select(CommunityEvidenceItem).where(CommunityEvidenceItem.published_at >= bounds['start'],
        CommunityEvidenceItem.published_at <= now, eligibility).order_by(CommunityEvidenceItem.published_at.desc(), CommunityEvidenceItem.id).limit(301)).all()
    truncated = len(rows) > 300
    rows = [row for row in rows[:300] if (ticker in row.tickers if ticker else bool(row.tickers))]
    items = [row.model_dump() for row in rows]
    for row in items:
        for key in ('published_at', 'first_seen_at', 'last_seen_at'):
            row[key] = utc(row[key])
    groups = deduplicate(items)
    excluded = [ticker] if ticker else []
    for stock in discovery_metadata(session):
        excluded.extend([stock.symbol, stock.company_name or ''])
    themes = extract_themes(groups, excluded)
    if topic:
        themes = [theme for theme in themes if theme['id'] == topic]
    counts = Counter(t for group in groups for t in set(t for row in group for t in row['tickers']))
    sources = source_statuses(session, now=now)
    return dict(as_of=now, window=bounds, sources=sources,
        coverage_partial=any(s['enabled'] and s['status'] != 'healthy' for s in sources),
        sampled_items=len(items), unique_items=len(groups), truncated=truncated, items=items, themes=themes,
        active_tickers=[dict(ticker=t, item_count=n) for t,n in sorted(counts.items(), key=lambda pair:(-pair[1],pair[0]))])
