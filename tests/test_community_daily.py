"""Daily Community contracts, using synthetic public-page fixtures only."""
from datetime import datetime, timedelta, timezone
import json
import pytest
from src.community.adapters import parse_chungsy_post

NOW = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)


def test_public_chungsy_post_preserves_native_identity_time_and_ticker_context():
    record = {'postId': 'post-22', 'textContent': '$XYZ tây bán ròng, test hỗ trợ MA50',
              'publishDate': '2026-10-06T10:00:00Z', 'user_FullName': 'Public investor',
              'mentionedTickers': [{'symbol': 'XYZ', 'marketType': 'stock'}]}
    # Actual public SSR envelope; no private /api calls or executable page scripts.
    payload = '6:' + json.dumps(['$', 'div', None, {'initialPostData': record}])
    html = '<script>self.__next_f.push(' + json.dumps([1, payload]) + ')</script>'
    rows = parse_chungsy_post(html.encode(), 'https://chungsy.vn/posts/post-22')
    assert len(rows) == 1
    assert rows[0]['source_item_id'] == 'post-22' and rows[0]['item_type'] == 'post'
    assert rows[0]['direct_tickers'] == ['XYZ']
    assert rows[0]['published_at'] == NOW - timedelta(hours=2)
    assert rows[0]['replies'] is None and rows[0]['views'] is None
    assert rows[0]['excerpt'] == record['textContent']
    assert parse_chungsy_post(b'<html>Login</html>', 'https://chungsy.vn/posts/post-22') == []


def test_money_only_accepts_public_community_category_and_absolute_time():
    from src.community.adapters import parse_money_post
    data = b'<script type="application/ld+json">{"headline":"Stock XYZ","description":"Public discussion", "datePublished":"2026-10-06T19:00:00+07:00"}</script><div class="stock-relate-news-box"><a href="/stock/XYZ">XYZ</a></div>'
    url = 'https://24hmoney.vn/news/example-c30a222.html'
    row = parse_money_post(data, url)[0]
    assert row['source_item_id'] == '222'
    assert row['direct_tickers'] == ['XYZ']
    assert row['published_at'] == NOW
    assert parse_money_post(data, url.replace('c30', 'c4')) == []
    assert parse_money_post(b'<html></html>', url) == []


def test_f319_comment_has_its_own_timestamp_and_removes_quoted_old_content():
    from src.community.adapters import parse_f319_posts
    data = '<li class="message" id="post-99" data-author="Investor"><a class="datePermalink" href="/threads/example.22/page-3#post-99">06/10/2026, 19:00</a><blockquote class="messageText"><div class="bbCodeBlock">Old quoted foreign selling</div>cổ phiếu XYZ test hỗ trợ MA50</blockquote></li>'
    row = parse_f319_posts(data.encode(), 'https://newf319.com/threads/example.22/page-3', 'cổ phiếu XYZ')[0]
    assert row['id'] == 'f319_public:thread_comment:99'
    assert row['item_type'] == 'thread_comment'
    assert row['published_at'] == NOW
    assert 'Old quoted' not in row['excerpt']
    assert row['url'].endswith('#post-99')
    assert row['replies'] is None


def test_vietnam_day_is_not_observation_time_and_24h_is_explicit():
    from src.community.daily import time_window, in_window
    midnight = datetime(2026, 10, 6, 17, 5, tzinfo=timezone.utc)
    window = time_window(midnight)
    assert window['label'] == 'Today'
    assert window['start'] == datetime(2026, 10, 6, 17, tzinfo=timezone.utc)
    assert in_window(midnight - timedelta(minutes=4), window)
    assert not in_window(midnight - timedelta(minutes=6), window)
    assert not in_window(midnight + timedelta(seconds=1), window)
    fallback = time_window(midnight, 'last24h')
    assert fallback['label'] == 'Last 24 hours'
    assert in_window(midnight - timedelta(minutes=6), fallback)


