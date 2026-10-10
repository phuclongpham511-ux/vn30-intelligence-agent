from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from sqlmodel import Session, select, create_engine
from scripts import ingest_data
from src.db.session import create_tables
from src.community.models import CommunityThread, CommunityThreadObservation, CommunitySourceState
from src.community.service import ingest, parse_listing, source_status, SOURCE_ID
from src.news.models import NewsArticle, NewsSourceState
from src.news.registry import Source
from src.news.adapters import ArticleInput
from src.news.service import ingest_cycle
from src.news.normalization import utc

NOW = datetime(2026, 10, 6, 5, tzinfo=timezone.utc)
ROWS = parse_listing(Path('tests/fixtures/community/listing.html').read_bytes())
SOURCES = [Source(source_id=sid, name=sid, endpoint=f'https://{sid}.example/feed',
    country='VN', language='vi', category='VN', publisher_group=sid) for sid in ('good', 'bad')]


@pytest.fixture(autouse=True)
def isolate_universe_acquisition(monkeypatch):
    monkeypatch.setattr(ingest_data, 'sync_universe', lambda session: {'status': 'skipped'})
    monkeypatch.setattr(ingest_data, 'sync_index_groups', lambda session: {'status': 'skipped'})


def test_successful_observations_are_chronological_nullable_and_atomic(session):
    assert ingest(session, fetch=lambda: ROWS, now=NOW)['status'] == 'ok'
    changed = [dict(ROWS[0], replies=None, views=None)]
    assert ingest(session, fetch=lambda: changed, now=NOW + timedelta(minutes=30))['status'] == 'ok'
    thread = session.get(CommunityThread, ROWS[0]['id'])
    assert thread.replies is None and thread.views is None
    assert utc(thread.first_seen_at) == NOW
    observations = session.exec(select(CommunityThreadObservation).order_by(CommunityThreadObservation.observed_at)).all()
    assert [(utc(o.observed_at), o.replies, o.views) for o in observations] == [
        (NOW, 1234, 12345), (NOW + timedelta(minutes=30), None, None)]
    assert ingest(session, fetch=lambda: pytest.fail('Skipped cycle fetched'), now=NOW + timedelta(minutes=31)) == {'status': 'skipped'}
    def fail(): raise TimeoutError('secret request contents')
    assert ingest(session, fetch=fail, now=NOW + timedelta(hours=1))['status'] == 'error'
    # A failure after a partial write must roll back its observation too.
    assert ingest(session, fetch=lambda: [ROWS[0], {'id': 'invalid'}], now=NOW + timedelta(minutes=90))['status'] == 'error'
    assert len(session.exec(select(CommunityThreadObservation)).all()) == 2
    assert len(session.exec(select(CommunityThread)).all()) == 1
    assert source_status(session, now=NOW + timedelta(minutes=90))['last_success_at'] == NOW + timedelta(minutes=30)


def test_community_source_status_api_and_reads_never_acquire(session, client, monkeypatch):
    monkeypatch.setattr('src.community.service.acquire', lambda: pytest.fail('Read acquired upstream'))
    assert source_status(session, now=NOW)['status'] == 'not_attempted'
    assert client.get('/community/sources').json()[0]['last_success_at'] is None
    assert client.get('/community/pulse').status_code == 200
    ingest(session, fetch=lambda: ROWS, now=NOW)
    assert source_status(session, now=NOW + timedelta(minutes=60))['status'] == 'healthy'
    assert source_status(session, now=NOW + timedelta(minutes=61))['status'] == 'stale'
    state = session.get(CommunitySourceState, SOURCE_ID)
    state.last_error, state.last_attempt_at = 'TimeoutError', NOW + timedelta(minutes=61)
    session.add(state); session.commit()
    status = source_status(session, now=NOW + timedelta(minutes=61))
    assert status['status'] == 'error' and status['threads_received'] == 1
    response = client.get('/community/sources').json()[0]
    assert response['poll_interval_minutes'] == 15
    assert response['last_success_at'].endswith('Z')
    assert client.get('/community/pulse').json()['sampled_items'] == 0


