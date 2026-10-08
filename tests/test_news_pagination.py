from datetime import datetime, timedelta, timezone
from src.news.adapters import ArticleInput
from src.news.service import ingest_cycle
from tests.test_news import source


def illustrated(*args):
    return ArticleInput(*args,thumbnail_url="https://image.example/photo.jpg",thumbnail_provenance="media:thumbnail")


def test_archive_pages_keep_one_earliest_representative_and_expire_by_publication(session, client, monkeypatch):
    now=datetime(2030,1,10,12,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None): return now
    monkeypatch.setattr('routers.news.datetime',Clock)
    for sid, age in [('early',3),('late',1)]:
        ingest_cycle(session,[source(sid)],now=now,force=True,fetch=lambda _,sid=sid,age=age:[
            illustrated('Steel industry production grows',f'https://{sid}.example/a',now-timedelta(hours=age))])
    for i in range(3):
        ingest_cycle(session,[source('extra')],now=now,force=True,fetch=lambda _,i=i:[
            illustrated(f'Banking sector changes regulation {i+10}',f'https://extra.example/{i}',now-timedelta(hours=4+i))])
    first=client.get('/news/feed?research_category=INDUSTRY&limit=2').json()
    assert len(first)==2 and first[0]['representative_article']['source_id']=='early'
    assert len(first[0]['articles'])==2
    second=client.get('/news/feed?research_category=INDUSTRY&limit=2&offset=2').json()
    assert len(second)==2 and not ({x['story']['id'] for x in first}&{x['story']['id'] for x in second})
    assert client.get('/news/feed?offset=-1').status_code==422
    now+=timedelta(hours=72)
    assert client.get('/news/feed?research_category=INDUSTRY').json()==[]


def test_hot_topics_require_independent_publishers_and_reingestion_does_not_add_mentions(session,client):
    now=datetime.now(timezone.utc)
    src=source('one')
    ingest_cycle(session,[src],now=now,fetch=lambda _:[
        illustrated('Steel industry production grows', 'https://one.example/a',now),
        illustrated('Steel industry production grows strongly','https://one.example/b',now)])
    assert client.get('/news/hot').json()==[]
    ingest_cycle(session,[source('two')],now=now,fetch=lambda _:[
        illustrated('Steel industry production grows', 'https://two.example/a',now)])
    assert len(client.get('/news/hot').json())==1
    ingest_cycle(session,[src],now=now,force=True,fetch=lambda _:[
        illustrated('Steel industry production grows','https://one.example/a',now)])
    assert client.get('/news/hot').json()[0]['story']['article_count']==3


def test_page_snapshot_does_not_shift_when_new_articles_arrive(session,client,monkeypatch):
    now=datetime(2030,1,10,12,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None): return now
    monkeypatch.setattr('routers.news.datetime',Clock)
    src=source()
    incoming=[illustrated(f'Banking sector regulation changes {n}',f'https://one.example/{n}',now-timedelta(minutes=n)) for n in range(10,14)]
    ingest_cycle(session,[src],now=now,fetch=lambda _:incoming)
    first=client.get('/news/feed/page?research_category=INDUSTRY&limit=2').json()
    assert len(first['items'])==2 and first['has_more'] and first['next_offset']==2
    assert first['items'][0]['representative_article']['published_at']=='2030-01-10T11:50:00Z'
    now+=timedelta(minutes=5)
    ingest_cycle(session,[src],now=now,force=True,fetch=lambda _:[illustrated('Steel industry production grows','https://one.example/new',now)])
    second=client.get('/news/feed/page',params={'research_category':'INDUSTRY','limit':2,'offset':2,'as_of':first['as_of']}).json()
    assert len(second['items'])==2 and not second['has_more'] and second['next_offset'] is None
    ids=[x['story']['id'] for x in first['items']+second['items']]
    assert len(set(ids))==4
    latest=client.get('/news/feed/page?research_category=INDUSTRY').json()
    assert len(latest['items'])==5
    assert latest['items'][0]['representative_article']['url']=='https://one.example/new'
    for bad in ('2030-01-10T12:10:00Z','2030-01-10T12:00:00'):
        assert client.get('/news/feed/page',params={'as_of':bad}).status_code==422


def test_publication_expiry_does_not_delete_evidence_or_renew_on_reingestion(session,client,monkeypatch):
    from sqlmodel import select
    from src.news.models import NewsArticle
    now=datetime(2030,1,10,12,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None): return now
    monkeypatch.setattr('routers.news.datetime',Clock)
    src=source();old=illustrated('Steel industry production grows','https://one.example/a',now-timedelta(hours=71))
    ingest_cycle(session,[src],now=now,fetch=lambda _:[old])
    first=client.get('/news/feed/page?research_category=INDUSTRY').json()
    assert len(first['items'])==1
    now+=timedelta(hours=2)
    ingest_cycle(session,[src],now=now,force=True,fetch=lambda _:[old])
    assert client.get('/news/feed/page?research_category=INDUSTRY').json()['items']==[]
    assert len(session.exec(select(NewsArticle)).all())==1
    assert client.get('/news/stories/'+first['items'][0]['story']['id']).status_code==200
