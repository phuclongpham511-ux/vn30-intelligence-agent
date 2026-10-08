from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import pytest
from sqlmodel import select
from src.models import Stock
from src.news.adapters import ArticleInput, parse_feed, fetch_feed
from src.news.models import NewsArticle, NewsStory, NewsSourceState
from src.news.registry import Source, load_sources
from src.news.normalization import parse_time, normalized, canonical_url, utc
from src.news.tagging import Tagger, Tags
from src.news.matching import LexicalStoryMatcher
from src.news.service import ingest_cycle, story_score, trending, articles

NOW = datetime(2026, 10, 4, 10, tzinfo=timezone.utc)


def source(sid='one', **kw):
    args = dict(source_id=sid, name=sid.title(), endpoint=f'https://{sid}.example/rss',
        country='VN', language='vi', category='VN', publisher_group=sid, timezone='Asia/Ho_Chi_Minh')
    args.update(kw)
    return Source(**args)


def item(title='ABC bank profit rises 2026', url='https://one.example/a', published=NOW):
    return ArticleInput(title, url, published)


def ingest(session, inputs, sources=None, now=NOW, **kw):
    return ingest_cycle(session, sources or [source()], now=now, force=True, fetch=lambda _: inputs, **kw)


def test_feed_normalizes_without_retaining_body():
    rows = parse_feed(Path('tests/fixtures/news/feed.xml').read_bytes(), source())
    assert len(rows) == 2
    assert rows[0].url == 'https://example.org/news/1'
    assert rows[0].published_at == datetime(2026, 10, 4, 5, tzinfo=timezone.utc)
    assert rows[1].published_at is None
    assert 'SECRET' not in str([asdict(a) for a in rows])


def test_mocked_http_and_size_limit(monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size): return Path('tests/fixtures/news/feed.xml').read_bytes()
    calls = []
    def open_(request, timeout, context):
        import ssl
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        calls.append((request.full_url, timeout))
        return Response()
    monkeypatch.setattr('src.news.adapters.urlopen', open_)
    assert len(parse_feed(fetch_feed(source()), source())) == 2
    assert calls == [('https://one.example/rss', 20)]
    monkeypatch.setattr('src.news.adapters.MAX_FEED_BYTES', 1)
    with pytest.raises(ValueError): fetch_feed(source())


def test_compressed_feed_is_bounded_after_expansion(monkeypatch):
    import gzip
    payload = Path('tests/fixtures/news/feed.xml').read_bytes()
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size): return gzip.compress(payload)
    monkeypatch.setattr('src.news.adapters.urlopen', lambda *args, **kw: Response())
    assert len(parse_feed(fetch_feed(source()), source())) == 2
    payload = b' ' * 10_000
    monkeypatch.setattr('src.news.adapters.MAX_FEED_BYTES', 1_000)
    with pytest.raises(ValueError, match='Expanded feed exceeds size limit'):
        fetch_feed(source())


@pytest.mark.parametrize('payload', [b'<html>Challenge</html>', b'<!DOCTYPE rss><rss/>', b'<!ENTITY e "x"><rss/>'])
def test_unsafe_feeds_rejected(payload):
    with pytest.raises(ValueError): parse_feed(payload, source())


def test_atom_publication_semantics():
    payload = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Gold</title><link href="https://example.org/a"/><updated>2026-10-04T10:00:00Z</updated></entry></feed>'
    assert parse_feed(payload, source())[0].published_at is None
    assert parse_feed(payload.replace(b'<updated>', b'<published>').replace(b'</updated>', b'</published>'), source())[0].published_at == NOW


@pytest.mark.parametrize('sid,date,expected', [
    ('tuoitre', '10/4/2026 5:38:00\u202fPM', '2026-10-04T10:38:00+00:00'),
    ('baochinhphu', '10/8/2026 12:54:00 PM', '2026-10-08T05:54:00+00:00'),
    ('vietnambiz', 'Sat, 03 Oct 2026 15:12:54 GMT+7', '2026-10-03T08:12:54+00:00'),
])
def test_publisher_date_adapters(sid, date, expected):
    payload = f'<rss><channel><item><title>Stocks</title><link>https://example.org/a</link><pubDate>{date}</pubDate></item></channel></rss>'.encode()
    if sid == 'vietnambiz': payload = b'<?xml version="1.0" encoding="utf-16"?>' + payload
    result = parse_feed(payload, source(sid))[0]
    assert utc(result.published_at).isoformat() == expected


