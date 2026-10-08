from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, field_validator
from src.news.models import NewsArticle, NewsStory
from src.news.normalization import utc
from src.news.service import articles, story_score, equity_tagger
from src.news.registry import load_sources

class StoryResponse(BaseModel):
    story: NewsStory
    articles: list[NewsArticle]
    representative_article: NewsArticle
    thumbnail_url: str | None = None
    thumbnail_article_id: str | None = None
    ranking_score: float
    ranking_reason: str = 'Independent publisher diversity, capped activity and recency'
    research_category: Literal['COMPANY', 'INDUSTRY', 'MARKET_BRIEF'] | None = None

    @field_validator('story', mode='before')
    @classmethod
    def validate_story(cls, value):
        return NewsStory.model_validate(value) if isinstance(value, dict) else value

    @field_validator('articles', mode='before')
    @classmethod
    def validate_articles(cls, value):
        return [NewsArticle.model_validate(row) if isinstance(row, dict) else row for row in value]

    @field_validator('representative_article', mode='before')
    @classmethod
    def validate_representative(cls, value):
        return NewsArticle.model_validate(value) if isinstance(value, dict) else value


def representative(rows, priorities):
    # Earliest documented publication wins; unknown publication dates sort last.
    return min(rows, key=lambda a: (a.published_at is None,
        utc(a.published_at or a.first_seen_at), a.canonical_url, a.id))


def cluster_thumbnail(chosen, members, priorities):
    from urllib.parse import urlsplit
    def valid(article):
        try:
            url = urlsplit(article.thumbnail_url or '')
            return url.scheme in ('https', 'http') and bool(url.hostname) and not url.username and not url.password
        except ValueError:
            return False
    if valid(chosen):
        return chosen
    candidates = [a for a in members if valid(a)]
    return representative(candidates, priorities) if candidates else None


def build_research_rows(session, options, category=None, *, hot=False, offset=0, now=None, story_ids=None, hours=72, include_future_publication=False):
    from src.news.research import research_category, attention_order
    tagger = equity_tagger(session)
    now = utc(now or datetime.now(timezone.utc))
    eligible = {row.symbol: row for row in tagger.stocks}
    # Re-tag copies for older articles without destructive migration or lost provenance.
    selected = []
    options = dict(options)
    limit = options.pop('limit')
    ticker = options.pop('ticker', None)
    current = articles(session, now=now, story_ids=story_ids, hours=hours, include_future_publication=include_future_publication)
    for article in articles(session, now=now, story_ids=story_ids, hours=hours, include_future_publication=include_future_publication, **options):
        tags = tagger.tag(article.title, article.category)
        copy = article.model_copy(update={'tickers': tags.tickers,
            'sectors': sorted(set(article.sectors) | set(tags.sectors))})
        kind = research_category(copy, [eligible[symbol] for symbol in tags.tickers])
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
        members = [a for a in current if a.story_id == story_id]
        source_count = len({a.publisher_group for a in members})
        # Multiple distinct reports indicate attention; re-ingestion does not count.
        if hot and source_count < 2:
            continue
        image = cluster_thumbnail(chosen, members, priorities)
        # User-facing archive and Hot Topics wait until a source image exists.
        if image is None:
            continue
        story = story.model_copy(update={'source_count': source_count, 'article_count': len(members),
            'last_updated_at': max(a.first_seen_at for a in members)})
        output.append(StoryResponse(story=story, articles=[chosen, *[a for a in members if a.id != chosen.id]],
            representative_article=chosen, thumbnail_url=image.thumbnail_url if image else None,
            thumbnail_article_id=image.id if image else None, research_category=kind, ranking_score=story_score(story, now),
            ranking_reason='Independent publishers first, capped article activity, then latest activity' if hot else 'Latest publication first; earliest source represents each story'))
    order = attention_order if hot else lambda row: (-max(utc(a.published_at or a.first_seen_at).timestamp() for a in row.articles), row.story.id)
    return sorted(output, key=order)[offset:offset+limit]
