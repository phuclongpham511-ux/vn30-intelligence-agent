"""Definition/basis regressions using synthetic notes, never copied issuer data."""
import hashlib
import pytest
from test_free_financial_sources import reviewed
from src.providers.reviewed_reports import report_packet
from src.services.personal_financials import personal_projection
from src.services.financial_intelligence import metric_unit


def notes(tmp_path, *, contradiction=False):
    e=reviewed(tmp_path)
    e.update(company_type='NH',profile='bank')
    e['amounts']=[a for a in e['amounts'] if a['field'] not in ('revenue','gross_profit')]
    page=e['pages'][0]
    for field,value in dict(customer_loans=1200,customer_deposits=800,customer_demand_deposits=400,
            classified_loans=1000,loan_grade_1=810 if contradiction else 800,loan_grade_2=100,
            loan_grade_3=40,loan_grade_4=30,loan_grade_5=30,
            loan_allowance_general=30,loan_allowance_specific=20).items():
        row=f'{field} {value} {value}';page['text']+='\n'+row
        for year in (2024,2025):
            e['amounts'].append(dict(field=field,code='row:'+field,code_kind='reviewed_row_locator',label=field,
                year=year,raw_token=str(value),column_values=[str(value)]*2,column_periods=['2025','2024'],
                source_row=dict(page=1,text=row),column_header=dict(page=1,text='2025 VND 2024 VND'),
                unit_quote=dict(page=1,text='VND'),unit='VND',period_start=None,period_end=f'{year}-12-31'))
    page['text_sha256']=hashlib.sha256(page['text'].encode()).hexdigest()
    return e


def test_classified_credit_denominators_exclude_margin_loans_and_keep_rights_independent(tmp_path):
    packet,_=report_packet(notes(tmp_path),tmp_path)
    view=personal_projection(packet,authorization_reference='synthetic:test')
    row=view['rows'][-1]
    assert row['classified_nonperforming_loans']==100
    assert row['npl_classified_ratio']==.1  # Not 100 / 1,200 consolidated gross lending.
    assert row['classified_loan_allowance']==50 and row['classified_loan_coverage']==.5
    assert row['demand_deposit_share']==.5
    states=view['verification']['periods'][-1]['metrics']
    for key in ('demand_deposit_share','npl_classified_ratio','classified_loan_coverage'):
        assert metric_unit(key)=='fraction'
        assert states[key]['dimensions']['ACCOUNTING_VERIFIED']
        assert states[key]['dimensions']['REPORTING_METADATA_COMPLETE']
        assert not states[key]['dimensions']['POINT_IN_TIME_VERIFIED']
        assert not states[key]['dimensions']['PUBLICATION_RIGHTS_APPROVED']
    assert row['revenue'] is None and 'nim' not in row


def test_credit_note_contradiction_blocks_affected_ratios_without_blanking_other_financials(tmp_path):
    packet,_=report_packet(notes(tmp_path,contradiction=True),tmp_path)
    view=personal_projection(packet,authorization_reference='synthetic:test')
    row=view['rows'][-1]
    assert row['npl_classified_ratio'] is None and row['classified_loan_coverage'] is None
    assert row['demand_deposit_share']==.5 and row['cash_operating']==200
    state=view['verification']['periods'][-1]['metrics']['loan_grade_1']
    assert state['dimensions']['SOURCE_VERIFIED'] and not state['dimensions']['ACCOUNTING_VERIFIED']


def test_peer_distribution_and_company_lookup_keep_missing_members(tmp_path,monkeypatch):
    from test_free_financial_sources import membership_bundle
    from src.services import observed_industries as service
    from src.services.personal_financials import saved_packet
    import json
    index=membership_bundle(tmp_path)
    (tmp_path/'index.json').write_text(json.dumps(index))
    def load(directory,ticker,**kwargs):
        folder=tmp_path/ticker
        (folder/'index.json').write_text(json.dumps(dict(contract='personal-saved-captures-v1',captures={ticker:dict(file='review.json',sha256=index['captures'][ticker]['sha256'],format='reviewed-report-v2')})))
        return saved_packet(folder,ticker)
    monkeypatch.setattr(service,'saved_research_packet',load)
    body=service.company_peers(tmp_path,'ABC',period='2025')
    metric=body['metrics']['net_profit']
    assert metric['distribution']==dict(count=2,minimum=100,median=100,maximum=100)
    assert metric['expected_companies']==3 and metric['missing']=={'GHI':'no_saved_financial_evidence'}
    assert body['sector_totals'] is None and not body['historical_aggregation_enabled']
    with pytest.raises(FileNotFoundError):service.company_peers(tmp_path,'UNKNOWN',period='2025')
