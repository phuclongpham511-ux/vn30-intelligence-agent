"""Persisted SSI ordinary-equity discovery; acquisition belongs to the worker."""
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from sqlalchemy import func
from src.models import Security, SecurityUniverseState
from src.news.normalization import normalized, utc
from src.providers.ssi import SsiMarketDataProvider

REFRESH_INTERVAL = timedelta(hours=24)
RETRY_INTERVAL = timedelta(minutes=15)


def discovery_metadata(session):
    """Reuse provider identity for evidence tagging, retaining legacy fixture metadata."""
    from src.models import Stock
    stocks = {row.symbol: row for row in session.exec(select(Stock)).all()}
    for row in session.exec(select(Security).where(Security.is_active == True)).all():
        stocks.setdefault(row.symbol, row)
    return list(stocks.values())


def sync_universe(session: Session, *, provider=None, now=None, force=False):
    now = now or datetime.now(timezone.utc)
    state = session.get(SecurityUniverseState, 'ssi') or SecurityUniverseState()
    interval = RETRY_INTERVAL if state.last_error else REFRESH_INTERVAL
    if not force and state.last_attempt_at and now - utc(state.last_attempt_at) < interval:
        return {'status': 'skipped'}
    state.last_attempt_at = now
    session.add(state); session.commit()
    try:
        if provider is None:
            with SsiMarketDataProvider() as upstream:
                snapshot = upstream.get_security_universe()
        else:
            snapshot = provider.get_security_universe()
        if not snapshot.securities:
            raise ValueError('Empty equity snapshot')
        existing = {s.symbol: s for s in session.exec(select(Security)).all()}
        included = set()
        for metadata in snapshot.securities:
            included.add(metadata.symbol)
            record = existing.get(metadata.symbol) or Security(symbol=metadata.symbol,
                exchange=metadata.exchange, last_synced_at=now)
            for key, value in metadata.model_dump().items():
                setattr(record, key, value)
            record.is_active, record.last_synced_at = True, now
            record.search_text = normalized(' '.join([record.symbol, record.company_name or '', record.display_name_en or '']))
            session.add(record)
        for symbol, record in existing.items():
            if symbol not in included:
                record.is_active = False
                session.add(record)
        state.last_success_at, state.last_error = now, None
        state.raw_count, state.exclusions = snapshot.raw_count, snapshot.exclusions
        state.duplicate_count = snapshot.duplicate_count
        session.add(state); session.commit()
        return {'status': 'ok', 'raw_count': snapshot.raw_count, 'equity_count': len(included),
            'exclusions': snapshot.exclusions}
    except Exception as exc:
        session.rollback()
        state = session.get(SecurityUniverseState, 'ssi')
        state.last_error = type(exc).__name__
        session.add(state); session.commit()
        return {'status': 'error', 'error': state.last_error}


def browse_universe(session: Session, *, q='', exchange=None, offset=0, limit=100, now=None):
    now = now or datetime.now(timezone.utc)
    state = session.get(SecurityUniverseState, 'ssi')
    query = select(Security).where(Security.is_active == True)
    if exchange:
        query = query.where(Security.exchange == exchange)
    if q.strip():
        query = query.where(Security.search_text.contains(normalized(q), autoescape=True))
    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    total_universe = session.exec(select(func.count()).select_from(Security).where(Security.is_active == True)).one()
    status = ('not_attempted' if not state else 'error' if state.last_error else
        'stale' if not state.last_success_at or now - utc(state.last_success_at) > 2 * REFRESH_INTERVAL else 'healthy')
    return dict(items=session.exec(query.order_by(Security.symbol).offset(offset).limit(limit)).all(),
        total=total, total_universe=total_universe, offset=offset, limit=limit, status=status,
        last_synced_at=utc(state.last_success_at) if state and state.last_success_at else None)
