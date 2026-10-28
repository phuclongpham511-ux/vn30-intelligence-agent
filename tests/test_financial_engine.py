"""Public normalization, analytics and HTTP seams; synthetic, no source acquisition."""
import copy
from datetime import datetime, timezone
import pytest
from sqlalchemy import event
from src.providers.vnstock.financial_statements import MAP, SECTIONS, normalize_statement
from src.providers.vnstock.financial_packet import packet_from_payloads
from src.analytics.financial_engine import financial_engine
from src.models import Security
from src.services.data import get_fundamental_provider
from main import app

LABELS = {
 'isa3':'Net sales','isa5':'Gross profit','isa20':'Net profit after tax','isa22':'Attributable to parent company',
 'isa23':'EPS basic (VND)','isb38':'Total Operating Income','isb27':'Net Interest Income',
 'bsa53':'Total assets','bsa54':'Liabilities','bsa78':"Owner's equity",'bsa1':'Current assets',
 'bsa55':'Current liabilities','bsa15':'Inventories, net','bsa2':'Cash and cash equivalents',
 'bsa56':'Short-term borrowings','bsa71':'Long-term borrowings','bsb104':'Loans and advances to customers',
 'bsb113':'Deposits from customers','cfa18':'Net cash from operating activities',
 'cfa26':'Net cash from investing activities','cfa34':'Net cash from financing activities',
 'cfa19':'Purchases of fixed assets and other long term assets',
 'cfa35':'Net increase in cash and cash equivalents','cfa36':'Cash and cash equivalents at beginning of period',
 'cfa38':'Cash and cash equivalents at end of period'}


def fixture(company_type='CT'):
    metadata=[dict(field_name=code,report_name=SECTIONS[kind],en_name=LABELS[code],name=LABELS[code])
              for kind, fields in MAP.items() for code,_ in fields.values()]
    reports={kind:dict(years=[],quarters=[]) for kind in MAP}
    for kind in MAP:
        for year in (2023,2024,2025):
            raw=dict(ticker='ABC',yearReport=year,lengthReport=5,currency='VND')
            raw.update({code:None for code,_ in MAP[kind].values()})
            raw.update({'isa3':100 if year!=2025 else 120,'isa5':30,'isa20':10 if year!=2025 else 12,'isa22':9,'isa23':2,
              'isb38':80,'isb27':60} if kind=='income' else
              {'bsa53':200,'bsa54':120,'bsa78':80 if year!=2025 else 100,'bsa1':80,'bsa55':40,'bsa15':20,'bsa56':10,'bsa71':5} if kind=='balance' else
              {'cfa18':18,'cfa19':-5,'cfa26':-6,'cfa34':2,'cfa35':14,'cfa36':30,'cfa38':44})
            reports[kind]['years'].append(raw)
            for quarter in range(1,5):
                q={**raw,'lengthReport':quarter}
                if kind!='balance':
                    for code in MAP[kind].values():
                        if q.get(code[0]) is not None:q[code[0]]/=4
                reports[kind]['quarters'].append(q)
    return metadata,reports


def packet(metadata=None,reports=None,company_type='CT'):
    defaults=fixture(company_type)
    return packet_from_payloads('ABC','test:VCI',company_type,metadata or defaults[0], reports or defaults[1],
        source_version='fixture',is_fixture=True)


def test_calculations_match_accounting_inputs_and_group_profit_basis():
    result=financial_engine(packet())
    row=result.rows[-1]
    assert row['revenue']==120 and row['revenue_growth_yoy']==pytest.approx(.2)
    assert row['roe']==pytest.approx(12/90) and row['roa']==pytest.approx(12/200)
    assert row['gross_margin']==.25 and row['net_margin']==.1
    assert row['total_debt']==15 and row['debt_equity']==.15
    assert row['current_ratio']==2 and row['quick_ratio']==1.5
    assert row['cash_conversion']==1.5 and row['free_cash_flow']==13
    assert row['profit_parent']==9 and row['eps_reported']==2
    assert row['calculations']['roe']['inputs'][0]['code']=='isa20'
    assert row['calculations']['roe']['inputs'][-1]['period']=='2024'
    assert row['is_fixture'] and result.is_fixture and result.source_receipts[0]['content_sha256']


def test_bank_metadata_excludes_padded_fields_and_conflicting_cash_code():
    meta,reports=fixture('NH')
    meta=[item for item in meta if item['field_name'] not in ('isa3','isa5','cfa35')]
    next(item for item in meta if item['field_name']=='cfa34')['en_name']='Net Increase/(Decrease) in cash and cash equivalents'
    result=financial_engine(packet(meta,reports,'NH'))
    row=result.rows[-1]
    assert result.profile=='bank' and row['operating_income']==80
    assert row['revenue'] is None and row['gross_margin'] is None and row['current_ratio'] is None
    assert row['cash_financing'] is None and row['cash_net_change'] is None
    assert row['roe']==pytest.approx(12/90)
    original=next(item for item in result.statements['cash']['periods'][-1]['items'] if item['code']=='cfa34')
    assert original['raw_value']==2 and original['value'] is None and original['semantic_status']=='conflicted'


