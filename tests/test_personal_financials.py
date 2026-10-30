"""Synthetic security/semantic fixtures; saved real captures validated separately."""
import copy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.personal_research import router
from src.services.personal_financials import personal_projection
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response
from test_financial_engine import fixture
from src.providers.vnstock.financial_packet import packet_from_payloads
from src.schemas.financials import FinancialLine


def source(company='CT', ticker='ABC'):
    metadata,reports=fixture(company)
    for report in reports.values():
        for bucket in report.values():
            for row in bucket: row['ticker']=ticker
    return packet_from_payloads(ticker,'vnstock:VCI',company,metadata,reports,source_version='synthetic-test')


@pytest.mark.parametrize('frequency',['annual','quarterly','ttm'])
@pytest.mark.parametrize('ticker',['ABC','FPT','PNJ','VCB','OTHER'])
def test_personal_observations_are_separate_from_public_and_never_certify_unknown_basis(ticker,frequency):
    packet=source(ticker=ticker);before=packet.model_dump()
    result=personal_projection(packet,frequency=frequency,authorization_reference='synthetic-test')
    assert result['display_scope']=='personal_research' and result['access_classification']=='PERSONAL_RESEARCH'
    assert result['data_confidence']=='SOURCE_REPORTED'
    last=result['rows'][-1]
    assert last['revenue']==(None if frequency=='ttm' else 30 if frequency=='quarterly' else 120)
    assert last['roe'] is None and last['net_margin'] is None and last['revenue_growth_yoy'] is None
    assert last['total_assets']==200
    assert all(o.consolidation is None for r in packet.reports.values() for o in r.observations)
    public=display_financial_response(financial_engine(packet,frequency=frequency))
    assert all(m.value is None for m in public.fundamental_summary.metrics)
    assert packet.model_dump()==before


@pytest.mark.parametrize('mutation',['prohibited','unit','basis','missing','conflict'])
def test_source_gates_remain_enforced(mutation):
    packet=source()
    for row in packet.reports['income'].observations:
        if mutation=='prohibited':row.source_context.display_rights='prohibited'
        elif mutation=='unit':row.source_context.unit_evidence='original_filing'
        elif mutation=='basis':row.basis='unknown'
        elif mutation=='missing':row.fields['revenue']=None
        else:row.fields['revenue']=None;row.items[0].semantic_status='conflicted'
    result=personal_projection(packet,authorization_reference='synthetic')
    assert result['rows'][-1]['revenue'] is None
    assert result['rows'][-1]['total_assets']==200


def test_bank_is_not_given_industrial_revenue_or_inventory_ratios():
    view=personal_projection(source('NH'),authorization_reference='synthetic')
    assert view['profile']=='bank'
    assert view['rows'][-1]['operating_income']==80
    assert all(view['rows'][-1][k] is None for k in ['revenue','gross_margin','net_margin','current_ratio'])
    assert next(p for p in view['research_panels'] if p['key']=='growth')['series'][0]['key']=='operating_income'


def test_bank_growth_is_visible_only_as_partially_verified_from_exact_private_vci_period_pairs():
    packet=source('NH')
    for obs in packet.reports['balance'].observations:
        if obs.frequency=='annual':
            loan,deposit={'2023':(100,80),'2024':(110,88),'2025':(121,96)}[obs.period]
        elif obs.period.startswith('2023'):
            loan,deposit=100,80
        elif obs.period.startswith('2024'):
            loan,deposit=110,88
        else:
            loan,deposit=120+int(obs.period[-1])*10,96+int(obs.period[-1])*8
        obs.fields.update(customer_loans=loan,customer_deposits=deposit)
        obs.field_codes.update(customer_loans='bsb104',customer_deposits='bsb113')
        for field,code,value in [('customer_loans','bsb104',loan),('customer_deposits','bsb113',deposit)]:
            line=next(line for line in obs.items if line.code==code)
            line.value=value;line.raw_value=value;line.unit='VND';line.semantic_status='reported'
    annual=personal_projection(packet,frequency='annual',authorization_reference='synthetic-bank-growth')
    qtr=personal_projection(packet,frequency='quarterly',authorization_reference='synthetic-bank-growth')
    annual_latest=annual['rows'][-1]
    assert annual_latest['customer_loans_growth_yoy']==pytest.approx(.1)
    assert annual['verification']['periods'][-1]['metrics']['customer_loans_growth_yoy']['status']=='PARTIALLY_VERIFIED'
    assert annual['verification']['periods'][-1]['metrics']['customer_loans_growth_yoy']['display_eligible'] is True
    assert annual['verification']['periods'][-1]['metrics']['customer_loans_growth_yoy']['dimensions']['ACCOUNTING_VERIFIED'] is False
    growth=next(panel for panel in annual['research_panels'] if panel['key']=='bank_growth')
    assert growth['status']=='PARTIALLY_VERIFIED'
    assert growth['rows'][-1]['values']['customer_loans_growth_yoy']==pytest.approx(.1)
    assert growth['rows'][-1]['statuses']['customer_loans_growth_yoy']=='PARTIALLY_VERIFIED'
    assert growth['rows'][-1]['values']['customer_loans_growth_qoq'] is None
    qgrowth=next(panel for panel in qtr['research_panels'] if panel['key']=='bank_growth')
    assert qgrowth['rows'][-1]['values']['customer_loans_growth_qoq']==pytest.approx(10/150)
    assert qgrowth['rows'][-1]['values']['customer_deposits_growth_qoq']==pytest.approx(8/120)
    assert qgrowth['rows'][-1]['values']['customer_loans_growth_yoy']==pytest.approx(50/110)
    public=display_financial_response(financial_engine(packet,frequency='annual'))
    assert all(row['customer_loans_growth_yoy'] is None for row in public.rows)


