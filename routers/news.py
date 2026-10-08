from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from src.db.session import get_session
from src.news.models import NewsArticle, NewsStory, NewsSourceState
from src.news.registry import load_sources
from src.news.normalization import utc
from src.news.service import articles, story_score, trending, relevant_article, equity_tagger

from src.news.read import StoryResponse, representative, cluster_thumbnail
from src.news.read_cache import research_rows

router = APIRouter(prefix='/news', tags=['news'])
DB = Annotated[Session, Depends(get_session)]


# Explicit query signatures keep OpenAPI and validation stable across FastAPI versions.
def filters(country: str | None = None, source: str | None = None,
            topic: str | None = None, ticker: str | None = None, sector: str | None = None,
            category: Literal['VN', 'GLOBAL'] | None = None,
            financial_only: bool = False,
            limit: int = Query(default=20, ge=1, le=100)):
    return dict(country=country, source=source, topic=topic, ticker=ticker, sector=sector, category=category, financial_only=financial_only, limit=limit)


class TrendingResponse(BaseModel):
    topic: str
    story_count: int
    source_count: int
    recent_mentions: int
    previous_mentions: int
    mention_velocity: float
    score: float


class FeedPageResponse(BaseModel):
    items: list[StoryResponse]
    as_of: datetime
    has_more: bool
    next_offset: int | None


class SourceResponse(BaseModel):
    source_id: str
    name: str
    country: str
    category: Literal['VN', 'GLOBAL']
    enabled: bool
    poll_interval_minutes: int
    status: Literal['healthy', 'stale', 'error', 'not_attempted', 'disabled']
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    articles_received: int | None
    priority: str | None = None
    next_due_at: datetime | None = None
    refresh_requested_at: datetime | None = None
    refresh_execution: str = 'pending requests require scripts.ingest_data --watch'
    consecutive_failures: int = 0
    fetch_duration_seconds: float | None = None
    newly_inserted_articles: int = 0
    fetch_attempts: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    refresh_requests: int = 0


@router.get('/sources', response_model=list[SourceResponse])
def sources(session: DB):
    from src.news.scheduling import cadence_minutes, load_schedule, next_due
    now = datetime.now(timezone.utc)
    config = load_schedule()
    states = {state.source_id: state for state in session.exec(select(NewsSourceState)).all()}
    output = []
    for source in load_sources():
        state = states.get(source.source_id)
        if not source.enabled:
            status = 'disabled'
        elif state is None or state.last_attempt_at is None:
            status = 'not_attempted'
        elif state.last_error:
            status = 'error'
        elif state.last_success_at is None or utc(state.last_success_at) < now - timedelta(minutes=2 * cadence_minutes(source, now, config)):
            status = 'stale'
        else:
            status = 'healthy'
        output.append(SourceResponse(
            source_id=source.source_id, name=source.name, country=source.country,
            category=source.category, enabled=source.enabled,
            poll_interval_minutes=cadence_minutes(source, now, config), status=status,
            last_attempt_at=utc(state.last_attempt_at) if state and state.last_attempt_at else None,
            last_success_at=utc(state.last_success_at) if state and state.last_success_at else None,
            last_error=state.last_error if state else None,
            articles_received=state.articles_received if state and state.last_attempt_at else None,
            priority=source.scheduling_priority, next_due_at=next_due(source, state, now, config),
            refresh_requested_at=utc(state.refresh_requested_at) if state and state.refresh_requested_at else None,
            **{field: getattr(state, field) for field in ('consecutive_failures', 'fetch_duration_seconds',
                'newly_inserted_articles', 'fetch_attempts', 'successful_fetches', 'failed_fetches', 'refresh_requests')} if state else {},
        ))
    return output


@router.post('/refresh')
def refresh_news(session: DB):
    from src.news.scheduling import request_due_refresh
    return request_due_refresh(session, load_sources())


@router.get('/latest', response_model=list[NewsArticle])
def latest(session: DB, options: dict = Depends(filters)):
    from src.news.scheduling import request_due_refresh
    request_due_refresh(session, load_sources())
    limit = options.pop('limit')
    return articles(session, **options)[:limit]


