"""Synthetic publisher evidence only; no provider or product database access."""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from sqlmodel import select
from src.models import Security
from src.news.adapters import ArticleInput, parse_feed
from src.news.service import ingest_cycle
from src.news.tagging import Tagger
from src.news.models import NewsArticle, NewsTextReceipt, NewsReadCache
from tests.test_news import source


def seed(session):
    now=datetime.now(timezone.utc)-timedelta(minutes=5)
    names=[('ABC','Example Technology Corporation'),('XYZ','Example Steel Corporation'),('USD','Example Utilities Corporation')]
    session.add_all([Security(symbol=s,company_name=n,exchange='HOSE',last_synced_at=now) for s,n in names]);session.commit()
    incoming=[ArticleInput('VN-Index tăng nhờ cổ phiếu ABC','https://one.example/market',now),
        ArticleInput('Ngành thép: cổ phiếu ABC, XYZ mở rộng xuất khẩu','https://one.example/industry',now-timedelta(minutes=1)),
        ArticleInput('ABC công bố lợi nhuận quý III','https://one.example/company',now-timedelta(minutes=2),
            text='Example Technology Corporation mở rộng trung tâm dữ liệu tại Việt Nam.',text_provenance='rss:description'),
        ArticleInput('Tỷ giá USD giảm, lãi suất ổn định','https://one.example/currency',now-timedelta(minutes=3))]
    ingest_cycle(session,[source()],now=now+timedelta(minutes=1),force=True,fetch=lambda _:incoming)
    return now,incoming


def test_every_category_carries_only_evidenced_tickers_and_keeps_classification(session,client):
    seed(session)
    for category,expected in [('MARKET_BRIEF',['ABC']),('INDUSTRY',['ABC','XYZ']),('COMPANY',['ABC'])]:
        rows=client.get('/news/feed',params={'research_category':category,'ticker':'ABC'}).json()
        assert rows and rows[0]['research_category']==category
        assert rows[0]['representative_article']['tickers']==expected
    currency=next(r for r in client.get('/news/feed?research_category=MARKET_BRIEF').json() if '/currency' in r['representative_article']['url'])
    assert currency['ticker_associations']==[]


def test_unified_search_ticker_names_text_keywords_and_categories(session,client,monkeypatch):
    seed(session)
    def forbidden(*a,**k):raise AssertionError('HTTP may not acquire or retag')
    monkeypatch.setattr(Tagger,'resolve',forbidden)
    cases=[('ABC',3),('Example Technology Corporation',3),('thép',1),('VN-Index',1),('trung tâm dữ liệu',1),('USD',0),('thép lãi suất',0),('Earnings',1),('Rates',1)]
    for query,count in cases:
        response=client.get('/news/feed/page',params={'research_category':'ALL','q':query})
        assert response.status_code==200,response.text
        assert len(response.json()['items'])==count,(query,response.json())
    assert len(client.get('/news/feed/page',params={'q':'ABC','research_category':'INDUSTRY'}).json()['items'])==1
    assert client.get('/news/feed/page',params={'q':'x'*121}).status_code==422


def test_worker_projection_is_idempotent_and_preserves_original_articles(session,client):
    now,incoming=seed(session)
    before=[r.model_dump(mode='json') for r in session.exec(select(NewsArticle)).all()]
    receipts=[r.id for r in session.exec(select(NewsTextReceipt)).all()]
    refreshes=session.get(NewsReadCache,'research').refresh_count
    ingest_cycle(session,[source()],now=now+timedelta(minutes=2),force=True,fetch=lambda _:incoming)
    assert [r.id for r in session.exec(select(NewsTextReceipt)).all()]==receipts
    assert session.get(NewsReadCache,'research').refresh_count==refreshes
    after=[r.model_dump(mode='json') for r in session.exec(select(NewsArticle)).all()]
    for a,b in zip(before,after):
        for key in ('id','title','url','first_seen_at','published_at','tickers'):assert a[key]==b[key]