def test_zero_negative_missing_bases_gaps_and_capex_sign_are_not_fabricated():
    meta,reports=fixture()
    reports['income']['years'][1]['isa3']=0
    reports['income']['years'][1]['isa20']=-2
    reports['income']['years'][2]['isa20']=0
    reports['cash']['years'][2]['cfa19']=5
    result=financial_engine(packet(meta,reports),limit=1)
    row=result.rows[-1]
    assert row['net_profit']==0 and row['revenue_growth_yoy'] is None and row['net_profit_growth_yoy'] is None
    assert row['cash_conversion'] is None and row['capex_cash_outflow'] is None and row['free_cash_flow'] is None
    assert result.changes[-1]['absolute_change']==2
    reports={kind:{'years':[item for item in report['years'] if item['yearReport']!=2024],'quarters':[]} for kind,report in reports.items()}
    missing=financial_engine(packet(meta,reports))
    assert missing.rows[-1]['roe'] is None and missing.rows[-1]['revenue_growth_yoy'] is None
    assert missing.chart_rows[1]['period']=='2024' and missing.chart_rows[1]['revenue'] is None


def test_quarter_and_ttm_flows_point_balances_and_eps_are_distinct():
    p=packet()
    annual=financial_engine(p).rows[-1]
    quarter=financial_engine(p,frequency='quarterly').rows[-1]
    ttm=financial_engine(p,frequency='ttm').rows[-1]
    assert quarter['revenue']==30 and quarter['roe']==pytest.approx(3/100)
    assert ttm['revenue']==annual['revenue'] and ttm['total_assets']==200
    assert ttm['roe']==annual['roe'] and ttm['eps_reported'] is None
    assert ttm['calculations']['revenue']['inputs'][0]['period']=='2025-Q1'
    meta,reports=fixture()
    reports['income']['quarters']=[q for q in reports['income']['quarters'] if not(q['yearReport']==2025 and q['lengthReport']==2)]
    broken=financial_engine(packet(meta,reports),frequency='ttm').rows[-1]
    assert broken['revenue'] is None and broken['net_profit'] is None


def test_explicit_ytd_requires_previous_same_year_and_comparable_basis():
    meta,reports=fixture()
    for kind in ('income','cash'):
        for q in reports[kind]['quarters']:
            q['flowBasis']='ytd'
            for code in MAP[kind].values():
                if q.get(code[0]) is not None:q[code[0]]*=q['lengthReport']
    result=financial_engine(packet(meta,reports),frequency='quarterly')
    assert result.rows[-1]['revenue']==30 and result.rows[-1]['cash_operating']==4.5
    reports['income']['quarters'][-2]['consolidation']='standalone'
    assert financial_engine(packet(meta,reports),frequency='quarterly').rows[-1]['revenue'] is None


@pytest.mark.parametrize('mutation', ['owner','currency','period','duplicate','unit'])
def test_normalizer_rejects_corrupt_records(mutation):
    meta,reports=fixture()
    raw=reports['income']['years'][-1]
    if mutation=='owner':raw['ticker']='OTHER'
    if mutation=='currency':raw['currency']='USD'
    if mutation=='unit':raw['unit']='millions'
    if mutation=='period':raw['lengthReport']=1
    if mutation=='duplicate':reports['income']['years'].append(copy.deepcopy(raw))
    with pytest.raises(ValueError):normalize_statement('ABC','test:VCI','income',reports['income'],meta,'non_financial')


def test_api_contract_is_select_only_and_old_route_is_unchanged(client,session):
    session.add(Security(symbol='ABC',exchange='HOSE',company_name='ABC',last_synced_at=datetime.now(timezone.utc)))
    session.commit()
    class Provider:
        source='test:VCI'
        def get_reports(self,ticker):return packet()
    app.dependency_overrides[get_fundamental_provider]=Provider
    queries=[]
    def inspect(conn,cursor,statement,params,context,many):queries.append(statement)
    event.listen(session.get_bind(),'before_cursor_execute',inspect)
    try:
        for frequency in ('annual','quarterly','ttm'):
            response=client.get('/stocks/ABC/financials',params={'frequency':frequency,'limit':2})
            assert response.status_code==200
            body=response.json()
            assert len(body['rows'])==2 and body['period_type']==frequency and body['is_fixture']
            assert body['source_receipts'][0]['content_sha256']
        assert client.get('/stocks/ABC/financials?frequency=monthly').status_code==422
        for kind in ('income','balance','cash'):
            response=client.get(f'/stocks/ABC/financials/statements/{kind}?frequency=quarterly&limit=1')
            assert response.status_code==200 and len(response.json()['rows'])==1
            assert response.json()['statement']==kind and response.json()['receipt']['observations']==[]
        assert client.get('/stocks/ABC/financials/statements/cash?frequency=ttm').status_code==422
        assert client.get('/stocks/UNKNOWN/financials').status_code==404
        assert not any(q.lstrip().upper().startswith(('INSERT','UPDATE','DELETE','CREATE')) for q in queries)
    finally:event.remove(session.get_bind(),'before_cursor_execute',inspect)


