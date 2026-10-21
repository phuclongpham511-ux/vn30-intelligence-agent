"""Synthetic provider/original-report boundaries; real receipts are private."""
import copy
import hashlib
import json
import pytest
from src.providers.reviewed_reports import report_packet
from src.providers.cafef_statements import cafef_packet, SOURCE, ENDPOINT
from src.services.personal_financials import personal_projection
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response


def reviewed(tmp_path):
    pdf=b'%PDF-synthetic-test'; png=b'\x89PNG\r\n\x1a\nsynthetic-page'
    (tmp_path/'source.pdf').write_bytes(pdf);(tmp_path/'page.png').write_bytes(png)
    header='2025 VND 2024 VND'
    text='ABC Example issuer CONSOLIDATED 1 January to 31 December VND\n'+header
    fields=[]
    for field,values in [('revenue',['1.000','800']),('gross_profit',['300','200']),('net_profit',['100','80']),
            ('total_assets',['2.000','1.500']),('total_liabilities',['1.200','900']),('equity',['800','600']),
            ('cash_operating',['200','180']),('cash_investing',['(80)','(60)']),
            ('cash_financing',['(20)','(20)']),('cash_net_change',['100','100'])]:
        row=field+' '+' '.join(values);text+='\n'+row
        for i,year in enumerate((2025,2024)):
            fields.append(dict(field=field,code='row:'+field,code_kind='reviewed_row_locator',label=field,
                year=year,raw_token=values[i],column_periods=['2025','2024'],column_values=values,
                source_row=dict(page=1,text=row),column_header=dict(page=1,text=header),
                unit_quote=dict(page=1,text='VND'),unit='VND',period_start=None if field in ('total_assets','total_liabilities','equity') else f'{year}-01-01',period_end=f'{year}-12-31'))
    return dict(contract='reviewed-report-v2',ticker='ABC',source='issuer:example',issuer='Example issuer',
        company_type='CT',profile='non_financial',document_url='https://example.test/original.pdf',
        discovery_url='https://example.test/ir',document_file='source.pdf',document_sha256=hashlib.sha256(pdf).hexdigest(),
        observed_at='2026-10-21T00:00:00Z',review_reference='synthetic-test-review',scope='consolidated',
        scope_quote=dict(page=1,text='CONSOLIDATED'),identity_quote=dict(page=1,text='Example issuer'),
        calendar_quote=dict(page=1,text='1 January to 31 December'),currency_quote=dict(page=1,text='VND'),
        pages=[dict(number=1,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),image_file='page.png',
            image_sha256=hashlib.sha256(png).hexdigest(),method='pdf_text_and_visual_review')],amounts=fields)


def test_original_reports_unlock_supported_calculations_but_not_publication_or_rights(tmp_path):
    evidence=reviewed(tmp_path);before=copy.deepcopy(evidence)
    packet,audit=report_packet(evidence,tmp_path)
    raw=financial_engine(packet); public=display_financial_response(raw)
    private=personal_projection(packet,authorization_reference='task:private-review')
    latest=private['rows'][-1]
    assert latest['net_margin']==.1 and latest['gross_margin']==.3
    assert latest['revenue_growth_yoy']==.25 and latest['roe']==pytest.approx(100/700)
    assert latest['cash_financing']==-20
    assert latest['free_cash_flow'] is None
    assert next(m for m in private['fundamental_summary']['metrics'] if m['key']=='pe')['value'] is None
    assert private['display_scope']=='internal_research'
    d=private['verification']['periods'][-1]['metrics']['roe']['dimensions']
    assert d==dict(SOURCE_VERIFIED=True,ACCOUNTING_VERIFIED=True,REPORTING_METADATA_COMPLETE=True,POINT_IN_TIME_VERIFIED=False,PUBLICATION_RIGHTS_APPROVED=False,FULLY_VERIFIED=False)
    assert all(m.value is None for m in public.fundamental_summary.metrics)
    assert evidence==before and audit['selected_reported_fields']==20