@pytest.mark.parametrize('mutation',['prohibited','wrong_line','missing_comparable','conflicting_scope'])
def test_private_bank_growth_fails_closed_on_bad_source_evidence(mutation):
    packet=source('NH')
    for obs in packet.reports['balance'].observations:
        value=100 if obs.period=='2024' else 110
        obs.fields.update(customer_loans=value,customer_deposits=value)
        obs.field_codes.update(customer_loans='bsb104',customer_deposits='bsb113')
        for code in ('bsb104','bsb113'):
            line=next(line for line in obs.items if line.code==code)
            line.value=value;line.raw_value=value;line.unit='VND';line.semantic_status='reported'
    current=next(obs for obs in packet.reports['balance'].observations if obs.period=='2025')
    prior=next(obs for obs in packet.reports['balance'].observations if obs.period=='2024')
    if mutation=='prohibited':current.source_context.display_rights='prohibited'
    elif mutation=='wrong_line':current.field_codes['customer_loans']='bsb999'
    elif mutation=='missing_comparable':packet.reports['balance'].observations.remove(prior)
    else:prior.consolidation='consolidated';current.consolidation='standalone'
    result=personal_projection(packet,authorization_reference='synthetic-bank-growth')
    assert result['rows'][-1]['customer_loans_growth_yoy'] is None


def test_conflicting_bases_remain_individual_observations_but_never_form_a_chart():
    packet=source()
    for kind,receipt in packet.reports.items():
        for row in receipt.observations:
            row.consolidation='consolidated' if row.period.startswith('2025') else 'standalone'
    result=personal_projection(packet,authorization_reference='synthetic')
    assert result['rows'][-1]['total_assets']==200
    for key in ['growth','balance_history']:
        panel=next(p for p in result['research_panels'] if p['key']==key)
        assert panel['status']=='UNQUALIFIED'
        assert all(v is None for p in panel['rows'] for v in p['values'].values())


def test_unknown_basis_does_not_turn_ytd_into_reported_quarter_or_fill_missing_period():
    packet=source()
    for row in packet.reports['income'].observations:
        if row.frequency=='quarterly':row.basis='ytd'
    result=personal_projection(packet,frequency='quarterly',authorization_reference='synthetic')
    assert result['rows'][-1]['revenue'] is None
    assert all(p['values']['revenue'] is None for p in next(p for p in result['research_panels'] if p['key']=='growth')['rows'])


def test_private_statement_table_exposes_direct_ytd_vci_lines_without_relabeling_them():
    packet=source()
    observation=next(row for row in packet.reports['income'].observations if row.period=='2025-Q1')
    observation.basis='ytd'
    observation.source_context.original_metadata['flowBasis']='ytd'
    observation.items.append(FinancialLine(code='isa900',name_en='Other reported income',name_vi='Thu nhập khác',
        parent=None,unit='VND',value=77,raw_value=77,semantic_status='reported'))
    balance=next(row for row in packet.reports['balance'].observations if row.period=='2025-Q1')
    balance.items.append(FinancialLine(code='nos360',name_en='Outstanding Shares (Volume)',name_vi='Khối lượng cổ phiếu lưu hành',
        parent=None,unit='VND',value=123456,raw_value=123456,semantic_status='reported'))
    balance.items.append(FinancialLine(code='ratio999',name_en='Return ratio (%)',name_vi='Tỷ lệ sinh lời (%)',
        parent=None,unit='VND',value=15,raw_value=15,semantic_status='reported'))
    result=personal_projection(packet,frequency='quarterly',limit=34,authorization_reference='synthetic')
    period=next(row for row in result['statements']['income']['periods'] if row['period']=='2025-Q1')
    direct=next(row for row in period['items'] if row['code']=='isa900')
    assert direct['value']==77 and direct['semantic_status']=='reported'
    assert period['basis']=='ytd' and period['access_classification']=='PERSONAL_RESEARCH'
    balance_period=next(row for row in result['statements']['balance']['periods'] if row['period']=='2025-Q1')
    volume=next(row for row in balance_period['items'] if row['code']=='nos360')
    assert volume['value']==123456 and volume['unit']=='shares'
    assert all(row['code']!='ratio999' or row['value'] is None for row in balance_period['items'])
    row=next(row for row in result['rows'] if row['period']=='2025-Q1')
    assert row['revenue'] is None