def test_http_source_failure_is_not_a_successful_empty_archive(client,session):
    session.add(Security(symbol='ABC',exchange='HOSE',last_synced_at=datetime.now(timezone.utc)))
    session.commit()
    broken=packet()
    for report in broken.reports.values():report.status='error';report.observations=[]
    class Provider:
        source='test:VCI'
        def get_reports(self,ticker):return broken
    app.dependency_overrides[get_fundamental_provider]=Provider
    assert client.get('/stocks/ABC/financials').status_code==502


def test_conflicting_duplicate_metadata_withholds_one_code_not_whole_statement():
    meta,reports=fixture()
    meta.append({'field_name':None,'report_name':'CASH_FLOW','en_name':'Group header'})
    meta.append({**next(item for item in meta if item['field_name']=='cfa34'),'en_name':'Another incompatible label'})
    result=financial_engine(packet(meta,reports))
    assert result.rows[-1]['cash_operating']==18 and result.rows[-1]['cash_financing'] is None
    line=next(item for item in result.statements['cash']['periods'][-1]['items'] if item['code']=='cfa34')
    assert len(line['source_labels'])==2 and line['raw_value']==2 and line['value'] is None


def test_unknown_flow_basis_and_incompatible_statements_fail_closed():
    meta,reports=fixture()
    reports['cash']['quarters'][-1]['flowBasis']='unknown'
    result=financial_engine(packet(meta,reports),frequency='quarterly')
    assert result.rows[-1]['cash_operating'] is None and result.rows[-1]['free_cash_flow'] is None
    reports['income']['years'][-1]['consolidation']='consolidated'
    reports['balance']['years'][-1]['consolidation']='standalone'
    changed=financial_engine(packet(meta,reports)).rows[-1]
    assert changed['roe'] is None and changed['net_margin'] is None and changed['revenue_growth_yoy'] is None


def test_annual_quarter_difference_is_inspectable_without_overwriting_annual():
    meta,reports=fixture()
    reports['income']['quarters'][-1]['isa20']+=2
    result=financial_engine(packet(meta,reports))
    assert result.rows[-1]['net_profit']==12
    difference=next(item for item in result.reconciliations if item['period']=='2025' and item['field']=='net_profit')
    assert difference['annual_reported']==12 and difference['quarter_sum']==14 and difference['difference']==2


def test_finite_source_inputs_cannot_create_nonfinite_growth_or_ttm_outputs():
    meta,reports=fixture()
    reports['income']['years'][1]['isa3']=1e-300
    reports['income']['years'][2]['isa3']=1e300
    for row in reports['income']['quarters']:row['isa3']=1e308
    p=packet(meta,reports)
    annual=financial_engine(p).rows[-1]
    assert annual['revenue_growth_yoy'] is None
    assert annual['calculations']['revenue_growth_yoy']['reason']=='nonfinite_result'
    ttm=financial_engine(p,frequency='ttm')
    assert ttm.rows[-1]['revenue'] is None and ttm.rows[-1]['gross_margin'] is None
    assert 'Infinity' not in ttm.model_dump_json()


def test_provider_packet_reads_once_per_section_with_finite_timeouts_and_shared_cache(monkeypatch):
    from types import SimpleNamespace
    from src.providers.vnstock import VnstockFundamentalDataProvider
    from src.providers.vnstock.financial_packet import fetch_packet
    import vnstock.core.utils.client as transport
    meta,reports=fixture()
    rawmeta={section:[dict(field=item['field_name'],titleEn=item['en_name'],titleVi=item['name'],parent=None)
        for item in meta if item['report_name']==section] for section in SECTIONS.values()}
    calls=[]
    def request(**kwargs):
        calls.append(kwargs)
        assert kwargs['timeout']==15 and kwargs['request_mode']=='direct' and kwargs['method']=='GET'
        if kwargs['url'].endswith('/metrics'):return {'data':rawmeta}
        kind=next(key for key,value in SECTIONS.items() if value==kwargs['params']['section'])
        if kind=='cash':raise TimeoutError('synthetic transport failure')
        return {'data':reports[kind]}
    monkeypatch.setattr(transport,'send_request',request)
    fake=SimpleNamespace(Finance=lambda **kwargs:SimpleNamespace(provider=SimpleNamespace(base_url='https://example.test',headers={},com_type_code='CT')))
    provider=VnstockFundamentalDataProvider()
    monkeypatch.setattr('src.providers.vnstock.financial_packet.fetch_packet',lambda symbol,sdk:fetch_packet(symbol,lambda:fake))
    first=provider.get_reports('ABC');second=provider.get_reports('ABC')
    assert len(calls)==4 and first.reports['cash'].status=='error' and first.reports['income'].status=='healthy'
    assert second.reports['cash'].status=='error'
    second.reports['income'].observations.clear()
    assert provider.get_reports('ABC').reports['income'].observations
