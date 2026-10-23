"""Private financial-insight seams; synthetic evidence only, no source calls."""
import hashlib
import copy
import pytest

from src.providers.reviewed_reports import report_packet
from src.services.financial_insights import financial_insights
from test_free_financial_sources import reviewed


def test_annual_change_preserves_evidence_and_attention_criteria(tmp_path):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    out = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic-review')
    insight = out.insights[0]
    assert insight.current_period == '2025' and insight.comparison_period == '2024'
    assert insight.current_value == 1000 and insight.comparison_value == 800
    assert insight.absolute_change == 200 and insight.percentage_change == .25
    assert insight.qualification_status == 'COMPARABLE'
    assert insight.observed_change == 'INCREASE'
    assert insight.attention_reason.criteria == ['RELATIVE_MOVEMENT']
    assert {r['role'] for r in insight.evidence_references} == {'current', 'comparison'}
    current = next(r for r in insight.evidence_references if r['role'] == 'current')
    assert current['original_value'] == '1.000' and current['page'] == 1
    assert current['source_url'] == 'https://example.test/original.pdf'
    assert 'public_display_permission' in insight.missing_information
    assert insight.causal_explanation is None and out.public_display_activated is False


def quarter_packet(tmp_path, comparison='yoy'):
    evidence = reviewed(tmp_path)
    for a in evidence['amounts']:
        is_current = a['year'] == 2025
        quarter = 1 if comparison == 'yoy' or not is_current else 2
        if comparison == 'qoq':
            a['year'] = 2025
        start = f"{a['year']}-{'01' if quarter == 1 else '04'}-01"
        end = f"{a['year']}-{'03-31' if quarter == 1 else '06-30'}"
        title = f'Period from {start} to {end}'
        balance = a['field'] in ('total_assets', 'total_liabilities', 'equity')
        a.update(quarter=quarter, flow_basis=None if balance else 'standalone',
            period_start=None if balance else start, period_end=end,
            period_quote=dict(page=1, text=title),
            column_periods=['2025-Q1', '2024-Q1'] if comparison == 'yoy' else ['2025-Q2', '2025-Q1'])
        evidence['pages'][0]['text'] += '\n' + title
    page = evidence['pages'][0]
    page['text_sha256'] = hashlib.sha256(page['text'].encode()).hexdigest()
    return report_packet(evidence, tmp_path)[0]


@pytest.mark.parametrize('comparison,period,prior', [('yoy','2025-Q1','2024-Q1'), ('qoq','2025-Q2','2025-Q1')])
def test_quarterly_comparisons_use_exact_period_and_standalone_basis(tmp_path, comparison, period, prior):
    packet = quarter_packet(tmp_path, comparison)
    out = financial_insights(packet, metrics=['revenue'], frequency='quarterly', comparison=comparison,
        authorization_reference='synthetic')
    insight = out.insights[0]
    assert (insight.current_period, insight.comparison_period) == (period, prior)
    assert insight.absolute_change == 200 and insight.percentage_change == .25


@pytest.mark.parametrize('bad,reason', [
    ('scope','incompatible_source_scope_or_document_revision'),
    ('unknown_scope','unverified_reporting_scope'),
    ('definition','incompatible_financial_definition_or_basis'),
    ('basis','incompatible_period_basis'),
    ('boundaries','unverified_fiscal_boundaries'),
    ('unit','unverified_currency_or_units'),
    ('revision','incompatible_source_scope_or_document_revision'),
])
def test_incompatible_pairs_never_get_a_change(tmp_path, bad, reason):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    prior = packet.reports['income'].observations[0]
    assert prior.period == '2024'
    if bad == 'scope': prior.consolidation = 'standalone'
    elif bad == 'unknown_scope':
        for obs in packet.reports['income'].observations: obs.consolidation = None
    elif bad == 'definition': prior.field_codes['revenue'] = 'different-definition'
    elif bad == 'basis': prior.basis = 'ytd'
    elif bad == 'boundaries': prior.source_context.period_start = None
    elif bad == 'unit': prior.source_context.original_unit = 'shares'
    else: prior.source_context.original_metadata['binary_sha256'] = 'f' * 64
    insight = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic').insights[0]
    assert insight.qualification_status == 'INSUFFICIENT_COMPARABLE_DATA'
    assert insight.absolute_change is None and insight.percentage_change is None
    assert reason in insight.missing_information
    assert not insight.attention_reason.noteworthy


