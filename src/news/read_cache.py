"""Worker-built research snapshot. HTTP filters/ranks persisted evidence only."""
from datetime import datetime, timedelta, timezone
from sqlmodel import select
from sqlalchemy import update, text
from sqlalchemy.exc import IntegrityError
from src.news.models import NewsReadCache, NewsStory
from src.news.normalization import utc


def refresh_cache(session, changed, *, now, observations=None):
    from src.news.read import build_research_rows
    from src.news.service import equity_tagger
    from src.news.research import research_category
    from src.models import SecurityUniverseState
    cache = session.get(NewsReadCache, 'research')
    bootstrap = cache is None
    if bootstrap:
        session.add(NewsReadCache(id='research', updated_at=now))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
    # Share evidence-writer ownership through dirty-marker acknowledgement.
    if session.get_bind().dialect.name == 'postgresql':
        session.execute(text('SELECT pg_advisory_xact_lock(73193001)'))
    # Serialize projection writers too: two workers can finish different sources.
    session.execute(update(NewsReadCache).where(NewsReadCache.id == 'research')
                    .values(updated_at=NewsReadCache.updated_at).execution_options(synchronize_session=False))
    session.expire_all()
    cache = session.get(NewsReadCache, 'research')
    universe = session.get(SecurityUniverseState, 'ssi')
    version = str(universe.last_success_at) if universe else None
    metadata = session.get(NewsReadCache, 'universe_version')
    changed = set(changed) | set(session.exec(select(NewsStory.id).where(NewsStory.read_cache_dirty == True)).all())
    rebuild = bootstrap or metadata is None or metadata.rows != [{'version': version}]
    if not changed and not rebuild and not observations:
        session.rollback()
        return False
    # Older persisted databases bootstrap once in the worker, never in HTTP.
    ids = None if rebuild else changed
    rows = build_research_rows(session, {'limit': 10001}, now=now, story_ids=ids, hours=96, include_future_publication=True) if rebuild or changed else []
    tagger = equity_tagger(session) if rows else None
    eligible = {s.symbol: s for s in tagger.stocks} if tagger else {}
    from copy import deepcopy
    entries = {} if rebuild else {r['row']['story']['id']: r for r in deepcopy(cache.rows)
                                    if r['row']['story']['id'] not in changed}
    for row in rows:
        kinds = {}
        # Fresh validated copies have no shared SQLAlchemy instance state.
        row = type(row).model_validate_json(row.model_dump_json())
        for article in row.articles:
            tags = tagger.tag(article.title, article.category)
            article.tickers = tags.tickers
            article.sectors = sorted(set(article.sectors) | set(tags.sectors))
            kinds[article.id] = research_category(article, [eligible[s] for s in tags.tickers])
        entries[row.story.id] = {'row': row.model_dump(mode='json'), 'categories': kinds}
    # Duplicate observations only update the image retry revision; no tagging,
    # Story aggregation or Hot ranking rebuild is needed.
    for entry in entries.values():
        for article in entry['row']['articles']:
            if observations and article['id'] in observations:
                article['last_seen_at'] = utc(observations[article['id']]).isoformat().replace('+00:00', 'Z')
    # Prune only the derivative cache, never underlying stored evidence.
    # A day of grace preserves Show more snapshots crossing a publication expiry.
    # HTTP still applies its exact 72-hour window; stored evidence is never pruned.
    cutoff = now-timedelta(hours=96)
    entries = {key: entry for key, entry in entries.items() if any(
        datetime.fromisoformat(a['published_at'] or a['first_seen_at']) >= cutoff
        for a in entry['row']['articles'])}
    if len(entries) > 10000:
        entries = dict(sorted(entries.items(), key=lambda pair: max(
            a['published_at'] or a['first_seen_at'] for a in pair[1]['row']['articles']), reverse=True)[:10000])
    cache = cache or NewsReadCache(id='research', updated_at=now)
    cache.rows = list(entries.values())
    cache.updated_at = now
    meaningful = bool(changed or rebuild)
    cache.refresh_count += int(meaningful)
    session.add(cache)
    metadata = metadata or NewsReadCache(id='universe_version', updated_at=now)
    metadata.rows, metadata.updated_at = [{'version': version}], now
    session.add(metadata)
    if changed:
        session.execute(update(NewsStory).where(NewsStory.id.in_(changed))
                        .values(read_cache_dirty=False).execution_options(synchronize_session=False))
    session.commit()
    return meaningful


def research_rows(session, options, category=None, *, hot=False, attention=False, offset=0, now=None):
    from src.news.read import StoryResponse, representative, cluster_thumbnail
    from src.news.service import story_score
    from src.news.research import attention_order
    from src.news.registry import load_sources
    from src.news.scheduling import request_due_refresh
    now = utc(now or datetime.now(timezone.utc))
    request_due_refresh(session, load_sources())
    cache = session.get(NewsReadCache, 'research')
    if cache is None:
        return []  # explicit empty cached state; pending intent does not mean completed
    cutoff = now-timedelta(hours=72)
    output = []
    for entry in cache.rows:
        row = StoryResponse.model_validate(entry['row'])
        members = [a for a in row.articles if utc(a.first_seen_at) <= now and
                   cutoff <= utc(a.published_at or a.first_seen_at) <= now]
        if not members:
            continue
        matching = []
        for article in members:
            kind = entry['categories'].get(article.id)
            if not kind or (category and kind != category):
                continue
            if any(options.get(field) and options[field].casefold() != str(getattr(article, column)).casefold()
                   for field, column in [('country', 'country'), ('source', 'source_id'), ('category', 'category')]):
                continue
            if any(options.get(field) and options[field].casefold() not in {v.casefold() for v in getattr(article, column)}
                   for field, column in [('topic', 'topics'), ('ticker', 'tickers'), ('sector', 'sectors')]):
                continue
            if options.get('financial_only') and not (article.topics or article.tickers or article.sectors):
                continue
            matching.append(article)
        if not matching:
            continue
        count = len({a.publisher_group for a in members})
        if hot and count < 2:
            continue
        chosen = representative(matching, {})
        image = cluster_thumbnail(chosen, members, {})
        if image is None:
            continue
        row.story.source_count, row.story.article_count = count, len(members)
        row.story.last_updated_at = max(a.first_seen_at for a in members)
        row.representative_article = chosen
        row.articles = [chosen, *[a for a in members if a.id != chosen.id]]
        row.thumbnail_url, row.thumbnail_article_id = image.thumbnail_url, image.id
        row.research_category = entry['categories'][chosen.id]
        row.ranking_score = story_score(row.story, now)
        row.ranking_reason = ('Independent publishers first, capped article activity, then latest activity' if hot or attention
                              else 'Latest publication first; earliest source represents each story')
        output.append(row)
    # Recency/window filtering is lightweight and exact, including snapshot pagination.
    order = attention_order if hot or attention else lambda row: (-max(utc(a.published_at or a.first_seen_at).timestamp() for a in row.articles), row.story.id)
    return sorted(output, key=order)[offset:offset+options['limit']]
