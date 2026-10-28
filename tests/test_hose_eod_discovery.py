"""Official-source parsing seams use explicitly synthetic HTTP payloads."""
from datetime import date,datetime,timedelta,timezone
from email.utils import format_datetime
import json
from pathlib import Path
import pytest
from src.services.hose_eod_discovery import (OfficialHoseSource,NEWS,RSS,seed_calendar,
    publication_anchor,qualified_definition,extend_calendar)

DOCS=Path(__file__).resolve().parents[1]/'docs'
NOW=datetime(2026,10,10,10,tzinfo=timezone.utc)
DAY=date(2026,10,9)


def source():
    anchor=publication_anchor(DOCS)
    item={'id':9001,'title':'HOSE: Điểm tin giao dịch ngày 09/10/2026',
        'catId':1048,'postedDate':int(datetime(2026,10,9,16,tzinfo=timezone.utc).timestamp()),
        'deleted':0,'summary':'TRADING SUMMARY Date: 09/10/2026'}
    item['approvedDate']=item['postedDate']
    anchor_item={'id':2503043,'postedDate':int(datetime(2026,10,8,16,34,41,tzinfo=timezone.utc).timestamp())}
    anchor_item['approvedDate']=anchor_item['postedDate']
    values={NEWS+'/2503043':{'data':anchor_item,'success':True},
        NEWS+'/cate':{'data':{'list':[item],'paging':{'totalCount':1,'totalPages':1}},'success':True},
        NEWS+'/9001':{'data':dict(item),'success':True}}
    rss={'raw':('<rss><channel><lastBuildDate>'+format_datetime(NOW.astimezone(timezone(timedelta(hours=7))))+'</lastBuildDate></channel></rss>').encode()}
    calls=[]
    def fetch(url,params=None):
        calls.append((url,params))
        return rss['raw'] if url==RSS else json.dumps(values[url]).encode()
    return OfficialHoseSource(anchor,fetch=fetch,clock=lambda:NOW),values,rss,calls


def test_qualified_seed_has_69_sessions_31_closures_and_no_gap():
    cal=seed_calendar(DOCS)
    assert len(cal.records)==100
    assert sum(r.status=='OCCURRED' for r in cal.records)==69
    assert sum(r.status=='CLOSED' for r in cal.records)==31
    assert len({r.session for r in cal.records})==100


def test_official_bulletin_separates_publication_client_time_and_ssi_unknown():
    s,values,rss,calls=source()
    proof=s.qualify_day(DAY)
    assert proof['publication']['published_at']=='2026-10-09T16:00:00+07:00'
    assert proof['receipt']['ssi_publication_time'] is None
    assert proof['receipt']['ssi_finality_evidence'] is False
    assert proof['receipt']['retrieved_at']==NOW.isoformat()
    assert len(calls)==4
    cal=extend_calendar(seed_calendar(DOCS),DAY,proof,NOW)
    definition=qualified_definition('ANY',cal,__import__('src.services.provisional_eod',fromlist=['HosePublicationEvidence']).HosePublicationEvidence.model_validate(proof['publication']),NOW)
    assert definition['calendar'].coverage_end==DAY
    assert len(definition['calendar'].records)==101


@pytest.mark.parametrize('mutation', ['anchor','timezone','stale-rss','pagination','duplicate','title','summary','published','approval','deleted'])
def test_ambiguous_or_missing_publication_fails_closed(mutation):
    s,v,rss,_=source()
    detail=v[NEWS+'/9001']['data']
    if mutation=='anchor':v[NEWS+'/2503043']['data']['postedDate']+=1
    if mutation=='timezone':rss['raw']=rss['raw'].replace(b'+0700',b'+0000')
    if mutation=='stale-rss':rss['raw']=rss['raw'].replace(b'10 Oct',b'01 Oct')
    if mutation=='pagination':v[NEWS+'/cate']['data']['paging']['totalPages']=2
    if mutation=='duplicate':
        listing=v[NEWS+'/cate']['data'];listing['list']*=2;listing['paging']['totalCount']=2
    if mutation=='title':detail['title']='Unrelated issuer notice'
    if mutation=='summary':detail['summary']='No occurred-session evidence'
    if mutation=='published':detail['postedDate']+=86400
    if mutation=='approval':detail['approvedDate']-=1
    if mutation=='deleted':detail['deleted']=1
    with pytest.raises(ValueError):s.qualify_day(DAY)


def test_no_bulletin_is_unknown_not_a_holiday_and_current_day_is_ineligible():
    s,v,rss,calls=source()
    v[NEWS+'/cate']['data']={'list':[],'paging':{'totalCount':0,'totalPages':0}}
    assert s.qualify_day(DAY) is None
    seed=seed_calendar(DOCS)
    assert extend_calendar(seed,DAY,None,NOW)==seed
    with pytest.raises(ValueError):s.qualify_day(NOW.date())


def test_growing_calendar_does_not_change_prior_job_definition_or_fabricate_weekday():
    s,*_=source()
    proof=s.qualify_day(DAY)
    cal=extend_calendar(seed_calendar(DOCS),DAY,proof,NOW)
    from src.services.provisional_eod import HosePublicationEvidence
    pub=HosePublicationEvidence.model_validate(proof['publication'])
    before=qualified_definition('ANY',cal,pub,NOW)
    later=extend_calendar(cal,date(2026,10,10),None,NOW+timedelta(days=1))
    after=qualified_definition('ANY',later,pub,NOW+timedelta(days=1))
    assert before==after
    assert later.records[-1].status=='CLOSED'
    with pytest.raises(ValueError):extend_calendar(cal,date(2026,10,12),None,NOW)


def test_source_bytes_and_entity_expansion_are_bounded():
    s,v,rss,_=source()
    rss['raw']=b'<!DOCTYPE rss [<!ENTITY x "unsafe">]><rss/>'
    with pytest.raises(ValueError):s.qualify_day(DAY)
    s.fetch=lambda *a:b'x'*512001
    with pytest.raises(ValueError):s.qualify_day(DAY)
