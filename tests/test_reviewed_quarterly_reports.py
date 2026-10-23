"""Quarter boundaries and evidence gates on the existing reviewed-report seam."""
import hashlib

import pytest

from src.providers.reviewed_reports import report_packet
from src.providers.vnstock.financial_statements import content_hash
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response
from src.services.financial_journal import MetricJournal
from src.services.personal_financials import personal_projection
from test_free_financial_sources import reviewed


def quarterly_report(tmp_path, *, quarter=1, basis='standalone'):
    evidence = reviewed(tmp_path)
    rows = [a for a in evidence['amounts'] if a['year'] == 2025]
    ends = {1: '2025-03-31', 2: '2025-06-30'}
    start = '2025-01-01' if basis == 'ytd' or quarter == 1 else '2025-04-01'
    title = f'Period from {start} to {ends[quarter]}'
    for a in rows:
        a.update(quarter=quarter, period_quote=dict(page=1, text=title),
            flow_basis=None if a['field'] in ('total_assets', 'total_liabilities', 'equity') else basis,
            period_start=None if a['field'] in ('total_assets', 'total_liabilities', 'equity') else start,
            period_end=ends[quarter], column_periods=[f'2025-Q{quarter}', f'2024-Q{quarter}'])
    evidence['amounts'] = rows
    evidence['pages'][0]['text'] += '\n' + title
    evidence['pages'][0]['text_sha256'] = hashlib.sha256(evidence['pages'][0]['text'].encode()).hexdigest()
    return evidence


@pytest.mark.parametrize('quarter,basis', [(1, 'standalone'), (2, 'standalone'), (2, 'ytd')])
def test_quarter_report_preserves_flow_basis_and_balance_date(tmp_path, quarter, basis):
    evidence = quarterly_report(tmp_path, quarter=quarter, basis=basis)
    packet, audit = report_packet(evidence, tmp_path)
    income = packet.reports['income'].observations[0]
    balance = packet.reports['balance'].observations[0]
    assert income.period == f'2025-Q{quarter}' and income.frequency == 'quarterly'
    assert income.basis == basis
    assert income.source_context.fiscal_quarter == quarter
    assert income.source_context.period_end == evidence['amounts'][0]['period_end']
    assert balance.basis == 'point_in_time' and balance.source_context.period_start is None
    assert audit['selected_reported_fields'] == 10
    journal = MetricJournal(tmp_path / 'journal.sqlite')
    journal.initialize()
    imported = journal.import_packet(packet, evidence['document_sha256'])
    assert journal.read_packet(imported['capture_id']) == packet
    assert journal.import_packet(packet, evidence['document_sha256'])['inserted_observations'] == 0
    view = personal_projection(packet, frequency='quarterly', authorization_reference='synthetic-quarter-review')
    assert view['rows'][0]['period'] == f'2025-Q{quarter}'
    assert view['statements']['income']['periods'][0]['basis'] == basis
    assert view['rows'][0]['net_margin'] == (.1 if basis == 'standalone' else None)
    assert view['rows'][0]['free_cash_flow'] is None
    public = display_financial_response(financial_engine(packet, frequency='quarterly'))
    assert all(metric.value is None for metric in public.fundamental_summary.metrics)


@pytest.mark.parametrize('bad', ['missing_quote', 'wrong_end', 'wrong_start', 'missing_basis', 'wrong_quote', 'annual_mislabel'])
def test_quarter_report_rejects_unsubstantiated_periods(tmp_path, bad):
    evidence = quarterly_report(tmp_path)
    a = evidence['amounts'][0]
    if bad == 'missing_quote': a.pop('period_quote')
    elif bad == 'wrong_end': a['period_end'] = '2025-06-30'
    elif bad == 'wrong_start': a['period_start'] = '2025-02-01'
    elif bad == 'missing_basis': a.pop('flow_basis')
    elif bad == 'wrong_quote': a['period_quote']['text'] = '2025 VND 2024 VND'
    else: a.pop('quarter')
    with pytest.raises(ValueError):
        report_packet(evidence, tmp_path)


