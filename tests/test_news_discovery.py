from datetime import datetime, timedelta, timezone

from src.models import Stock
from src.news.models import NewsSourceState, NewsArticle, NewsStory
from tests.test_news import source, item, ingest
from src.news.tagging import Tagger, Tags
from src.news.normalization import utc
from sqlmodel import select


def test_source_status_is_explicit_without_exposing_feed_payload(client, session, monkeypatch):
    now = datetime.now(timezone.utc)
    feeds = [source('fresh'), source('stale'), source('failed'), source('new'), source('off', enabled=False)]
    monkeypatch.setattr('routers.news.load_sources', lambda: feeds)
    session.add_all([
        NewsSourceState(source_id='fresh', last_attempt_at=now, last_success_at=now, articles_received=5),
        NewsSourceState(source_id='stale', last_attempt_at=now-timedelta(hours=2), last_success_at=now-timedelta(hours=2)),
        NewsSourceState(source_id='failed', last_attempt_at=now, last_success_at=now-timedelta(hours=1), last_error='TimeoutError'),
    ])
    session.commit()
    response = client.get('/news/sources')
    assert response.status_code == 200
    rows = {row['source_id']: row for row in response.json()}
    assert {sid: row['status'] for sid, row in rows.items()} == {
        'fresh': 'healthy', 'stale': 'stale', 'failed': 'error', 'new': 'not_attempted', 'off': 'disabled',
    }
    assert rows['new']['last_success_at'] is None
    assert rows['new']['articles_received'] is None
    assert rows['failed']['last_success_at'] is not None
    assert rows['fresh']['articles_received'] == 5
    assert all('endpoint' not in row and 'body' not in row for row in rows.values())


def test_discovery_filters_apply_consistently_without_watchlist(client, session):
    now = datetime.now(timezone.utc)
    session.add_all([Stock(symbol='XYZ', sector='Technology'), Stock(symbol='ABC', sector='Financials')])
    session.commit()
    ingest(session, [item('XYZ earnings rise', 'https://one.example/xyz', now)], now=now)
    ingest(session, [item('ABC bank earnings rise', 'https://two.example/abc', now)], sources=[source('two')], now=now)
    query = '?ticker=xyz&sector=technology&source=one&country=VN&topic=Earnings&limit=1'
    latest = client.get('/news/latest' + query).json()
    top = client.get('/news/top' + query).json()
    topics = client.get('/news/topics/trending' + query).json()
    assert len(latest) == len(top) == len(topics) == 1
    assert latest[0]['tickers'] == ['XYZ']
    assert top[0]['articles'][0]['id'] == latest[0]['id']
    assert topics[0]['topic'] == 'Earnings'
    assert client.get('/news/latest?ticker=UNSEEN').json() == []


def test_financial_view_preserves_unclassified_articles_in_full_feed(client, session):
    now = datetime.now(timezone.utc)
    ingest(session, [item('Lottery jackpot winner', 'https://one.example/lottery', now),
                     item('Interest rates rise', 'https://one.example/rates', now)], now=now)
    assert len(client.get('/news/latest').json()) == 2
    financial = client.get('/news/latest?financial_only=true').json()
    assert [row['title'] for row in financial] == ['Interest rates rise']
    assert len(client.get('/news/top?financial_only=true').json()) == 1
    assert client.get('/news/latest?financial_only=true&topic=Gold').json() == []


def test_ambiguous_food_and_charity_terms_are_not_financial_tags():
    tagger = Tagger()
    assert tagger.tag('Amsterdam chip shop lands in court', 'GLOBAL').topics == []
    assert tagger.tag('New baby bank open to everybody', 'GLOBAL').topics == []
    assert tagger.tag('New baby bank open to everybody', 'GLOBAL').sectors == []
    assert 'Semiconductors' in tagger.tag('Computer chip demand rises', 'GLOBAL').topics
    assert 'Banking' in tagger.tag('Commercial bank expands lending', 'GLOBAL').topics


def test_repeat_ingestion_refreshes_derived_tags_without_renewing_story_activity(session):
    now = datetime.now(timezone.utc)
    class OldTagger:
        def tag(self, title, category):
            return Tags(['Semiconductors'], [], [], 'MARKET')
    feed = [source('local')]
    rows = [item('Amsterdam chip shop lands in court', 'https://global.example/chips', now)]
    ingest(session, rows, sources=feed, now=now, tagger=OldTagger())
    original = session.exec(select(NewsArticle)).one()
    identifier, story_id = original.id, original.story_id
    ingest(session, rows, sources=feed, now=now+timedelta(minutes=30), tagger=Tagger())
    article = session.exec(select(NewsArticle)).one()
    story = session.get(NewsStory, story_id)
    assert article.id == identifier and article.topics == [] and story.topics == []
    assert utc(article.first_seen_at) == utc(article.published_at) == now
    assert utc(article.last_seen_at) == now+timedelta(minutes=30)
    assert utc(story.last_updated_at) == now
    assert story.article_count == story.source_count == 1