@pytest.mark.parametrize('bad',['binary','page','owner','scope','unit','swapped_column','period','bank_revenue','duplicate','publication_grant','numeric_token'])
def test_reviewed_reports_reject_unsubstantiated_promotions(tmp_path,bad):
    e=reviewed(tmp_path)
    if bad=='binary':(tmp_path/'source.pdf').write_bytes(b'changed')
    elif bad=='page':(tmp_path/'page.png').write_bytes(b'changed')
    elif bad=='owner':e['issuer']='Other issuer'
    elif bad=='scope':e['scope']='standalone'
    elif bad=='unit':e['amounts'][0]['unit']='million VND'
    elif bad=='swapped_column':e['amounts'][0]['raw_token']='800'
    elif bad=='period':e['amounts'][0]['period_end']='2025-06-30'
    elif bad=='bank_revenue':e.update(company_type='NH',profile='bank')
    elif bad=='duplicate':e['amounts'].append(e['amounts'][0])
    elif bad=='publication_grant':e['display_rights']='permitted'
    else:e['amounts'][0]['raw_token']='1.000x'
    with pytest.raises(ValueError):report_packet(e,tmp_path)


def test_statement_contradiction_keeps_source_values_but_withholds_affected_ratios(tmp_path):
    e=reviewed(tmp_path)
    # A genuinely reported but contradictory balance, not a parser mutation.
    for a in e['amounts']:
        if a['field']=='total_assets':
            a.update(raw_token='3.000' if a['year']==2025 else '1.500',column_values=['3.000','1.500'],source_row=dict(page=1,text='total_assets 3.000 1.500'))
    p=e['pages'][0];p['text']=p['text'].replace('total_assets 2.000 1.500','total_assets 3.000 1.500');p['text_sha256']=hashlib.sha256(p['text'].encode()).hexdigest()
    packet,audit=report_packet(e,tmp_path)
    view=personal_projection(packet,authorization_reference='task:test')
    assert view['rows'][-1]['total_assets']==3000 and view['rows'][-1]['roe'] is None
    assert view['rows'][-1]['net_margin']==.1
    state=view['verification']['periods'][-1]['metrics']['total_assets']['dimensions']
    assert state['SOURCE_VERIFIED'] and not state['ACCOUNTING_VERIFIED']
    assert any(r['balance_identity']=='FAIL' for r in audit['checks'])


def cafe_capture():
    data=dict(Success=True,Data=dict(Value=[dict(Time='2025',Year=2025,Quater=0,ReportType='HK',Conten='provider audit description',Value=[
        dict(Code='DTTBHCCDV',Name='Doanh thu bán hàng và CCDV',Value=200),
        dict(Code='LNGBHCCDV',Name='Lợi nhuận gộp về BH và CCDV',Value=30),
        dict(Code='LNSTTNDN',Name='Lợi nhuận sau thuế',Value=10),
        dict(Code='NetIncome',Name='Lợi nhuận sau thuế của công ty mẹ',Value=9)])]))
    body=json.dumps(data,ensure_ascii=False)
    return dict(contract='cafef-saved-annual-v1',source=SOURCE,ticker='ABC',company_type='CT',observed_at='2026-10-21T00:00:00Z',reports=dict(income=dict(
        url=ENDPOINT,params=dict(Type=1,Symbol='ABC',ReportType='NAM',TotalRow=4),status=200,
        observed_at='2026-10-21T00:00:00Z',body=body,body_sha256=hashlib.sha256(body.encode()).hexdigest())))


def test_cafef_summary_never_relabels_gross_sales_or_grants_unknown_basis_calculations():
    p=cafef_packet(cafe_capture());view=personal_projection(p,authorization_reference='task:research')
    r=view['rows'][-1]
    assert r['revenue'] is None and r['gross_profit']==30000 and r['net_profit']==10000
    assert r['net_margin'] is None and r['roe'] is None and r['cash_operating'] is None
    line=p.reports['income'].observations[0]
    assert line.source_context.original_unit is None and line.source_context.original_currency is None
    assert line.source_context.amount_multiplier==1000 and line.consolidation is None
    assert view['statements']['income']['periods'][0]['items']
    assert all(m.value is None for m in display_financial_response(financial_engine(p)).fundamental_summary.metrics)


@pytest.mark.parametrize('bad',['hash','owner','type','period','boolean','duplicate','label','quarter_boolean','request_boolean'])
def test_cafef_rejects_bad_receipts_and_quarantines_semantic_conflicts(bad):
    e=cafe_capture();r=e['reports']['income']
    if bad=='hash':r['body']+=' '
    elif bad=='owner':r['params']['Symbol']='OTHER'
    elif bad=='type':r['params']['Type']=2
    elif bad=='request_boolean':r['params']['Type']=True
    else:
        data=json.loads(r['body']); row=data['Data']['Value'][0]
        if bad=='period':row['Quater']=1
        elif bad=='quarter_boolean':row['Quater']=False
        elif bad=='boolean':row['Value'][1]['Value']=True
        elif bad=='duplicate':row['Value'].append(row['Value'][1])
        else:row['Value'][1]['Name']='Operating income'
        r['body']=json.dumps(data,ensure_ascii=False);r['body_sha256']=hashlib.sha256(r['body'].encode()).hexdigest()
    if bad=='label':
        p=cafef_packet(e);assert p.reports['income'].observations[0].fields['gross_profit'] is None
        assert p.reports['income'].observations[0].fields['net_profit']==10000
    else:
        with pytest.raises(ValueError):cafef_packet(e)


