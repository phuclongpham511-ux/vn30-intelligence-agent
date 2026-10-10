"""Public Watchlist contracts over synthetic persisted evidence only."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import event
from sqlmodel import select

from src.models import Stock,Security
from src.news.models import NewsArticle,NewsStory
import pytest
from src.community.models import CommunityEvidenceItem
from src.services.watchlist_intelligence import intelligence
from tests.test_news import ingest, item, source
from test_technical_eod_persistence import setup, run, fresh


def configure(monkeypatch):
    monkeypatch.setattr('src.services.watchlist_intelligence.load_sources',lambda:[source(),source('two')])


def discussion(session, now, id='discussion-1', ticker='XYZ'):
    row=CommunityEvidenceItem(id=id,source_id='chungsy_public',source_item_id=id,
        item_type='post',title=None,excerpt='A public XYZ discussion',url='https://chungsy.vn/posts/'+id,
        published_at=now-timedelta(minutes=1),first_seen_at=now-timedelta(minutes=1),
        last_seen_at=now,tickers=[ticker],revision_id='native-1')
    session.add(row);session.commit();return row


def test_public_empty_invalid_bounds_and_unknown_counts(client):
    assert client.post('/watchlists/intelligence',json={'symbols':[]}).json()['stocks']==[]
    for body in [{'symbols':['BAD!']},{'symbols':['XYZ']*51},{'symbols':['XYZ'],'page_size':13},
                 {'symbols':['XYZ'],'offset':-1},{'symbols':['XYZ'],'offset':997}]:
        assert client.post('/watchlists/intelligence',json=body).status_code==422
    row=client.post('/watchlists/intelligence',json={'symbols':['XYZ']}).json()['stocks'][0]
    assert row['status']=='unavailable'
    assert row['news'] is row['community'] is row['technical'] is None


def test_unified_exact_company_story_identity_not_article_counts(session,monkeypatch,client):
    configure(monkeypatch)
    now=datetime.now(timezone.utc)
    session.add_all([Stock(symbol='XYZ',company_name='Example issuer'),Stock(symbol='ABC')]);session.commit()
    ingest(session,[item('XYZ earnings rise','https://one.example/xyz',now)],now=now-timedelta(minutes=2))
    ingest(session,[item('XYZ earnings rise','https://two.example/xyz',now)],sources=[source('two')],now=now-timedelta(minutes=1))
    ingest(session,[item('ABC reports profit','https://one.example/abc',now),item('Stock market rises with XYZ','https://one.example/market',now)],now=now)
    discussion(session,now)
    discussion(session,now,'other','ABC')
    row=client.post('/watchlists/intelligence',json={'symbols':[' xyz ','XYZ']}).json()['stocks'][0]
    assert row['company_name']=='Example issuer'
    assert len(row['news']['items'])==1
    story=row['news']['items'][0]
    assert story['id']=='news:'+story['entity_id']
    assert story['source_count']==2 and len(story['evidence'])==2
    assert all('XYZ' in a['tickers'] for a in story['evidence'])
    assert len(row['community']['items'])==1
    assert row['community']['items'][0]['id']=='community:discussion-1'
    assert row['technical']['data']['kind']=='diagnostic' and row['technical']['items']==[]


def test_news_reingestion_duplicate_sources_revisions_withdrawal_and_stable_anchor(session,monkeypatch):
    configure(monkeypatch)
    now=datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ'));session.commit()
    old=now-timedelta(hours=71)
    ingest(session,[item('XYZ earnings rise','https://one.example/a',old)],now=old)
    before=intelligence(session,['XYZ'],now=now)['stocks'][0]['news']['items'][0]
    ingest(session,[item('XYZ earnings rise','https://two.example/a',now)],sources=[source('two')],now=now)
    after=intelligence(session,['XYZ'],now=now)['stocks'][0]['news']['items'][0]
    assert (before['id'],before['revision'])==(after['id'],after['revision'])
    assert len(after['revision_members'])==2
    aged=intelligence(session,['XYZ'],now=now+timedelta(hours=2))['stocks'][0]['news']['items'][0]
    assert aged['revision']==before['revision']
    article=session.exec(select(NewsArticle).where(NewsArticle.source_id=='two')).one()
    article.title='XYZ reports revised profit';session.add(article);session.commit()
    revised=intelligence(session,['XYZ'],now=now)['stocks'][0]['news']['items'][0]
    assert revised['revision_members'][article.id]!=after['revision_members'][article.id]
    for article in session.exec(select(NewsArticle)).all():
        article.tickers=[];session.add(article)
    session.commit()
    assert intelligence(session,['XYZ'],now=now)['stocks'][0]['news']['items']==[]


def test_community_content_revisions_ignore_engagement_and_expire_honestly(session,monkeypatch):
    configure(monkeypatch)
    now=datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ'));session.commit()
    row=discussion(session,now)
    first=intelligence(session,['XYZ'],now=now)['stocks'][0]['community']['items'][0]
    row.replies=999;row.views=12000;row.revision_id='native-engagement';row.last_seen_at=now+timedelta(minutes=1)
    session.add(row);session.commit()
    second=intelligence(session,['XYZ'],now=now)['stocks'][0]['community']['items'][0]
    assert first['revision']==second['revision']
    row.excerpt+=' Revised source text';row.revision_id='native-text';session.add(row);session.commit()
    revised=intelligence(session,['XYZ'],now=now)['stocks'][0]['community']['items'][0]
    assert revised['revision']!=first['revision'] and revised['id']==first['id']
    assert intelligence(session,['XYZ'],now=now+timedelta(days=1))['stocks'][0]['community']['items']==[]
    session.delete(row);session.commit()
    assert intelligence(session,['XYZ'],now=now)['stocks'][0]['community']['items']==[]


def test_bounded_pages_select_only_no_acquisition_or_full_universe(session,client,monkeypatch):
    configure(monkeypatch)
    now=datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ'));session.commit()
    for n in range(16):discussion(session,now,f'discussion-{n:02}')
    ingest(session,[item(f'XYZ reports profit for project {n}','https://one.example/'+str(n),now) for n in range(16)],now=now)
    monkeypatch.setattr('src.services.universe.discovery_metadata',lambda *a:(_ for _ in ()).throw(AssertionError('full universe')))
    monkeypatch.setattr('src.services.technical_eod_store.capture_fresh_ssi_read',lambda *a:(_ for _ in ()).throw(AssertionError('SSI HTTP')))
    monkeypatch.setattr('src.news.adapters.acquire',lambda *a:(_ for _ in ()).throw(AssertionError('News HTTP')))
    statements=[]
    def capture(conn,cursor,statement,*args):statements.append(statement)
    event.listen(session.get_bind(),'before_cursor_execute',capture)
    try:
        first=client.post('/watchlists/intelligence',json={'symbols':['XYZ'],'page_size':3}).json()
        second=client.post('/watchlists/intelligence',json={'symbols':['XYZ'],'page_size':3,'offset':3}).json()
    finally:event.remove(session.get_bind(),'before_cursor_execute',capture)
    a=first['stocks'][0]['community'];b=second['stocks'][0]['community']
    assert len(a['items'])==len(b['items'])==3 and a['has_more'] and b['has_more']
    assert not ({e['id'] for e in a['items']}&{e['id'] for e in b['items']})
    assert statements and all(s.lstrip().upper().startswith('SELECT') for s in statements)
    assert all('LIMIT' in s.upper() for s in statements if 'FROM newsarticle' in s or 'FROM communityevidenceitem' in s)


def test_technical_accepted_events_freshness_retraction_and_corrected_version(session,monkeypatch):
    configure(monkeypatch)
    target,cal,pub,first,second,now=setup(session)
    run(session,second,now);session.expire_all()
    result=intelligence(session,['XYZ'],now=now)['stocks'][0]['technical']
    assert result['data']['assurance']=='PROVISIONAL'
    assert result['data']['safe_to_display_as_verified'] is False
    assert result['data']['packet']['packet_state']=='HAS_INSIGHTS'
    events=result['data']['packet']['top_insights']
    assert [item['entity_id'] for item in result['items']]==[e['event_id'] for e in events]
    assert [item['evidence'] for item in result['items']]==events
    assert result['data']['last_checked_at']==second.received_at.isoformat().replace('+00:00','Z')
    assert intelligence(session,['XYZ'],now=now)['stocks'][0]['technical']['items']==result['items']
    later=now+timedelta(hours=25)
    revised=fresh(second,later,revision=True)
    run(session,revised,later);session.expire_all()
    retracted=intelligence(session,['XYZ'],now=later)['stocks'][0]['technical']
    assert retracted['items']==[] and retracted['data']['kind']=='diagnostic'
    assert 'ssi_history_revision_detected' in retracted['data']['reason_codes']
    accepted=later+timedelta(hours=6,minutes=1)
    run(session,fresh(revised,accepted),accepted);session.expire_all()
    corrected=intelligence(session,['XYZ'],now=accepted)['stocks'][0]['technical']
    assert corrected['data']['snapshot_version']==2


def test_no_meaningful_change_is_an_accepted_empty_packet(session,monkeypatch):
    from src.services.technical_eod_store import read_latest_operational_packet
    configure(monkeypatch)
    *_,second,now=setup(session)
    run(session,second,now);session.expire_all()
    accepted=read_latest_operational_packet(session,'XYZ',now)
    # Transport fixture only; no changes to stored snapshots or D1/D4/D5.
    empty=accepted.model_copy(update={'packet':accepted.packet.model_copy(update={
        'packet_state':'NO_MEANINGFUL_TECHNICAL_CHANGE','top_insights':()})})
    monkeypatch.setattr('src.services.watchlist_intelligence.read_latest_operational_packet',lambda *a:empty)
    result=intelligence(session,['XYZ'],now=now)['stocks'][0]['technical']
    assert result['items']==[] and result['waiting_for_gate'] is False
    assert result['data']['packet']['packet_state']=='NO_MEANINGFUL_TECHNICAL_CHANGE'


def test_technical_delayed_gate_distinct_from_incomplete(session,monkeypatch):
    configure(monkeypatch)
    target,cal,pub,first,second,now=setup(session,import_first=False)
    incomplete=intelligence(session,['XYZ'],now=now)['stocks'][0]['technical']
    assert incomplete['waiting_for_gate'] is False and incomplete['data']['kind']=='diagnostic'
    run(session,fresh(first,now),now);session.expire_all()
    pending=intelligence(session,['XYZ'],now=now)['stocks'][0]['technical']
    assert pending['waiting_for_gate'] is True and pending['next_check_due_at'] is not None
    assert pending['items']==[]
    due=intelligence(session,['XYZ'],now=now+timedelta(hours=7))['stocks'][0]['technical']
    assert due['waiting_for_gate'] is False and due['awaiting_source_check'] is True
    assert due['items']==[]


def test_identity_falls_back_to_existing_stock_name_without_mutating_metadata(session,monkeypatch):
    configure(monkeypatch)
    now=datetime.now(timezone.utc)
    session.add_all([Stock(symbol='XYZ',company_name='Existing company',display_name_en='Existing company'),
        Security(symbol='XYZ',exchange='HOSE',last_synced_at=now)])
    session.commit()
    result=intelligence(session,['XYZ'],now=now)['stocks'][0]
    assert result['company_name']==result['display_name_en']=='Existing company'
    assert session.get(Security,'XYZ').company_name is None


def test_source_success_time_is_not_response_time_and_rechecks_do_not_renew_events(session,monkeypatch):
    from src.news.models import NewsSourceState
    configure(monkeypatch)
    target,cal,pub,first,second,now=setup(session)
    run(session,second,now);session.expire_all()
    before=intelligence(session,['XYZ'],now=now)['stocks'][0]['technical']['items']
    later=now+timedelta(hours=25)
    run(session,fresh(second,later),later);session.expire_all()
    assert intelligence(session,['XYZ'],now=later)['stocks'][0]['technical']['items']==before
    known=__import__('src.news.registry',fromlist=['load_sources']).load_sources()[0]
    success=later-timedelta(hours=4)
    session.add(NewsSourceState(source_id=known.source_id,last_success_at=success,last_attempt_at=later,last_error='SyntheticFailure'))
    session.commit()
    result=intelligence(session,['XYZ'],now=later)
    status=next(row for row in result['news_sources'] if row.source_id==known.source_id)
    assert status.last_success_at==success and status.last_attempt_at==later


@pytest.mark.parametrize('count',[13,305])
def test_story_pages_are_distinct_and_large_samples_disclose_truncation(session,client,monkeypatch,count):
    configure(monkeypatch)
    now=datetime.now(timezone.utc)
    session.add(Stock(symbol='XYZ'));session.commit()
    for n in range(count):
        seen=now-timedelta(seconds=n)
        story=NewsStory(id=f'synthetic-{n}',representative_title=f'XYZ reports synthetic project {n}',first_seen_at=seen,last_updated_at=seen)
        session.add(story);session.flush()
        session.add(NewsArticle(id=f'synthetic-article-{n}',source_id='one',source_name='Synthetic test source',
            publisher_group='one',title=story.representative_title,url=f'https://one.example/{n}',canonical_url=f'https://one.example/{n}',
            url_hash=f'synthetic-url-{n}',title_hash=f'synthetic-title-{n}',country='VN',language='en',category='VN',scope='company',
            tickers=['XYZ'],story_id=story.id,published_at=seen,first_seen_at=seen,last_seen_at=seen))
    session.commit()
    a=client.post('/watchlists/intelligence',json={'symbols':['XYZ']}).json()['stocks'][0]['news']
    b=client.post('/watchlists/intelligence',json={'symbols':['XYZ'],'offset':12}).json()['stocks'][0]['news']
    assert len(a['items'])==12 and a['has_more']
    assert a['truncated']==(count>300)
    assert [e['entity_id'] for e in a['items']]==[f'synthetic-{n}' for n in range(12)]
    assert not ({e['id'] for e in a['items']}&{e['id'] for e in b['items']})
