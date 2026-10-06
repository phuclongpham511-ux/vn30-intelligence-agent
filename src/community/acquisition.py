"""Conservative source-specific acquisition from unauthenticated public pages."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
import xml.etree.ElementTree as ET
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from src.community.adapters import parse_chungsy_post, parse_money_post, parse_f319_posts, timestamp
from src.community.service import parse_listing, community_tags
from src.news.normalization import canonical_url


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    interval: int = 15
    enabled: bool = True
    reason: str | None = None


SOURCES = (
    Source('f319_public', 'F319 · newf319.com', 'https://newf319.com/'),
    Source('money24_public', '24HMoney', 'https://24hmoney.vn/'),
    Source('chungsy_public', 'Chứng Sỹ · Vietstock', 'https://chungsy.vn/'),
    Source('fireant_public', 'FireAnt', 'https://fireant.vn/', enabled=False,
        reason='Deferred: no stable unauthenticated discussion feed with item IDs and timestamps was verified.'),
)
USER_AGENT = 'VN30Community/2.0 (bounded public discussion reader)'
MAX_BYTES = 1_000_000


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        # A redirected path has not passed this cycle's robots check.
        raise ValueError('Unexpected public redirect')


def read_public(url):
    # Exactly two public headers; never cookies, user tokens or sessions.
    request = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xml,text/plain'})
    with build_opener(NoRedirects()).open(request, timeout=15) as response:
        if urlsplit(response.url).hostname != urlsplit(url).hostname:
            raise ValueError('Unexpected public redirect')
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Oversized response')
    return data


def acquire(source, stocks, *, read=read_public, sleep=time.sleep, now=None):
    now = now or datetime.now(timezone.utc)
    robots = RobotFileParser()
    robots.parse(read(urljoin(source.url, 'robots.txt')).decode('utf-8').splitlines())
    delay = max(1, robots.crawl_delay(USER_AGENT) or 0)
    if delay > 60:
        raise ValueError('Cadence disallowed')
    calls = 0
    def public(url):
        nonlocal calls
        if calls >= 20 or urlsplit(url).hostname != urlsplit(source.url).hostname or not robots.can_fetch(USER_AGENT, url):
            raise ValueError('Public access limit or robots restriction')
        sleep(delay)
        calls += 1
        data = read(url)
        if b'cf-chl-' in data or b'Just a moment...' in data:
            raise ValueError('Upstream challenge')
        return data
    rows, threads = [], []
    if source.id == 'chungsy_public':
        root = ET.fromstring(public(urljoin(source.url, 'posts/sitemap.xml')))
        entries = root.findall('{*}url')
        if not entries:
            raise ValueError('Public post sitemap unavailable')
        for entry in entries[:12]:
            loc = entry.find('{*}loc')
            modified_node = entry.find('{*}lastmod')
            modified = timestamp(modified_node.text if modified_node is not None else None)
            if loc is not None and loc.text and modified and now - timedelta(days=1) <= modified <= now:
                url = loc.text.strip()
                parsed = parse_chungsy_post(public(url), url)
                rows.extend(parsed)
        if not rows:
            raise ValueError('No parseable public discussion items')
    elif source.id == 'money24_public':
        soup = BeautifulSoup(public(source.url), 'html.parser')
        links = list(dict.fromkeys(urlsplit(urljoin(source.url, a['href']))._replace(query='',fragment='').geturl() for a in soup.select('a[href]')
            if re.search(r'-c30a\d+\.html', a['href'])))
        if not links:
            raise ValueError('Public community listing unavailable')
        for url in links[:12]:
            parsed = parse_money_post(public(url), url)
            rows.extend(parsed)
        if not rows:
            raise ValueError('No parseable public discussion items')
    elif source.id == 'f319_public':
        threads = parse_listing(public(source.url))
        # Prefer confidently tagged titles, while still sampling general discussion.
        threads.sort(key=lambda r: (not bool(community_tags(r['title'], stocks)[0]),
            -(r['activity_at'].timestamp() if r['activity_at'] else 0), r['id']))
        for thread in threads[:6]:
            data, url = public(thread['url']), thread['url']
            nav = BeautifulSoup(data, 'html.parser').select_one('.PageNav[data-last][data-baseurl]')
            if nav and nav['data-last'].isdigit() and int(nav['data-last']) > 1:
                url = urljoin(source.url, nav['data-baseurl'].replace('{{sentinel}}', nav['data-last']))
                if not urlsplit(url).path.startswith(urlsplit(thread['url']).path):
                    raise ValueError('Unexpected thread pagination')
                data = public(url)
            parsed = parse_f319_posts(data, url, thread['title'])
            if not parsed:
                raise ValueError('Public comment format changed')
            rows.extend(parsed)
    else:
        raise ValueError('Source not integrated')
    return rows, threads
