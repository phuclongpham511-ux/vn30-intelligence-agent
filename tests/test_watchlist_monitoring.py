from datetime import datetime, timedelta, timezone

from src.models import Stock
from src.news.models import NewsArticle
from sqlmodel import select
from tests.test_news import ingest, item, source


def test_monitoring_matches_ticker_tags_and_counts_stories_not_articles(client, session):
    now = datetime.now(timezone.utc)
    session.add_all([Stock(symbol='XYZ'), Stock(symbol='ABC'), Stock(symbol='EMPTY')])
    session.commit()
    title = 'XYZ earnings rise after quarterly results'
    ingest(session, [item(title, 'https://one.example/xyz', now)], now=now)
    ingest(session, [item(title, 'https://two.example/xyz', now)], sources=[source('two')], now=now)
    ingest(session, [item('ABC bank earnings rise', 'https://one.example/abc', now)], now=now)
    response = client.post('/watchlists/monitoring', json={'symbols': [' xyz ', 'EMPTY', 'XYZ']})
    assert response.status_code == 200
    rows = response.json()['stocks']
    assert [row['symbol'] for row in rows] == ['XYZ', 'EMPTY']
    assert rows[0]['status'] == 'ready'
    assert len(rows[0]['developments']) == 1
    story = rows[0]['developments'][0]
    assert len(story['articles']) == story['source_count'] == 2
    assert all('XYZ' in article['tickers'] for article in story['articles'])
    assert all(article['first_seen_at'].endswith('Z') for article in story['articles'])
    assert rows[1]['status'] == 'ready' and rows[1]['developments'] == []
    assert len(client.get('/news/latest?ticker=XYZ').json()) == 2


def test_monitoring_only_recent_ingestion_no_sector_or_global_inference(client, session):
    now = datetime.now(timezone.utc)
    session.add_all([Stock(symbol='XYZ', sector='Technology'), Stock(symbol='ABC', sector='Technology')])
    session.commit()
    ingest(session, [item('XYZ earnings rise', 'https://one.example/old', now-timedelta(days=4))], now=now-timedelta(days=4))
    ingest(session, [item('ABC earnings rise', 'https://one.example/abc', now)], now=now)
    ingest(session, [item('Global technology shares rise', 'https://global.example/tech', now)], sources=[source('global', category='GLOBAL')], now=now)
    rows = client.post('/watchlists/monitoring', json={'symbols': ['XYZ']}).json()['stocks']
    assert rows[0]['developments'] == []


def test_monitoring_unavailable_stock_is_distinct_from_no_change(client):
    data = client.post('/watchlists/monitoring', json={'symbols': ['MISSING']}).json()
    assert data['stocks'][0]['status'] == 'unavailable'
    assert data['stocks'][0]['developments'] is None
    assert client.post('/watchlists/monitoring', json={'symbols': []}).json()['stocks'] == []
    assert client.post('/watchlists/monitoring', json={'symbols': ['BAD!']}).status_code == 422


def test_repeated_ingestion_does_not_create_a_new_development(client, session):
    now = datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ')); session.commit()
    feed = [item('XYZ earnings rise', 'https://one.example/xyz', now)]
    ingest(session, feed, now=now-timedelta(minutes=10))
    before = client.post('/watchlists/monitoring', json={'symbols': ['XYZ']}).json()['stocks'][0]['developments']
    ingest(session, feed, now=now)
    after = client.post('/watchlists/monitoring', json={'symbols': ['XYZ']}).json()['stocks'][0]['developments']
    assert [(row['story_id'], row['first_seen_at']) for row in before] == [
        (row['story_id'], row['first_seen_at']) for row in after]


def test_monitoring_shared_story_uses_matching_evidence_first_seen(client, session):
    now = datetime.now(timezone.utc)
    session.add_all([Stock(symbol='XYZ'), Stock(symbol='ABC')]); session.commit()
    ingest(session, [item('XYZ earnings rise', 'https://one.example/xyz', now)], now=now)
    article = session.exec(select(NewsArticle)).one()
    article.tickers = ['XYZ', 'ABC']; session.add(article); session.commit()
    rows = client.post('/watchlists/monitoring', json={'symbols': ['XYZ', 'ABC']}).json()['stocks']
    assert rows[0]['developments'][0]['story_id'] == rows[1]['developments'][0]['story_id']
    assert rows[0]['developments'][0]['first_seen_at'].startswith(now.isoformat()[:19])