def test_normalization():
    assert normalized('  LÃI SUẤT – tăng! ') == 'lai suat tang'
    assert canonical_url('https://Example.org/a?b=2&utm_campaign=x&a=1#more') == 'https://example.org/a?a=1&b=2'
    assert parse_time('2026-10-04T17:00:00', 'Asia/Ho_Chi_Minh') == NOW
    assert parse_time('bad') is None
    with pytest.raises(ValueError): canonical_url('https://user:password@example.org/a')


def test_registry_reload_and_unique_ids(tmp_path):
    entries = [source().model_dump(mode='json')]
    file = tmp_path / 'sources.json'
    file.write_text(json.dumps(entries))
    assert load_sources(str(file))[0].enabled
    entries[0]['enabled'] = False
    file.write_text(json.dumps(entries))
    assert not load_sources(str(file))[0].enabled
    file.write_text(json.dumps(entries * 2))
    with pytest.raises(ValueError): load_sources(str(file))
    assert len([s for s in load_sources() if s.category == 'VN']) >= 10
    assert not [s for s in load_sources() if s.category != 'VN' or s.country != 'VN']


def test_idempotent_urls_titles_and_timestamps(session):
    published = NOW - timedelta(hours=2)
    ingest(session, [item(published=published)])
    ingest(session, [item(url='https://one.example/a?utm_source=x', published=published), item(url='https://one.example/reprinted', published=published)], now=NOW+timedelta(minutes=30))
    rows = session.exec(select(NewsArticle)).all()
    assert len(rows) == 1
    a = rows[0]
    assert utc(a.published_at) == published
    assert utc(a.first_seen_at) == NOW
    assert utc(a.last_seen_at) == NOW + timedelta(minutes=30)
    s = session.get(NewsStory, a.story_id)
    assert s.article_count == 1
    assert utc(s.last_updated_at) == NOW  # polling is not renewed story activity
    assert session.get(NewsSourceState, 'one').articles_received == 2


def test_cross_source_story_and_independent_diversity(session):
    ingest(session, [item()])
    ingest(session, [item(url='https://two.example/a')], sources=[source('two', publisher_group='one')])
    ingest(session, [item(url='https://three.example/a')], sources=[source('three')])
    stories = session.exec(select(NewsStory)).all()
    assert len(stories) == 1
    assert stories[0].article_count == 3
    assert stories[0].source_count == 2


def test_story_matching_threshold_time_numbers():
    matcher = LexicalStoryMatcher()
    s = NewsStory(id='a', representative_title='Federal Reserve cuts interest rates', first_seen_at=NOW, topics=['Rates'])
    tags = Tags(['Rates'], [], [], 'GLOBAL')
    assert matcher.match('Federal Reserve cuts interest rates again', tags, [s], NOW) is s
    assert matcher.match('Oil prices rise after supply disruption', tags, [s], NOW) is None
    assert matcher.match(s.representative_title, tags, [s], NOW+timedelta(hours=73)) is None
    s.representative_title = 'ABC bank profit 2025'
    assert matcher.match('ABC bank profit 2026', tags, [s], NOW) is None
    assert LexicalStoryMatcher(similarity_threshold=2).match(s.representative_title, tags, [s], NOW) is None


def test_dynamic_ticker_alias_sector_and_global_tagging(session):
    stock = Stock(symbol='XYZ', company_name='Example Technology', sector='Technology')
    session.add(stock);session.commit()
    tagger = Tagger([stock], company_aliases={'XYZ': ['Example Tech']})
    tags = tagger.tag('XYZ và Example Tech tăng doanh thu', 'VN')
    assert tags.tickers == ['XYZ'] and tags.sectors == ['Technology'] and tags.scope == 'COMPANY'
    assert 'Earnings' in tags.topics
    assert tagger.tag('example tech posts earnings', 'VN').tickers == ['XYZ']
    assert not tagger.tag('xyz is an unrelated word', 'VN').tickers
    assert tagger.tag('Gold prices rise on Fed rate cut', 'GLOBAL').scope == 'GLOBAL'
    assert tagger.tag('Local parade and celebrity marriage', 'GLOBAL').topics == []
    assert Tagger().tag('Ngân hàng tăng tín dụng', 'VN').scope == 'SECTOR'
    assert Tagger().tag('VN-Index tăng điểm', 'VN').scope == 'MARKET'


