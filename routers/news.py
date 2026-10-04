from datetime import datetime, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from src.db.session import get_session
from src.news.models import NewsArticle, NewsStory
from src.news.service import articles, story_score, trending

router = APIRouter(prefix='/news', tags=['news'])
DB = Annotated[Session, Depends(get_session)]


# Explicit query signatures keep OpenAPI and validation stable across FastAPI versions.
def filters(country: str | None = None, source: str | None = None,
            topic: str | None = None, ticker: str | None = None, sector: str | None = None,
            category: Literal['VN', 'GLOBAL'] | None = None,
            limit: int = Query(default=20, ge=1, le=100)):
    return dict(country=country, source=source, topic=topic, ticker=ticker, sector=sector, category=category, limit=limit)


class StoryResponse(BaseModel):
    story: NewsStory
    articles: list[NewsArticle]
    ranking_score: float
    ranking_reason: str = 'Independent publisher diversity, capped activity and recency'


class TrendingResponse(BaseModel):
    topic: str
    story_count: int
    source_count: int
    recent_mentions: int
    previous_mentions: int
    mention_velocity: float
    score: float


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
    for story_id, matching in grouped.items():
        story = session.get(NewsStory, story_id)
        if story:
            output.append(StoryResponse(story=story, articles=matching[:5], ranking_score=story_score(story, now)))
    return sorted(output, key=lambda x: (-x.ranking_score, x.story.id))[:limit]


@router.get('/topics/trending', response_model=list[TrendingResponse])
def topics(session: DB, options: dict = Depends(filters)):
    limit = options.pop('limit')
    now = datetime.now(timezone.utc)
    return trending(articles(session, now=now, hours=12, **options), now)[:limit]


@router.get('/stories/{story_id}', response_model=StoryResponse)
def detail(story_id: str, session: DB):
    story = session.get(NewsStory, story_id)
    if not story:
        raise HTTPException(status_code=404, detail='News story not found')
    rows = session.exec(select(NewsArticle).where(NewsArticle.story_id == story_id).order_by(NewsArticle.first_seen_at.desc())).all()
    return StoryResponse(story=story, articles=rows, ranking_score=story_score(story, datetime.now(timezone.utc)))
