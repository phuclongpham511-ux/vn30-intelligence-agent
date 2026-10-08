from datetime import datetime, timezone
from src.models import Stock, Security
from src.news.registry import Source
from src.news.adapters import ArticleInput
from src.news.service import ingest_cycle


def test_quick_news_keeps_coverage_ranking_while_archive_keeps_recency(session, client, monkeypatch):
    session.add_all([Stock(symbol='XYZ'), Security(symbol='XYZ', exchange='HOSE', last_synced_at=datetime.now(timezone.utc))])
    session.commit()
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    sources = [Source(source_id=x, name=x, endpoint=f'https://{x}.example/feed', country='VN',
                      language='vi', category='VN', publisher_group=x) for x in ('one', 'two')]
    broad = 'XYZ appoints new chief executive'
    recent = 'XYZ reports quarterly revenue growth'
    for source in sources:
        ingest_cycle(session, [source], force=True, now=now, fetch=lambda s: [ArticleInput(
            broad, f'https://{s.source_id}.example/a', now-timedelta(hours=1),
            'https://image.example/a.png', 'media:thumbnail')])
    ingest_cycle(session, [sources[0]], force=True, now=now, fetch=lambda _: [ArticleInput(
        recent, 'https://one.example/b', now, 'https://image.example/b.png', 'media:thumbnail')])
    def forbidden(*args, **kwargs):
        raise AssertionError('Quick News must not fetch upstream or rebuild projections')
    monkeypatch.setattr('src.news.service.acquire', forbidden)
    monkeypatch.setattr('src.news.read.build_research_rows', forbidden)
    query = '/news/feed?research_category=COMPANY&ticker=XYZ&limit=10'
    assert client.get(query).json()[0]['representative_article']['title'] == recent
    quick = client.get(query+'&ranking=attention').json()
    assert quick[0]['representative_article']['title'] == broad
    assert quick[0]['story']['source_count'] == 2
    assert len(quick[0]['articles']) == 2
    assert quick[0]['thumbnail_url']
    assert client.get(query+'&ranking=unknown').status_code == 422


def test_archives_keep_single_source_evidence_while_hot_requires_coverage_and_image(session, client):
    session.add_all([Stock(symbol='XYZ'), Security(symbol='XYZ',exchange='HOSE',last_synced_at=datetime.now(timezone.utc))]); session.commit()
    now = datetime.now(timezone.utc)
    sources = [Source(source_id=x,name=x,endpoint=f'https://{x}.example/feed',country='VN',language='vi',category='VN',publisher_group=x) for x in ('one','two')]
    inputs = [ArticleInput(title, f'https://one.example/{n}', now, 'https://one.example/image.png', 'media:thumbnail') for n,title in enumerate([
        'XYZ appoints new chief executive', 'Steel industry production grows', 'Central bank monetary policy changes', 'A beautiful weekend destination'])]
    ingest_cycle(session,[sources[0]],fetch=lambda _:inputs,now=now,force=True)
    response = client.get('/news/feed?research_category=COMPANY')
    assert response.status_code == 200 and len(response.json()) == 1
    assert len(client.get('/news/feed?research_category=INDUSTRY').json()) == 1
    assert len(client.get('/news/feed?research_category=MARKET_BRIEF').json()) == 1
    assert client.get('/news/hot').json() == []
    ingest_cycle(session,[sources[1]],fetch=lambda _:[ArticleInput(inputs[2].title,'https://two.example/a',now,'https://two.example/image.png','media:thumbnail')],now=now,force=True)
    market = client.get('/news/feed?research_category=MARKET_BRIEF').json()
    assert market[0]['story']['source_count'] == 2
    assert market[0]['research_category'] == 'MARKET_BRIEF'
    assert client.get('/news/hot').json()[0]['story']['id'] == market[0]['story']['id']


