from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from sqlmodel import select
from src.models import Stock
from src.news.models import NewsArticle, NewsStory
from src.community.models import CommunityThread
from src.community.service import acquire, parse_listing, community_tags, ingest, pulse, SOURCE_ID

NOW = datetime(2026, 10, 4, 10, tzinfo=timezone.utc)
PAYLOAD = Path('tests/fixtures/community/listing.html').read_bytes()


def test_public_listing_metadata_and_stable_urls():
    rows = parse_listing(PAYLOAD)
    assert len(rows) == 1
    assert rows[0]['id'] == SOURCE_ID + ':22'
    assert rows[0]['url'] == 'https://newf319.com/threads/discussion.22/'
    assert rows[0]['replies'] == 1234 and rows[0]['views'] == 12345
    assert rows[0]['published_at'].tzinfo == timezone.utc
    assert parse_listing(PAYLOAD.replace(b'1.234', b'unknown'))[0]['replies'] is None
    assert parse_listing(PAYLOAD.replace(b'threads/discussion.22/', b'https://evil.example/threads/discussion.22/')) == []
    with pytest.raises(ValueError): parse_listing(b'<html>Login or CAPTCHA</html>')


def test_robots_fail_closed_and_bounded_access(monkeypatch):
    calls = []
    def read(url):
        calls.append(url)
        return b'User-agent: *\nDisallow: /' if url.endswith('robots.txt') else PAYLOAD
    monkeypatch.setattr('src.community.service.read_public', read)
    with pytest.raises(ValueError): acquire()
    assert len(calls) == 1
    monkeypatch.setattr('src.community.service.read_public', lambda url: b'User-agent: *\nAllow: /' if url.endswith('robots.txt') else PAYLOAD)
    assert len(acquire()) == 1


def test_discussion_relevance_requires_explicit_context():
    stocks = [Stock(symbol='XYZ', company_name='Example Company')]
    assert community_tags('XYZ and ABC chatter', stocks)[0] == []
    assert community_tags('Cổ phiếu XYZ lợi nhuận tăng', stocks) == (['XYZ'], ['Earnings', 'Equities'])
    assert community_tags('$XYZ discussion', stocks)[0] == ['XYZ']
    assert community_tags('Example Company earnings', stocks)[0] == ['XYZ']
    assert community_tags('Example Industries (XYZ) discussion', [Stock(symbol='XYZ', company_name='Example Industries Group')])[0] == ['XYZ']
    assert community_tags('XYZ discussion', [Stock(symbol='XYZ', company_name='XYZ Corporation')])[0] == []


def test_idempotent_sample_metrics_and_source_isolation(session, client):
    session.add(Stock(symbol='XYZ', company_name='Example Company')); session.commit()
    rows = parse_listing(PAYLOAD)
    assert ingest(session, fetch=lambda: rows, now=NOW)['status'] == 'ok'
    assert ingest(session, fetch=lambda: rows, now=NOW + timedelta(minutes=1))['status'] == 'skipped'
    assert ingest(session, fetch=lambda: rows, now=NOW + timedelta(minutes=31))['status'] == 'ok'
    assert len(session.exec(select(CommunityThread)).all()) == 1
    assert not session.exec(select(NewsArticle)).all() and not session.exec(select(NewsStory)).all()
    data = pulse(session, now=NOW + timedelta(minutes=32))
    assert data['most_discussed'] == [{'ticker': 'XYZ', 'thread_count': 1}]
    assert data['threads'][0].first_seen_at.replace(tzinfo=timezone.utc) == NOW
    assert pulse(session, ticker='UNKNOWN', now=NOW)['threads'] == []
    def fail(): raise TimeoutError('private response must not be stored')
    ingest(session, fetch=fail, now=NOW + timedelta(hours=1, minutes=2))
    assert pulse(session, now=NOW + timedelta(hours=1, minutes=2))['source']['status'] == 'error'
    assert pulse(session, now=NOW + timedelta(hours=1, minutes=2))['source']['last_error'] == 'TimeoutError'
    assert client.get('/news/latest').status_code == 200
    assert client.get('/community/pulse').status_code == 200


def test_empty_unattempted_and_stale_are_distinct(session):
    assert pulse(session, now=NOW)['source']['status'] == 'not_attempted'
    ingest(session, fetch=lambda: [], now=NOW)
    assert pulse(session, now=NOW)['source']['status'] == 'healthy'
    assert pulse(session, now=NOW + timedelta(hours=2))['source']['status'] == 'stale'
