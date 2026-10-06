from datetime import datetime, timedelta, timezone
import math
from sqlalchemy import or_, text
from sqlmodel import Session, select
from src.models import Stock
from src.news.adapters import acquire
from src.news.models import NewsArticle, NewsStory, NewsSourceState
from src.news.matching import LexicalStoryMatcher
from src.news.normalization import canonical_url, clean_title, digest, normalized, utc
from src.news.tagging import Tagger


def story_score(story: NewsStory, now: datetime) -> float:
    age = max(0, (utc(now) - utc(story.last_updated_at)).total_seconds() / 3600)
    # Diversity dominates; repeated articles from one publisher have a capped contribution.
    activity = min(story.article_count, 5) / 5
    return round((3 * math.log1p(story.source_count) + activity) * 2 ** (-age / 24), 4)


def ingest_cycle(session: Session, sources, *, fetch=acquire, now=None, force=False, matcher=None, tagger=None):
    supplied_now = now
    now = utc(now or datetime.now(timezone.utc))
    matcher = matcher or LexicalStoryMatcher()
    from src.services.universe import discovery_metadata
    tagger = tagger or Tagger(discovery_metadata(session))
    result = {}
    for source in sources:
        now = utc(supplied_now or datetime.now(timezone.utc))
        if not source.enabled or source.country != 'VN' or source.category != 'VN':
            continue
        state = session.get(NewsSourceState, source.source_id)
        if state and state.last_attempt_at and not force and utc(state.last_attempt_at) > now - timedelta(minutes=source.poll_interval_minutes):
            continue
        # Fetch outside the write transaction. One scheduler process is recommended.
        try:
            incoming = fetch(source)
            # PostgreSQL serializes news writers, including manual ingestion commands.
            if session.get_bind().dialect.name == 'postgresql':
                session.execute(text('SELECT pg_advisory_xact_lock(73193001)'))
            state = session.get(NewsSourceState, source.source_id) or NewsSourceState(source_id=source.source_id)
            state.last_attempt_at = now
            stories = list(session.exec(select(NewsStory).where(NewsStory.first_seen_at >= now - timedelta(hours=matcher.window_hours if isinstance(matcher, LexicalStoryMatcher) else 72))).all())
            added = 0
            for item in incoming:
                title = clean_title(item.title)
                if not title:
                    continue
                url = canonical_url(item.url)
                title_hash, url_hash = digest(normalized(title)), digest(url)
                existing = session.exec(select(NewsArticle).where(or_(NewsArticle.url_hash == url_hash, (NewsArticle.source_id == source.source_id) & (NewsArticle.title_hash == title_hash)))).first()
                if existing:
                    existing.last_seen_at = now
                    # Refresh derived tags after taxonomy/universe changes, without
                    # changing publisher evidence or renewing story activity.
                    tags = tagger.tag(existing.title, existing.category)
                    existing.topics, existing.tickers, existing.sectors = tags.topics, tags.tickers, tags.sectors
                    existing.scope = tags.scope
                    if item.thumbnail_url:
                        existing.thumbnail_url = canonical_url(item.thumbnail_url)
                        existing.thumbnail_provenance = item.thumbnail_provenance
                    session.add(existing)
                    session.flush()
                    story = session.get(NewsStory, existing.story_id)
                    if story:
                        members = session.exec(select(NewsArticle).where(NewsArticle.story_id == story.id)).all()
                        for field in ('topics', 'tickers', 'sectors'):
                            setattr(story, field, sorted({v for a in members for v in getattr(a, field)}))
                        session.add(story)
                    continue
                published = utc(item.published_at) if item.published_at else None
                # No historical backfill, and reject implausible future dates.
                if published and (published < now - timedelta(hours=72) or published > now + timedelta(minutes=10)):
                    continue
                tags = tagger.tag(title, source.category)
                if source.category == 'GLOBAL' and not tags.topics:
                    continue
                story = matcher.match(title, tags, stories, now)
                if story is None:
                    story = NewsStory(representative_title=title, first_seen_at=now, last_updated_at=now)
                    stories.append(story)
                    session.add(story)
                    session.flush()
                article = NewsArticle(source_id=source.source_id, source_name=source.name,
                    publisher_group=source.publisher_group, title=title, url=url, canonical_url=url,
                    title_hash=title_hash, url_hash=url_hash, published_at=published,
                    first_seen_at=now, last_seen_at=now, country=source.country, language=source.language,
                    category=source.category, scope=tags.scope, topics=tags.topics, tickers=tags.tickers,
                    sectors=tags.sectors, story_id=story.id,
                    thumbnail_url=canonical_url(item.thumbnail_url) if item.thumbnail_url else None,
                    thumbnail_provenance=item.thumbnail_provenance)
                session.add(article)
                session.flush()
                members = session.exec(select(NewsArticle).where(NewsArticle.story_id == story.id)).all()
                story.article_count = len(members)
                story.source_count = len({a.publisher_group for a in members})
                for field in ('topics', 'tickers', 'sectors'):
                    setattr(story, field, sorted({v for a in members for v in getattr(a, field)}))
                story.last_updated_at = now
                story.trend_score = story_score(story, now)
                session.add(story)
                added += 1
            state.last_success_at = utc(supplied_now or datetime.now(timezone.utc))
            state.last_error = None
            state.articles_received = len(incoming)
            session.add(state)
            session.commit()
            result[source.source_id] = {'received': len(incoming), 'added': added, 'status': 'ok'}
        except Exception as exc:
            session.rollback()
            state = session.get(NewsSourceState, source.source_id) or NewsSourceState(source_id=source.source_id)
            state.last_attempt_at = now
            # Never save response bodies, URLs with credentials, or exception payloads.
            state.last_error = type(exc).__name__
            state.articles_received = 0
            session.add(state)
            session.commit()
            result[source.source_id] = {'status': 'error', 'error': state.last_error}
    return result


