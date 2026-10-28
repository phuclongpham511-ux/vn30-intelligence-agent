"""Bounded official HOSE occurrence/publication qualification, never SSI finality."""
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup
from .session_evidence import CalendarEvidence, SessionEvidence, aware
from .provisional_eod import HosePublicationEvidence, assess_provisional_eod
from src.evaluation.benchmark.inputs import ZONE

NEWS = 'https://api.hsx.vn/n/api/v1/1/news'
RSS = 'https://api.hsx.vn/n/api/v1/News/NewsFeed'
WEEKDAY_RULE = 'https://staticfile.hsx.vn/Uploads/UploadDocuments/2372196/2.Thoi%20gian%20giao%20dich.pdf'
HOLIDAY_NOTICE = 'https://www.hsx.vn/vi/lich-giao-dich'
MAX_SOURCE_BYTES = 512_000
SEED_HASH = '88b288afa760f13e09522624f17b9fa6dce481047bf2bbfee839d13ebec9bd49'
ANCHOR_HASH = '416f1fbc0e4cb0f95c2db1174858997b0bfe485480b706fca45d235f4413ad8e'


def digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def seed_calendar(directory):
    """Import the previously independently qualified metadata, with pinned hashes."""
    directory = Path(directory)
    raw = (directory/'TECHNICAL_V1_HOSE_SESSION_INDEX_2026-07-01_2026-10-08.tsv').read_bytes()
    anchor = (directory/'TECHNICAL_V1_HOSE_PUBLICATION_2026-10-08.json').read_bytes()
    if sha256(raw).hexdigest()!=SEED_HASH or sha256(anchor).hexdigest()!=ANCHOR_HASH:
        raise ValueError('Qualified seed checksum mismatch')
    proof=json.loads(anchor)
    observed=datetime.fromisoformat(proof['verified_at'].replace('Z','+00:00'))
    index={}
    for line in raw.decode().splitlines():
        if not line or line.startswith('#'): continue
        day,news_id,prefix=line.split()
        day=date.fromisoformat(day)
        if day in index or not news_id.isdigit() or prefix not in ('h','d'):
            raise ValueError('Invalid qualified index')
        slug=('hose-' if prefix=='h' else '')+'diem-tin-giao-dich-ngay-'+day.strftime('%d-%m-%Y')
        index[day]='https://www.hsx.vn/vi/tin-tuc/'+slug+'/'+news_id
    start,end=date(2026,7,1),date(2026,10,8)
    holidays={date(2026,8,31),date(2026,9,1),date(2026,9,2)}
    records=[]
    for i in range((end-start).days+1):
        day=start+timedelta(days=i)
        if day in index:
            status,kind,ref='OCCURRED','exchange_session_record',index[day]
        elif day.weekday()>=5 or day in holidays:
            status,kind,ref='CLOSED','official_schedule',HOLIDAY_NOTICE if day in holidays else WEEKDAY_RULE
        else:
            raise ValueError('Unqualified seed date')
        records.append(SessionEvidence(session=day,status=status,evidence_kind=kind,source_ref=ref,
            observed_at=observed,verified_at=observed))
    if len(index)!=69 or len(records)!=100:
        raise ValueError('Qualified seed coverage mismatch')
    return CalendarEvidence(venue='HOSE',coverage_start=start,coverage_end=end,
        version=SEED_HASH,records=tuple(records))


def publication_anchor(directory):
    raw=(Path(directory)/'TECHNICAL_V1_HOSE_PUBLICATION_2026-10-08.json').read_bytes()
    if sha256(raw).hexdigest()!=ANCHOR_HASH: raise ValueError('Publication anchor changed')
    return json.loads(raw)


class HoseSourceUnavailable(ValueError):
    pass