def test_matching_but_wrong_line_units_do_not_establish_comparability(tmp_path):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    for observation in packet.reports['income'].observations:
        next(line for line in observation.items if line.code == 'row:revenue').unit = 'shares'
    insight = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic').insights[0]
    assert insight.qualification_status == 'INSUFFICIENT_COMPARABLE_DATA'
    assert 'source_line_mapping_unverified' in insight.missing_information


def replace_amount(evidence, field, tokens):
    rows = [a for a in evidence['amounts'] if a['field'] == field]
    old_row = rows[0]['source_row']['text']
    new_row = field + ' ' + ' '.join(tokens)
    for a in rows:
        a.update(raw_token=tokens[0 if a['year'] == 2025 else 1], column_values=tokens,
            source_row=dict(page=1, text=new_row))
    page = evidence['pages'][0]
    page['text'] = page['text'].replace(old_row, new_row)
    page['text_sha256'] = hashlib.sha256(page['text'].encode()).hexdigest()


@pytest.mark.parametrize('tokens,delta,criterion', [
    (['50','0'], 50, 'ZERO_BASE_MOVEMENT'),
    (['50','(100)'], 150, 'SIGN_REVERSAL'),
    (['(50)','(100)'], 50, None),
])
def test_nonpositive_bases_keep_absolute_change_without_percentage(tmp_path, tokens, delta, criterion):
    evidence = reviewed(tmp_path)
    replace_amount(evidence, 'net_profit', tokens)
    packet, _ = report_packet(evidence, tmp_path)
    insight = financial_insights(packet, metrics=['net_profit'], authorization_reference='synthetic').insights[0]
    assert insight.qualification_status == 'COMPARABLE' and insight.absolute_change == delta
    assert insight.percentage_change is None
    assert 'percentage_change_requires_positive_comparison_value' in insight.missing_information
    assert insight.attention_reason.criteria == ([criterion] if criterion else [])


def test_single_quarter_preserves_facts_without_inventing_prior_or_trend(tmp_path):
    packet = quarter_packet(tmp_path)
    for receipt in packet.reports.values():
        receipt.observations = [o for o in receipt.observations if o.period == '2025-Q1']
    insight = financial_insights(packet, metrics=['revenue'], frequency='quarterly',
        authorization_reference='synthetic').insights[0]
    assert insight.current_value == 1000 and insight.comparison_value is None
    assert insight.absolute_change is None and insight.observed_change == 'OBSERVATION_ONLY'
    assert 'missing_exact_comparison_period' in insight.missing_information
    assert insight.attention_reason.historical_status == 'INSUFFICIENT_COMPARABLE_DATA'
    assert len(insight.evidence_references) == 1


def test_ytd_flows_are_not_treated_as_standalone_comparisons(tmp_path):
    packet = quarter_packet(tmp_path)
    for obs in packet.reports['income'].observations: obs.basis = 'ytd'
    insight = financial_insights(packet, metrics=['revenue'], frequency='quarterly',
        authorization_reference='synthetic').insights[0]
    assert insight.qualification_status == 'INSUFFICIENT_COMPARABLE_DATA'
    assert insight.absolute_change is None and 'incompatible_period_basis' in insight.missing_information


