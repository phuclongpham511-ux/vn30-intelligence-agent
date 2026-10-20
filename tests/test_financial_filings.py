"""Synthetic boundary tests. The actual PNJ filing is validated offline separately."""
import copy
import hashlib
import pytest
from src.providers.financial_filings import filing_packet, reconcile_filing
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response
from test_financial_foundation_v2 import prepared


def evidence(ticker='ABC', unit='VND'):
    fields = []
    for index, (field, code, values) in enumerate([
        ('revenue','10',['1.000','900']),('net_profit','60',['100','90']),
        ('total_assets','270',['1.000','900']),('total_liabilities','300',['400','350']),
        ('equity','400',['600','550'])]):
        # Use source integer tokens with an explicit decimal grouping convention.
        values = [str(int(v.replace('.',''))*1000) for v in values]
        row = f'L{index+1}@P0: {code} {field} '+ ' '.join(values)
        fields.append(dict(field=field, code=code, label=field, page=1,
            printed_page='1', source_row=row, raw_values=values))
    e = dict(contract='reviewed-filing-v1',ticker=ticker,issuer='Synthetic company',
        exchange='HOSE',profile='non_financial',source='issuer:test',
        document_url='https://issuer.example/report.pdf',discovery_url='https://issuer.example/ir',
        document_title='Synthetic annual consolidated filing',document_sha256=None,
        observed_at='2026-10-20T00:00:00Z',published_date=None,publication_quote=None,
        consolidation='consolidated',basis_quote='CONSOLIDATED',identity_quote='Ticker '+ticker,
        period_quote='Annual period 1 January to 31 December',year_columns=[2024,2023],
        year_header='2024 VND 2023 VND',period_starts=['2024-01-01','2023-01-01'],
        period_ends=['2024-12-31','2023-12-31'],currency='VND',original_unit=unit,
        unit_quote='Units: '+unit,thousands_separator='none',
        extraction_method='reviewed_page_text',confidence='text_and_arithmetic_verified_not_visual',
        review_reference='synthetic-only://explicit-internal-review',fields=fields)
    text='\n'.join([e[k] for k in ['issuer','exchange','document_url','discovery_url','basis_quote','identity_quote','period_quote','year_header','unit_quote']]+[f['source_row'] for f in fields])
    e['extraction_sha256']=hashlib.sha256(text.encode()).hexdigest()
    return e,text


def test_source_to_canonical_to_scoped_engine_preserves_provenance_and_public_guard():
    e,text=evidence();before=copy.deepcopy(e)
    packet,audit=filing_packet(e,text)
    assert audit['normalized_fields']==10 and all(x['status']=='PASS' for x in audit['balance_identities'])
    assert packet.source=='issuer:test' and not packet.is_fixture
    obs=packet.reports['income'].observations[-1]
    assert obs.fields['revenue']==1000000 and obs.consolidation=='consolidated'
    assert obs.source_context.original_metadata['document_sha256'] is None
    assert obs.source_context.original_metadata['fields']['revenue']['page']==1
    assert obs.source_context.display_rights=='unreviewed'
    raw=financial_engine(packet)
    public=display_financial_response(raw)
    assert all(m.value is None for m in public.fundamental_summary.metrics)
    internal=display_financial_response(raw,internal_authorization_reference=e['review_reference'])
    metric=next(m for m in internal.fundamental_summary.metrics if m.key=='revenue')
    assert metric.value==1000000 and metric.status=='QUALIFIED'
    assert internal.display_scope=='internal_research' and internal.read_kind=='saved_filing_review'
    assert internal.statements['income']['periods'][-1]['items'][0]['value']==1000000
    assert internal.rows[-1]['cash_operating'] is None
    assert next(m for m in internal.fundamental_summary.metrics if m.key=='pe').value is None
    assert e==before and raw.display_scope=='public'
    with pytest.raises(ValueError,match='republished'):display_financial_response(internal)


@pytest.mark.parametrize('unit,multiplier',[('VND',1),('thousand VND',1000),('million VND',1000000),('billion VND',1000000000)])
def test_explicit_source_scale_is_applied_once(unit,multiplier):
    e,text=evidence(unit=unit);packet,_=filing_packet(e,text)
    observation=packet.reports['balance'].observations[-1]
    assert observation.fields['total_assets']==1000000*multiplier
    assert observation.items[0].raw_value==1000000
    assert observation.source_context.amount_multiplier==multiplier
    assert observation.source_context.original_unit==unit


