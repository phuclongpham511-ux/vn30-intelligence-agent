from datetime import datetime, timezone
from src.models import Stock
from src.news.registry import Source
from src.news.adapters import ArticleInput
from src.news.service import ingest_cycle


def test_semantic_feeds_keep_single_company_and_industry_but_require_market_coverage(session, client):
    session.add(Stock(symbol='XYZ')); session.commit()
    now = datetime.now(timezone.utc)
    sources = [Source(source_id=x,name=x,endpoint=f'https://{x}.example/feed',country='VN',language='vi',category='VN',publisher_group=x) for x in ('one','two')]
    inputs = [ArticleInput(title, f'https://one.example/{n}', now) for n,title in enumerate([
        'XYZ appoints new chief executive', 'Steel industry production grows', 'Central bank monetary policy changes', 'A beautiful weekend destination'])]
    ingest_cycle(session,[sources[0]],fetch=lambda _:inputs,now=now,force=True)
    response = client.get('/news/feed?research_category=COMPANY')
    assert response.status_code == 200 and len(response.json()) == 1
    assert len(client.get('/news/feed?research_category=INDUSTRY').json()) == 1
    assert client.get('/news/feed?research_category=MARKET_BRIEF').json() == []
    assert client.get('/news/hot').json() == []
    ingest_cycle(session,[sources[1]],fetch=lambda _:[ArticleInput(inputs[2].title,'https://two.example/a',now)],now=now,force=True)
    market = client.get('/news/feed?research_category=MARKET_BRIEF').json()
    assert market[0]['story']['source_count'] == 2
    assert market[0]['research_category'] == 'MARKET_BRIEF'
    assert client.get('/news/hot').json()[0]['story']['id'] == market[0]['story']['id']


def test_hot_topics_rank_independent_groups_before_recency_or_repeated_articles(session, client):
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    sources = [Source(source_id=str(n),name=str(n),endpoint=f'https://p{n}.example/rss',country='VN',language='vi',category='VN',publisher_group=str(n)) for n in range(5)]
    for source in sources:
        ingest_cycle(session,[source],fetch=lambda s:[ArticleInput('Steel industry capacity expands',f'https://p{s.source_id}.example/a',now-timedelta(hours=12))],now=now,force=True)
    for source in sources[:2]:
        ingest_cycle(session,[source],fetch=lambda s:[ArticleInput('Retail sector new operating rules',f'https://p{s.source_id}.example/b',now)],now=now,force=True)
    rows=client.get('/news/hot').json()
    assert [row['story']['source_count'] for row in rows] == [5,2]
    assert [row['story']['id'] for row in rows] == [row['story']['id'] for row in client.get('/news/hot').json()]


def test_primary_market_or_industry_framing_is_not_overridden_by_incidental_issuers():
    from src.news.research import research_category
    from types import SimpleNamespace
    assert research_category(SimpleNamespace(title='Steel industry dividend outlook improves', tickers=[], sectors=['Industrials'])) == 'INDUSTRY'
    assert research_category(SimpleNamespace(title='VN-Index climbs with AAA and BBB leading the broad market', tickers=['AAA','BBB'], sectors=[])) == 'MARKET_BRIEF'
    assert research_category(SimpleNamespace(title='AAA earnings benefit from lower interest rates', tickers=['AAA'], sectors=['Industrials'])) == 'COMPANY'
    assert research_category(SimpleNamespace(title='Example Bank - ngân hàng đầu tiên nâng vốn điều lệ', tickers=[], sectors=['Financials'])) == 'COMPANY'
    assert research_category(SimpleNamespace(title='Example Bank trở thành ngân hàng đầu tiên nâng vốn điều lệ', tickers=[], sectors=['Financials'])) == 'COMPANY'
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


def test_named_organization_headlines_are_company_while_sector_framing_stays_industry():
    from src.news.research import research_category
    from types import SimpleNamespace
    for title in ['ExampleBank được vinh danh tại giải thưởng ngân hàng','MB becomes the first bank in Vietnam to increase charter capital','Ngân hàng ExampleBank công bố kế hoạch mới','Chứng khoán ExampleBroker mở rộng hoạt động', 'Bank Y reports higher earnings','Company X plans expansion', 'Bảo hiểm ExampleInsurer tăng vốn']:
        assert research_category(SimpleNamespace(title=title,tickers=[],sectors=['Financials']))=='COMPANY'
    for title in ['Các ngân hàng nâng lãi suất tiền gửi','Securities industry grows with ABC leading brokerage','Real estate sector supply improves']:
        assert research_category(SimpleNamespace(title=title,tickers=['ABC'],sectors=['Financials']))=='INDUSTRY'

    assert research_category(SimpleNamespace(title='Interbank interest rates rise',tickers=[],sectors=['Financials']))=='MARKET_BRIEF'
    assert research_category(SimpleNamespace(title='Nonbank lending grows',tickers=[],sectors=['Financials']))=='INDUSTRY'