def test_saved_insights_read_explicit_revision_without_changing_selection(tmp_path):
    from src.services.financial_journal import MetricJournal
    from src.services.personal_financials import saved_financial_insights
    evidence = reviewed(tmp_path)
    evidence['review_reference'] = 'synthetic: Doanh thu thuần'
    first, _ = report_packet(evidence, tmp_path)
    journal = MetricJournal(tmp_path / 'journal.sqlite')
    journal.initialize()
    old = journal.import_packet(first, evidence['document_sha256'])
    replace_amount(evidence, 'revenue', ['1.200','800'])
    (tmp_path / 'source.pdf').write_bytes(b'%PDF-synthetic-revised')
    evidence['document_sha256'] = hashlib.sha256(b'%PDF-synthetic-revised').hexdigest()
    revised, _ = report_packet(evidence, tmp_path)
    new = journal.import_packet(revised, evidence['document_sha256'])
    selection = journal.selected_statements('ABC', first.source)
    original = saved_financial_insights(journal.path, old['capture_id'], metrics=['revenue'], authorization_reference='synthetic')
    latest = saved_financial_insights(journal.path, new['capture_id'], metrics=['revenue'], authorization_reference='synthetic')
    assert original.insights[0].current_value == 1000 and latest.insights[0].current_value == 1200
    assert original.packet_sha256 != latest.packet_sha256
    assert original.packet_sha256 == financial_insights(first, metrics=['revenue'],
        authorization_reference='synthetic').packet_sha256
    assert original.capture_id == old['capture_id'] and latest.capture_id == new['capture_id']
    assert {r['capture_id'] for r in latest.insights[0].evidence_references} == {new['capture_id']}
    assert journal.selected_statements('ABC', first.source) == selection
    assert saved_financial_insights(journal.path, old['capture_id'], metrics=['revenue'], authorization_reference='synthetic') == original


def revenue_history(tmp_path, values):
    evidence = reviewed(tmp_path)
    template = next(a for a in evidence['amounts'] if a['field'] == 'revenue')
    periods = [str(2018 + i) for i in range(len(values))]
    tokens = [str(v) for v in values]
    header = ' VND '.join(periods) + ' VND'
    row = 'revenue ' + ' '.join(tokens)
    evidence['amounts'] = [dict(copy.deepcopy(template), year=int(period), raw_token=token,
        column_periods=periods, column_values=tokens, period_start=period+'-01-01',
        period_end=period+'-12-31', source_row=dict(page=1, text=row), column_header=dict(page=1, text=header))
        for period, token in zip(periods, tokens)]
    page = evidence['pages'][0]
    page['text'] += '\n' + header + '\n' + row
    page['text_sha256'] = hashlib.sha256(page['text'].encode()).hexdigest()
    return report_packet(evidence, tmp_path)[0]


def test_unusual_movement_has_a_compatible_prior_baseline_and_inspectable_evidence(tmp_path):
    packet = revenue_history(tmp_path, [100,110,120,130,140,150,200])
    insight = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic').insights[0]
    attention = insight.attention_reason
    assert attention.historical_status == 'ASSESSED'
    assert attention.historical_median_absolute_change == 10
    assert len(attention.historical_comparisons) == 5
    assert 'UNUSUAL_HISTORICAL_MOVEMENT' in attention.criteria
    references = {r['reference_id'] for r in insight.evidence_references}
    assert all(set(p['evidence_reference_ids']) <= references for p in attention.historical_comparisons)
    early = financial_insights(packet, metrics=['revenue'], current_period='2022', authorization_reference='synthetic').insights[0]
    assert early.attention_reason.historical_status == 'INSUFFICIENT_COMPARABLE_DATA'
    assert all(p['current_period'] < '2022' for p in early.attention_reason.historical_comparisons)


def test_ordinary_movement_is_not_flagged_as_historically_unusual(tmp_path):
    packet = revenue_history(tmp_path, [100,110,120,130,140,150,155])
    insight = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic').insights[0]
    assert insight.attention_reason.historical_status == 'ASSESSED'
    assert not insight.attention_reason.noteworthy


def test_composition_change_uses_existing_ratio_and_inclusive_fraction_threshold(tmp_path):
    evidence = reviewed(tmp_path)
    replace_amount(evidence, 'total_liabilities', ['700','450'])
    replace_amount(evidence, 'equity', ['1.300','1.050'])
    packet, _ = report_packet(evidence, tmp_path)
    insight = financial_insights(packet, metrics=['liabilities_assets'], authorization_reference='synthetic').insights[0]
    assert insight.current_value == .35 and insight.comparison_value == .3
    assert insight.absolute_change == pytest.approx(.05)
    assert insight.attention_reason.criteria == ['FRACTION_MOVEMENT']
    assert {r['field'] for r in insight.evidence_references} == {'total_liabilities', 'total_assets'}