def test_ingestion_restart_revisions_failure_isolation_and_today_api(session):
    from src.community.daily import ingest_source, pulse, source_statuses
    from src.community.acquisition import SOURCES
    from src.community.adapters import item
    from src.models import Stock
    session.add(Stock(symbol='XYZ', company_name='Example Company')); session.commit()
    row = item('chungsy_public', '22', 'https://chungsy.vn/posts/22', '$XYZ tây bán ròng', NOW - timedelta(hours=1), tickers=['XYZ'])
    fetch = lambda *_: ([row], [])
    assert ingest_source(session, SOURCES[2], fetch=fetch, now=NOW)['received'] == 1
    assert ingest_source(session, SOURCES[2], fetch=lambda *_: pytest.fail('not due'), now=NOW + timedelta(minutes=1))['status'] == 'skipped'
    first = pulse(session, ticker='XYZ', now=NOW)
    assert first['unique_items'] == 1
    assert first['items'][0]['tickers'] == ['XYZ']
    assert first['items'][0]['is_fixture'] is False
    assert first['themes'][0]['evidence_ids'] == [row['id']]
    before = first['items'][0]['revision_id']
    row['excerpt'] += ', test hỗ trợ MA50'
    assert ingest_source(session, SOURCES[2], fetch=fetch, now=NOW + timedelta(minutes=16))['status'] == 'ok'
    assert pulse(session, ticker='XYZ', now=NOW)['items'][0]['revision_id'] != before
    assert pulse(session, ticker='XYZ', now=NOW + timedelta(days=1))['items'] == []
    def fail(*_): raise RuntimeError('secret must not appear')
    assert ingest_source(session, SOURCES[2], fetch=fail, now=NOW + timedelta(minutes=32)) == {'status': 'error', 'error': 'RuntimeError'}
    state = source_statuses(session, now=NOW + timedelta(minutes=33))[2]
    assert state['status'] == 'error'
    assert state['items_received'] == 1
    assert state['last_success_at'] == NOW + timedelta(minutes=16)
    assert source_statuses(session, now=NOW)[3]['status'] == 'disabled'


def test_vietnamese_theme_attention_preserves_ids_breadth_and_independent_comments():
    from src.community.themes import deduplicate, extract_themes
    def row(identity, source, excerpt):
        return dict(id=identity, source_id=source, title=None, excerpt=excerpt, published_at=NOW, revision_id='r1', tickers=['XYZ'])
    rows = [row('a','one','cổ phiếu XYZ khối ngoại bán ròng'), row('b','two','XYZ tây bán, NN bán ròng'),
        row('c','one','XYZ test hỗ trợ MA50'), row('d','two','XYZ thủng MA, test hỗ trợ'),
        row('e','one','công suất tăng, lợi nhuận Dung Quất'), row('f','two','cổ tức chia thưởng'), row('g','one','kéo trụ tím break')]
    groups = deduplicate(rows)
    assert len(groups) == 7  # same ticker is never dedup evidence
    themes = extract_themes(groups, ['XYZ', 'Example Company'])
    assert len(themes) == 3
    foreign = next(t for t in themes if t['id'] == 'foreign_flows')
    technical = next(t for t in themes if t['id'] == 'technical_levels')
    assert foreign['item_count'] == 2 and foreign['source_count'] == 2
    assert set(foreign['evidence_ids']) == {'a','b'}
    assert set(technical['evidence_ids']) == {'c','d'}
    assert foreign['summary'] in [r['excerpt'] for r in rows]
    for phrase, expected in [('cổ tức chia thưởng','distributions'), ('kéo trụ tím break','price_action'), ('công suất lợi nhuận','earnings_capacity')]:
        assert extract_themes(deduplicate([row('solo','one',phrase)]))[0]['id'] == expected
    long = 'cổ phiếu XYZ: ' + 'khối ngoại bán ròng và các nhà đầu tư thảo luận về dòng tiền hôm nay. ' * 3
    copied = deduplicate([row('original','one',long),row('repost','two',long)])
    assert len(copied) == 1
    assert extract_themes(copied)[0]['source_count'] == 2
    assert extract_themes(copied)[0]['item_count'] == 1