def test_hot_topics_rank_independent_groups_before_recency_or_repeated_articles(session, client):
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    sources = [Source(source_id=str(n),name=str(n),endpoint=f'https://p{n}.example/rss',country='VN',language='vi',category='VN',publisher_group=str(n)) for n in range(5)]
    for source in sources:
        ingest_cycle(session,[source],fetch=lambda s:[ArticleInput('Steel industry capacity expands',f'https://p{s.source_id}.example/a',now-timedelta(hours=12),'https://image.example/a.png','media:thumbnail')],now=now,force=True)
    for source in sources[:2]:
        ingest_cycle(session,[source],fetch=lambda s:[ArticleInput('Retail sector new operating rules',f'https://p{s.source_id}.example/b',now,'https://image.example/b.png','media:thumbnail')],now=now,force=True)
    rows=client.get('/news/hot').json()
    assert [row['story']['source_count'] for row in rows] == [5,2]
    assert [row['story']['id'] for row in rows] == [row['story']['id'] for row in client.get('/news/hot').json()]


def test_primary_market_or_industry_framing_is_not_overridden_by_incidental_issuers():
    from src.news.research import research_category
    from types import SimpleNamespace
    assert research_category(SimpleNamespace(title='Steel industry dividend outlook improves', tickers=[], sectors=['Industrials'])) == 'INDUSTRY'
    assert research_category(SimpleNamespace(title='VN-Index climbs with AAA and BBB leading the broad market', tickers=['AAA','BBB'], sectors=[])) == 'MARKET_BRIEF'
    assert research_category(SimpleNamespace(title='AAA earnings benefit from lower interest rates', tickers=['AAA'], sectors=['Industrials']), [SimpleNamespace(symbol='AAA',company_name=None,display_name_en=None)]) == 'COMPANY'
    assert research_category(SimpleNamespace(title='Example Bank - ngân hàng đầu tiên nâng vốn điều lệ', tickers=[], sectors=['Financials'])) is None
    assert research_category(SimpleNamespace(title='Example Bank trở thành ngân hàng đầu tiên nâng vốn điều lệ', tickers=[], sectors=['Financials'])) is None
    assert research_category(SimpleNamespace(title='Banking system - banks prepare for dividends', tickers=[], sectors=['Financials'])) == 'INDUSTRY'


def test_language_context_disambiguates_currency_roles_and_locations_from_symbols():
    from src.news.tagging import Tagger
    from types import SimpleNamespace
    tagger = Tagger([SimpleNamespace(symbol=s, company_name=None, sector=None) for s in ('ABC','XYZ','USD','CEO','HCM','VTV')])
    assert tagger.tag('ABC huy động 285 triệu USD', 'VN').tickers == ['ABC']
    assert tagger.tag('CEO XYZ appoints a new director', 'VN').tickers == ['XYZ']
    assert tagger.tag('CEO reports higher earnings', 'VN').tickers == ['CEO']
    assert tagger.tag('Hạ tầng TP.HCM tăng trưởng', 'VN').tickers == []
    assert tagger.tag('Rời VTV, đạo diễn chuyển công việc', 'VN').tickers == []
    assert tagger.tag('Trở thành tỷ phú USD trong năm nay', 'VN').tickers == []
    assert tagger.tag('Cổ phiếu USD tăng giá', 'VN').tickers == ['USD']


def test_unverified_organization_names_do_not_become_company():
    from src.news.research import research_category
    from types import SimpleNamespace
    for title in ['ExampleBank được vinh danh tại giải thưởng ngân hàng','MB becomes the first bank in Vietnam to increase charter capital','Ngân hàng ExampleBank công bố kế hoạch mới','Chứng khoán ExampleBroker mở rộng hoạt động', 'Bank Y reports higher earnings','Company X plans expansion', 'Bảo hiểm ExampleInsurer tăng vốn']:
        assert research_category(SimpleNamespace(title=title,tickers=[],sectors=['Financials'])) is None
    for title in ['Các ngân hàng nâng lãi suất tiền gửi','Securities industry grows with ABC leading brokerage','Real estate sector supply improves']:
        assert research_category(SimpleNamespace(title=title,tickers=['ABC'],sectors=['Financials']))=='INDUSTRY'

    assert research_category(SimpleNamespace(title='Interbank interest rates rise',tickers=[],sectors=['Financials']))=='MARKET_BRIEF'
    assert research_category(SimpleNamespace(title='Nonbank lending grows',tickers=[],sectors=['Financials'])) is None