def test_bank_specialist_changes_reuse_engine_definitions(tmp_path):
    evidence = reviewed(tmp_path)
    evidence.update(company_type='NH', profile='bank')
    evidence['amounts'] = [a for a in evidence['amounts'] if a['field'] not in ('revenue','gross_profit')]
    template = next(a for a in evidence['amounts'] if a['field']=='total_assets')
    for field, tokens in [('customer_loans',['1.500','1.000']), ('customer_deposits',['800','700'])]:
        row = field + ' ' + ' '.join(tokens)
        for year, token in zip((2025,2024), tokens):
            evidence['amounts'].append(dict(copy.deepcopy(template), field=field, code='row:'+field,
                label=field, year=year, raw_token=token, column_values=tokens,
                period_end=f'{year}-12-31', source_row=dict(page=1,text=row)))
        evidence['pages'][0]['text'] += '\n' + row
    page = evidence['pages'][0]
    page['text_sha256'] = hashlib.sha256(page['text'].encode()).hexdigest()
    packet, _ = report_packet(evidence, tmp_path)
    out = financial_insights(packet, metrics=['customer_loans','loan_deposit_ratio'], authorization_reference='synthetic')
    assert out.insights[0].absolute_change == 500 and out.insights[0].percentage_change == .5
    assert out.insights[1].current_value == 1.875
    assert 'not regulatory' in out.insights[1].metric_formula


def test_numeric_changes_do_not_create_causal_claims_or_recommendations(tmp_path):
    from pydantic import ValidationError
    from src.schemas.financial_intelligence import FinancialInsight
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    insight = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic').insights[0]
    with pytest.raises(ValidationError):
        FinancialInsight.model_validate(dict(insight.model_dump(), causal_explanation='Because demand increased'))
    with pytest.raises(ValidationError):
        FinancialInsight.model_validate(dict(insight.model_dump(), recommendation='BUY'))


def test_read_is_repeatable_and_does_not_mutate_packet_or_engine(tmp_path):
    from src.analytics.financial_engine import financial_engine
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    before, engine_rows = packet.model_dump_json(), financial_engine(packet).rows
    options = dict(metrics=['revenue','net_profit'], authorization_reference='synthetic')
    assert financial_insights(packet, **options) == financial_insights(packet, **options)
    assert packet.model_dump_json() == before
    assert financial_engine(packet).rows == engine_rows


def test_gaps_do_not_fall_back_to_nearest_observation(tmp_path):
    packet = revenue_history(tmp_path, [100,110,120])
    packet.reports['income'].observations = [o for o in packet.reports['income'].observations if o.period!='2019']
    insight = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic').insights[0]
    assert insight.comparison_period == '2019' and insight.comparison_value is None
    assert insight.absolute_change is None and 'missing_exact_comparison_period' in insight.missing_information


def test_unrelated_loan_note_failure_does_not_disqualify_total_assets(tmp_path):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    for obs in packet.reports['balance'].observations:
        obs.source_context.original_metadata['loan_quality_identity'] = 'FAIL'
    insight = financial_insights(packet, metrics=['total_assets'], authorization_reference='synthetic').insights[0]
    assert insight.qualification_status == 'COMPARABLE' and insight.absolute_change == 500


def test_prohibited_values_are_not_leaked_through_evidence(tmp_path):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    for obs in packet.reports['income'].observations: obs.source_context.display_rights = 'prohibited'
    insight = financial_insights(packet, metrics=['revenue'], authorization_reference='synthetic').insights[0]
    assert insight.current_value is None and insight.comparison_value is None
    assert all(r['value'] is None and r['original_value'] is None and r['source_row'] is None
        for r in insight.evidence_references)


@pytest.mark.parametrize('options', [dict(authorization_reference=''),dict(frequency='ttm'),dict(comparison='qoq'),
    dict(metrics=['nim']), dict(current_period='2025-Q1')])
def test_invalid_or_unauthorized_requests_fail_without_expanding_scope(tmp_path, options):
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    with pytest.raises(ValueError):
        financial_insights(packet, **dict(dict(authorization_reference='synthetic'), **options))
