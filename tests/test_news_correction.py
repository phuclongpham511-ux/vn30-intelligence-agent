from datetime import datetime, timezone
from types import SimpleNamespace
from src.models import Security
from src.news.research import research_category
from src.news.registry import load_sources
from src.news.adapters import ArticleInput
from src.news.service import ingest_cycle
from tests.test_news import source


def test_strict_primary_subject_requires_current_listed_equity():
    universe = [SimpleNamespace(symbol='XYZ', company_name='Example Bank', display_name_en=None)]
    def category(title, tickers=()):
        return research_category(SimpleNamespace(title=title, tickers=list(tickers), sectors=['Financials']), universe)
    assert category('XYZ bank earnings rise', ['XYZ']) == 'COMPANY'
    assert category('Example Bank announces earnings growth') == 'COMPANY'
    assert category('PrivateBank announces earnings growth') is None
    assert category('Inactive bank XYZ reports earnings', ['XYZ']) is None
    assert category('USD/VND exchange rate rises', ['USD']) == 'MARKET_BRIEF'
    assert category('Banking sector regulations change with XYZ as an example', ['XYZ']) == 'INDUSTRY'
    assert category('XYZ raises capital for its private subsidiary', ['XYZ']) == 'COMPANY'
    assert category('Private subsidiary expands; XYZ is mentioned as a customer', ['XYZ']) is None
    assert category('Nvidia leads global technology boom') is None
    assert category('Private technology company plans an acquisition') is None
    assert category('PrivateBank earnings improve as interest rates fall') is None
    assert category('Fed policy affects Vietnam exchange rates') == 'MARKET_BRIEF'


def test_hot_same_story_image_and_foreign_ingestion_gate(session, client):
    now = datetime.now(timezone.utc)
    for sid, image in [('one', None), ('two', 'https://two.example/photo.png')]:
        ingest_cycle(session, [source(sid)], fetch=lambda _, image=image, sid=sid: [ArticleInput(
            'Steel industry production grows', f'https://{sid}.example/story', now, image, 'media:thumbnail' if image else None)], now=now, force=True)
    rows = client.get('/news/hot').json()
    assert len(rows) == 1
    assert rows[0]['thumbnail_url'] == 'https://two.example/photo.png'
    assert rows[0]['thumbnail_article_id'] in {a['id'] for a in rows[0]['articles']}
    ingest_cycle(session, [source('foreign', country='US', category='GLOBAL')], fetch=lambda _: (_ for _ in ()).throw(AssertionError('must not fetch')), now=now, force=True)
    assert all(s.country == 'VN' and s.category == 'VN' for s in load_sources())


def test_no_image_story_kept_in_archive_not_visual_hot(session, client):
    now = datetime.now(timezone.utc)
    for sid in ('one', 'two'):
        ingest_cycle(session, [source(sid)], fetch=lambda _, sid=sid: [ArticleInput('Retail sector production grows', f'https://{sid}.example/noimage', now)], now=now, force=True)
    assert client.get('/news/hot').json() == []
    assert len(client.get('/news/feed?research_category=INDUSTRY').json()) == 1


def test_stock_fixture_alone_is_not_company_eligibility(session, client):
    from src.models import Stock
    now = datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ')); session.commit()
    ingest_cycle(session, [source()], fetch=lambda _: [ArticleInput('XYZ earnings rise', 'https://one.example/x', now)], now=now, force=True)
    assert client.get('/news/feed?research_category=COMPANY').json() == []
    session.add(Security(symbol='XYZ', exchange='HOSE', last_synced_at=now)); session.commit()
    assert len(client.get('/news/feed?research_category=COMPANY').json()) == 1


def test_historical_foreign_members_do_not_leak_or_inflate_current_evidence(session, client):
    from src.news.models import NewsArticle, NewsStory
    from sqlmodel import select
    now=datetime.now(timezone.utc)
    for sid in ('one','two'):
        ingest_cycle(session,[source(sid)],fetch=lambda _,sid=sid:[ArticleInput('Steel industry output expands',f'https://{sid}.example/a',now,'https://image.example/a.png','media:thumbnail')],now=now,force=True)
    foreign=session.exec(select(NewsArticle).where(NewsArticle.source_id=='two')).one()
    foreign.country='US';foreign.category='GLOBAL';session.add(foreign);session.commit()
    assert len(session.exec(select(NewsArticle)).all())==2
    assert session.get(NewsStory,foreign.story_id).source_count==2
    assert len(client.get('/news/latest').json())==1
    assert client.get('/news/hot').json()==[]
    for path in ('/news/top','/news/feed?research_category=INDUSTRY'):
        row=client.get(path).json()[0]
        assert row['story']['source_count']==1 and len(row['articles'])==1


