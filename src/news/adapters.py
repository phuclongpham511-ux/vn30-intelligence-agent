"""Only adapters know feed formats. Descriptions/content are never returned or saved."""
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from src.news.normalization import canonical_url, clean_title, parse_time
from src.news.registry import Source

MAX_FEED_BYTES = 3_000_000


@dataclass(frozen=True)
class ArticleInput:
    title: str
    url: str
    published_at: datetime | None


def fetch_feed(source: Source) -> bytes:
    request = Request(str(source.endpoint), headers={'User-Agent': 'VN30News/1.0 (public RSS metadata reader)', 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'})
    with urlopen(request, timeout=20) as response:
        data = response.read(MAX_FEED_BYTES + 1)
    if len(data) > MAX_FEED_BYTES:
        raise ValueError('Feed exceeds size limit')
    return data


def parse_feed(data: bytes, source: Source) -> list[ArticleInput]:
    if len(data) > MAX_FEED_BYTES or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Unsafe or oversized feed')
    # VietnamBiz declares UTF-16 but delivers UTF-8 bytes.
    if source.source_id == 'vietnambiz':
        data = data.decode('utf-8-sig').replace('encoding="utf-16"', 'encoding="utf-8"', 1).encode()
    root = ET.fromstring(data.strip())
    atom = '{http://www.w3.org/2005/Atom}'
    if root.tag not in ('rss', atom + 'feed', '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF'):
        raise ValueError('Expected RSS or Atom, not an HTML challenge')
    nodes = root.findall('./channel/item') + root.findall(atom + 'entry') + root.findall('{http://purl.org/rss/1.0/}item')
    items = []
    for node in nodes[:500]:
        def value(name):
            return node.findtext(name) or node.findtext(atom + name) or node.findtext('{http://purl.org/rss/1.0/}' + name)
        title = clean_title(value('title') or '')
        link = value('link')
        if node.tag == atom + 'entry':
            link = next((n.get('href') for n in node.findall(atom + 'link') if n.get('rel', 'alternate') == 'alternate'), None)
        if not title or not link:
            continue
        try:
            url = canonical_url(link)
        except ValueError:
            continue
        date = value('pubDate') or value('published') or node.findtext('{http://purl.org/dc/elements/1.1/}date')
        # Atom updated is not necessarily the original publication time.
        if source.source_id == 'tuoitre' and date:
            try:
                published = datetime.strptime(' '.join(date.split()), '%m/%d/%Y %I:%M:%S %p').replace(tzinfo=ZoneInfo(source.timezone))
            except ValueError:
                published = parse_time(date, source.timezone)
        else:
            if source.source_id == 'vietnambiz' and date:
                date = date.replace('GMT+7', '+0700')
            published = parse_time(date, source.timezone)
        items.append(ArticleInput(title, url, published))
    return items


ADAPTERS = {'RSS': lambda source: parse_feed(fetch_feed(source), source)}


def acquire(source: Source) -> list[ArticleInput]:
    if source.method not in ADAPTERS:
        raise ValueError('No adapter registered for source method')
    return ADAPTERS[source.method](source)
