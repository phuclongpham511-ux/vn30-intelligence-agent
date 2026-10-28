"""One bounded public listing; no post bodies, pagination, profiles or private APIs."""
from datetime import datetime, timedelta, timezone
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from sqlmodel import select
from src.community.models import CommunityThread, CommunitySourceState, CommunityThreadObservation
from src.models import Stock
from src.news.normalization import canonical_url, clean_title, utc
from src.news.tagging import Tagger, contains
from src.services.ingestion_owner import collector_owned

SOURCE_ID = 'f319_public'
SOURCE_NAME = 'F319 · newf319.com'
ENDPOINT = 'https://newf319.com/'
USER_AGENT = 'VN30Community/1.0 (public thread metadata reader)'
POLL_MINUTES = 30
MAX_BYTES = 1_000_000


def read_public(url):
    request = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,text/plain'})
    with urlopen(request, timeout=15) as response:
        if urlsplit(response.url).hostname != urlsplit(ENDPOINT).hostname:
            raise ValueError('Unexpected redirect')
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Oversized response')
    return data


def acquire():
    # Re-check restrictions each cycle. Failure to read robots fails closed.
    robots = RobotFileParser()
    robots.parse(read_public(urljoin(ENDPOINT, 'robots.txt')).decode('utf-8').splitlines())
    if not robots.can_fetch(USER_AGENT, ENDPOINT):
        raise ValueError('Access disallowed')
    delay = robots.crawl_delay(USER_AGENT)
    if delay and delay > 60:
        raise ValueError('Cadence disallowed')
    if delay:
        import time
        time.sleep(delay)
    return parse_listing(read_public(ENDPOINT))


def public_time(node):
    if not node:
        return None
    raw = node.get('data-time')
    try:
        if raw:
            return datetime.fromtimestamp(int(raw), timezone.utc)
        from zoneinfo import ZoneInfo
        date = node.get('title') or node.get_text(' ', strip=True)
        for fmt in ('%d/%m/%Y lúc %H:%M', '%d/%m/%Y'):
            try:
                return datetime.strptime(date, fmt).replace(tzinfo=ZoneInfo('Asia/Ho_Chi_Minh')).astimezone(timezone.utc)
            except ValueError:
                continue
    except (ValueError, OverflowError, OSError):
        pass
    return None


def count(node):
    if node is None:
        return None
    text = node.get_text('', strip=True)
    return int(text.replace('.', '').replace(',', '')) if re.fullmatch(r'\d+(?:[.,]\d{3})*', text) else None


def parse_listing(data):
    if len(data) > MAX_BYTES:
        raise ValueError('Oversized listing')
    soup = BeautifulSoup(data, 'html.parser')
    nodes = soup.select('.discussionListItem')
    if not nodes:
        raise ValueError('No public thread listing; possible challenge or format change')
    output = {}
    for node in nodes[:50]:
        if 'sticky' in node.get('class', []):
            continue
        link = node.select_one('h3.title a[href]')
        identity = re.fullmatch(r'thread-(\d+)', node.get('id', ''))
        if not link or not identity:
            continue
        url = canonical_url(urljoin(ENDPOINT, link['href']))
        if urlsplit(url).hostname != 'newf319.com' or not urlsplit(url).path.startswith('/threads/'):
            continue
        thread_id = identity.group(1)
        if not re.search(r'\.' + thread_id + r'/$', urlsplit(url).path):
            continue
        title = clean_title(link.get_text(' ', strip=True))
        if not title:
            continue
        output[thread_id] = dict(id=SOURCE_ID + ':' + thread_id, source_id=SOURCE_ID,
            title=title, url=url, author=node.get('data-author'),
            published_at=public_time(node.select_one('.startDate .DateTime')),
            activity_at=public_time(node.select_one('.lastPostInfo .DateTime')),
            replies=count(node.select_one('.stats .major dd')),
            views=count(node.select_one('.stats .minor dd')))
    return list(output.values())


def community_tags(title, stocks):
    # Reuse dictionaries/company aliases, but bare uppercase tokens alone are too ambiguous.
    from src.news.normalization import normalized
    aliases = {}
    for stock in stocks:
        name = normalized(stock.company_name or '')
        short = re.sub(r'^(?:ctcp|cong ty co phan|tap doan) ', '', name)
        short = re.sub(r' (?:group|corporation|corp|limited|ltd|inc)$', '', short)
        # Multi-word company identity plus an explicit parenthesized known ticker.
        # Single-word truncations (e.g. an ambiguous ticker) are never aliases.
        aliases[stock.symbol] = [short] if len(short.split()) >= 2 else []
    tags = Tagger(stocks, company_aliases=aliases).tag(title, 'VN')
    text = normalized(title)
    tickers = []
    for stock in stocks:
        explicit = re.search(r'(?:\$|#)' + re.escape(stock.symbol) + r'\b', title) or re.search(
            r'(?:cổ phiếu|mã|ticker|stock)\s*[:\-]?\s*' + re.escape(stock.symbol) + r'\b', title, re.I)
        company = stock.company_name and contains(text, stock.company_name)
        named_ticker = any(contains(text, name) for name in aliases[stock.symbol]) and bool(re.search(r'\(' + re.escape(stock.symbol) + r'\)', title))
        if stock.symbol in tags.tickers and (explicit or company or named_ticker):
            tickers.append(stock.symbol)
    return sorted(tickers), tags.topics


