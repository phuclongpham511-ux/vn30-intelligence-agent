"""Bounded public HTML adapters. No authenticated endpoints or script execution."""
from datetime import datetime, timezone
import json
import re
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from src.news.normalization import canonical_url, clean_title


def timestamp(raw):
    try:
        value = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        return value.astimezone(timezone.utc) if value.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def item(source, native_id, url, text, published, *, title=None, author=None, tickers=(), context='', kind='post'):
    return dict(id=f'{source}:{kind}:{native_id}', source_id=source, source_item_id=str(native_id),
        item_type=kind, url=url, excerpt=clean_title(text)[:1200], title=clean_title(title)[:200] if title else None,
        author=clean_title(author)[:100] if author else None, published_at=published,
        direct_tickers=sorted(set(tickers)), context_text=context[:200], replies=None, views=None,
        provenance={'access': 'public_no_auth', 'method': 'public_html', 'url': url}, is_fixture=False)


def parse_chungsy_post(data, url):
    if urlsplit(url).hostname != 'chungsy.vn' or not urlsplit(url).path.startswith('/posts/'):
        return []
    text = data.decode('utf-8', errors='replace')
    chunks = []
    for match in re.finditer(r'self\.__next_f\.push\((\[1,\s*"(?:\\.|[^"\\])*"\])\)', text):
        try:
            chunks.append(json.loads(match[1])[1])
        except (ValueError, IndexError):
            continue
    payload = ''.join(chunks)
    for match in re.finditer(r'"initialPostData"\s*:', payload):
        try:
            post, _ = json.JSONDecoder().raw_decode(payload[match.end():].lstrip())
            published = timestamp(post.get('publishDate'))
            identity, body = post.get('postId'), post.get('textContent')
            if not identity or not published or not isinstance(body, str) or not body.strip():
                continue
            if urlsplit(url).path.rstrip('/').split('/')[-1] != identity:
                continue
            tags = [r['symbol'] for r in post.get('mentionedTickers', [])
                if isinstance(r, dict) and r.get('marketType') == 'stock' and isinstance(r.get('symbol'), str)]
            return [item('chungsy_public', identity, url, body, published, author=post.get('user_FullName'), tickers=tags)]
        except (ValueError, TypeError, AttributeError, KeyError):
            continue
    return []


def parse_money_post(data, url):
    identity = re.search(r'-c30a(\d+)\.html$', urlsplit(url).path)
    if urlsplit(url).hostname != '24hmoney.vn' or not identity:
        return []
    soup = BeautifulSoup(data, 'html.parser')
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            record = json.loads(node.string or node.get_text())
            if not isinstance(record, dict):
                continue
            published = timestamp(record.get('datePublished'))
            body = record.get('description')
            blocks = soup.select('.news-content .news-content-block')
            full_text = ' '.join(block.get_text(' ', strip=True) for block in blocks)
            if full_text:
                body = full_text
            if not published or not isinstance(body, str) or not body.strip():
                continue
            tags = []
            for link in soup.select('.stock-relate-news-box a[href]'):
                path = urlsplit(link['href']).path
                match = re.fullmatch(r'/stock/([A-Z0-9]+)', path)
                if match:
                    tags.append(match[1])
            author = soup.select_one('.user-name')
            return [item('money24_public', identity[1], canonical_url(url), body, published,
                title=record.get('headline'), author=author.get_text(' ', strip=True) if author else None, tickers=tags)]
        except (ValueError, TypeError):
            continue
    return []


def parse_f319_posts(data, url, context=''):
    if urlsplit(url).hostname != 'newf319.com' or not urlsplit(url).path.startswith('/threads/'):
        return []
    soup = BeautifulSoup(data, 'html.parser')
    output = {}
    for node in soup.select('li.message[id^="post-"]'):
        identity = re.fullmatch(r'post-(\d+)', node.get('id', ''))
        link, body = node.select_one('.datePermalink'), node.select_one('.messageText')
        if not identity or not link or not body:
            continue
        try:
            published = datetime.strptime(link.get_text(' ', strip=True), '%d/%m/%Y, %H:%M').replace(
                tzinfo=ZoneInfo('Asia/Ho_Chi_Minh')).astimezone(timezone.utc)
        except ValueError:
            continue
        original = urljoin('https://newf319.com/', link.get('href', ''))
        if urlsplit(original).hostname != 'newf319.com' or urlsplit(original).path != urlsplit(url).path:
            continue
        for quote in body.select('.bbCodeBlock, .quote, .signature, script, style'):
            if quote.parent is not None:
                quote.decompose()
        text = body.get_text(' ', strip=True)
        if text:
            output[identity[1]] = item('f319_public', identity[1], canonical_url(original) + '#post-' + identity[1],
                text, published, author=node.get('data-author'), context=context, kind='thread_comment')
    return list(output.values())
