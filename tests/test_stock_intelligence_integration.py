"""Stock Detail reuses persisted research; all evidence and SQL are test fixtures."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import event
from src.models import Stock
from src.community.models import CommunityEvidenceItem
from src.services.watchlist_intelligence import intelligence, community_page
from tests.test_news import ingest, item, source


def test_stock_research_windows_and_source_provenance_remain_canonical(session, monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr('src.services.watchlist_intelligence.load_sources', lambda: [source()])
    session.add_all([Stock(symbol='XYZ'), Stock(symbol='ABC')]); session.commit()
    ingest(session, [item('XYZ reports older earnings', 'https://one.example/old', now-timedelta(hours=80))], now=now-timedelta(hours=73))
    ingest(session, [item('XYZ announces profit', 'https://one.example/current', now-timedelta(hours=2)),
        item('ABC reports profit', 'https://one.example/foreign', now-timedelta(hours=1))], now=now-timedelta(hours=1))
    result = intelligence(session, ['XYZ'], now=now)
    news = result['stocks'][0]['news']
    assert news['window_start'] == now-timedelta(hours=72)
    assert len(news['items']) == 1
    evidence = news['items'][0]['evidence'][0]
    assert evidence['source_name'] == 'One' and evidence['published_at'] != evidence['first_seen_at']
    assert evidence['tickers'] == ['XYZ']
    assert result['stocks'][0]['community']['window_start'] == now-timedelta(hours=24)


def test_existing_pulse_dedup_groups_copy_text_but_keeps_independent_native_ids(session):
    now = datetime.now(timezone.utc)
    long_text = 'XYZ company results and original financial discussion with explicit source context. ' * 4
    for identity, excerpt in [('one', long_text), ('copy', long_text), ('separate', 'XYZ short independent comment')]:
        session.add(CommunityEvidenceItem(id=identity, source_id='f319_public', source_item_id=identity,
            item_type='post', title=None, excerpt=excerpt, url='https://newf319.com/threads/'+identity,
            published_at=now-timedelta(hours=1), first_seen_at=now-timedelta(minutes=30), last_seen_at=now,
            tickers=['XYZ'], replies=None, views=0, revision_id='v1', is_fixture=True))
    session.commit()
    original = community_page(session, 'XYZ', now, 0, 12, ['f319_public'])
    result = community_page(session, 'XYZ', now, 0, 12, ['f319_public'], group_copies=True)
    assert 'display_groups' not in original and result['items'] == original['items']
    assert len(result['items']) == 3 and len(result['display_groups']) == 2
    assert sorted(len(group) for group in result['display_groups']) == [1, 2]
    assert {entry['entity_id'] for entry in result['items']} == {'one', 'copy', 'separate'}
    assert all(entry['evidence']['views'] == 0 and entry['evidence']['replies'] is None for entry in result['items'])


def test_stock_detail_persisted_read_is_select_only_and_cannot_acquire_sources(client, session, monkeypatch):
    session.add(Stock(symbol='XYZ')); session.commit()
    def forbidden(*_args, **_kwargs): raise AssertionError('No acquisition in Stock Detail')
    monkeypatch.setattr('src.news.adapters.acquire', forbidden)
    monkeypatch.setattr('src.community.acquisition.acquire', forbidden)
    monkeypatch.setattr('src.community.daily.acquire', forbidden)
    monkeypatch.setattr('src.services.technical_eod_store.capture_fresh_ssi_read', forbidden)
    queries = []
    def capture(_conn, _cursor, query, *_args): queries.append(query)
    event.listen(session.get_bind(), 'before_cursor_execute', capture)
    try:
        reply = client.post('/watchlists/intelligence', json={'symbols':['XYZ'], 'offset':0, 'page_size':12, 'community_groups':True})
        assert reply.status_code == 200
        body = reply.json()
        assert len(body['stocks']) == 1 and body['stocks'][0]['symbol'] == 'XYZ'
        assert queries and all(query.lstrip().upper().startswith('SELECT') for query in queries)
        assert 'display_groups' in body['stocks'][0]['community']
    finally:
        event.remove(session.get_bind(), 'before_cursor_execute', capture)
