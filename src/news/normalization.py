import hashlib
import html
import re
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def normalized(text: str) -> str:
    text = unicodedata.normalize('NFKD', text.casefold()).replace('đ', 'd')
    return ' '.join(re.findall(r'[a-z0-9]+', ''.join(c for c in text if not unicodedata.combining(c))))


def clean_title(value: str) -> str:
    return ' '.join(re.sub(r'<[^>]+>', '', html.unescape(value)).split())[:1000]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def canonical_url(value: str) -> str:
    p = urlsplit(value.strip())
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        raise ValueError('Invalid publisher URL')
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith('utm_') and k.lower() not in {'fbclid', 'gclid', 'ref', 'referrer'}]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', urlencode(sorted(query)), ''))


def parse_time(value: str | None, source_timezone: str = 'UTC') -> datetime | None:
    if not value:
        return None
    try:
        try:
            result = parsedate_to_datetime(value)
        except (ValueError, TypeError):
            result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            result = result.replace(tzinfo=ZoneInfo(source_timezone))
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None
