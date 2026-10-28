"""Isolated public-page fixtures. No canonical DB or external source calls."""
from datetime import datetime, timedelta, timezone
import pytest
from src.community.acquisition import SOURCES, acquire

NOW = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)


def sitemap_read(date, calls, body=b'unparseable post'):
    def read(url):
        calls.append(url)
        if url.endswith('/robots.txt'):
            return b'User-agent: *\nAllow: /'
        if url.endswith('/sitemap.xml'):
            return (f'<urlset><url><loc>https://chungsy.vn/posts/42</loc>'
                    f'<lastmod>{date}</lastmod></url></urlset>').encode()
        return body
    return read


def test_valid_quiet_sitemap_is_success_without_inventing_current_items(session):
    from src.community.daily import ingest_source, source_statuses
    calls = []
    read = sitemap_read('2026-10-12T08:00:00Z', calls)
    def fetch(source, stocks):
        return acquire(source, stocks, read=read, sleep=lambda _:None, now=NOW)
    assert ingest_source(session, SOURCES[2], fetch=fetch, now=NOW) == {'status':'ok','received':0}
    status = next(row for row in source_statuses(session, now=NOW) if row['source_id']==SOURCES[2].id)
    assert status['status']=='healthy' and status['last_success_at']==NOW
    assert len(calls)==2  # Robots + valid old sitemap; no artificial post fetch.


def test_recent_unparseable_post_remains_a_failure():
    calls = []
    with pytest.raises(ValueError):
        acquire(SOURCES[2], [], read=sitemap_read('2026-10-15T10:00:00Z', calls), sleep=lambda _:None, now=NOW)
    assert len(calls)==3


@pytest.mark.parametrize('date', ['not-a-date', '2026-10-16T10:00:00Z'])
def test_unqualified_sitemap_is_not_promoted_to_quiet_success(date):
    with pytest.raises(ValueError):
        acquire(SOURCES[2], [], read=sitemap_read(date, []), sleep=lambda _:None, now=NOW)


def test_sanitized_diagnostics_retain_cooldown_and_source_failure_isolation(session):
    from src.community.acquisition import PublicSourceError
    from src.community.daily import ingest_cycle, source_statuses
    calls=[]
    def fetch(source, stocks):
        calls.append(source.id)
        if source.id==SOURCES[0].id:
            raise PublicSourceError('UPSTREAM_TIMEOUT')
        return [], []
    result=ingest_cycle(session.get_bind(), sources=SOURCES[:2], fetch=fetch, now=NOW)
    assert result[SOURCES[0].id]=={'status':'error','error':'UPSTREAM_TIMEOUT'}
    assert result[SOURCES[1].id]=={'status':'ok','received':0}
    states={row['source_id']:row for row in source_statuses(session,now=NOW)}
    assert states[SOURCES[0].id]['status']=='error'
    assert states[SOURCES[0].id]['next_due_at']==NOW+timedelta(minutes=15)
    assert states[SOURCES[3].id]['next_due_at'] is None
    assert all(value['status']=='skipped' for value in ingest_cycle(session.get_bind(),sources=SOURCES[:2],fetch=fetch,now=NOW+timedelta(minutes=14)).values())
    assert calls==[SOURCES[0].id,SOURCES[1].id]


@pytest.mark.parametrize('failure,expected', [
    ('http','UPSTREAM_HTTP_429'),('timeout','UPSTREAM_TIMEOUT'),('connection','UPSTREAM_CONNECTION_ERROR')])
def test_public_transport_diagnostics_never_include_url_body_or_secrets(monkeypatch,failure,expected):
    from urllib.error import HTTPError,URLError
    import src.community.acquisition as module
    class Opener:
        def open(self,*args,**kwargs):
            assert kwargs['timeout']==15
            if failure=='http':raise HTTPError('https://example.test/?token=SECRET',429,'SECRET',{},None)
            if failure=='timeout':raise TimeoutError('SECRET')
            raise URLError('SECRET')
    monkeypatch.setattr(module,'build_opener',lambda *_:Opener())
    with pytest.raises(module.PublicSourceError) as exc:
        module.read_public('https://example.test/')
    assert str(exc.value)==expected and exc.value.code==expected


def test_robots_and_challenges_remain_fail_closed_with_distinct_codes():
    from src.community.acquisition import PublicSourceError
    for data,expected in [(b'User-agent: *\nDisallow: /','PUBLIC_ACCESS_LIMIT_OR_ROBOTS_RESTRICTION'),
                          (b'User-agent: *\nAllow: /','UPSTREAM_CHALLENGE')]:
        def read(url):return data if url.endswith('robots.txt') else b'Just a moment... cf-chl-'
        with pytest.raises(PublicSourceError) as exc:
            acquire(SOURCES[2],[],read=read,sleep=lambda _:None,now=NOW)
        assert exc.value.code==expected


def test_public_source_api_keeps_additive_scheduling_diagnostic(client, session, monkeypatch):
    from src.community.daily import ingest_source
    import src.community.acquisition as module
    assert ingest_source(session,SOURCES[2],fetch=lambda *_:([],[]),now=NOW)['status']=='ok'
    monkeypatch.setattr(module,'read_public',lambda *_:pytest.fail('HTTP status must not acquire'))
    response=client.get('/community/sources')
    assert response.status_code==200
    row=next(x for x in response.json() if x['source_id']==SOURCES[2].id)
    assert datetime.fromisoformat(row['next_due_at'].replace('Z','+00:00'))==NOW+timedelta(minutes=15)
