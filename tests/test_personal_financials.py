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
    monkeypatch.setattr('routers.personal_research.saved_packet',lambda *args:(source(),'f'*64))
    app=FastAPI();app.include_router(router)
    response=TestClient(app,client=('127.0.0.1',1234),base_url='http://127.0.0.1').get('/personal-research/financials/ABC')
    assert response.status_code==200 and response.json()['rows'][-1]['revenue']==120
    assert response.headers['cache-control']=='private, no-store'