def vietnam_article(article):
    return article.country == 'VN' and article.category == 'VN'


def equity_tagger(session):
    from src.services.universe import listed_equities
    return Tagger(listed_equities(session))


def relevant_article(article, tagger):
    from src.news.research import vietnam_relevance, primary_issuers
    if not vietnam_article(article):
        return False
    if vietnam_relevance(article.title):
        return True
    tags = tagger.tag(article.title, article.category)
    return vietnam_relevance(article.title,
        primary_issuers(article.title, [row for row in tagger.stocks if row.symbol in tags.tickers]))


def articles(session, *, country=None, source=None, topic=None, ticker=None, sector=None, category=None, financial_only=False, now=None, hours=72):
    now = utc(now or datetime.now(timezone.utc))
    query = select(NewsArticle).where(NewsArticle.first_seen_at >= now - timedelta(hours=hours), NewsArticle.country == 'VN', NewsArticle.category == 'VN')
    for field, value in [('country', country), ('source_id', source), ('category', category)]:
        if value:
            query = query.where(getattr(NewsArticle, field) == value)
    rows = session.exec(query).all()
    tagger = equity_tagger(session)
    rows = [a for a in rows if relevant_article(a, tagger)]
    return sorted([a for a in rows if (not financial_only or a.topics or a.tickers or a.sectors) and all(not value or value.casefold() in {x.casefold() for x in getattr(a, field)} for field, value in [('topics', topic), ('tickers', ticker), ('sectors', sector)])],
        key=lambda a: (utc(a.published_at or a.first_seen_at), a.id), reverse=True)


def trending(rows, now):
    now = utc(now)
    topics = sorted({t for a in rows for t in a.topics})
    output = []
    for topic in topics:
        current = [a for a in rows if topic in a.topics and utc(a.first_seen_at) >= now - timedelta(hours=6)]
        previous = [a for a in rows if topic in a.topics and now - timedelta(hours=12) <= utc(a.first_seen_at) < now - timedelta(hours=6)]
        if not current:
            continue
        # Count story/publisher pairs, preventing one publisher's repeated articles from dominating.
        mentions = len({(a.story_id, a.publisher_group) for a in current})
        prior = len({(a.story_id, a.publisher_group) for a in previous})
        velocity = (mentions - prior) / 6
        if velocity <= 0:
            continue
        diversity = len({a.publisher_group for a in current})
        stories = len({a.story_id for a in current})
        age = max(0, (now - max(utc(a.first_seen_at) for a in current)).total_seconds() / 3600)
        score = (stories + 2 * diversity + velocity) * 2 ** (-age / 6)
        output.append(dict(topic=topic, story_count=stories, source_count=diversity,
            recent_mentions=mentions, previous_mentions=prior, mention_velocity=round(velocity, 3), score=round(score, 4)))
    return sorted(output, key=lambda x: (-x['score'], x['topic']))