def test_foreign_subject_gate_applies_to_legacy_current_feeds(session, client):
    now=datetime.now(timezone.utc)
    ingest_cycle(session,[source()],fetch=lambda _:[ArticleInput('Nvidia drives global technology earnings','https://one.example/global',now),ArticleInput('Fed policy affects Vietnam exchange rates','https://one.example/domestic',now)],now=now,force=True)
    for path in ('/news/latest','/news/top'):
        rows=client.get(path).json()
        assert len(rows)==1


def test_hot_image_preference_is_stable_and_never_crosses_stories(session, client):
    from routers.news import cluster_thumbnail
    a=SimpleNamespace(id='a',source_id='one',published_at=None,first_seen_at=datetime.now(timezone.utc),canonical_url='https://one.example/a',thumbnail_url='https://one.example/image.png')
    b=SimpleNamespace(id='b',source_id='two',published_at=None,first_seen_at=a.first_seen_at,canonical_url='https://two.example/b',thumbnail_url='https://two.example/image.png')
    assert cluster_thumbnail(a,[b,a],{'two':1}).id=='a'
    a.thumbnail_url='javascript:alert(1)'
    assert cluster_thumbnail(a,[a,b],{}).id=='b'
    assert cluster_thumbnail(a,[a],{}) is None
    now=datetime.now(timezone.utc)
    for sid in ('one','two'):
        ingest_cycle(session,[source(sid)],fetch=lambda _,sid=sid:[
            ArticleInput('Steel industry production grows',f'https://{sid}.example/image',now,'https://image.example/a.png','media:thumbnail'),
            ArticleInput('Retail sector demand declines',f'https://{sid}.example/noimage',now)],now=now,force=True)
    rows=client.get('/news/hot').json()
    assert len(rows)==1 and 'Steel industry' in rows[0]['representative_article']['title']


def test_word_order_title_case_and_foreign_geography():
    universe=[SimpleNamespace(symbol='XYZ',company_name=None,display_name_en=None)]
    for title in ('Lợi nhuận XYZ tăng mạnh trong quý III','XYZ Announces Earnings Growth','XYZ Expands domestic operations'):
        assert research_category(SimpleNamespace(title=title,tickers=['XYZ'],sectors=[]),universe)=='COMPANY'
    for title in ('Ngành công nghệ Mỹ tăng trưởng mạnh','Lãi suất tại Nhật Bản tiếp tục tăng','Italian banking industry expands'):
        assert research_category(SimpleNamespace(title=title,tickers=[],sectors=[]),universe) is None


def test_irrelevant_cluster_member_cannot_supply_image_or_publisher_count(session, client):
    from src.news.models import NewsArticle,NewsStory
    from sqlmodel import select
    now=datetime.now(timezone.utc)
    for sid,title in [('one','Fed interest rates affect Vietnam'),('two','Fed interest rates affect global markets')]:
        ingest_cycle(session,[source(sid)],fetch=lambda _,sid=sid,title=title:[ArticleInput(title,f'https://{sid}.example/a',now,'https://image.example/a.png' if sid=='two' else None,'media:thumbnail' if sid=='two' else None)],now=now,force=True)
    members=session.exec(select(NewsArticle)).all()
    # Model the already-persisted cluster identified during review.
    other=members[1];other.story_id=members[0].story_id;session.add(other);session.commit()
    assert client.get('/news/hot').json()==[]
    for path in ('/news/top','/news/feed?research_category=MARKET_BRIEF'):
        row=client.get(path).json()[0]
        assert len(row['articles'])==1 and row['story']['source_count']==1
        assert row.get('thumbnail_url') is None


def test_unlisted_entity_extension_is_case_independent():
    universe=[SimpleNamespace(symbol='XYZ',company_name='XYZ Holdings Corporation',display_name_en=None)]
    for extension in ('Finance','finance','FINANCE','Retail','retail','RETAIL','Tài chính','Chứng khoán'):
        title=f'XYZ {extension} reports earnings growth'
        assert research_category(SimpleNamespace(title=title,tickers=['XYZ'],sectors=[]),universe) is None
    assert research_category(SimpleNamespace(title='XYZ Holdings Corporation reports earnings growth',tickers=['XYZ'],sectors=[]),universe)=='COMPANY'
    assert research_category(SimpleNamespace(title='Ngành thuế phát hiện hồ sơ giả mạo',tickers=[],sectors=[]),universe) is None


def test_market_subject_in_issuer_attributed_forecast_is_not_company():
    universe=[SimpleNamespace(symbol='XYZ',company_name='XYZ Holdings Corporation',display_name_en=None)]
    article=SimpleNamespace(title='XYZ: VN-Index có thể giảm về vùng hỗ trợ',tickers=['XYZ'],sectors=[])
    assert research_category(article,universe)=='MARKET_BRIEF'
