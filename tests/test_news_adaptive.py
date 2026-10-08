from datetime import datetime, timedelta, timezone
from src.news.registry import Source
from src.news.scheduling import NewsSchedule, cadence_minutes


def source(priority='standard', sid='one'):
    return Source(source_id=sid, name=sid, country='VN', language='vi',
                  endpoint=f'https://{sid}.example/rss', category='VN',
                  publisher_group=sid, scheduling_priority=priority)


def vn_time(day, hour, minute=0):
    return datetime(2026, 10, day, hour-7, minute, tzinfo=timezone.utc)


def test_adaptive_cadences_follow_vietnam_session_heuristic():
    config = NewsSchedule()
    assert cadence_minutes(source('priority'), vn_time(8, 10), config) == 30
    assert cadence_minutes(source(), vn_time(8, 10), config) == 120
    assert cadence_minutes(source(), vn_time(8, 12), config) == 240
    assert cadence_minutes(source(), vn_time(8, 18), config) == 240
    assert cadence_minutes(source(), vn_time(10, 10), config) == 360


def test_fresh_sources_skip_and_stale_visitors_coalesce_until_worker(session):
    from src.news.service import ingest_cycle
    from src.news.scheduling import request_due_refresh
    from src.news.models import NewsSourceState
    from src.news.normalization import utc
    now = vn_time(8, 10)
    feeds = [source('priority', 'fresh'), source('priority', 'old')]
    calls = []
    ingest_cycle(session, [feeds[1]], now=now-timedelta(hours=3), fetch=lambda s: calls.append(s.source_id) or [])
    ingest_cycle(session, [feeds[0]], now=now-timedelta(minutes=15), fetch=lambda s: calls.append(s.source_id) or [])
    for n in range(10):
        response = request_due_refresh(session, feeds, now=now+timedelta(seconds=n))
        assert response['requested'] == (1 if n == 0 else 0)
    assert calls == ['old', 'fresh']  # visitors perform zero fetches
    state = session.get(NewsSourceState, 'old')
    session.refresh(state)
    assert utc(state.refresh_requested_at) == now and state.refresh_requests == 1
    result = ingest_cycle(session, feeds, now=now+timedelta(minutes=2), fetch=lambda s: calls.append(s.source_id) or [])
    assert set(result) == {'old'} and calls == ['old', 'fresh', 'old']
    session.refresh(state)
    assert state.refresh_requested_at is None


def test_failure_backoff_preserves_success_and_empty_cycles_reuse_hot_cache(session):
    from src.news.service import ingest_cycle
    from src.news.models import NewsSourceState, NewsReadCache
    from src.news.normalization import utc
    now = vn_time(8, 10)
    feed = source('priority')
    ingest_cycle(session, [feed], now=now, fetch=lambda _: [])
    count = session.get(NewsReadCache, 'research').refresh_count
    def fail(_): raise TimeoutError('private response must not persist')
    first = now+timedelta(minutes=30)
    assert ingest_cycle(session, [feed], now=first, fetch=fail)['one']['status'] == 'error'
    state = session.get(NewsSourceState, 'one')
    assert utc(state.last_success_at) == now
    assert utc(state.next_due_at) == first+timedelta(minutes=30)
    assert state.last_error == 'TimeoutError'
    assert ingest_cycle(session, [feed], now=first+timedelta(minutes=29), fetch=fail) == {}
    second = first+timedelta(minutes=30)
    ingest_cycle(session, [feed], now=second, fetch=fail)
    session.refresh(state)
    assert state.consecutive_failures == 2 and utc(state.next_due_at) == second+timedelta(minutes=60)
    ingest_cycle(session, [feed], now=second+timedelta(minutes=60), fetch=lambda _: [])
    session.refresh(state)
    assert state.consecutive_failures == 0 and state.last_error is None
    assert session.get(NewsReadCache, 'research').refresh_count == count


def test_bounded_parallel_fetches_continue_after_source_failure(session):
    from threading import Lock, Event
    from src.news.service import ingest_cycle
    active = peak = 0
    lock, overlap = Lock(), Event()
    calls = []
    def fetch(feed):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
            calls.append(feed.source_id)
            if active == 2: overlap.set()
        assert overlap.wait(2)
        with lock: active -= 1
        if feed.source_id == 'bad': raise TimeoutError()
        return []
    feeds = [source(sid=sid) for sid in ['bad', 'good', 'later']]
    result = ingest_cycle(session, feeds, now=vn_time(8, 10), fetch=fetch,
                          config=NewsSchedule(max_sources_per_cycle=2))
    assert peak == 2 and len(calls) == 2
    assert result['bad']['status'] == 'error' and result['good']['status'] == 'ok'