@pytest.mark.parametrize('ticker',['ABC','FPT','PNJ','VCB','XYZ123'])
def test_ticker_support_is_manifest_driven(ticker):
    e,text=evidence(ticker);packet,_=filing_packet(e,text)
    assert packet.ticker==ticker


@pytest.mark.parametrize('change',[
    lambda e:e.update(extraction_sha256='0'*64),
    lambda e:e.update(ticker='OTHER'),
    lambda e:e.update(basis_quote='Missing basis'),
    lambda e:e.update(consolidation='standalone'),
    lambda e:e.update(year_columns=[2023,2024]),
    lambda e:e.update(year_columns=[2024,2024]),
    lambda e:e.update(original_unit='thousand VND'),
    lambda e:e.update(currency='USD'),
    lambda e:e.update(period_starts=['2025-01-01','2023-01-01']),
    lambda e:e.update(period_starts=['2024-02-01','2023-01-01']),
    lambda e:e.update(observed_at='2026-10-20'),
    lambda e:e.update(document_url='https://user:password@issuer.example/report.pdf'),
    lambda e:e.update(document_sha256='a'*64),
    lambda e:e.update(display_rights='permitted'),
    lambda e:e['fields'][0].update(page=2),
    lambda e:e['fields'][0].update(raw_values=['123','900000']),
    lambda e:e['fields'][0].update(raw_values=['1000','900000']),
    lambda e:e['fields'][0].update(raw_values=['10','900000']),
    lambda e:e['fields'][0].update(raw_values=['900000','1000000']),
    lambda e:e['fields'][0].update(raw_values=['NaN','900000']),
    lambda e:e.update(profile='bank'),
    lambda e:e.update(published_date='2025-01-01',publication_quote='not in source'),
])
def test_incomplete_or_contradictory_evidence_fails_closed(change):
    e,text=evidence();change(e)
    with pytest.raises(ValueError):filing_packet(e,text)


def test_missing_optional_field_stays_missing_and_exact_duplicate_is_not_summed():
    e,text=evidence();e['fields'].append(copy.deepcopy(e['fields'][0]))
    packet,audit=filing_packet(e,text)
    assert len(audit['duplicates'])==2 and audit['normalized_fields']==10
    assert packet.reports['income'].observations[-1].fields['revenue']==1000000
    e['fields']=[f for f in e['fields'] if f['field']!='equity']
    packet,audit=filing_packet(e,text)
    assert all(x['status']=='UNVERIFIED' for x in audit['balance_identities'])
    assert packet.reports['balance'].observations[-1].fields['equity'] is None


def test_arithmetic_contradiction_rejected_without_repair():
    e,text=evidence();item=next(f for f in e['fields'] if f['field']=='equity')
    old=item['source_row'];item['source_row']=old.replace('600000','601000');item['raw_values'][0]='601000'
    text=text.replace(old,item['source_row']);e['extraction_sha256']=hashlib.sha256(text.encode()).hexdigest()
    with pytest.raises(ValueError,match='balance identity'):filing_packet(e,text)


def test_reported_zero_profit_remains_zero_without_invented_growth():
    import re
    e,text=evidence();item=next(f for f in e['fields'] if f['field']=='net_profit')
    old=item['source_row'];item['source_row']=re.sub(r'\d+ \d+$','0 0',old);item['raw_values']=['0','0']
    text=text.replace(old,item['source_row']);e['extraction_sha256']=hashlib.sha256(text.encode()).hexdigest()
    packet,_=filing_packet(e,text)
    view=display_financial_response(financial_engine(packet),internal_authorization_reference='synthetic-review')
    assert view.rows[-1]['net_profit']==0 and view.rows[-1]['net_profit_growth_yoy'] is None