def test_robots_restrictions_empty_and_upstream_errors_are_not_success(session):
    from src.community.acquisition import acquire, SOURCES
    from src.community.daily import ingest_source
    calls = []
    def read(url):
        calls.append(url)
        return b'User-agent: *\nDisallow: /'
    for source in SOURCES[:3]:
        with pytest.raises(ValueError): acquire(source, [], read=read, sleep=lambda _: None, now=NOW)
    assert all(url.endswith('/robots.txt') for url in calls)
    for source in SOURCES[:3]:
        def failed(*_): raise TimeoutError('secret auth token')
        assert ingest_source(session, source, fetch=failed, now=NOW)['status'] == 'error'
        assert ingest_source(session, source, fetch=lambda *_: ([], []), now=NOW+timedelta(minutes=16)) == {'status':'ok', 'received':0}


def test_today_api_reads_persisted_items_only_and_explicit_fallback(session, client, monkeypatch):
    from src.community.daily import ingest_source
    from src.community.acquisition import SOURCES
    from src.community.adapters import item
    from src.models import Stock
    now = datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ', company_name='Example Company')); session.commit()
    row = item('chungsy_public','api','https://chungsy.vn/posts/api','$XYZ tây bán',now-timedelta(seconds=1),tickers=['XYZ'])
    assert ingest_source(session,SOURCES[2],fetch=lambda *_: ([row],[]),now=now)['status']=='ok'
    monkeypatch.setattr('src.community.acquisition.read_public', lambda *_: pytest.fail('Read acquired upstream'))
    data = client.get('/community/pulse?ticker= xyz ').json()
    assert data['window']['label'] == 'Today'
    assert data['items'][0]['id'] == row['id']
    assert data['themes'][0]['evidence_revisions'][0]['revision_id'] == data['items'][0]['revision_id']
    assert client.get('/community/pulse?ticker=UNKNOWN').json()['items'] == []
    assert client.get('/community/pulse?window=last24h').json()['window']['label'] == 'Last 24 hours'
    assert client.get('/community/pulse?window=72h').status_code == 422


def test_money_body_without_description_and_malformed_items():
    from src.community.adapters import parse_money_post, parse_f319_posts
    url='https://24hmoney.vn/news/example-c30a222.html'
    data='<script type="application/ld+json">{"datePublished":"2026-10-06T19:00:00+07:00", "description":""}</script><div class="news-content"><div class="news-content-block">cổ phiếu XYZ test hỗ trợ</div></div>'
    assert parse_money_post(data.encode(),url)[0]['excerpt']=='cổ phiếu XYZ test hỗ trợ'
    assert parse_money_post(data.replace('2026-10-06T19:00:00+07:00','today').encode(),url)==[]
    assert parse_money_post(b'<script type="application/ld+json">broken</script>',url)==[]
    assert parse_f319_posts(b'<li class="message" id="post-bad"></li>', 'https://newf319.com/threads/example.22/')==[]


@pytest.mark.parametrize('source_index', [0,1,2])
def test_acquisition_is_bounded_public_and_deduplicates_discovery_links(source_index):
    from src.community.acquisition import acquire, SOURCES
    source=SOURCES[source_index]
    calls=[]
    public_post='<script>self.__next_f.push('+json.dumps([1, '6:'+json.dumps({'initialPostData':{'postId':'22','textContent':'$XYZ tây bán','publishDate':'2026-10-06T10:00:00Z'}})])+')</script>'
    money='<script type="application/ld+json">{"description":"cổ phiếu XYZ test hỗ trợ", "datePublished":"2026-10-06T10:00:00Z"}</script>'
    forum='<li class="message" id="post-99"><a class="datePermalink" href="threads/discussion.22/#post-99">06/10/2026, 17:00</a><blockquote class="messageText">cổ phiếu XYZ test hỗ trợ</blockquote></li>'
    from pathlib import Path
    listing=Path('tests/fixtures/community/listing.html').read_bytes()
    def read(url):
        calls.append(url)
        assert '/api/' not in url
        if source_index == 0:
            assert '/posts/' not in url
        if url.endswith('robots.txt'): return b'User-agent: *\nAllow: /\nDisallow: /api/'
        if url.endswith('sitemap.xml'): return b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://chungsy.vn/posts/22</loc><lastmod>2026-10-06T10:00:00Z</lastmod></url></urlset>'
        if url==source.url:
            return listing if source_index==0 else b'<a href="/news/example-c30a222.html?from_source=social">Post</a><a href="/news/example-c30a222.html">Duplicate discovery</a>'
        return [forum,money,public_post][source_index].encode()
    rows,_=acquire(source,[],read=read,sleep=lambda _:None,now=NOW)
    assert len(rows)==1 and rows[0]['source_id']==source.id
    assert len(calls)==3


