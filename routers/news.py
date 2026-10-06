from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from src.db.session import get_session
from src.news.models import NewsArticle, NewsStory, NewsSourceState
from src.news.registry import load_sources
from src.news.normalization import utc
from src.news.service import articles, story_score, trending

router = APIRouter(prefix='/news', tags=['news'])
DB = Annotated[Session, Depends(get_session)]


# Explicit query signatures keep OpenAPI and validation stable across FastAPI versions.
def filters(country: str | None = None, source: str | None = None,
            topic: str | None = None, ticker: str | None = None, sector: str | None = None,
            category: Literal['VN', 'GLOBAL'] | None = None,
            financial_only: bool = False,
            limit: int = Query(default=20, ge=1, le=100)):
    return dict(country=country, source=source, topic=topic, ticker=ticker, sector=sector, category=category, financial_only=financial_only, limit=limit)


class StoryResponse(BaseModel):
    story: NewsStory
    articles: list[NewsArticle]
    representative_article: NewsArticle
    ranking_score: float
    ranking_reason: str = 'Independent publisher diversity, capped activity and recency'
    research_category: Literal['COMPANY', 'INDUSTRY', 'MARKET_BRIEF'] | None = None


def representative(rows, priorities):
    # Selection never changes diversity or ranking. Ties are stable across ingestion order.
    return min(rows, key=lambda a: (priorities.get(a.source_id, 100),
        -utc(a.published_at or a.first_seen_at).timestamp(), a.canonical_url, a.id))


class TrendingResponse(BaseModel):
    topic: str
    story_count: int
    source_count: int
    recent_mentions: int
    previous_mentions: int
    mention_velocity: float
    score: float


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


@router.get('/sources', response_model=list[SourceResponse])
def sources(session: DB):
    now = datetime.now(timezone.utc)
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
        elif state.last_success_at is None or utc(state.last_success_at) < now - timedelta(minutes=2 * source.poll_interval_minutes):
            status = 'stale'
        else:
            status = 'healthy'
        output.append(SourceResponse(
            source_id=source.source_id, name=source.name, country=source.country,
            category=source.category, enabled=source.enabled,
            poll_interval_minutes=source.poll_interval_minutes, status=status,
            last_attempt_at=utc(state.last_attempt_at) if state and state.last_attempt_at else None,
            last_success_at=utc(state.last_success_at) if state and state.last_success_at else None,
            last_error=state.last_error if state else None,
            articles_received=state.articles_received if state and state.last_attempt_at else None,
        ))
    return output


@router.get('/latest', response_model=list[NewsArticle])
def latest(session: DB, options: dict = Depends(filters)):
    limit = options.pop('limit')
    return articles(session, **options)[:limit]


@router.get('/top', response_model=list[StoryResponse])
def top(session: DB, options: dict = Depends(filters)):
    limit = options.pop('limit')
    now = datetime.now(timezone.utc)
    rows = articles(session, now=now, **options)
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
            members = session.exec(select(NewsArticle).where(NewsArticle.story_id == story_id)).all()
            evidence = [chosen, *sorted((a for a in members if a.id != chosen.id), key=lambda a: (a.source_id, a.canonical_url))]
            output.append(StoryResponse(story=story, articles=evidence, representative_article=chosen, ranking_score=story_score(story, now)))
    return sorted(output, key=lambda x: (-x.ranking_score, x.story.id))[:limit]


@router.get('/topics/trending', response_model=list[TrendingResponse])
def topics(session: DB, options: dict = Depends(filters)):
    limit = options.pop('limit')
    now = datetime.now(timezone.utc)
    return trending(articles(session, now=now, hours=12, **options), now)[:limit]


def research_rows(session, options, category=None, *, hot=False):
    from src.news.research import research_category, attention_order
    from src.news.tagging import Tagger
    from src.services.universe import discovery_metadata
    tagger = Tagger(discovery_metadata(session))
    # Re-tag copies for older articles without destructive migration or lost provenance.
    selected = []
    options = dict(options)
    limit = options.pop('limit')
    ticker = options.pop('ticker', None)
    for article in articles(session, **options):
        tags = tagger.tag(article.title, article.category)
        copy = article.model_copy(update={'tickers': tags.tickers,
            'sectors': sorted(set(article.sectors) | set(tags.sectors))})
        kind = research_category(copy)
        if kind and (not category or kind == category) and (not ticker or ticker.upper() in copy.tickers):
            selected.append((copy, kind))
    grouped = {}
    for article, kind in selected:
        grouped.setdefault(article.story_id, []).append((article, kind))
    priorities = {s.source_id: s.representative_priority for s in load_sources()}
    output = []
    for story_id, matching in grouped.items():
        story = session.get(NewsStory, story_id)
        if not story:
            continue
        chosen = representative([row[0] for row in matching], priorities)
        kind = next(kind for row, kind in matching if row.id == chosen.id)
        members = session.exec(select(NewsArticle).where(NewsArticle.story_id == story_id)).all()
        source_count = len({a.publisher_group for a in members})
        # Broad Market Brief and Hot Topics need two independent publisher groups.
        if (hot or kind == 'MARKET_BRIEF') and source_count < 2:
            continue
        story = story.model_copy(update={'source_count': source_count})
        output.append(StoryResponse(story=story, articles=[chosen, *[a for a in members if a.id != chosen.id]],
            representative_article=chosen, research_category=kind, ranking_score=story_score(story, datetime.now(timezone.utc)),
            ranking_reason='Independent publishers first, capped article activity, then latest activity'))
    return sorted(output, key=attention_order)[:limit]


@router.get('/feed', response_model=list[StoryResponse])
def feed(session: DB, research_category: Literal['COMPANY', 'INDUSTRY', 'MARKET_BRIEF'] = 'COMPANY',
         options: dict = Depends(filters)):
    return research_rows(session, options, research_category)


@router.get('/hot', response_model=list[StoryResponse])
def hot(session: DB, options: dict = Depends(filters)):
    return research_rows(session, options, hot=True)


@router.get('/stories/{story_id}', response_model=StoryResponse)
def detail(story_id: str, session: DB):
    story = session.get(NewsStory, story_id)
    if not story:
        raise HTTPException(status_code=404, detail='News story not found')
    rows = session.exec(select(NewsArticle).where(NewsArticle.story_id == story_id).order_by(NewsArticle.first_seen_at.desc())).all()
    return StoryResponse(story=story, articles=rows, representative_article=representative(rows, {s.source_id: s.representative_priority for s in load_sources()}), ranking_score=story_score(story, datetime.now(timezone.utc)))