def test_conflicting_duplicate_does_not_replace_retained_evidence():
    e,text=evidence();alternative=copy.deepcopy(e['fields'][0]);alternative['code']='11'
    alternative['source_row']=alternative['source_row'].replace('10 revenue','11 revenue')
    text+='\n'+alternative['source_row'];e['fields'].append(alternative)
    e['extraction_sha256']=hashlib.sha256(text.encode()).hexdigest()
    before=copy.deepcopy(e)
    with pytest.raises(ValueError,match='Conflicting duplicate'):filing_packet(e,text)
    assert e==before


def test_reconciliation_preserves_uncertainty_and_distinct_versions_without_overwrite():
    e,text=evidence();official,_=filing_packet(e,text);other=official.model_copy(deep=True)
    for receipt in other.reports.values():
        for obs in receipt.observations:obs.consolidation=None
    other.reports['income'].observations[-1].fields['net_profit']+=1
    other.reports['income'].content_sha256='b'*64
    before=other.model_dump()
    result=reconcile_filing(official,other)
    assert all(r['basis']=='UNKNOWN' for r in result)
    conflict=next(r for r in result if r['field']=='net_profit' and r['period']=='2024')
    assert conflict['numeric']=='CONFLICT' and conflict['restatement']=='UNPROVEN_POSSIBLE_VERSION_DIFFERENCE'
    assert conflict['vintage']=='DISTINCT_RECEIPTS' and other.model_dump()==before
    other.ticker='OTHER'
    with pytest.raises(ValueError,match='different issuers'):reconcile_filing(official,other)


def test_reconciliation_reports_original_unit_and_period_differences_separately():
    e,text=evidence();official,_=filing_packet(e,text);other=official.model_copy(deep=True)
    for receipt in other.reports.values():
        for obs in receipt.observations:
            obs.source_context.original_unit=None
            obs.source_context.period_start=None
    result=reconcile_filing(official,other)
    assert all(r['numeric']=='MATCH' and r['original_unit_comparison']=='UNKNOWN' and r['period_comparison']=='LABEL_MATCH_BOUNDARIES_UNVERIFIED' for r in result)
    for receipt in other.reports.values():
        for obs in receipt.observations:
            obs.source_context.original_unit='million VND'
            obs.source_context.period_start=obs.period+'-02-01'
    result=reconcile_filing(official,other)
    assert all(r['original_unit_comparison']=='DIFFERENT' and r['period_comparison']=='CONFLICT' for r in result)


def test_original_unit_cannot_be_silently_downgraded_to_vnd():
    e,text=evidence(unit='million VND');e['original_unit']='VND'
    with pytest.raises(ValueError,match='scale contradicts'):filing_packet(e,text)


def test_internal_review_never_grants_vci_permission_or_overrides_prohibition():
    vci=prepared()
    for receipt in vci.reports.values():
        for obs in receipt.observations:
            obs.source_context.display_rights='unreviewed'
            obs.source_context.original_metadata['extraction_verified']=True
    view=display_financial_response(financial_engine(vci),internal_authorization_reference='synthetic-review')
    assert all(m.value is None for m in view.fundamental_summary.metrics)
    e,text=evidence();packet,_=filing_packet(e,text)
    for receipt in packet.reports.values():
        for obs in receipt.observations:obs.source_context.display_rights='prohibited'
    view=display_financial_response(financial_engine(packet),internal_authorization_reference='synthetic-review')
    assert all(m.value is None for m in view.fundamental_summary.metrics)


def test_public_http_query_cannot_select_internal_scope(client, session):
    from datetime import datetime, timezone
    from main import app
    from src.models import Security
    from src.services.data import get_fundamental_provider
    e,text=evidence();packet,_=filing_packet(e,text)
    session.add(Security(symbol='ABC',exchange='HOSE',last_synced_at=datetime.now(timezone.utc)))
    session.commit()
    class Provider:
        source=packet.source
        def get_reports(self,symbol):return packet.model_copy(deep=True)
    app.dependency_overrides[get_fundamental_provider]=Provider
    try:
        response=client.get('/stocks/ABC/financials?projection=display&display_scope=internal_research&internal_authorization_reference=test')
        assert response.status_code==200
        body=response.json()
        assert body['display_scope']=='public' and body['internal_authorization_reference'] is None
        assert all(m['value'] is None for m in body['fundamental_summary']['metrics'])
    finally:
        app.dependency_overrides.pop(get_fundamental_provider,None)