def test_failure_isolation_atomic_source_and_error_hygiene(session):
    def fetch(s):
        if s.source_id == 'bad': raise RuntimeError('SECRET_BODY')
        if s.source_id == 'partial': return [item(url='https://partial.example/a'), item(url='javascript:bad')]
        return [item(url='https://good.example/a')]
    result = ingest_cycle(session, [source('bad'), source('partial'), source('good')], fetch=fetch, now=NOW)
    assert result['bad']['status'] == result['partial']['status'] == 'error'
    assert result['good']['added'] == 1
    assert len(session.exec(select(NewsArticle)).all()) == 1
    assert session.get(NewsSourceState, 'bad').last_error == 'RuntimeError'
    assert session.get(NewsSourceState, 'good').last_success_at is not None


def test_cadence_and_disabled_source(session):
    calls = []
    def fetch(s): calls.append(s.source_id);return [item()]
    feeds = [source(), source('disabled', enabled=False)]
    ingest_cycle(session, feeds, fetch=fetch, now=NOW)
    ingest_cycle(session, feeds, fetch=fetch, now=NOW+timedelta(minutes=19))
    assert calls == ['one']
    ingest_cycle(session, feeds, fetch=fetch, now=NOW+timedelta(minutes=20))
    assert calls == ['one', 'one']


def test_recency_and_global_relevance(session):
    ingest(session, [item(published=NOW-timedelta(days=5)), item(url='https://one.example/future', published=NOW+timedelta(days=1))])
    assert not session.exec(select(NewsArticle)).all()
    ingest(session, [item('Celebrity wedding', 'https://global.example/1'), item('Gold prices rise', 'https://global.example/2', None)], sources=[source('global', category='GLOBAL', country='US')])
    rows = session.exec(select(NewsArticle)).all()
    assert rows == []
    assert articles(session, category='GLOBAL', now=NOW) == []


def test_ranking_diversity_over_repetition_and_decay():
    diverse = NewsStory(source_count=3, article_count=3, last_updated_at=NOW)
    repeated = NewsStory(source_count=1, article_count=100, last_updated_at=NOW)
    assert story_score(diverse, NOW) > story_score(repeated, NOW)
    assert story_score(diverse, NOW+timedelta(days=1)) < story_score(diverse, NOW)


def test_trending_increasing_coverage_and_idempotence(session):
    ingest(session, [item('Gold prices rise', 'https://one.example/old', NOW-timedelta(hours=8))], now=NOW-timedelta(hours=8))
    ingest(session, [item('Gold prices jump after dollar falls', 'https://one.example/a')])
    ingest(session, [item('Gold demand rises in China with implications for Vietnam', 'https://two.example/a')], sources=[source('two')])
    rows = articles(session, now=NOW)
    topics = trending(rows, NOW)
    gold = next(x for x in topics if x['topic'] == 'Gold')
    assert gold['source_count'] == 2 and gold['mention_velocity'] > 0
    assert gold['previous_mentions'] == 1
    before = topics
    ingest(session, [item('Gold prices jump after dollar falls', 'https://one.example/a')], now=NOW+timedelta(minutes=1))
    assert trending(articles(session, now=NOW), NOW) == before
    assert trending(rows, NOW+timedelta(hours=7)) == []


def test_api_contracts_filters_no_body_and_no_personalization(client, session):
    now = datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ', company_name='Example Corp', sector='Technology'));session.commit()
    ingest(session, [item('XYZ profit rises', published=now)], now=now)
    ingest(session, [item('Gold prices rise', 'https://global.example/a', now)], sources=[source('global', category='GLOBAL', country='US')], now=now)
    response = client.get('/news/latest?ticker=XYZ&sector=Technology&source=one&country=VN')
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1 and rows[0]['tickers'] == ['XYZ']
    assert client.get('/news/latest?category=GLOBAL').json() == []
    assert client.get('/news/latest?limit=0').status_code == 422
    assert client.get('/news/latest?limit=101').status_code == 422
    assert client.get('/news/latest?category=BAD').status_code == 422
    assert client.get('/news/latest?topic=Gold').json() == []
    top = client.get('/news/top?limit=1').json()
    assert len(top) == 1 and top[0]['ranking_score'] > 0
    detail = client.get('/news/stories/' + rows[0]['story_id'])
    assert detail.status_code == 200 and len(detail.json()['articles']) == 1
    assert client.get('/news/stories/missing').status_code == 404
    assert client.get('/news/topics/trending').status_code == 200
    assert not any(k in NewsArticle.model_fields for k in ('body', 'content', 'html', 'summary', 'summary_or_content'))
    assert not any(k in rows[0] for k in ('body', 'content', 'html', 'summary'))