def test_independent_source_failure_and_future_item_rejection(session):
    from src.community.acquisition import SOURCES
    from src.community.daily import ingest_cycle, pulse
    from src.community.adapters import item
    def fetch(source,stocks):
        if source.id==SOURCES[0].id: raise TimeoutError('private request')
        return [item(source.id,'future',source.url,'future claim',NOW+timedelta(seconds=1))],[]
    result=ingest_cycle(session.get_bind(),sources=SOURCES[:2],fetch=fetch,now=NOW)
    assert result[SOURCES[0].id]['status']=='error'
    assert result[SOURCES[1].id]=={'status':'ok','received':0}
    assert pulse(session,now=NOW)['items']==[]


def test_busy_other_tickers_cannot_hide_today_matches_before_the_view_cap(session):
    from src.community.models import CommunityEvidenceItem
    from src.community.daily import pulse
    for index in range(300):
        session.add(CommunityEvidenceItem(id=f'other:{index}',source_id='f319_public',source_item_id=str(index),
            item_type='thread_comment',excerpt='Other discussion',url='https://newf319.com/',published_at=NOW,
            first_seen_at=NOW,last_seen_at=NOW,tickers=['ABC'],revision_id='r1',is_fixture=True))
    session.add(CommunityEvidenceItem(id='matched',source_id='chungsy_public',source_item_id='matched',item_type='post',
        excerpt='XYZ tây bán',url='https://chungsy.vn/posts/matched',published_at=NOW-timedelta(minutes=1),
        first_seen_at=NOW,last_seen_at=NOW,tickers=['XYZ','OTHER'],revision_id='r1',is_fixture=True))
    session.commit()
    assert [r['id'] for r in pulse(session,ticker='XYZ',now=NOW)['items']]==['matched']
    assert pulse(session,ticker='XY',now=NOW)['items']==[]


def test_shared_publisher_links_do_not_create_a_recurring_discussion_theme():
    from src.community.themes import deduplicate,extract_themes
    rows=[dict(id='one',source_id='chungsy_public',title=None,excerpt='Thị phần môi giới đổi khác https://vietstock.vn/one',published_at=NOW,revision_id='r1',tickers=['XYZ']),
        dict(id='two',source_id='chungsy_public',title=None,excerpt='Bán lẻ mở chuỗi mới https://vietstock.vn/two',published_at=NOW,revision_id='r1',tickers=['XYZ'])]
    themes=extract_themes(deduplicate(rows),['XYZ'])
    assert len(themes)==2
    assert not any(theme['id'].startswith('phrase:') for theme in themes)


@pytest.mark.parametrize('prefix', ['', 'https://example.org/khoi-ngoai-ban-rong '])
def test_representative_excerpt_is_drawn_from_the_part_that_supports_the_theme(prefix):
    from src.community.themes import deduplicate,extract_themes
    body=prefix+'Bối cảnh thị trường hôm nay. '*20+'Khối ngoại bán ròng, nhà đầu tư bàn về dòng tiền.'
    row=dict(id='late',source_id='f319_public',title=None,excerpt=body,published_at=NOW,revision_id='r1',tickers=['XYZ'])
    theme=extract_themes(deduplicate([row]))[0]
    assert theme['id']=='foreign_flows'
    assert 'Khối ngoại bán ròng' in theme['summary']
    assert theme['summary'].strip('…') in body
