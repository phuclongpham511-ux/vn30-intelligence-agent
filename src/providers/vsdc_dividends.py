"""Saved official cash-dividend notices; no ex-date inference or acquisition."""
from datetime import datetime, timezone
import hashlib
from html import unescape
from html.parser import HTMLParser
import re
from src.corporate_actions.models import CorporateActionNotice, CorporateActionObservation
from src.corporate_actions.repository import content_hash


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth=0;self.sections=0;self.parts=[]

    def handle_starttag(self,tag,attrs):
        classes=dict(attrs).get('class','').split()
        if tag=='div' and 'content-category' in classes:
            self.sections+=1;self.depth=1
        elif tag=='div' and self.depth:self.depth+=1

    def handle_endtag(self,tag):
        if tag=='div' and self.depth:self.depth-=1

    def handle_data(self,data):
        if self.depth:self.parts.append(data)


def parse_cash_notice(receipt):
    body=receipt['body']
    if (receipt.get('status')!=200 or not isinstance(body,str) or len(body.encode())>1_000_000
            or hashlib.sha256(body.encode()).hexdigest()!=receipt.get('sha256')
            or not re.fullmatch(r'https://vsdc\.vn/vi/ad/\d+',receipt.get('url',''))):
        raise ValueError('Invalid official dividend receipt')
    observed=datetime.fromisoformat(receipt['observed_at'])
    if observed.utcoffset() is None:raise ValueError('Dividend receipt requires timezone')
    parser=ArticleText();parser.feed(body)
    if parser.sections!=1:raise ValueError('Ambiguous official article body')
    text=' '.join(' '.join(parser.parts).split())
    title=re.findall(r'<h3 class="title-category">([^<]+)</h3>',body)
    updates=re.findall(r'<div class="time-newstcph">(.*?)</div>',body,re.S)
    if len(title)!=1 or len(updates)!=1:raise ValueError('Missing official notice identity')
    title=unescape(title[0])
    if 'cổ tức' not in title.casefold() or 'bằng tiền' not in title.casefold():
        raise ValueError('Only explicit cash dividends supported')
    owners=re.findall(r'Mã chứng khoán:\s*([A-Z0-9]{1,20})\b',text)
    tokens=re.findall(r'(?:01|1) cổ phiếu được nhận ([0-9.]+) đồng',text)
    if len(owners)!=1 or len(tokens)!=1 or not title.startswith(owners[0]+':'):
        raise ValueError('Ambiguous dividend owner or monetary terms')
    if not re.fullmatch(r'\d{1,3}(?:\.\d{3})*|\d+',tokens[0]):raise ValueError('Ambiguous cash amount')

    def recorded_date(label):
        found=re.findall(re.escape(label)+r':\s*(\d{2}/\d{2}/\d{4})',text)
        if len(found)>1:raise ValueError('Ambiguous dividend date')
        return datetime.strptime(found[0],'%d/%m/%Y').date() if found else None

    updated=re.findall(r'(\d{2}/\d{2}/\d{4})',unescape(updates[0]))
    announced=datetime.strptime(updated[0],'%d/%m/%Y').date() if len(updated)==1 else None
    record=recorded_date('Ngày đăng ký cuối cùng');payment=recorded_date('Ngày thanh toán')
    if record and payment and payment<record:raise ValueError('Contradictory dividend dates')
    notice=CorporateActionNotice(symbol=owners[0],action_type='cash_dividend',
        effective_date=None,record_date=record,payment_date=payment,announced_on=announced,
        source='VSDC:official-notice',source_url=receipt['url'],source_id=receipt['url'].rsplit('/',1)[-1],
        source_title=title,source_revision=content_hash(text),
        terms=dict(cash_vnd_per_share=int(tokens[0].replace('.',''))),verified=True,
        verification_note='Exact saved official notice fields; incomplete coverage. Ex-date and public reuse permission are not inferred.')
    identity=content_hash([notice.source,notice.source_id,notice.symbol,notice.action_type.value])
    return CorporateActionObservation(**notice.model_dump(),action_id=identity,
        observation_id=content_hash([identity,receipt['sha256'],receipt['observed_at']]),observed_at=observed)


def dividend_page(capture,ticker):
    if capture.get('contract')!='vsdc-cash-dividends-v1' or not isinstance(capture.get('pages'),list) or len(capture['pages'])>50:
        raise ValueError('Invalid saved dividend collection')
    rows=[parse_cash_notice(p) for p in capture['pages']]
    if len({r.action_id for r in rows})!=len(rows):raise ValueError('Retain dividend revisions in separate immutable captures')
    items=sorted((r for r in rows if r.symbol==ticker),key=lambda r:r.announced_on or r.observed_at.date(),reverse=True)
    return dict(ticker=ticker,as_of=datetime.now(timezone.utc).isoformat(),coverage='INCOMPLETE',
        display_scope='personal_research',items=[r.model_dump(mode='json') for r in items],has_more=False,
        public_display_eligible=False)
