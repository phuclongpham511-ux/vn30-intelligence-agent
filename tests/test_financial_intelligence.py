"""Synthetic public seams: no live providers, credentials or production database."""
from datetime import datetime, timezone
import pytest
from src.analytics.financial_engine import financial_engine
from test_financial_foundation_v2 import prepared


def balanced(ticker='ABC'):
    p = prepared()
    p.ticker = ticker
    for receipt in p.reports.values():
        for obs in receipt.observations:
            obs.ticker = ticker
            if obs.statement == 'balance':
                obs.fields['total_assets'] = obs.fields['total_liabilities'] + obs.fields['equity']
    return p


def test_new_working_capital_and_bank_metrics_use_appropriate_models():
    result = financial_engine(balanced())
    row = result.rows[-1]
    assert row['net_working_capital'] == 40
    assert row['average_equity'] == 90
    assert row['asset_turnover'] == pytest.approx(120 / 210)
    assert row['loan_deposit_ratio'] is None
    p = balanced()
    p.profile = 'bank'
    for obs in p.reports['balance'].observations:
        obs.fields.update(customer_loans=90, customer_deposits=100)
        obs.field_codes.update(customer_loans='bsb104', customer_deposits='bsb113')
    bank = financial_engine(p).rows[-1]
    assert bank['loan_deposit_ratio'] == .9
    assert bank['customer_loans_growth_yoy'] == 0
    assert bank['asset_turnover'] is None


def test_normalized_observations_preserve_actual_fetch_vintage_and_unknown_publication():
    from src.services.financial_intelligence import normalized_metrics
    p = balanced()
    original = p.model_dump()
    values = normalized_metrics(p)
    revenue = next(m for m in values if m.metric_id == 'revenue' and m.fiscal_year == 2025)
    assert revenue.value == 120 and revenue.metric_kind == 'reported'
    assert revenue.quality_status == 'QUALIFIED'
    assert revenue.report_scope == 'consolidated'
    assert revenue.published_at is None and revenue.period_start is None
    assert revenue.fetched_at == p.reports['income'].observed_at
    assert revenue.revision and revenue.formula_version and revenue.input_refs
    assert p.model_dump() == original


def test_unknown_scope_and_unbalanced_inputs_cannot_enter_industry_metrics():
    from src.services.financial_intelligence import normalized_metrics
    p = balanced()
    for receipt in p.reports.values():
        for obs in receipt.observations:
            obs.consolidation = None
    blocked = normalized_metrics(p)
    assert all(m.value is None for m in blocked)
    assert next(m for m in blocked if m.metric_id=='revenue' and m.fiscal_year==2025).metric_kind=='reported'
    assert next(m for m in blocked if m.metric_id=='current_ratio' and m.fiscal_year==2025).metric_kind=='derived'
    p = balanced()
    previous_roe = next(m for m in normalized_metrics(p) if m.metric_id=='roe' and m.fiscal_year==2025)
    next(o for o in p.reports['balance'].observations if o.period == '2025').fields['total_assets'] = 1
    rows = {m.metric_id:m for m in normalized_metrics(p) if m.fiscal_year == 2025}
    assert rows['roe'].value is None and rows['roe'].quality_status == 'INVALID'
    assert 'balance_identity_failed' in rows['roe'].quality_reasons
    assert rows['roe'].metric_kind=='derived'
    assert rows['roe'].input_refs==previous_roe.input_refs
    assert rows['roe'].revision!=previous_roe.revision
    assert rows['revenue'].value == 120


def test_revision_journal_is_idempotent_and_asof_never_uses_future_or_unknown_dates(tmp_path):
    from src.services.financial_intelligence import normalized_metrics
    from src.services.financial_journal import MetricJournal
    item = next(m for m in normalized_metrics(balanced()) if m.metric_id == 'revenue')
    item = item.model_copy(update={'published_at':datetime(2024,3,1,tzinfo=timezone.utc),
        'fetched_at':datetime(2024,3,2,tzinfo=timezone.utc)})
    journal = MetricJournal(tmp_path/'research.sqlite')
    assert journal.append([item, item]) == 1
    revised = item.model_copy(update={'value':101, 'revision':'b'*64,
        'published_at':datetime(2024,4,1,tzinfo=timezone.utc),
        'fetched_at':datetime(2024,4,2,tzinfo=timezone.utc)})
    assert journal.append([revised]) == 1
    assert journal.read(as_of=datetime(2024,3,3,tzinfo=timezone.utc))[0].value == 100
    assert journal.read()[0].value == 101
    assert journal.read(as_of=datetime(2024,3,1,tzinfo=timezone.utc)) == []
    with pytest.raises(ValueError):
        journal.read(as_of=datetime(2024,3,3))
    with pytest.raises(ValueError):
        journal.append([item.model_copy(update={'value':999})])