@collector_owned
def ingest(session, *, fetch=acquire, now=None):
    supplied_now = now
    now = utc(now or datetime.now(timezone.utc))
    state = session.get(CommunitySourceState, SOURCE_ID)
    if state and state.last_attempt_at and utc(state.last_attempt_at) > now - timedelta(minutes=POLL_MINUTES):
        return {'status': 'skipped'}
    state = state or CommunitySourceState(source_id=SOURCE_ID)
    state.last_attempt_at = now
    session.add(state); session.commit()
    try:
        incoming = fetch()
        observed_at = utc(supplied_now or datetime.now(timezone.utc))
        stocks = session.exec(select(Stock)).all()
        for row in incoming:
            existing = session.get(CommunityThread, row['id'])
            tickers, topics = community_tags(row['title'], stocks)
            thread = existing or CommunityThread(**row, first_seen_at=observed_at, last_seen_at=observed_at)
            for field, value in row.items():
                setattr(thread, field, value)
            thread.last_seen_at, thread.tickers, thread.topics = observed_at, tickers, topics
            session.add(thread)
            session.flush()  # parent exists before the observation foreign key
            session.add(CommunityThreadObservation(thread_id=thread.id,
                observed_at=observed_at, replies=thread.replies, views=thread.views))
        state = state or CommunitySourceState(source_id=SOURCE_ID)
        state.last_attempt_at, state.last_success_at = now, observed_at
        state.last_error, state.threads_received = None, len(incoming)
        session.add(state)
        session.commit()
        return {'status': 'ok', 'received': len(incoming)}
    except Exception as exc:
        session.rollback()
        state = session.get(CommunitySourceState, SOURCE_ID) or CommunitySourceState(source_id=SOURCE_ID)
        state.last_attempt_at, state.last_error = now, type(exc).__name__
        session.add(state)
        session.commit()
        return {'status': 'error', 'error': state.last_error}


def source_status(session, *, now=None):
    now = utc(now or datetime.now(timezone.utc))
    state = session.get(CommunitySourceState, SOURCE_ID)
    status = 'not_attempted' if not state or not state.last_attempt_at else 'error' if state.last_error else 'stale' if not state.last_success_at or utc(state.last_success_at) < now - timedelta(minutes=2 * POLL_MINUTES) else 'healthy'
    return dict(source_id=SOURCE_ID, name=SOURCE_NAME, url=ENDPOINT,
        status=status, poll_interval_minutes=POLL_MINUTES,
        last_attempt_at=utc(state.last_attempt_at) if state and state.last_attempt_at else None,
        last_success_at=utc(state.last_success_at) if state and state.last_success_at else None,
        last_error=state.last_error if state else None,
        threads_received=state.threads_received if state and state.last_attempt_at else None)


def pulse(session, *, ticker=None, topic=None, now=None):
    now = utc(now or datetime.now(timezone.utc))
    ticker = ticker.strip().upper() if ticker else None
    source = source_status(session, now=now)
    rows = session.exec(select(CommunityThread).where(CommunityThread.last_seen_at >= now - timedelta(hours=72))).all()
    rows = [r for r in rows if (not ticker or ticker.upper() in r.tickers) and (not topic or topic in r.topics)]
    from collections import Counter
    tickers = Counter(t for row in rows for t in row.tickers)
    topics = Counter(t for row in rows for t in row.topics)
    # Lifetime replies are an exposed activity level, never a rate or recent reply count.
    rows.sort(key=lambda r: (-(r.replies if r.replies is not None else -1), -utc(r.activity_at or r.last_seen_at).timestamp(), r.id))
    def utc_row(row):
        return row.model_copy(update={f: utc(getattr(row, f)) if getattr(row, f) else None for f in ('published_at', 'activity_at', 'first_seen_at', 'last_seen_at')})
    return dict(as_of=now, source=dict(id=SOURCE_ID, **source),
        sampled_threads=len(rows), most_discussed=[dict(ticker=t, thread_count=n) for t,n in sorted(tickers.items(), key=lambda x:(-x[1],x[0]))],
        topics=[dict(topic=t, thread_count=n) for t,n in sorted(topics.items(), key=lambda x:(-x[1],x[0]))], threads=[utc_row(r) for r in rows[:20]])
