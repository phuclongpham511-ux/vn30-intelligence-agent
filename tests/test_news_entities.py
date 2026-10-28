"""Issuer association accuracy: currency and acronym tokens are not equity evidence."""
from types import SimpleNamespace
import pytest
from src.news.tagging import Tagger


def equities():
    return [SimpleNamespace(symbol=s, company_name=name, display_name_en=None, sector=None)
            for s, name in [('USD', 'Công ty Cổ phần Công trình Đô thị Sóc Trăng'),
                            ('VND', 'Công ty Cổ phần Chứng khoán VNDIRECT'),
                            ('NDT', 'Công ty Cổ phần Dệt Nam Định'),
                            ('IT', 'Information Technology Corporation'),
                            ('CEO', 'Công ty Cổ phần Tập đoàn C.E.O'),
                            ('HCM', 'Công ty Cổ phần Chứng khoán Thành phố Hồ Chí Minh'),
                            ('ABC', 'Example Technology Corporation'),
                            ('XYZ', 'Example Manufacturing Corporation')]]


@pytest.mark.parametrize('headline', [
    'Lãi suất tiền đồng và giá USD liên ngân hàng liên tục giảm',
    'Đồng USD tăng mạnh tuần thứ tư liên tiếp do lo ngại lạm phát và giá dầu cao',
    'Tỷ giá hôm nay: Giá USD và NDT tiếp tục đi xuống',
    'VND thuộc nhóm hiếm hoi tăng giá trước USD',
    'IT is changing how people work',
    'IT reports higher earnings',
    'CEO reports higher earnings',
    'CEO nhận giải thưởng cá nhân',
    'Hạ tầng TP.HCM tăng trưởng',
    'USD tăng mạnh',
    'ABC và XYZ: điều gì đang xảy ra?',
    'XABC reports earnings',
    'Đồng tiền mang mã USD tăng giá',
    'Thiết bị mới mang mã USD đang bán chạy',
    'Không rõ lý do mà USD tăng mạnh',
    'Tỷ giá: mã USD tăng giá trong bảng tiền tệ ISO 4217',
    '$USD tăng giá so với VND',
])
def test_ambiguous_tokens_fail_closed(headline):
    assert Tagger(equities()).tag(headline, 'VN').tickers == []


@pytest.mark.parametrize('headline,expected', [
    ('Cổ phiếu USD tăng giá', ['USD']),
    ('Công ty Cổ phần Công trình Đô thị Sóc Trăng trả cổ tức', ['USD']),
    ('Mã VND phát hành cổ phiếu', ['VND']),
    ('Mã cổ phiếu USD tăng giá', ['USD']),
    ('$XYZ discussion', ['XYZ']),
    ('#XYZ discussion', ['XYZ']),
    ('Cổ phiếu IT reports higher earnings', ['IT']),
    ('ABC reports quarterly revenue growth', ['ABC']),
    ('XYZ huy động vốn bằng trái phiếu', ['XYZ']),
    ('Cổ phiếu ABC và XYZ tăng giá', ['ABC', 'XYZ']),
    ('Example Technology Corporation và Example Manufacturing Corporation ký hợp tác', ['ABC', 'XYZ']),
    ('Tỷ giá USD tăng, cổ phiếu ABC tăng doanh thu', ['ABC']),
    ('Giá USD mua 10 triệu cổ phiếu ABC', ['ABC']),
    ('CEO XYZ appoints a new director', ['XYZ']),
    ('XYZ công bố kết quả kinh doanh quý III', ['XYZ']),
    ('XYZ đặt mục tiêu doanh thu 2026', ['XYZ']),
    ('XYZ đã gom gần 117 triệu cổ phiếu ABC với giá 20.000 đồng', ['ABC', 'XYZ']),
])
def test_context_and_verified_identity_retain_real_issuers(headline, expected):
    assert Tagger(equities()).tag(headline, 'VN').tickers == expected


def test_verified_alias_is_whole_phrase_and_unique():
    tagger = Tagger(equities(), company_aliases={'ABC': ['Example Tech']})
    assert tagger.tag('Example Tech posts earnings', 'VN').tickers == ['ABC']
    assert tagger.tag('Example TechnologyX posts earnings', 'VN').tickers == []
    duplicate = Tagger(equities(), company_aliases={'ABC': ['Example Group'], 'XYZ': ['Example Group']})
    assert duplicate.tag('Example Group posts earnings', 'VN').tickers == []


def test_language_ambiguity_is_not_a_security_blacklist():
    for token in ('EUR', 'ALL', 'CFO', 'ZZQ'):
        tagger = Tagger([SimpleNamespace(symbol=token,company_name=f'Example {token} Corporation',sector=None)])
        assert tagger.tag(f'Cổ phiếu {token} tăng giá','VN').tickers == [token]
        assert tagger.tag(f'Example {token} Corporation reports earnings','VN').tickers == [token]
        assert tagger.tag(f'{token} reports earnings','VN').tickers == ([] if token != 'ZZQ' else ['ZZQ'])


