from datetime import datetime, timezone
from sqlmodel import select
from src.models import Stock
from src.news.adapters import parse_feed, ArticleInput
from src.news.models import NewsArticle
from src.news.registry import Source
from src.news.service import ingest_cycle
from routers.news import representative

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)


def source(sid='one', priority=100):
    return Source(source_id=sid, name=sid, endpoint='https://example.org/feed', country='VN', language='vi', category='VN', publisher_group=sid, representative_priority=priority)


def test_explicit_feed_thumbnail_only():
    template = '<rss xmlns:media="http://search.yahoo.com/mrss/"><channel><item><title>Stocks</title><link>https://example.org/a</link>{}</item></channel></rss>'
    for metadata, url, provenance in [
        ('<media:thumbnail url="https://example.org/photo.jpg"/>', 'https://example.org/photo.jpg', 'media:thumbnail'),
        ('<media:content medium="image" url="https://example.org/p.png"/>', 'https://example.org/p.png', 'media:content'),
        ('<enclosure type="image/jpeg" url="https://example.org/p.jpg"/>', 'https://example.org/p.jpg', 'enclosure'),
        ('<media:thumbnail url="javascript:alert(1)"/>', None, None),
        ('<media:thumbnail url="https://user:secret@example.org/p"/>', None, None),
        ('<media:thumbnail url="/relative.jpg"/>', None, None),
        ('<description>&lt;img src="https://example.org/fake.jpg"/&gt;</description>', None, None),
        ('', None, None),
    ]:
        row = parse_feed(template.format(metadata).encode(), source())[0]
        assert (row.thumbnail_url, row.thumbnail_provenance) == (url, provenance)


def test_representative_preserves_evidence_diversity_and_ranking(session, client, monkeypatch):
    sources = [source('one', 20), source('two', 10)]
    monkeypatch.setattr('routers.news.load_sources', lambda: sources)
    for src in sources:
        item = ArticleInput('XYZ bank earnings rise strongly', f'https://example.org/{src.source_id}', NOW, 'https://example.org/image.jpg', 'media:thumbnail')
        ingest_cycle(session, [src], fetch=lambda _: [item], now=NOW, force=True)
    response = client.get('/news/top').json()[0]
    assert response['representative_article']['source_id'] == 'two'
    assert response['representative_article']['thumbnail_provenance'] == 'media:thumbnail'
    assert response['story']['source_count'] == 2
    assert len(response['articles']) == len(session.exec(select(NewsArticle)).all()) == 2
    filtered = client.get('/news/top?source=one').json()[0]
    assert filtered['representative_article']['source_id'] == 'one'
    assert len(filtered['articles']) == 2 and filtered['story']['source_count'] == 2
    score = response['ranking_score']
    monkeypatch.setattr('routers.news.load_sources', lambda: [source('one', 1), source('two', 20)])
    changed = client.get('/news/top').json()[0]
    assert changed['representative_article']['source_id'] == 'one'
    assert abs(changed['ranking_score'] - score) < .001
    rows = session.exec(select(NewsArticle)).all()
    assert representative(rows, {}) == representative(list(reversed(rows)), {})


def test_sector_missing_not_fabricated_and_supported_filter(session, client):
    session.add_all([Stock(symbol='XYZ', sector='Technology'), Stock(symbol='ABC')]); session.commit()
    inputs = [ArticleInput('XYZ earnings rise', 'https://example.org/x', NOW), ArticleInput('ABC earnings rise', 'https://example.org/a', NOW)]
    ingest_cycle(session, [source()], fetch=lambda _: inputs, now=NOW, force=True)
    assert len(client.get('/news/latest?sector=Technology').json()) == 1
    assert client.get('/news/latest?sector=Unknown').json() == []
    assert client.get('/news/latest?ticker=ABC').json()[0]['sectors'] == []
