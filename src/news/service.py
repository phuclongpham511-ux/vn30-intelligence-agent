from datetime import datetime, timedelta, timezone
import math
from sqlalchemy import or_, text
from sqlmodel import Session, select
from src.models import Stock
from src.news.adapters import acquire
from src.news.models import NewsArticle, NewsStory, NewsSourceState
from src.news.matching import LexicalStoryMatcher
from src.news.normalization import canonical_url, cafef_article_suffix, clean_title, digest, normalized, utc
from src.news.tagging import Tagger
from src.services.ingestion_owner import collector_owned


def story_score(story: NewsStory, now: datetime) -> float:
    age = max(0, (utc(now) - utc(story.last_updated_at)).total_seconds() / 3600)
    # Diversity dominates; repeated articles from one publisher have a capped contribution.
    activity = min(story.article_count, 5) / 5
    return round((3 * math.log1p(story.source_count) + activity) * 2 ** (-age / 24), 4)


def _title_key(session, source_id, title_hash, identity, article_id=None):
    # Preserve the existing publisher-title uniqueness constraint without merging
    # authoritative identities which happen to share a corrected headline.
    owner = session.exec(select(NewsArticle).where(
        NewsArticle.source_id == source_id, NewsArticle.title_hash == title_hash)).first()
    # Retain the normalized-headline prefix so ordinary reprint lookup can still
    # find this row if the unsuffixed key's owner later corrects its own headline.
    return title_hash + ':' + digest(identity) if owner and owner.id != article_id else title_hash