def test_worker_links_are_explainable_and_legacy_labels_never_grant_links(session, client, monkeypatch):
    from datetime import datetime, timezone
    from sqlmodel import select
    from src.models import Security
    from src.news.adapters import ArticleInput
    from src.news.models import NewsArticle, NewsReadCache
    from src.news.service import ingest_cycle
    from tests.test_news import source
    now = datetime.now(timezone.utc)
    session.add_all([Security(symbol=e.symbol, company_name=e.company_name, exchange='HOSE', last_synced_at=now) for e in equities()])
    session.commit()
    titles = ['Lãi suất tiền đồng và giá USD liên ngân hàng liên tục giảm', 'Cổ phiếu USD tăng giá', 'ABC reports quarterly revenue growth']
    ingest_cycle(session, [source()], now=now, force=True, fetch=lambda _: [ArticleInput(
        title, f'https://one.example/{n}', now, 'https://image.example/a.png', 'media:thumbnail') for n,title in enumerate(titles)])
    market = client.get('/news/feed?research_category=MARKET_BRIEF').json()
    assert market[0]['representative_article']['title'] == titles[0]
    assert market[0]['ticker_associations'] == []
    company = client.get('/news/feed?research_category=COMPANY&ticker=USD').json()
    assert len(company) == 1
    proof = company[0]['ticker_associations'][0]
    assert proof['symbol'] == 'USD' and proof['kind'] == 'explicit_stock'
    assert proof['article_title'] == titles[1] and proof['matched_text']
    assert client.get('/news/stories/'+company[0]['story']['id']).json()['ticker_associations'] == company[0]['ticker_associations']

    # Emulate the real pre-upgrade raw evidence and unqualified cached projection.
    article = session.exec(select(NewsArticle).where(NewsArticle.title == titles[0])).one()
    article.tickers = ['USD']; session.add(article)
    cache = session.get(NewsReadCache, 'research')
    from copy import deepcopy
    rows = deepcopy(cache.rows)
    for entry in rows:
        entry['row'].pop('ticker_associations', None)
        if entry['row']['representative_article']['id'] == article.id:
            entry['row']['representative_article']['tickers'] = ['USD']
            for member in entry['row']['articles']: member['tickers'] = ['USD']
    cache.rows = rows; session.add(cache); session.commit(); session.refresh(article)
    baseline = article.model_dump(mode='json')
    def forbidden(*args, **kwargs): raise AssertionError('HTTP must not acquire or rebuild/tag evidence')
    monkeypatch.setattr('src.news.service.acquire', forbidden)
    monkeypatch.setattr('src.news.tagging.Tagger.resolve', forbidden)
    response = client.get('/news/feed?research_category=MARKET_BRIEF').json()[0]
    assert response['representative_article']['tickers'] == ['USD']
    assert response['ticker_associations'] == []
    assert client.get('/news/feed?research_category=MARKET_BRIEF&ticker=USD').json() == []
    assert client.get('/news/stories/'+article.story_id).json()['ticker_associations'] == []
    session.refresh(article)
    assert article.model_dump(mode='json') == baseline


def test_policy_upgrade_rebuild_is_idempotent_and_preserves_raw_evidence(session):
    from datetime import datetime, timezone
    from sqlmodel import select
    from src.models import Security
    from src.news.models import NewsArticle, NewsStory, NewsReadCache
    from src.news.read_cache import refresh_cache
    from tests.test_news import source, item
    from src.news.service import ingest_cycle
    now = datetime.now(timezone.utc)
    session.add(Security(symbol='USD', company_name=equities()[0].company_name, exchange='UPCOM', last_synced_at=now));session.commit()
    from src.news.adapters import ArticleInput
    title = 'Lãi suất tiền đồng và giá USD liên ngân hàng liên tục giảm'
    ingest_cycle(session, [source()], now=now, force=True, fetch=lambda _: [ArticleInput(title,'https://one.example/legacy',now,'https://image.example/a.png','media:thumbnail')])
    a = session.exec(select(NewsArticle)).one(); a.tickers=['USD'];session.add(a)
    s = session.exec(select(NewsStory)).one(); s.tickers=['USD'];session.add(s)
    metadata = session.get(NewsReadCache,'universe_version');metadata.rows=[{'version': None}];session.add(metadata);session.commit()
    session.refresh(a);session.refresh(s)
    before = (a.model_dump(mode='json'),s.model_dump(mode='json'))
    assert refresh_cache(session, set(), now=now)
    row = session.get(NewsReadCache,'research').rows[0]['row']
    assert row['ticker_associations'] == []
    assert row['representative_article']['tickers'] == []
    session.refresh(a);session.refresh(s)
    assert (a.model_dump(mode='json'),s.model_dump(mode='json')) == before
    assert not refresh_cache(session,set(),now=now)


def test_corrected_title_or_old_policy_cannot_reuse_issuer_proof():
    from datetime import datetime, timezone
    from src.news.models import NewsArticle, NewsStory
    from src.news.read import StoryResponse, TickerAssociation
    from src.news.tagging import ENTITY_POLICY
    a = NewsArticle(source_id='one',source_name='One',publisher_group='one',title='Tỷ giá USD giảm',url='https://one.example/a',canonical_url='https://one.example/a',url_hash='a',title_hash='a',country='VN',language='vi',category='VN',scope='MARKET',story_id='story')
    s = NewsStory(id='story',representative_title=a.title)
    for title,policy in [('Cổ phiếu USD tăng giá',ENTITY_POLICY),(a.title,'old')]:
        proof = TickerAssociation(symbol='USD',article_id=a.id,article_title=title,kind='explicit_stock',matched_text='usd',policy=policy)
        row=StoryResponse(story=s,articles=[a],representative_article=a,ranking_score=0,ticker_associations=[proof])
        assert row.ticker_associations == []