def test_hierarchy_component_panels_keep_siblings_and_missing_periods_without_parent_totals():
    packet=source()
    observations=packet.reports['balance'].observations
    for observation in observations:
        observation.items.extend([
            FinancialLine(code='bsa900',name_en='Source parent total',name_vi='Tổng nguồn',
                parent=None,unit='VND',value=100,raw_value=100,semantic_status='reported'),
            FinancialLine(code='bsa901',name_en='Cash component',name_vi='Tiền',
                parent='BSA900',unit='VND',value=65,raw_value=65,semantic_status='reported'),
            FinancialLine(code='bsa902',name_en='Other component',name_vi='Khác',
                parent='BSA900',unit='VND',value=35,raw_value=35,semantic_status='reported'),
        ])
    observations[-1].items[-1].value=None
    observations[-1].items[-1].raw_value=None
    result=personal_projection(packet,frequency='quarterly',limit=34,authorization_reference='synthetic')
    panel=next(p for p in result['research_panels'] if p['key']=='components:balance:bsa900')
    assert panel['chart']=='stacked' and panel['partial'] is True
    assert [series['key'] for series in panel['series']]==['bsa901','bsa902']
    assert all(series['key']!='bsa900' for series in panel['series'])
    assert panel['rows'][-1]['statement_basis']=='point_in_time'
    assert panel['rows'][-1]['values']=={'bsa901':65,'bsa902':None}
    assert panel['rows'][-1]['statuses']=={'bsa901':'SOURCE_REPORTED','bsa902':'UNAVAILABLE'}
    assert any('1/2 observed child codes have values' in reason and 'not a share of the reported parent total' in reason for reason in panel['reasons'])


@pytest.mark.parametrize('mutation',['prohibited','unit'])
def test_unmapped_statement_lines_stay_hidden_without_vci_rights_and_unit_evidence(mutation):
    packet=source()
    observation=next(row for row in packet.reports['balance'].observations if row.period=='2025-Q1')
    observation.items.append(FinancialLine(code='bsa900',name_en='Other reported assets',name_vi='Tài sản khác',
        unit='VND',value=123,raw_value=123,semantic_status='reported'))
    if mutation=='prohibited':observation.source_context.display_rights='prohibited'
    else:observation.source_context.unit_evidence='original_filing'
    result=personal_projection(packet,frequency='quarterly',limit=34,authorization_reference='synthetic')
    period=next(row for row in result['statements']['balance']['periods'] if row['period']=='2025-Q1')
    assert all(line['code']!='bsa900' for line in period['items'])


@pytest.mark.parametrize('peer,host,env,headers',[
 ('127.0.0.1','127.0.0.1',{},{}),
 ('192.0.2.1','127.0.0.1',{'WOOFI_PERSONAL_RESEARCH':'1'}, {'X-Forwarded-For':'127.0.0.1'}),
 ('127.0.0.1','evil.example',{'WOOFI_PERSONAL_RESEARCH':'1'},{}),
 ('127.0.0.1','127.0.0.1',{'WOOFI_PERSONAL_RESEARCH':'1','APP_ENV':'production'},{}),
])
def test_public_request_cannot_select_personal_mode(monkeypatch,peer,host,env,headers):
    for key in ('WOOFI_PERSONAL_RESEARCH','APP_ENV','WOOFI_PERSONAL_BIND'):monkeypatch.delenv(key,raising=False)
    monkeypatch.setenv('APP_ENV','development');monkeypatch.setenv('WOOFI_PERSONAL_BIND','127.0.0.1')
    for k,v in env.items():monkeypatch.setenv(k,v)
    app=FastAPI();app.include_router(router)
    client=TestClient(app,client=(peer,12345),base_url='http://'+host)
    response=client.get('/personal-research/financials/ABC?personal=1&scope=personal_research',headers=headers|{'X-Personal-Research':'1','Cookie':'personal=1'})
    assert response.status_code==404 and '120' not in response.text


def test_loopback_opt_in_uses_saved_evidence_only(monkeypatch):
    for key,value in dict(WOOFI_PERSONAL_RESEARCH='1',APP_ENV='development',WOOFI_PERSONAL_BIND='127.0.0.1',WOOFI_PERSONAL_CAPTURES='synthetic').items():monkeypatch.setenv(key,value)
    monkeypatch.setattr('src.services.personal_financials.saved_research_packet',lambda *args,**kwargs:(source(),'f'*64))
    app=FastAPI();app.include_router(router)
    client=TestClient(app,client=('127.0.0.1',1234),base_url='http://127.0.0.1')
    response=client.get('/personal-research/financials/ABC?frequency=quarterly&limit=34')
    assert response.status_code==200 and response.json()['rows'][-1]['revenue']==30
    assert response.headers['cache-control']=='private, no-store'