def test_unified_worker_persisted_restart_cadence_and_source_failure(tmp_path, monkeypatch):
    url = 'sqlite:///' + str(tmp_path / 'restart.db')
    clock = [NOW]
    calls = []
    def news_fetch(source):
        calls.append(source.source_id)
        if source.source_id == 'bad': raise TimeoutError('secret')
        return [ArticleInput('Bank earnings increase', 'https://good.example/a', NOW)]
    def community_fetch(*_):
        calls.append('community')
        return [], ROWS
    monkeypatch.setattr(ingest_data, 'load_sources', lambda _: SOURCES)
    monkeypatch.setattr(ingest_data, 'ingest_cycle', lambda session, sources, **kw:
        ingest_cycle(session, sources, fetch=news_fetch, now=clock[0], **kw))
    from src.community.daily import ingest_cycle as daily_cycle
    from src.community.acquisition import SOURCES as community_sources
    monkeypatch.setattr(ingest_data, 'ingest_community', lambda engine:
        daily_cycle(engine, sources=community_sources[:1], fetch=community_fetch, now=clock[0]))
    engine = create_engine(url); create_tables(engine)
    result = ingest_data.run_cycle(engine)
    assert result['news']['bad']['status'] == 'error'
    assert result['community'][SOURCE_ID]['status'] == 'ok' and ingest_data.failed(result)
    assert sorted(calls) == ['bad', 'community', 'good']
    engine.dispose()  # actual reconnect to persisted state, not an in-memory timer
    engine = create_engine(url); create_tables(engine)
    clock[0] += timedelta(minutes=1)
    result = ingest_data.run_cycle(engine)
    assert result == {'universe': {'status': 'skipped'}, 'groups': {'status': 'skipped'}, 'news': {}, 'community': {SOURCE_ID: {'status': 'skipped'}}, 'technical_eod': {'status': 'IDLE'}}
    assert sorted(calls) == ['bad', 'community', 'good']
    with Session(engine) as session:
        assert utc(session.get(NewsSourceState, 'good').last_success_at) == NOW
        assert utc(session.get(CommunitySourceState, SOURCE_ID).last_success_at) == NOW
    clock[0] = NOW + timedelta(minutes=30)
    result = ingest_data.run_cycle(engine)
    with Session(engine) as session:
        assert len(session.exec(select(NewsArticle)).all()) == 1
        assert len(session.exec(select(CommunityThread)).all()) == 1
        assert len(session.exec(select(CommunityThreadObservation)).all()) == 2
    engine.dispose()


@pytest.mark.parametrize('broken', ['news', 'community'])
def test_unexpected_domain_exception_does_not_suppress_other_domain(session, monkeypatch, broken):
    calls = []
    def invoke(domain):
        calls.append(domain)
        if domain == broken: raise RuntimeError('private contents')
        return {} if domain == 'news' else {'status': 'ok'}
    monkeypatch.setattr(ingest_data, 'load_sources', lambda _: [])
    monkeypatch.setattr(ingest_data, 'ingest_cycle', lambda *a, **kw: invoke('news'))
    monkeypatch.setattr(ingest_data, 'ingest_community', lambda *a: invoke('community'))
    result = ingest_data.run_cycle(session.get_bind())
    assert calls == ['news', 'community']
    assert result[broken] == {'status': 'error', 'error': 'RuntimeError'}


def test_failed_security_master_does_not_suppress_news_or_community(session, monkeypatch):
    calls = []
    def fail(*_): raise TimeoutError('private contents')
    monkeypatch.setattr(ingest_data, 'sync_universe', fail)
    monkeypatch.setattr(ingest_data, 'load_sources', lambda _: [])
    monkeypatch.setattr(ingest_data, 'ingest_cycle', lambda *a, **kw: calls.append('news') or {})
    monkeypatch.setattr(ingest_data, 'ingest_community', lambda *a: calls.append('community') or {})
    result = ingest_data.run_cycle(session.get_bind())
    assert calls == ['news', 'community']
    assert result['universe'] == {'status':'error','error':'TimeoutError'}


def test_watch_continues_after_failure_and_wait_is_interruptible(session, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(ingest_data, 'run_cycle', lambda *a, **kw: calls.append(kw) or
        {'news': {'status': 'error', 'error': 'RuntimeError'}, 'community': {SOURCE_ID: {'status': 'skipped'}}})
    class Stop:
        def is_set(self): return len(calls) >= 2
        def wait(self, seconds): assert seconds == 60
    assert ingest_data.run(session.get_bind(), watch=True, stop=Stop()) == 0
    assert len(calls) == 2 and 'RuntimeError' in capsys.readouterr().out


def test_worker_entrypoint_handles_keyboard_interrupt_and_restores_signal(monkeypatch):
    import signal
    original = signal.getsignal(signal.SIGTERM)
    monkeypatch.setattr('sys.argv', ['ingest_data', '--watch'])
    monkeypatch.setattr(ingest_data, 'create_tables', lambda: None)
    monkeypatch.setattr(ingest_data, 'get_engine', lambda: None)
    def interrupt(*args, **kwargs): raise KeyboardInterrupt
    monkeypatch.setattr(ingest_data, 'run', interrupt)
    assert ingest_data.main() == 0
    assert signal.getsignal(signal.SIGTERM) == original