def _persist_cycle(session: Session, sources, *, fetch=acquire, now=None, force=False, matcher=None, tagger=None, changed=None, observations=None):
    supplied_now = now
    now = utc(now or datetime.now(timezone.utc))
    matcher = matcher or LexicalStoryMatcher()
    from src.services.universe import discovery_metadata
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
            stories = None
            added = 0
            if incoming and tagger is None:
                tagger = Tagger(discovery_metadata(session))
            for item in incoming:
                title = clean_title(item.title)
                if not title:
                    continue
                url = canonical_url(item.url)
                title_hash, url_hash = digest(normalized(title)), digest(url)
                existing = session.exec(select(NewsArticle).where(NewsArticle.url_hash == url_hash)).first()
                suffix = cafef_article_suffix(url) if source.source_id == 'cafef' else None
                if existing is None and suffix:
                    candidates = session.exec(select(NewsArticle).where(
                        NewsArticle.source_id == source.source_id,
                        NewsArticle.canonical_url.endswith(suffix))
                        .order_by(NewsArticle.first_seen_at, NewsArticle.id).limit(10)).all()
                    existing = next((a for a in candidates if cafef_article_suffix(a.canonical_url) == suffix), None)
                if existing is None and not suffix:
                    existing = session.exec(select(NewsArticle).where(
                        NewsArticle.source_id == source.source_id,
                        or_(NewsArticle.title_hash == title_hash,
                            NewsArticle.title_hash.startswith(title_hash + ':')))
                        .order_by(NewsArticle.first_seen_at, NewsArticle.id)).first()
                if existing:
                    previous_title = existing.title
                    # A known URL/native identity can be corrected without becoming
                    # another article or renewing publication/first-seen time.
                    correction = (existing.source_id == source.source_id and
                        (existing.url_hash == url_hash or bool(suffix and cafef_article_suffix(existing.canonical_url) == suffix))
                        and (existing.title != title or existing.canonical_url != url))
                    if correction:
                        existing.title_hash = _title_key(session, source.source_id, title_hash,
                                                        suffix or url, existing.id)
                        existing.title = title
                        existing.url, existing.canonical_url, existing.url_hash = url, url, url_hash
                    existing.last_seen_at = now
                    if observations is not None:
                        observations[existing.id] = now
                    # Refresh derived tags after taxonomy/universe changes, without
                    # changing publisher evidence or renewing story activity.
                    tags = tagger.tag(existing.title, existing.category)
                    altered = (correction or existing.topics != tags.topics or existing.tickers != tags.tickers or existing.sectors != tags.sectors or existing.scope != tags.scope or
                               bool(item.thumbnail_url and (canonical_url(item.thumbnail_url) != existing.thumbnail_url or item.thumbnail_provenance != existing.thumbnail_provenance)))
                    existing.topics, existing.tickers, existing.sectors = tags.topics, tags.tickers, tags.sectors
                    existing.scope = tags.scope
                    if item.thumbnail_url:
                        existing.thumbnail_url = canonical_url(item.thumbnail_url)
                        existing.thumbnail_provenance = item.thumbnail_provenance
                    session.add(existing)
                    session.flush()
                    story = session.get(NewsStory, existing.story_id)
                    if story and altered:
                        if correction and story.representative_title == previous_title:
                            story.representative_title = title
                        story.read_cache_dirty = True
                        if changed is not None:
                            changed.add(story.id)
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
                if stories is None:
                    stories = list(session.exec(select(NewsStory).where(NewsStory.first_seen_at >= now - timedelta(hours=matcher.window_hours if isinstance(matcher, LexicalStoryMatcher) else 72))).all())
                story = matcher.match(title, tags, stories, now)
                if story is None:
                    story = NewsStory(representative_title=title, first_seen_at=now, last_updated_at=now)
                    stories.append(story)
                    session.add(story)
                    session.flush()
                article = NewsArticle(source_id=source.source_id, source_name=source.name,
                    publisher_group=source.publisher_group, title=title, url=url, canonical_url=url,
                    title_hash=_title_key(session, source.source_id, title_hash, suffix or url),
                    url_hash=url_hash, published_at=published,
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
                story.read_cache_dirty = True
                if changed is not None:
                    changed.add(story.id)
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


@collector_owned
def ingest_cycle(session: Session, sources, *, fetch=None, now=None, force=False,
                 matcher=None, tagger=None, config=None):
    """Claim in the database, fetch at most two feeds, serialize incremental writes."""
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
    from time import perf_counter
    import logging
    from sqlalchemy import update
    from src.news.scheduling import load_schedule, next_due, claim, cadence_minutes, release_slot
    from src.news.read_cache import refresh_cache
    config = config or load_schedule()
    clock = lambda: utc(now or datetime.now(timezone.utc))
    active = [s for s in sources if s.enabled and s.country == 'VN' and s.category == 'VN']
    states = {s.source_id: s for s in session.exec(select(NewsSourceState)).all()}
    due = sorted((s for s in active if force or next_due(s, states.get(s.source_id), clock(), config) <= clock()),
                 key=lambda s: (next_due(s, states.get(s.source_id), clock(), config), s.source_id))
    result, changed, observations = {}, set(), {}
    attempted = 0
    def fetch_one(source):
        started = perf_counter()
        try:
            incoming = fetch(source) if fetch is not None else acquire(source, timeout_seconds=config.timeout_seconds)
            return incoming, None, perf_counter()-started
        except Exception as exc:
            return None, type(exc).__name__, perf_counter()-started
    # Submit only active slots, never claim a long queued batch whose lease might expire.
    with ThreadPoolExecutor(max_workers=config.max_concurrent, thread_name_prefix='news-fetch') as pool:
        pending = {}
        cursor = iter(due)
        exhausted = False
        while pending or not exhausted:
            while not exhausted and len(pending) < config.max_concurrent:
                if attempted >= config.max_sources_per_cycle:
                    exhausted = True
                    break
                source = next(cursor, None)
                if source is None:
                    exhausted = True
                    break
                token = claim(session, source, clock(), config, force=force)
                if token:
                    attempted += 1
                    pending[pool.submit(fetch_one, source)] = (source, token)
            if not pending:
                continue
            finished, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in finished:
                source, token = pending.pop(future)
                incoming, error, duration = future.result()
                completed = clock()
                # Fenced ownership check before evidence writes. Expired workers discard results.
                fence = session.execute(update(NewsSourceState).where(
                    NewsSourceState.source_id == source.source_id,
                    NewsSourceState.lease_token == token, NewsSourceState.lease_until > completed
                ).values(lease_until=completed+timedelta(minutes=10)).execution_options(synchronize_session=False))
                if not fence.rowcount:
                    session.rollback()
                    release_slot(session, token)
                    session.commit()
                    result[source.source_id] = {'status': 'lease_lost'}
                    continue
                if error is None:
                    source_changes, source_observations = set(), {}
                    row = _persist_cycle(session, [source], fetch=lambda _: incoming, now=completed,
                                         force=True, matcher=matcher, tagger=tagger, changed=source_changes, observations=source_observations)[source.source_id]
                    error = row.get('error')
                    if error is None:
                        changed.update(source_changes)
                        observations.update(source_observations)
                else:
                    row = {'status': 'error', 'error': error}
                session.expire_all()
                state = session.get(NewsSourceState, source.source_id)
                if state.lease_token != token:
                    session.rollback()
                    continue
                state.last_error = error
                state.fetch_duration_seconds = duration
                state.newly_inserted_articles = row.get('added', 0)
                state.refresh_requested_at = None
                state.lease_until, state.lease_token = None, None
                if error:
                    state.consecutive_failures += 1
                    state.failed_fetches += 1
                    # One attempt per cycle, no immediate transport retries.
                    minutes = min(1440, config.failure_backoff_minutes * 2 ** min(state.consecutive_failures-1, 6))
                    state.articles_received = 0
                else:
                    state.consecutive_failures = 0
                    state.successful_fetches += 1
                    minutes = cadence_minutes(source, completed, config)
                state.next_due_at = completed+timedelta(minutes=minutes)
                session.add(state)
                release_slot(session, token)
                session.commit()
                result[source.source_id] = {**row, 'fetch_duration_seconds': round(duration, 4)}
    refreshed = refresh_cache(session, changed, now=clock(), observations=observations)
    logging.getLogger(__name__).info('news_cycle %s', {
        'attempts': attempted, 'successes': sum(v.get('status') == 'ok' for v in result.values()),
        'failures': sum(v.get('status') == 'error' for v in result.values()),
        'new_articles': sum(v.get('added', 0) for v in result.values()),
        'skipped_not_due': len(active)-len(due), 'deferred_due': max(0, len(due)-attempted),
        'story_updates': len(changed), 'hot_cache_refreshes': int(refreshed)})
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


def articles(session, *, country=None, source=None, topic=None, ticker=None, sector=None, category=None, financial_only=False, now=None, hours=72, story_ids=None, include_future_publication=False):
    now = utc(now or datetime.now(timezone.utc))
    cutoff = now - timedelta(hours=hours)
    query = select(NewsArticle).where(NewsArticle.first_seen_at <= now,
        or_(NewsArticle.published_at.is_(None), NewsArticle.published_at <= now + (timedelta(minutes=10) if include_future_publication else timedelta())),
        or_(NewsArticle.published_at >= cutoff,
            NewsArticle.published_at.is_(None) & (NewsArticle.first_seen_at >= cutoff)),
        NewsArticle.country == 'VN', NewsArticle.category == 'VN')
    if story_ids is not None:
        query = query.where(NewsArticle.story_id.in_(story_ids))
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