def test_two_workers_and_simultaneous_visitors_share_database_claims(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, Lock
    from sqlmodel import Session, create_engine
    from src.db.session import create_tables
    from src.news.service import ingest_cycle
    from src.news.scheduling import request_due_refresh
    engine = create_engine('sqlite:///'+str(tmp_path/'shared.db'), connect_args={'check_same_thread': False})
    create_tables(engine)
    feed, now = source('priority'), vn_time(8, 10)
    def visit(_):
        with Session(engine) as session:
            return request_due_refresh(session, [feed], now=now)
    with ThreadPoolExecutor(max_workers=4) as pool:
        visitors = list(pool.map(visit, range(10)))
    assert sum(row['requested'] for row in visitors) == 1
    started, release = Event(), Event()
    calls = []
    def fetch(_):
        calls.append('fetch')
        started.set()
        assert release.wait(3)
        return []
    def worker():
        with Session(engine) as session:
            return ingest_cycle(session, [feed], now=now, fetch=fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(worker)
        assert started.wait(2)
        second = pool.submit(worker)
        assert second.result(timeout=2) == {}
        release.set()
        assert first.result(timeout=3)['one']['status'] == 'ok'
    assert calls == ['fetch']
    engine.dispose()
    # Real reconnect: cadence survives restart.
    engine = create_engine('sqlite:///'+str(tmp_path/'shared.db'))
    with Session(engine) as session:
        assert ingest_cycle(session, [feed], now=now+timedelta(minutes=1), fetch=lambda _: 1/0) == {}
    engine.dispose()


def test_crashed_claim_expires_and_old_owner_cannot_reclaim(session):
    from src.news.scheduling import claim
    from src.news.service import ingest_cycle
    from src.news.models import NewsSourceState
    now, feed, config = vn_time(8, 10), source('priority'), NewsSchedule()
    token = claim(session, feed, now, config)
    assert token
    assert ingest_cycle(session, [feed], now=now+timedelta(minutes=9), fetch=lambda _: 1/0) == {}
    result = ingest_cycle(session, [feed], now=now+timedelta(minutes=10), fetch=lambda _: [])
    assert result['one']['status'] == 'ok'
    session.expire_all()
    assert session.get(NewsSourceState, 'one').lease_token is None


def test_cached_reads_do_not_fetch_or_build_and_page_size_is_bounded(session, client, monkeypatch):
    from src.news.service import ingest_cycle
    from src.news.adapters import ArticleInput
    now = datetime.now(timezone.utc)
    ingest_cycle(session, [source()], now=now, fetch=lambda _: [ArticleInput(
        f'Banking sector regulation changes {n}', f'https://one.example/{n}', now,
        'https://image.example/a.jpg', 'media:thumbnail') for n in range(10,25)])
    def forbidden(*a, **kw): raise AssertionError('HTTP attempted acquisition or projection build')
    monkeypatch.setattr('src.news.service.acquire', forbidden)
    monkeypatch.setattr('src.news.read.build_research_rows', forbidden)
    page = client.get('/news/feed/page?research_category=INDUSTRY&limit=100').json()
    assert len(page['items']) == 12 and page['next_offset'] == 12
    assert client.get('/news/hot').json() == []
    assert client.get('/news/top').status_code == 200
    assert client.get('/news/top?require_image=true').status_code == 200
    response = client.post('/news/refresh').json()
    assert response['status'] == 'pending_worker' and 'does not start a worker' in response['execution']


def test_global_slots_bound_different_sources_across_workers(tmp_path):
    from threading import Event, Lock
    from concurrent.futures import ThreadPoolExecutor
    from sqlmodel import Session, create_engine
    from src.db.session import create_tables
    from src.news.service import ingest_cycle
    engine = create_engine('sqlite:///'+str(tmp_path/'slots.db'), connect_args={'check_same_thread': False})
    create_tables(engine)
    release, occupied, lock = Event(), Event(), Lock()
    calls = []
    def fetch(feed):
        with lock:
            calls.append(feed.source_id)
            if len(calls) == 2: occupied.set()
        assert release.wait(3)
        return []
    def worker(feeds):
        with Session(engine) as session:
            return ingest_cycle(session, feeds, now=vn_time(8, 10), fetch=fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(worker, [source(sid='a'), source(sid='b')])
        assert occupied.wait(2)
        assert pool.submit(worker, [source(sid='c'), source(sid='d')]).result(timeout=2) == {}
        release.set()
        assert len(first.result(timeout=3)) == 2
    assert set(calls) == {'a','b'}
    engine.dispose()


def test_projection_recovers_if_worker_crashes_after_evidence_commit(session, client, monkeypatch):
    from src.news.service import ingest_cycle
    from src.news.adapters import ArticleInput
    import src.news.read_cache as cache
    now = datetime.now(timezone.utc)
    original = cache.refresh_cache
    def crash(*a, **kw): raise RuntimeError('simulated worker interruption')
    monkeypatch.setattr(cache, 'refresh_cache', crash)
    import pytest
    with pytest.raises(RuntimeError):
        ingest_cycle(session, [source()], now=now, fetch=lambda _: [ArticleInput(
            'Steel industry output expands','https://one.example/a',now,'https://image.example/a.jpg','media:thumbnail')])
    # Empty cache serves an honest empty response and durable intent, no HTTP rebuild.
    assert client.get('/news/feed?research_category=INDUSTRY').json() == []
    monkeypatch.setattr(cache, 'refresh_cache', original)
    assert ingest_cycle(session, [], now=now+timedelta(seconds=1)) == {}
    assert len(client.get('/news/feed?research_category=INDUSTRY').json()) == 1


def test_timeout_configuration_reaches_transport_and_no_immediate_retries(session, monkeypatch):
    from src.news.service import ingest_cycle
    from src.news.models import NewsSourceState
    calls = []
    def transport(request, timeout, context):
        calls.append(timeout)
        raise TimeoutError('upstream response')
    monkeypatch.setattr('src.news.adapters.urlopen', transport)
    result = ingest_cycle(session, [source()], now=vn_time(8,10), config=NewsSchedule(timeout_seconds=3))
    assert calls == [3] and result['one']['status'] == 'error'
    assert session.get(NewsSourceState,'one').last_success_at is None


def test_stale_cache_returns_while_provider_is_blocked(session, client, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from sqlmodel import Session
    from src.news.service import ingest_cycle
    from src.news.adapters import ArticleInput
    from src.news.models import NewsSourceState
    import time
    now, feed = datetime.now(timezone.utc), source('priority', 'cafef')
    ingest_cycle(session, [feed], now=now-timedelta(hours=6), fetch=lambda _: [ArticleInput(
        'Steel industry output expands','https://cafef.example/a',now-timedelta(hours=6),
        'https://image.example/a.jpg','media:thumbnail')])
    started, release = Event(), Event()
    def slow(_):
        started.set()
        assert release.wait(3)
        return []
    def worker():
        with Session(session.get_bind()) as own:
            return ingest_cycle(own,[feed],now=now,fetch=slow)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        assert started.wait(2)
        begin = time.perf_counter()
        response = client.get('/news/feed/page?research_category=INDUSTRY')
        duration = time.perf_counter()-begin
        assert response.status_code == 200 and len(response.json()['items']) == 1
        assert not future.done() and duration < 1
        release.set()
        assert future.result(timeout=3)['cafef']['status'] == 'ok'


def test_snapshot_can_finish_after_story_expires_and_worker_refreshes(session, client, monkeypatch):
    from src.news.service import ingest_cycle
    from src.news.adapters import ArticleInput
    now = datetime(2030,1,10,12,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return now
    monkeypatch.setattr('routers.news.datetime',Clock)
    def item(n, age):
        return ArticleInput(f'Banking sector regulation changes {n}',f'https://one.example/{n}',
                            now-timedelta(hours=age),'https://image.example/a.jpg','media:thumbnail')
    ingest_cycle(session,[source()],now=now,fetch=lambda _:[item(10,1),item(11,71.5)])
    first = client.get('/news/feed/page?research_category=INDUSTRY&limit=1').json()
    now += timedelta(hours=1)
    ingest_cycle(session,[source(sid='new')],now=now,fetch=lambda _:[item(12,0)])
    second = client.get('/news/feed/page', params={'research_category':'INDUSTRY','limit':1,
                        'offset':1,'as_of':first['as_of']}).json()
    assert len(second['items']) == 1 and second['items'][0]['representative_article']['url'].endswith('/11')
    current = client.get('/news/feed/page?research_category=INDUSTRY').json()
    assert len(current['items']) == 2


def test_duplicate_observation_renews_image_retry_without_rebuilding_hot(session, client, monkeypatch):
    from src.news.service import ingest_cycle
    from src.news.adapters import ArticleInput
    from src.news.models import NewsReadCache
    now = datetime.now(timezone.utc)-timedelta(minutes=2)
    article = ArticleInput('Steel industry output expands','https://one.example/a',now,
                           'https://image.example/a.jpg','media:thumbnail')
    ingest_cycle(session,[source()],now=now,fetch=lambda _:[article])
    first = client.get('/news/feed?research_category=INDUSTRY').json()[0]
    count = session.get(NewsReadCache,'research').refresh_count
    def forbidden(*a, **kw): raise AssertionError('Duplicate cycle rebuilt research')
    monkeypatch.setattr('src.news.read.build_research_rows',forbidden)
    ingest_cycle(session,[source()],now=now+timedelta(minutes=1),force=True,fetch=lambda _:[article])
    second = client.get('/news/feed?research_category=INDUSTRY').json()[0]
    assert second['articles'][0]['last_seen_at'] != first['articles'][0]['last_seen_at']
    assert second['story']['id'] == first['story']['id']
    assert session.get(NewsReadCache,'research').refresh_count == count


def test_accepted_clock_skew_publication_becomes_visible_without_another_fetch(session, client, monkeypatch):
    from src.news.service import ingest_cycle
    from src.news.adapters import ArticleInput
    now = datetime(2030,1,10,12,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return now
    monkeypatch.setattr('routers.news.datetime',Clock)
    ingest_cycle(session,[source()],now=now,fetch=lambda _:[ArticleInput(
        'Steel industry output expands','https://one.example/future',now+timedelta(minutes=5),
        'https://image.example/a.jpg','media:thumbnail')])
    assert client.get('/news/feed?research_category=INDUSTRY').json() == []
    now += timedelta(minutes=5)
    assert len(client.get('/news/feed?research_category=INDUSTRY').json()) == 1