class OfficialHoseSource:
    def __init__(self,anchor,*,fetch=None,clock=None):
        self.anchor=anchor
        self.fetch=fetch or self._fetch
        self.clock=clock or (lambda:datetime.now(timezone.utc))

    def _fetch(self,url,params=None):
        # Fixed official endpoints, no redirects or arbitrary URL fetching.
        if url!=RSS and not (url==NEWS+'/cate' or re.fullmatch(re.escape(NEWS)+r'/[0-9]+',url)):
            raise ValueError('Unqualified source endpoint')
        with httpx.Client(timeout=20,follow_redirects=False) as client:
            with client.stream('GET',url,params=params) as response:
                response.raise_for_status()
                raw=bytearray()
                for part in response.iter_bytes():
                    raw.extend(part)
                    if len(raw)>MAX_SOURCE_BYTES: raise ValueError('Official source exceeds bound')
        return bytes(raw)

    def _json(self,url,params=None):
        raw=self.fetch(url,params)
        if len(raw)>MAX_SOURCE_BYTES: raise ValueError('Official source exceeds bound')
        value=json.loads(raw)
        if not isinstance(value,dict) or value.get('success') is not True:
            raise ValueError('Official source schema changed')
        return value['data'],sha256(raw).hexdigest()

    def qualify_day(self,target):
        """One day's actual bulletin; fail closed on timezone/schema ambiguity."""
        now=aware(self.clock())
        if type(target) is not date or target>=now.astimezone(ZONE).date():
            raise ValueError('Only completed prior dates may be discovered')
        anchor,anchor_hash=self._json(NEWS+'/2503043')
        old=self.anchor
        published=datetime.fromisoformat(old['published_at'])
        expected=int(published.replace(tzinfo=timezone.utc).timestamp())
        if (anchor.get('id')!=2503043 or anchor.get('postedDate')!=expected
                or anchor.get('approvedDate')!=expected):
            raise ValueError('HOSE wall-time anchor no longer matches qualification')
        rss_raw=self.fetch(RSS)
        if len(rss_raw)>MAX_SOURCE_BYTES or b'<!DOCTYPE' in rss_raw.upper() or b'<!ENTITY' in rss_raw.upper():
            raise ValueError('Invalid official RSS')
        built=parsedate_to_datetime(ET.fromstring(rss_raw).findtext('./channel/lastBuildDate'))
        if built.utcoffset()!=timedelta(hours=7) or not now-timedelta(days=1)<=aware(built)<=now+timedelta(minutes=5):
            raise ValueError('Official timezone evidence unavailable or stale')
        listing,list_hash=self._json(NEWS+'/cate',{'pageIndex':1,'pageSize':20,
            'startDate':target.isoformat(),'endDate':target.isoformat(),'title':'Điểm tin giao dịch'})
        rows=listing.get('list')
        paging=listing.get('paging',{})
        if (not isinstance(rows,list) or len(rows)>20 or paging.get('totalCount')!=len(rows)
                or paging.get('totalPages') not in (0,1)):
            raise ValueError('Official index pagination incomplete')
        def is_bulletin(row):
            title=str(row.get('title','')).replace('Đ','D').replace('đ','d')
            title=unicodedata.normalize('NFD',title).encode('ascii','ignore').decode().lower()
            return row.get('catId')==1048 and re.fullmatch(
                r'(?:hose:\s*)?diem tin giao dich ngay '+re.escape(target.strftime('%d/%m/%Y')),title.strip()) is not None
        matching=[r for r in rows if isinstance(r,dict) and is_bulletin(r)]
        if not matching: return None
        if len(matching)!=1: raise ValueError('Contradictory official bulletin')
        item=matching[0]
        if type(item.get('id')) is not int or item['id']<1: raise ValueError('Invalid bulletin identity')
        ref=NEWS+'/'+str(item['id'])
        data,response_hash=self._json(ref)
        if (data.get('id')!=item['id'] or not is_bulletin(data)
                or data.get('postedDate')!=item.get('postedDate') or type(data.get('postedDate')) is not int
                or data.get('approvedDate')!=data['postedDate'] or data.get('deleted')!=0):
            raise ValueError('Official publication evidence inconsistent')
        text=BeautifulSoup(data.get('summary') or '', 'html.parser').get_text(' ',strip=True)
        if 'TRADING SUMMARY' not in text or target.strftime('%d/%m/%Y') not in text:
            raise ValueError('Actual session summary not independently evidenced')
        wall=datetime.fromtimestamp(data['postedDate'],timezone.utc).replace(tzinfo=ZONE)
        if wall.astimezone(ZONE).date()<target or aware(wall)>now:
            raise ValueError('Official publication timestamp invalid')
        observed=aware(self.clock())
        metadata={k:data.get(k) for k in ('id','title','postedDate','approvedDate','updatedDate','catId','deleted')}
        proof=HosePublicationEvidence(venue='HOSE',session=target,source_ref=ref,
            content_sha256=digest(metadata),published_at=wall,observed_at=observed,verified_at=observed)
        return {'record':SessionEvidence(session=target,status='OCCURRED',source_ref=ref,
            observed_at=observed,verified_at=observed).model_dump(mode='json'),
            'publication':proof.model_dump(mode='json'),'receipt':{
                'retrieved_at':observed.isoformat(),'source_ref':ref,'response_sha256':response_hash,
                'index_response_sha256':list_hash,'anchor_response_sha256':anchor_hash,
                'rss_sha256':sha256(rss_raw).hexdigest(),'metadata_sha256':digest(metadata),
                'timezone_basis':'qualified_page_wall_seconds_plus_anchor_and_official_rss_0700',
                'ssi_publication_time':None,'ssi_finality_evidence':False}}


def extend_calendar(calendar,day,qualified,now):
    if day!=calendar.coverage_end+timedelta(days=1): raise ValueError('Calendar adjacency required')
    if day.weekday()>=5:
        record=SessionEvidence(session=day,status='CLOSED',evidence_kind='official_schedule',
            source_ref=WEEKDAY_RULE,observed_at=now,verified_at=now)
    elif qualified:
        record=SessionEvidence.model_validate(qualified['record'])
        if record.session!=day or record.status!='OCCURRED': raise ValueError('Occurrence mismatch')
    else:
        return calendar
    records=calendar.records+(record,)
    if len(records)>731: raise ValueError('Calendar capacity reached')
    return calendar.model_copy(update={'coverage_end':day,'records':records,
        'version':digest([r.model_dump(mode='json') for r in records])})


def qualified_definition(ticker,calendar,publication,now):
    # A six-month window bounds resource use without manufacturing missing lookback.
    start=max(calendar.coverage_start,publication.session-timedelta(days=180))
    scoped=calendar.model_copy(update={'coverage_start':start,'coverage_end':publication.session,
        'records':tuple(r for r in calendar.records if start<=r.session<=publication.session),
        'version':digest([r.model_dump(mode='json') for r in calendar.records if start<=r.session<=publication.session])})
    assessment=assess_provisional_eod(ticker,publication.session,history_start=start,
        calendar=scoped,publication=publication,first=None,second=None,evaluation_as_of=now)
    if assessment.reason_codes!=('authenticated_fresh_read_unavailable',):
        raise ValueError('Independent calendar/publication not yet qualified')
    return {'history_start':start,'calendar':scoped,'publication':publication}