def test_quarter_one_title_is_explicit_period_evidence_with_calendar_year(tmp_path):
    evidence = quarterly_report(tmp_path)
    title = 'Separate statement of income for the first quarter ended 31 March 2025'
    evidence['pages'][0]['text'] += '\n' + title
    evidence['pages'][0]['text_sha256'] = hashlib.sha256(evidence['pages'][0]['text'].encode()).hexdigest()
    for a in evidence['amounts']:
        a['period_quote'] = dict(page=1, text=title)
    packet, _ = report_packet(evidence, tmp_path)
    assert packet.reports['income'].observations[0].source_context.period_start == '2025-01-01'


def test_annual_report_retains_existing_immutable_packet_identity(tmp_path):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    # Captured with the annual-only adapter at 8ffb36f. New optional quarter
    # fields must not create revisions of already imported annual evidence.
    assert content_hash(packet.model_dump(mode='json')) == '4e7b8d5b35f2771e2beea68e167ba3dda6ac3923c0816f1bc4446a9efe48da7a'


def test_mixed_flow_bases_in_one_statement_are_rejected(tmp_path):
    evidence = quarterly_report(tmp_path)
    evidence['amounts'][1]['flow_basis'] = 'ytd'
    with pytest.raises(ValueError, match='Conflicting statement period bases'):
        report_packet(evidence, tmp_path)


def comparative_report(tmp_path):
    evidence = quarterly_report(tmp_path)
    title = 'Separate statement of income for the first quarter ended 31 March 2025'
    header = title + '\nQuarter I This year Previous year'
    evidence['pages'][0]['text'] += '\n' + header
    evidence['pages'][0]['text_sha256'] = hashlib.sha256(evidence['pages'][0]['text'].encode()).hexdigest()
    evidence['amounts'] = [a for a in evidence['amounts'] if a['field']=='revenue']
    a = evidence['amounts'][0]
    a.update(year=2024, raw_token=a['column_values'][1], period_start='2024-01-01',
        period_end='2024-03-31', relative_year='previous_year',
        column_header=dict(page=1,text=header),period_quote=dict(page=1,text=title))
    return evidence


def test_explicit_previous_year_first_quarter_column(tmp_path):
    packet,_ = report_packet(comparative_report(tmp_path), tmp_path)
    obs = packet.reports['income'].observations[0]
    assert obs.period=='2024-Q1' and obs.source_context.period_start=='2024-01-01'
    assert obs.source_context.period_end=='2024-03-31'


def test_comparative_column_enables_saved_private_insight_only(tmp_path):
    import copy
    from src.services.personal_financials import saved_financial_insights
    evidence=comparative_report(tmp_path)
    current=copy.deepcopy(evidence['amounts'][0])
    current.pop('relative_year')
    current.update(year=2025,period_start='2025-01-01',period_end='2025-03-31',
        raw_token=current['column_values'][0])
    evidence['amounts'].append(current)
    packet,_=report_packet(evidence,tmp_path)
    journal=MetricJournal(tmp_path/'journal.sqlite')
    journal.initialize()
    capture=journal.import_packet(packet,content_hash(packet.model_dump(mode='json')))
    out=saved_financial_insights(journal.path,capture['capture_id'],metrics=['revenue'],
        frequency='quarterly',comparison='yoy',authorization_reference='synthetic-review')
    assert out.insights[0].qualification_status=='COMPARABLE'
    assert all(r['capture_id']==capture['capture_id'] for r in out.insights[0].evidence_references)
    public=display_financial_response(financial_engine(packet,frequency='quarterly'))
    assert all(m.value is None for m in public.fundamental_summary.metrics)
    assert journal.import_packet(packet,content_hash(packet.model_dump(mode='json')))['inserted_captures']==0


@pytest.mark.parametrize('bad',['relation','header','columns','basis','quarter'])
def test_previous_year_requires_unambiguous_same_quarter_column(tmp_path,bad):
    e=comparative_report(tmp_path)
    a=e['amounts'][0]
    if bad=='relation': a.pop('relative_year')
    elif bad=='header': a['column_header']['text']=a['period_quote']['text']
    elif bad=='columns': a['column_periods'].reverse()
    elif bad=='basis': a['flow_basis']='ytd'
    else: a['quarter']=2
    with pytest.raises(ValueError): report_packet(e,tmp_path)