@router.get('/top', response_model=list[StoryResponse])
def top(session: DB, require_image: bool = False, options: dict = Depends(filters)):
    from src.news.scheduling import request_due_refresh
    request_due_refresh(session, load_sources())
    limit = options.pop('limit')
    now = datetime.now(timezone.utc)
    if require_image:
        rows = research_rows(session, {**options, 'limit': 10000}, now=now)
        return sorted(rows, key=lambda row: (-row.ranking_score, row.story.id))[:limit]
    rows = articles(session, now=now, **options)
    current = articles(session, now=now)
    grouped = {}
    for article in rows:
        grouped.setdefault(article.story_id, []).append(article)
    output = []
    priorities = {s.source_id: s.representative_priority for s in load_sources()}
    for story_id, matching in grouped.items():
        story = session.get(NewsStory, story_id)
        if story:
            chosen = representative(matching, priorities)
            # Filters select discoveries/representatives; disclosure retains all
            # evidence for the selected Story, including other publishers.
            members = [a for a in current if a.story_id == story_id]
            if require_image and cluster_thumbnail(chosen, members, priorities) is None:
                continue
            evidence = [chosen, *sorted((a for a in members if a.id != chosen.id), key=lambda a: (a.source_id, a.canonical_url))]
            story = story.model_copy(update={'source_count': len({a.publisher_group for a in members}), 'article_count': len(members)})
            output.append(StoryResponse(story=story, articles=evidence, representative_article=chosen, ranking_score=story_score(story, now)))
    return sorted(output, key=lambda x: (-x.ranking_score, x.story.id))[:limit]


@router.get('/topics/trending', response_model=list[TrendingResponse])
def topics(session: DB, options: dict = Depends(filters)):
    limit = options.pop('limit')
    now = datetime.now(timezone.utc)
    return trending(articles(session, now=now, hours=12, **options), now)[:limit]


@router.get('/feed', response_model=list[StoryResponse])
def feed(session: DB, research_category: Literal['COMPANY', 'INDUSTRY', 'MARKET_BRIEF'] = 'COMPANY',
         offset: int = Query(default=0, ge=0, le=10000),
         options: dict = Depends(filters)):
    return research_rows(session, options, research_category, offset=offset, now=datetime.now(timezone.utc))


@router.get('/feed/page', response_model=FeedPageResponse)
def feed_page(session: DB, research_category: Literal['COMPANY', 'INDUSTRY', 'MARKET_BRIEF'] = 'COMPANY',
              offset: int = Query(default=0, ge=0, le=10000),
              as_of: datetime | None = None, options: dict = Depends(filters)):
    now = datetime.now(timezone.utc)
    if as_of is not None and (as_of.tzinfo is None or as_of > now):
        raise HTTPException(status_code=422, detail='as_of must be a past timezone-aware timestamp')
    cutoff = as_of or now
    size = options['limit']
    size = min(size, 12)
    rows = research_rows(session, {**options, 'limit': size+1}, research_category, offset=offset, now=cutoff)
    has_more = len(rows) > size and offset+size <= 10000
    return FeedPageResponse(items=rows[:size], as_of=cutoff, has_more=has_more,
        next_offset=offset+size if has_more else None)


@router.get('/hot', response_model=list[StoryResponse])
def hot(session: DB, options: dict = Depends(filters)):
    return research_rows(session, options, hot=True, now=datetime.now(timezone.utc))


@router.get('/stories/{story_id}', response_model=StoryResponse)
def detail(story_id: str, session: DB):
    story = session.get(NewsStory, story_id)
    if not story:
        raise HTTPException(status_code=404, detail='News story not found')
    rows = session.exec(select(NewsArticle).where(NewsArticle.story_id == story_id).order_by(NewsArticle.first_seen_at.desc())).all()
    return StoryResponse(story=story, articles=rows, representative_article=representative(rows, {s.source_id: s.representative_priority for s in load_sources()}), ranking_score=story_score(story, datetime.now(timezone.utc)))
