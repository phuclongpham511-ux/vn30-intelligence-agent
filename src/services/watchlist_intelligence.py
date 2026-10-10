"""Bounded persisted Watchlist projection; never acquire or score in HTTP."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

from sqlalchemy import func
from sqlmodel import select

from src.models import Stock, Security
from src.news.models import NewsArticle
from src.news.normalization import utc, normalized
from src.news.registry import load_sources
from src.news.research import research_category
from src.community.models import CommunityEvidenceItem
from src.community.daily import source_statuses
from src.services.technical_eod_store import read_latest_operational_packet
from src.models.technical_eod import TechnicalEODJob

SCAN_LIMIT = 300


def revision(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                            separators=(',', ':'), default=str).encode()).hexdigest()


def ticker_membership(session, column, symbol):
    values = (func.json_each(column) if session.get_bind().dialect.name == 'sqlite'
              else func.json_array_elements_text(column)).table_valued('value')
    if session.get_bind().dialect.name == 'postgresql':
        values = values.render_derived()
    return select(values.c.value).where(values.c.value == symbol).exists()


def news_page(session, symbol, identity, now, offset, size, source_ids):
    rows = session.exec(select(NewsArticle).where(
        NewsArticle.first_seen_at >= now-timedelta(hours=72),
        NewsArticle.first_seen_at <= now,
        NewsArticle.country == 'VN', NewsArticle.category == 'VN',
        NewsArticle.source_id.in_(source_ids),
        ticker_membership(session, NewsArticle.tickers, symbol))
        .order_by(NewsArticle.first_seen_at.desc(), NewsArticle.id).limit(SCAN_LIMIT+1)).all()
    truncated = len(rows) > SCAN_LIMIT
    grouped = {}
    for article in rows[:SCAN_LIMIT]:
        if article.published_at and utc(article.published_at) > now:
            continue
        if research_category(article, [identity]) != 'COMPANY':
            continue
        grouped.setdefault(article.story_id, []).append(article)
    ids = sorted(grouped, key=lambda key: (max(utc(a.first_seen_at) for a in grouped[key]), key), reverse=True)
    selected = ids[offset:offset+size]
    # A stable archive anchor avoids renewing the same Story when its earliest
    # source ages out of the discovery window. Bound evidence per selected Story.
    ranked = select(NewsArticle.id.label('article_id'), func.row_number().over(
        partition_by=NewsArticle.story_id, order_by=(NewsArticle.first_seen_at, NewsArticle.id)).label('position')).where(
            NewsArticle.story_id.in_(selected), NewsArticle.first_seen_at <= now,
            NewsArticle.source_id.in_(source_ids), NewsArticle.country=='VN', NewsArticle.category=='VN',
            ticker_membership(session,NewsArticle.tickers,symbol)).subquery()
    anchors = session.exec(select(NewsArticle).join(ranked, NewsArticle.id==ranked.c.article_id)
        .where(ranked.c.position <= 100).order_by(NewsArticle.first_seen_at,NewsArticle.id)
        .limit(size*100)).all() if selected else []
    archived = {}
    for article in anchors:
        if (not article.published_at or utc(article.published_at)<=now) and research_category(article,[identity])=='COMPANY':
            archived.setdefault(article.story_id,[]).append(article)
    events = []
    for story_id in selected:
        evidence = archived.get(story_id) or grouped[story_id]
        # Earliest matching source represents the story; another publisher is
        # evidence breadth, never another unread story or a content revision.
        evidence.sort(key=lambda a: (utc(a.first_seen_at), a.id))
        chosen = evidence[0]
        version = revision([normalized(chosen.title), chosen.canonical_url,
                            utc(chosen.published_at).isoformat() if chosen.published_at else None])
        events.append(dict(id='news:'+story_id, entity_id=story_id, revision=version,
            kind='news', title=chosen.title, occurred_at=min(utc(a.first_seen_at) for a in evidence),
            url=chosen.url,
            revision_members={a.id:revision([normalized(a.title),a.canonical_url,
                utc(a.published_at).isoformat() if a.published_at else None]) for a in evidence},
            source_count=len({a.publisher_group for a in evidence}),
            evidence=[a.model_dump(mode='json') for a in evidence[:5]],
            evidence_truncated=len(evidence)>5))
    return dict(items=events, has_more=len(ids)>offset+size,
                truncated=truncated, window_start=now-timedelta(hours=72))


def community_page(session, symbol, now, offset, size, source_ids):
    rows = session.exec(select(CommunityEvidenceItem).where(
        CommunityEvidenceItem.published_at >= now-timedelta(hours=24),
        CommunityEvidenceItem.published_at <= now,
        CommunityEvidenceItem.first_seen_at <= now,
        CommunityEvidenceItem.source_id.in_(source_ids),
        ticker_membership(session, CommunityEvidenceItem.tickers, symbol))
        .order_by(CommunityEvidenceItem.published_at.desc(), CommunityEvidenceItem.id)
        .offset(offset).limit(size+1)).all()
    items = []
    for row in rows[:size]:
        # Native revisions include engagement; attention changes only with
        # actual bounded evidence, attribution or ticker association.
        version = revision([row.title, row.excerpt, row.context_text, row.author,
                            row.url, utc(row.published_at).isoformat(), sorted(row.tickers)])
        items.append(dict(id='community:'+row.id, entity_id=row.id, revision=version,
            kind='community', title=row.title or row.excerpt[:100],
            occurred_at=utc(row.published_at), url=row.url,
            evidence={**row.model_dump(mode='json'),
                'published_at':utc(row.published_at).isoformat(),
                'first_seen_at':utc(row.first_seen_at).isoformat(),
                'last_seen_at':utc(row.last_seen_at).isoformat()}))
    return dict(items=items, has_more=len(rows)>size, truncated=False,
                window_start=now-timedelta(hours=24))


def technical_updates(session, symbol, now):
    try:
        result = read_latest_operational_packet(session, symbol, now).model_dump(mode='json')
    except (ValueError, TypeError, AttributeError):
        result = dict(kind='diagnostic', ticker=symbol, requested_session=None,
            readiness_status='INCOMPLETE_EVIDENCE', reason_codes=['invalid_persisted_eod_evidence'],
            safe_to_display_as_verified=False)
    items = []
    if result['kind'] == 'provisional_packet':
        for event in result['packet']['top_insights']:
            items.append(dict(id='technical:'+event['event_id'], entity_id=event['event_id'],
                revision=revision(event), kind='technical', title=event['event_type'],
                occurred_at=result['persisted_at'], url='/stocks/'+symbol+'#stock-technical-insights',
                evidence=event))
    job = session.exec(select(TechnicalEODJob).where(TechnicalEODJob.ticker == symbol)
        .order_by((TechnicalEODJob.version > 0).desc(), TechnicalEODJob.trading_session.desc())
        .limit(1)).first()
    scheduled = bool(result['kind']=='diagnostic' and job and job.status=='WAITING_FOR_TIME')
    waiting = bool(scheduled and utc(job.next_due_at)>now)
    return dict(items=items, data=result, has_more=False, truncated=False,
        waiting_for_gate=waiting, awaiting_source_check=scheduled and not waiting,
        next_check_due_at=utc(job.next_due_at) if scheduled else None,
        last_checked_at=utc(job.last_checked_at) if job and job.last_checked_at else None)


def intelligence(session, symbols, *, now=None, offset=0, size=12):
    now = utc(now or datetime.now(timezone.utc))
    if not symbols:
        return dict(as_of=now, offset=offset, page_size=size, stocks=[], news_sources=[], community_sources=[])
    stocks = {s.symbol:s for s in session.exec(select(Stock).where(
        Stock.symbol.in_(symbols), Stock.is_active == True)).all()}
    securities = {s.symbol:s for s in session.exec(select(Security).where(
        Security.symbol.in_(symbols), Security.is_active == True, Security.instrument_type == 'Stock')).all()}
    # These status reads disclose actual acquisition times, not this response time.
    from routers.news import sources as news_source_statuses
    news_sources = news_source_statuses(session)
    community_sources = source_statuses(session, now=now)
    news_ids = [s.source_id for s in load_sources() if s.enabled and s.country=='VN' and s.category=='VN']
    community_ids = [s['source_id'] for s in community_sources if s['enabled']]
    output = []
    for symbol in symbols:
        identity = securities.get(symbol) or stocks.get(symbol)
        if identity and symbol in stocks:
            identity = identity.model_copy(update={
                'company_name':identity.company_name or stocks[symbol].company_name,
                'display_name_en':identity.display_name_en or stocks[symbol].display_name_en})
        row = dict(symbol=symbol, status='ready' if identity else 'unavailable',
            company_name=identity.company_name if identity else None,
            display_name_en=identity.display_name_en if identity else None,
            exchange=identity.exchange if identity else None)
        row['news'] = news_page(session,symbol,identity,now,offset,size,news_ids) if identity else None
        row['community'] = community_page(session,symbol,now,offset,size,community_ids) if identity else None
        row['technical'] = technical_updates(session,symbol,now) if identity else None
        output.append(row)
    return dict(as_of=now, offset=offset, page_size=size, stocks=output,
                news_sources=news_sources, community_sources=community_sources)