def test_search_never_backdates_later_publisher_text(session,client):
    now,incoming=seed(session)
    revised=ArticleInput(incoming[2].title,incoming[2].url,incoming[2].published_at,
        text='Cổ phiếu ABC đầu tư điện toán lượng tử.',text_provenance='rss:description')
    ingest_cycle(session,[source()],now=now+timedelta(minutes=2),force=True,fetch=lambda _:[revised])
    current=client.get('/news/feed/page',params={'research_category':'ALL','q':'lượng tử'}).json()
    assert len(current['items'])==1
    historical=client.get('/news/feed/page',params={'research_category':'ALL','q':'lượng tử','as_of':(now+timedelta(seconds=90)).isoformat()}).json()
    assert historical['items']==[]


def test_verified_alias_and_explicit_lists_are_unique_and_language_safe():
    stocks=[SimpleNamespace(symbol=s,company_name=n,display_name_en=None,sector=None) for s,n in [('ABC','Example Technology Corporation'),('XYZ','Example Steel Corporation'),('USD','Example Utilities Corporation')]]
    tagger=Tagger(stocks,company_aliases={'ABC':['Example Tech']})
    assert [p['symbol'] for p in tagger.resolve('Ngành thép: cổ phiếu ABC, XYZ mở rộng xuất khẩu')]==['ABC','XYZ']
    assert [p['symbol'] for p in tagger.resolve('Thị trường lãi suất',body='Example Tech công bố lợi nhuận.')]==['ABC']
    assert tagger.resolve('Tỷ giá USD và VND trong thị trường chứng khoán')==[]
    assert tagger.resolve('Ngành thép tăng trưởng')==[]
    assert [p['symbol'] for p in tagger.resolve('VN-Index tăng nhờ ABC, XYZ')]==['ABC','XYZ']
    assert tagger.resolve('VN-Index và giá USD tăng')==[]
    assert tagger.resolve('VN-Index: ABC Retail mở rộng cửa hàng')==[]


def test_reviewed_alias_is_universe_gated_searchable_and_does_not_override_market_category(session,client):
    now=datetime.now(timezone.utc)-timedelta(minutes=2)
    session.add(Security(symbol='TCB',company_name='Ngân hàng TMCP Kỹ thương Việt Nam',exchange='HOSE',last_synced_at=now));session.commit()
    items=[ArticleInput('Techcombank công bố lợi nhuận quý III','https://one.example/tcb',now),
        ArticleInput('VN-Index: Techcombank dẫn đầu thanh khoản','https://one.example/tcb-market',now)]
    ingest_cycle(session,[source()],now=now,force=True,fetch=lambda _:items)
    for category in ['COMPANY','MARKET_BRIEF']:
        response=client.get('/news/feed/page',params={'q':'Techcombank','research_category':category}).json()
        assert len(response['items'])==1
        assert response['items'][0]['representative_article']['tickers']==['TCB']


def test_specialized_rss_sources_reuse_adapter_and_publisher_identity(session):
    from src.news.registry import load_sources
    selected=[s for s in load_sources() if s.source_id in {'vietstock_business','vietstock_dividends'}]
    assert len(selected)==2
    assert all(s.publisher_group=='vietstock' and s.method=='RSS' and s.verified_at for s in selected)
    xml=b'<rss><channel><item><title>ABC reports annual profit</title><link>https://vietstock.vn/synthetic/shared.htm</link><pubDate>Tue, 27 Oct 2026 10:00:00 +0700</pubDate><description>Original supplied feed summary.</description></item></channel></rss>'
    now=datetime.now(timezone.utc)
    def fetch(s):
        rows=parse_feed(xml,s);assert rows[0].published_at.utcoffset().total_seconds()==0
        return rows
    ingest_cycle(session,selected,now=now,force=True,fetch=fetch)
    ingest_cycle(session,selected,now=now+timedelta(minutes=1),force=True,fetch=fetch)
    assert len(session.exec(select(NewsArticle)).all())==1
    assert len(session.exec(select(NewsTextReceipt)).all())==1