def test_metric_api_reuses_provider_packet_and_keeps_public_guards(client,session):
    from main import app
    from src.models import Stock
    from src.services import data
    class Provider:
        source = 'test:VCI'
        calls = 0
        def get_reports(self,ticker):
            self.calls += 1
            return balanced(ticker)
    provider=Provider()
    session.add(Stock(symbol='ABC'));session.commit()
    app.dependency_overrides[data.get_fundamental_provider]=lambda:provider
    response=client.get('/stocks/ABC/financials/metrics?frequency=annual&limit=1')
    assert response.status_code == 200
    body=response.json()
    assert body['contract'] == 'financial-metrics-v1' and body['ticker'] == 'ABC'
    assert len({m['period'] for m in body['observations']}) == 1
    assert provider.calls == 1
    assert client.get('/stocks/ABC/financials/metrics?limit=100').status_code == 422


def test_new_turnover_requires_compatible_positive_opening_balances():
    p=balanced()
    row=financial_engine(p).rows[-1]
    assert row['inventory_turnover']==pytest.approx((120-30)/20)
    prior=next(o for o in p.reports['balance'].observations if o.period=='2024')
    prior.fields['inventory']=0
    assert financial_engine(p).rows[-1]['inventory_turnover'] is None
    prior.fields['inventory']=20;prior.consolidation='standalone'
    row=financial_engine(p).rows[-1]
    assert row['asset_turnover'] is None and row['average_equity'] is None


def test_metric_contract_rejects_numeric_coercion_and_separates_estimates():
    from src.schemas.financial_intelligence import MetricObservation
    from src.services.financial_intelligence import normalized_metrics
    data=normalized_metrics(balanced())[0].model_dump()
    for value in (True,'100',float('inf')):
        with pytest.raises(ValueError):MetricObservation.model_validate({**data,'value':value})
    with pytest.raises(ValueError):MetricObservation.model_validate({**data,'metric_kind':'estimated'})
    estimate=MetricObservation.model_validate({**data,'metric_kind':'estimated','quality_status':'ESTIMATED'})
    assert estimate.quality_status=='ESTIMATED'


def test_journal_filters_periods_rejects_application_db_and_never_dates_unknowns(tmp_path):
    import sqlite3
    from src.services.financial_intelligence import normalized_metrics
    from src.services.financial_journal import MetricJournal
    journal=MetricJournal(tmp_path/'journal.sqlite')
    facts=normalized_metrics(balanced())
    journal.append(facts)
    selected=journal.read(period='2025',frequency='annual')
    assert selected and all(f.period=='2025' for f in selected)
    assert journal.read(as_of=datetime(2100,1,1,tzinfo=timezone.utc))==[]
    with journal.connect() as db:
        plan=db.execute("EXPLAIN QUERY PLAN SELECT payload FROM financial_metric WHERE json_extract(payload,'$.period')=? AND json_extract(payload,'$.period_type')=?",('2025','annual')).fetchall()
    assert any('financial_metric_period' in str(r) for r in plan)
    application=tmp_path/'application.sqlite'
    with sqlite3.connect(application) as db:db.execute('CREATE TABLE stock (ticker TEXT)')
    with pytest.raises(ValueError):MetricJournal(application).append(facts)


def test_offline_ingestion_is_dynamic_idempotent_and_records_actual_denominators(tmp_path,monkeypatch):
    import json
    from scripts import ingest_financial_intelligence as command
    captures=tmp_path/'captures';captures.mkdir()
    (captures/'index.json').write_text(json.dumps({'contract':'personal-saved-captures-v1','captures':{'DEF':{}}}))
    monkeypatch.setattr(command,'saved_packet',lambda root,ticker:(balanced(ticker),'a'*64))
    first=command.ingest(captures,tmp_path/'journal.sqlite',tmp_path/'report')
    second=command.ingest(captures,tmp_path/'journal.sqlite',tmp_path/'report')
    assert first['inserted_revisions']>0 and second['inserted_revisions']==0
    assert first['tickers']==['DEF'] and first['provider_requests']==0
    assert (tmp_path/'report/DATA_COVERAGE_MATRIX.csv').read_text().count('DEF')>0