def dividend_receipt(ticker='ABC'):
    body=f'''<h3 class="title-category">{ticker}: Trả cổ tức bằng tiền</h3>
<div class="time-newstcph">Cập nhật ngày 04/06/2025 - 10:22:43</div>
<div class="content-category"><div>Mã chứng khoán: {ticker}</div><div>Ngày đăng ký cuối cùng: 13/06/2025</div>
<p>1 cổ phiếu được nhận 1.000 đồng</p><p>Ngày thanh toán: 20/06/2025</p></div>
<aside>OTHER: 1 cổ phiếu được nhận 9.000 đồng Ngày thanh toán: 01/01/2025</aside>'''
    return dict(url='https://vsdc.vn/vi/ad/12345',status=200,body=body,
        sha256=hashlib.sha256(body.encode()).hexdigest(),observed_at='2026-10-21T01:00:00Z')


def test_official_dividend_body_owns_terms_and_never_infers_exdate_or_publication_timezone():
    from src.providers.vsdc_dividends import parse_cash_notice,dividend_page
    r=dividend_receipt();item=parse_cash_notice(r)
    assert item.symbol=='ABC' and item.terms.cash_vnd_per_share==1000
    assert str(item.record_date)=='2025-06-13' and str(item.payment_date)=='2025-06-20'
    assert item.effective_date is None and item.announced_at is None and str(item.announced_on)=='2025-06-04'
    page=dividend_page(dict(contract='vsdc-cash-dividends-v1',pages=[r]),'ABC')
    assert page['coverage']=='INCOMPLETE' and page['public_display_eligible'] is False
    assert dividend_page(dict(contract='vsdc-cash-dividends-v1',pages=[r]),'OTHER')['items']==[]


@pytest.mark.parametrize('bad',['hash','host','naive_time','foreign_owner','reversed_dates','stock_dividend','duplicate_article'])
def test_dividend_evidence_fail_closed(bad):
    from src.providers.vsdc_dividends import parse_cash_notice
    r=dividend_receipt()
    if bad=='hash':r['body']+=' '
    elif bad=='host':r['url']='https://example.test/vi/ad/12345'
    elif bad=='naive_time':r['observed_at']='2026-10-21T01:00:00'
    else:
        if bad=='foreign_owner':r['body']=r['body'].replace('Mã chứng khoán: ABC','Mã chứng khoán: OTHER')
        elif bad=='reversed_dates':r['body']=r['body'].replace('20/06/2025','01/06/2025')
        elif bad=='stock_dividend':r['body']=r['body'].replace('cổ tức bằng tiền','cổ tức bằng cổ phiếu')
        else:r['body']+='<div class="content-category">Other article</div>'
        r['sha256']=hashlib.sha256(r['body'].encode()).hexdigest()
    with pytest.raises(ValueError):parse_cash_notice(r)


