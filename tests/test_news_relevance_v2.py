"""Public API regressions using isolated synthetic publisher feed receipts."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from sqlmodel import select
from src.models import Security
from src.news.adapters import ArticleInput, parse_feed
from src.news.models import NewsArticle, NewsTextReceipt, NewsReadCache
from src.news.service import ingest_cycle
from src.news.tagging import Tagger, ENTITY_POLICY
from tests.test_news import source


def universe():
    return [SimpleNamespace(symbol=s,company_name=n,display_name_en=None,sector=None) for s,n in
        [('MCH','Công ty Cổ phần Hàng Tiêu Dùng MaSan'),('MSN','Công ty Cổ phần Tập đoàn Masan'),
         ('USD','Công ty Cổ phần Công trình Đô thị Sóc Trăng'),('VND','Công ty Cổ phần Chứng khoán VNDIRECT'),
         ('NDT','Công ty Cổ phần Dệt Nam Định')]]


def test_body_recalls_explicit_issuer_without_ecosystem_inference():
    tagger=Tagger(universe())
    title='Một cổ phiếu hệ sinh thái Masan bị khối ngoại xả ròng'
    assert tagger.resolve(title)==[]
    proof=tagger.resolve(title,body='Nhà đầu tư nước ngoài bán ròng mạnh cổ phiếu MCH gần 9.600 tỷ đồng.')
    assert [p['symbol'] for p in proof]==['MCH']
    assert proof[0]['evidence_origin']=='publisher_text' and 'cổ phiếu MCH' in proof[0]['evidence_excerpt']
    assert tagger.resolve(title,body='Doanh nghiệp thuộc hệ sinh thái Masan mở cửa hàng.')==[]
    assert tagger.resolve(title,body='Cổ phiếu UNKNOWN bị bán mạnh.')==[]
    assert [p['symbol'] for p in tagger.resolve(title,body='Công ty Cổ phần Hàng Tiêu Dùng MaSan công bố lợi nhuận.')]==['MCH']


def test_currency_and_ordinary_tokens_in_text_never_become_stocks():
    tagger=Tagger(universe())
    for text in ['Giá USD liên ngân hàng giảm. VND tăng trước NDT.',
                 'Tỷ giá: mã USD tăng trong bảng ISO 4217.',
                 'Cổ phiếu giảm. USD tăng mạnh.', 'Giá trị 9.600 tỷ VND, quy đổi USD.']:
        assert tagger.resolve('Lãi suất tiền đồng và giá USD liên ngân hàng liên tục giảm',body=text)==[]
    assert [p['symbol'] for p in tagger.resolve('Thông tin doanh nghiệp',body='Cổ phiếu USD trả cổ tức.')]==['USD']


def test_feed_text_is_bounded_plain_attributed_and_no_network(monkeypatch):
    monkeypatch.setattr('src.news.adapters.urlopen',lambda *a,**k:(_ for _ in ()).throw(AssertionError('No page acquisition')))
    xml='<rss><channel><item><title>Issuer update</title><link>https://one.example/a</link><description><![CDATA[<p>Cổ phiếu MCH tăng.</p><script>USD</script><nav>VND</nav>]]></description></item></channel></rss>'
    item=parse_feed(xml.encode(),source())[0]
    assert item.text=='Cổ phiếu MCH tăng.' and item.text_provenance=='rss:description'


def test_body_receipts_correction_and_cache_only_contract(session,client,monkeypatch):
    now=datetime.now(timezone.utc)
    session.add_all([Security(symbol=s.symbol,company_name=s.company_name,exchange='HOSE',last_synced_at=now) for s in universe()]);session.commit()
    title='Một cổ phiếu hệ sinh thái Masan bị khối ngoại xả ròng'
    item=ArticleInput(title,'https://one.example/masan',now,text='Cổ phiếu MCH bị bán ròng.',text_provenance='rss:description')
    ingest_cycle(session,[source()],now=now,force=True,fetch=lambda _: [item])
    row=client.get('/news/feed?research_category=MARKET_BRIEF&ticker=MCH').json()[0]
    assert row['thumbnail_url'] is None
    proof=row['ticker_associations'][0]
    assert proof['symbol']=='MCH' and proof['policy']==ENTITY_POLICY
    assert proof['text_receipt_id'] and proof['text_hash'] and proof['evidence_excerpt']
    assert row['representative_article']['tickers']==['MCH']
    raw=session.exec(select(NewsArticle)).one();first=raw.first_seen_at
    receipt=session.exec(select(NewsTextReceipt)).one();baseline=receipt.model_dump()
    ingest_cycle(session,[source()],now=now+timedelta(minutes=1),force=True,fetch=lambda _: [item])
    assert len(session.exec(select(NewsTextReceipt)).all())==1
    corrected=ArticleInput('Tỷ giá USD giảm','https://one.example/masan',now)
    ingest_cycle(session,[source()],now=now+timedelta(minutes=2),force=True,fetch=lambda _: [corrected])
    assert client.get('/news/feed?ticker=MCH').json()==[]
    currency=client.get('/news/feed?research_category=MARKET_BRIEF').json()[0]
    assert currency['ticker_associations']==[]
    session.refresh(receipt);session.refresh(raw)
    assert receipt.model_dump()==baseline and raw.first_seen_at==first
    # HTTP must neither re-tag nor read/fetch publisher text to invent proofs.
    monkeypatch.setattr(Tagger,'resolve',lambda *a,**k:(_ for _ in ()).throw(AssertionError('HTTP cannot resolve')))
    assert client.get('/news/feed').status_code==200
    assert client.get('/news/stories/'+raw.story_id).json()['ticker_associations']==[]


def test_no_image_keeps_order_snapshot_pagination_and_hot_breadth(session,client):
    now=datetime.now(timezone.utc)
    items=[ArticleInput('Lãi suất thị trường thay đổi '+str(n),f'https://one.example/{n}',now-timedelta(minutes=n)) for n in range(15)]
    ingest_cycle(session,[source()],now=now,force=True,fetch=lambda _:items)
    first=client.get('/news/feed/page?research_category=MARKET_BRIEF&limit=12').json()
    assert len(first['items'])==12 and first['has_more']
    assert all(r['thumbnail_url'] is None for r in first['items'])
    assert client.get('/news/hot').json()==[]
    second=client.get('/news/feed/page',params={'research_category':'MARKET_BRIEF','limit':12,'offset':12,'as_of':first['as_of']}).json()
    assert len(second['items'])==3
    assert not {r['story']['id'] for r in first['items']} & {r['story']['id'] for r in second['items']}
    cache=session.get(NewsReadCache,'research');assert cache


def test_long_sentence_proof_keeps_actual_supporting_excerpt():
    body='Thông tin thị trường ổn định ' * 35 + 'cổ phiếu MCH bị bán ròng.'
    proof=Tagger(universe()).resolve('Thông tin doanh nghiệp',body=body)[0]
    assert proof['symbol']=='MCH' and len(proof['evidence_excerpt'])<=600
    assert 'cổ phiếu MCH' in proof['evidence_excerpt']


def test_related_links_are_not_article_body_evidence():
    xml='<rss><channel><item><title>Lãi suất thị trường</title><link>https://one.example/a</link><description><![CDATA[<p>Lãi suất thị trường ổn định.</p><div class="related-news"><a href="https://one.example/other">Cổ phiếu MCH tăng giá.</a></div><p><a href="https://one.example/issuer">Cổ phiếu MSN</a> chia cổ tức.</p>]]></description></item></channel></rss>'
    item=parse_feed(xml.encode(),source())[0]
    assert 'MCH' not in item.text and 'Cổ phiếu MSN' in item.text
    assert [p['symbol'] for p in Tagger(universe()).resolve(item.title,body=item.text)]==['MSN']


def test_a_b_a_text_corrections_follow_latest_receipt_and_watchlist_revision(session,client,monkeypatch):
    from src.services.watchlist_intelligence import intelligence
    monkeypatch.setattr('src.services.watchlist_intelligence.load_sources',lambda:[source()])
    now=datetime.now(timezone.utc)-timedelta(minutes=5)
    session.add_all([Security(symbol=s.symbol,company_name=s.company_name,exchange='HOSE',last_synced_at=now) for s in universe()]);session.commit()
    title='Thông tin doanh nghiệp trong tuần'
    versions=[]
    for n,symbol in enumerate(['MCH','MSN','MCH']):
        item=ArticleInput(title,'https://one.example/a',now,text=f'Cổ phiếu {symbol} chia cổ tức.',text_provenance='rss:description')
        ingest_cycle(session,[source()],now=now+timedelta(minutes=n),force=True,fetch=lambda _: [item])
        rows=client.get('/news/feed?research_category=COMPANY').json()
        assert rows[0]['representative_article']['tickers']==[symbol]
        assert rows[0]['ticker_associations'][0]['symbol']==symbol
        watched=intelligence(session,['MCH','MSN'],now=now+timedelta(minutes=n)+timedelta(seconds=1))['stocks']
        chosen=next(s for s in watched if s['symbol']==symbol)['news']['items'][0]
        versions.append(chosen['revision'])
        assert next(s for s in watched if s['symbol']!=symbol)['news']['items']==[]
    receipts=session.exec(select(NewsTextReceipt).order_by(NewsTextReceipt.sequence)).all()
    assert len(receipts)==3 and [r.sequence for r in receipts]==[1,2,3]
    assert receipts[0].text_hash==receipts[2].text_hash and receipts[0].id!=receipts[2].id
    # Returning to identical factual evidence need not become a new correction.
    assert versions[0]==versions[2]


def test_title_dedup_and_cross_publisher_url_match_do_not_borrow_body(session,client):
    now=datetime.now(timezone.utc)
    session.add_all([Security(symbol=s.symbol,company_name=s.company_name,exchange='HOSE',last_synced_at=now) for s in universe()]);session.commit()
    title='Thông tin doanh nghiệp trong tuần'
    first=ArticleInput(title,'https://one.example/a',now,text='Cổ phiếu MCH chia cổ tức.',text_provenance='rss:description')
    ingest_cycle(session,[source()],now=now,force=True,fetch=lambda _: [first])
    other=ArticleInput(title,'https://one.example/b',now,text='Cổ phiếu MSN chia cổ tức.',text_provenance='rss:description')
    ingest_cycle(session,[source()],now=now+timedelta(minutes=1),force=True,fetch=lambda _: [other])
    foreign=ArticleInput(title,first.url,now,text='Cổ phiếu USD trả cổ tức.',text_provenance='rss:description')
    ingest_cycle(session,[source('two')],now=now+timedelta(minutes=2),force=True,fetch=lambda _: [foreign])
    assert len(session.exec(select(NewsTextReceipt)).all())==1
    row=client.get('/news/feed?research_category=COMPANY').json()[0]
    assert row['representative_article']['url']==first.url
    assert row['representative_article']['tickers']==['MCH']


def test_new_body_association_never_backdates_snapshot_admission(session):
    from src.news.read_cache import research_rows
    now=datetime.now(timezone.utc)
    session.add_all([Security(symbol=s.symbol,company_name=s.company_name,exchange='HOSE',last_synced_at=now) for s in universe()]);session.commit()
    first=ArticleInput('Thông tin doanh nghiệp trong tuần','https://one.example/a',now)
    ingest_cycle(session,[source()],now=now,force=True,fetch=lambda _: [first])
    update=ArticleInput(first.title,first.url,now,text='Cổ phiếu MCH chia cổ tức.',text_provenance='rss:description')
    later=now+timedelta(minutes=2)
    ingest_cycle(session,[source()],now=later,force=True,fetch=lambda _: [update])
    assert research_rows(session,{'limit':12},category='COMPANY',now=now+timedelta(minutes=1))==[]
    assert research_rows(session,{'limit':12,'ticker':'MCH'},category='COMPANY',now=later)
