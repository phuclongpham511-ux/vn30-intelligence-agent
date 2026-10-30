from datetime import date
import pytest
from src.schemas.financial_intelligence import IndustryTaxonomy
from test_financial_intelligence import balanced


def taxonomy():
    return IndustryTaxonomy(name='Test classification',version='2025.1',source_reference='synthetic://review',
        industries=[dict(id='manufacturing',name_en='Manufacturing',name_vi='Sản xuất',model='non_financial')],
        memberships=[dict(ticker=t,industry_id='manufacturing',effective_from='2020-01-01',source_reference='synthetic://membership') for t in ('ABC','DEF','GHI')])


def facts():
    from src.services.financial_intelligence import normalized_metrics
    output=[]
    for ticker,profit,equity in [('ABC',10,100),('DEF',90,900)]:
        p=balanced(ticker)
        for receipt in p.reports.values():
            for obs in receipt.observations:
                if obs.frequency=='annual':
                    obs.source_context.period_start=f'{obs.period}-01-01'
                    obs.source_context.period_end=f'{obs.period}-12-31'
                if obs.statement=='income':
                    obs.fields['net_profit']=profit
                if obs.statement=='balance':
                    obs.fields.update(equity=equity,total_assets=equity+120)
        output.extend(normalized_metrics(p))
    return output


def test_aggregation_reports_observed_sum_and_matched_denominator_not_mean_ratios():
    from src.analytics.industry_financials import industry_snapshot
    response=industry_snapshot(taxonomy(),facts(),'manufacturing',period='2025',frequency='annual',membership_on=date(2025,12,31))
    m=response['metrics']['roe']
    assert m['value']==pytest.approx(100/1000)
    assert m['included_companies']==2 and m['expected_companies']==3
    assert m['coverage']==pytest.approx(2/3) and m['status']=='PARTIAL'
    assert response['metrics']['net_profit']['value']==100
    assert response['metrics']['pe']['value'] is None
    peers=response['metrics']['net_profit']['peers']
    assert peers[0]['ticker']=='DEF' and peers[0]['rank']==1
    assert peers[0]['percentile']==.75 and peers[0]['contribution']==.9
    assert response['missing_tickers']==['GHI']


def test_aggregation_rejects_unknown_dates_conflicting_sources_and_wrong_issuer_models():
    from src.analytics.industry_financials import industry_snapshot
    values=facts()
    values=[m.model_copy(update={'period_end':None}) if m.ticker=='DEF' else m for m in values]
    response=industry_snapshot(taxonomy(),values,'manufacturing',period='2025',frequency='annual',membership_on=date(2025,12,31))
    assert response['metrics']['net_profit']['included_companies']==1
    values=facts()
    duplicate=next(m for m in values if m.metric_id=='net_profit' and m.period=='2025' and m.ticker=='ABC')
    values.append(duplicate.model_copy(update={'source':'conflicting-provider'}))
    response=industry_snapshot(taxonomy(),values,'manufacturing',period='2025',frequency='annual',membership_on=date(2025,12,31))
    assert response['metrics']['net_profit']['included_companies']==1
    assert response['metrics']['net_profit']['excluded']['ABC']=='conflicting_observations'
    bank=[m.model_copy(update={'profile':'bank','company_type':'NH'}) for m in facts()]
    response=industry_snapshot(taxonomy(),bank,'manufacturing',period='2025',frequency='annual',membership_on=date(2025,12,31))
    assert response['metrics']['net_profit']['value'] is None


def test_taxonomy_memberships_are_versioned_unambiguous_and_effective_dated():
    data=taxonomy().model_dump()
    data['memberships'].append(data['memberships'][0])
    with pytest.raises(ValueError):IndustryTaxonomy.model_validate(data)
    data=taxonomy().model_dump();data['memberships'][1]['industry_id']='unknown'
    with pytest.raises(ValueError):IndustryTaxonomy.model_validate(data)


def test_industry_http_never_fetches_a_provider_or_invents_taxonomy(client,monkeypatch):
    monkeypatch.delenv('WOOFI_FINANCIAL_TAXONOMY',raising=False)
    response=client.get('/financial-intelligence/industries')
    assert response.status_code==200 and response.json()['industries']==[]
    assert response.json()['status']=='UNAVAILABLE'
    assert client.get('/financial-intelligence/industries/manufacturing?period=2025&membership_on=2025-12-31').status_code==404


def test_industry_http_reads_only_explicit_journal_and_validated_taxonomy(client,tmp_path,monkeypatch):
    from src.services.financial_journal import MetricJournal
    path=tmp_path/'taxonomy.json';path.write_text(taxonomy().model_dump_json(),encoding='utf-8')
    journal=tmp_path/'metrics.sqlite';MetricJournal(journal).append(facts())
    monkeypatch.setenv('WOOFI_FINANCIAL_TAXONOMY',str(path));monkeypatch.setenv('WOOFI_FINANCIAL_JOURNAL',str(journal))
    response=client.get('/financial-intelligence/industries/manufacturing?period=2025&frequency=annual&membership_on=2025-12-31')
    assert response.status_code==200 and response.json()['metrics']['net_profit']['value']==100
    assert 'no-store' in response.headers['cache-control']
    assert client.get('/financial-intelligence/industries/manufacturing?period=2025&frequency=quarterly&membership_on=2025-12-31').status_code==422


def test_nonfinite_aggregate_is_unavailable_instead_of_a_crash_or_infinity():
    from src.analytics.industry_financials import industry_snapshot
    values=[m.model_copy(update={'value':1e308}) if m.metric_id=='net_profit' else m for m in facts()]
    response=industry_snapshot(taxonomy(),values,'manufacturing',period='2025',frequency='annual',membership_on=date(2025,12,31))
    assert response['metrics']['net_profit']['value'] is None
    assert response['metrics']['net_profit']['status']=='UNAVAILABLE'
    # Severe positive/negative cancellation must not leak infinite contributions.
    values=facts()
    for item in values:
        if item.metric_id=='net_profit':
            item.value=1e308 if item.ticker=='ABC' else -1e308
    extra=next(m for m in values if m.metric_id=='net_profit' and m.period=='2025')
    values.append(extra.model_copy(update={'ticker':'GHI','value':1e-300}))
    response=industry_snapshot(taxonomy(),values,'manufacturing',period='2025',frequency='annual',membership_on=date(2025,12,31))
    assert response['metrics']['net_profit']['value']==1e-300
    assert response['metrics']['net_profit']['peers'][0]['contribution'] is None