def test_preferred_reports_preserve_original_provider_history_and_no_corrupt_fallback(tmp_path):
    from scripts.prepare_free_financial_bundle import prepare
    from src.services.personal_financials import saved_research_packet
    from test_personal_financials import source
    baseline=tmp_path/'baseline';baseline.mkdir()
    raw=source().model_dump_json().encode();(baseline/'packet.json').write_bytes(raw)
    (baseline/'index.json').write_text(json.dumps(dict(contract='personal-saved-captures-v1',captures=dict(ABC=dict(file='packet.json',sha256=hashlib.sha256(raw).hexdigest(),format='canonical-financial-packet-v1')))))
    reports=tmp_path/'reports';reports.mkdir();e=reviewed(reports)
    manifest=reports/'review.json';manifest.write_text(json.dumps(e),encoding='utf-8')
    destination=tmp_path/'bundle'
    prepare(baseline,destination,reports=[manifest])
    assert saved_research_packet(destination,'ABC')[0].source=='issuer:example'
    assert saved_research_packet(destination,'ABC',evidence='provider')[0].source=='vnstock:VCI'
    assert saved_research_packet(destination,'ABC',frequency='quarterly')[0].source=='vnstock:VCI'
    assert (baseline/'packet.json').read_bytes()==raw
    with pytest.raises(ValueError):prepare(baseline,destination,reports=[manifest])
    (destination/'source.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError):saved_research_packet(destination,'ABC')
    assert saved_research_packet(destination,'ABC',evidence='provider')[0].source=='vnstock:VCI'


def membership_bundle(tmp_path):
    from src.services.industry_membership_review import review_memberships
    records=[dict(symbol=t,board='HOSE',stockType='Stock',icbCode='1234',icbName='Observed category') for t in ('ABC','DEF','GHI')]
    review=review_memberships(records,receipt=dict(fetched_at='2026-10-17T00:00:00Z',document_sha256='a'*64),review_reference='synthetic-test')
    data=json.dumps(review).encode();(tmp_path/'memberships.json').write_bytes(data)
    index=dict(contract='personal-saved-captures-v1',captures={},observed_memberships=dict(file='memberships.json',sha256=hashlib.sha256(data).hexdigest()))
    for ticker in ('ABC','DEF'):
        sub=tmp_path/ticker;sub.mkdir();e=reviewed(sub);e.update(ticker=ticker)
        # Quotes/identity and numbers are a deliberately synthetic same-model cohort.
        name=ticker+'/review.json';body=json.dumps(e).encode();(tmp_path/name).write_bytes(body)
        index['captures'][ticker]=dict(file=name,sha256=hashlib.sha256(body).hexdigest(),format='reviewed-report-v2')
        # Report assets live beside the index in a real bundle.
    return index


def test_observed_membership_ranking_requires_compatible_accounting_evidence(tmp_path,monkeypatch):
    from src.services import observed_industries as service
    from src.services.personal_financials import saved_packet
    from test_personal_financials import source
    index=membership_bundle(tmp_path)
    (tmp_path/'index.json').write_text(json.dumps(index),encoding='utf-8')
    # Use the actual reviewed loader on per-issuer source directories.
    def load(directory,ticker,**kwargs):
        folder=tmp_path/ticker
        (folder/'index.json').write_text(json.dumps(dict(contract='personal-saved-captures-v1',captures={ticker:dict(file='review.json',sha256=index['captures'][ticker]['sha256'],format='reviewed-report-v2')})))
        return saved_packet(folder,ticker)
    monkeypatch.setattr(service,'saved_research_packet',load)
    response=service.observed_peers(tmp_path,'1234',period='2025')
    metric=response['metrics']['net_profit']
    assert metric['covered_companies']==2 and metric['expected_companies']==3
    assert metric['comparable_companies']==2 and all(o['comparison_eligible'] and o['rank'] is None and o['percentile'] is None for o in metric['observations'])
    assert response['sector_totals'] is None and response['classification_effective_at'] is None
    assert response['public_display_eligible'] is False and response['historical_aggregation_enabled'] is False
    # Unknown-scope source amounts remain inspectable but receive no rank.
    monkeypatch.setattr(service,'saved_research_packet',lambda directory,ticker,**kwargs:(source(ticker=ticker),'b'*64))
    partial=service.observed_peers(tmp_path,'1234',period='2025')['metrics']['net_profit']
    assert partial['covered_companies']==2 and partial['comparable_companies']==0
    assert all(o['rank'] is None and o['percentile'] is None for o in partial['observations'])


@pytest.mark.parametrize('path',['/personal-research/industries','/personal-research/industries/1234?period=2025','/personal-research/dividends/ABC','/personal-research/peers/ABC?period=2025'])
def test_new_research_routes_share_the_existing_socket_and_host_boundary(monkeypatch,path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routers.personal_research import router
    app=FastAPI();app.include_router(router)
    monkeypatch.setenv('APP_ENV','development');monkeypatch.setenv('WOOFI_PERSONAL_RESEARCH','1');monkeypatch.setenv('WOOFI_PERSONAL_BIND','127.0.0.1')
    client=TestClient(app,client=('127.0.0.1',1234),base_url='http://127.0.0.1')
    assert client.get(path,headers={'Host':'foreign.invalid'}).status_code==404
    assert TestClient(app,client=('203.0.113.1',1234),base_url='http://127.0.0.1').get(path,headers={'X-Forwarded-For':'127.0.0.1'}).status_code==404
    monkeypatch.setenv('WOOFI_PERSONAL_RESEARCH','0')
    assert client.get(path).status_code==404
