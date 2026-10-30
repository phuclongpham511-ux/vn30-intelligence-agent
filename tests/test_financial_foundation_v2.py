"""Synthetic edge cases. Saved real evidence is replayed separately, never fetched."""
import copy
import pytest
from src.analytics.financial_engine import financial_engine
from src.providers.vnstock.financial_statements import content_hash, normalize_statement
from src.services.financial_presentation import display_financial_response
from test_financial_engine import fixture, packet


def prepared():
    metadata, reports = fixture()
    for report in reports.values():
        for collection in report.values():
            for row in collection:
                row['consolidation'] = 'consolidated'
    p = packet(metadata, reports).model_copy(update={'is_fixture': False})
    # Only this synthetic test packet supplies reviewed rights; the provider
    # normalizer must never infer them from data, a URL, or SDK installation.
    for receipt in p.reports.values():
        for row in receipt.observations:
            row.source_context.display_rights = 'permitted'
            row.source_context.display_rights_reference = 'synthetic-only://permission-test'
    return p


def metric(result, key):
    return next(m for m in result.fundamental_summary.metrics if m.key == key)


def test_source_context_records_unknowns_without_inventing_fiscal_dates_or_audit_status():
    metadata, reports = fixture()
    raw = reports['income']['years'][-1]
    raw.pop('currency')
    raw.update(isAudited=True, isRestated=True, periodEnd='2025-12-31', updateDate='2026-02-01')
    saved = copy.deepcopy(reports)
    normalized = normalize_statement('ABC', 'test:VCI', 'income', reports['income'], metadata, 'non_financial')
    obs = next(o for o in normalized.observations if o.period == '2025')
    context = obs.source_context
    assert context.fiscal_year == 2025 and context.fiscal_quarter is None
    assert context.period_start is None and context.period_end is None
    assert context.original_currency is None and context.original_unit is None
    assert context.amount_multiplier == 1 and context.unit_evidence == 'audited_vci_adapter_contract'
    assert context.audit_status == context.restatement_status == 'unknown'
    assert context.original_metadata['isRestated'] is True
    assert context.original_metadata['periodEnd'] == '2025-12-31'
    assert not context.publication_time_qualified and context.display_rights == 'unreviewed'
    assert context.record_sha256 == content_hash(raw)
    assert normalized.content_sha256 == content_hash(reports['income'])
    assert reports == saved


def test_new_normalized_financials_never_acquire_display_rights_from_raw_flags():
    p = prepared()
    for obs in p.reports['income'].observations:
        obs.source_context.display_rights = 'unreviewed'
    full = financial_engine(p)
    view = display_financial_response(full)
    assert full.rows[-1]['revenue'] == 120
    assert metric(view, 'revenue').status == 'UNQUALIFIED'
    assert 'rights' in metric(view, 'revenue').reason
    assert view.rows[-1]['revenue'] is None
    assert metric(view, 'total_assets').value == 200, 'unrelated permitted balance data remains usable'
    line = next(x for x in view.statements['income']['periods'][-1]['items'] if x['code'] == 'isa3')
    assert line['value'] is None and line['raw_value'] == 120
    assert full.rows[-1]['calculations']['revenue']['inputs'][0]['source_context']['display_rights'] == 'unreviewed'


@pytest.mark.parametrize('rights', [None, 'unreviewed', 'prohibited'])
def test_absent_or_unreviewed_rights_never_bypass_live_display_guards(rights):
    p = prepared()
    for obs in p.reports['income'].observations:
        if rights is None:
            obs.source_context = None
        else:
            obs.source_context.display_rights = rights
    view = display_financial_response(financial_engine(p))
    assert metric(view, 'revenue').value is None
    assert metric(view, 'revenue').status == 'UNQUALIFIED'
    assert metric(view, 'total_assets').value == 200


def test_provider_payload_cannot_self_assert_redistribution_permission():
    metadata, reports = fixture()
    raw = reports['income']['years'][-1]
    raw.update(display_rights='permitted', source_context={'display_rights': 'permitted'})
    receipt = normalize_statement('ABC', 'test:VCI', 'income', reports['income'], metadata, 'non_financial')
    assert all(o.source_context.display_rights == 'unreviewed' for o in receipt.observations)


def test_permission_flag_without_reviewed_evidence_reference_is_not_a_rights_grant():
    p = prepared()
    for obs in p.reports['income'].observations:
        obs.source_context.display_rights_reference = None
    view = display_financial_response(financial_engine(p))
    assert metric(view, 'revenue').value is None
    assert metric(view, 'revenue').status == 'UNQUALIFIED'


@pytest.mark.parametrize('unrelated_basis', [None, 'standalone'])
def test_field_scoped_basis_does_not_block_income_or_balance_but_rejects_cross_basis_ratios(unrelated_basis):
    p = prepared()
    for obs in p.reports['cash'].observations:
        obs.consolidation = unrelated_basis
    view = display_financial_response(financial_engine(p))
    assert view.fundamental_summary.consolidation is None
    assert metric(view, 'revenue').value == 120
    assert metric(view, 'revenue').consolidation == 'consolidated'
    assert metric(view, 'gross_margin').value == .25
    assert metric(view, 'roe').value == pytest.approx(12 / 90)
    assert view.rows[-1]['cash_conversion'] is None
    assert view.rows[-1]['net_profit_growth_yoy'] == pytest.approx(.2)


def test_each_metric_retains_its_own_basis_and_mixed_ratio_is_never_certified():
    p = prepared()
    for obs in p.reports['balance'].observations:
        obs.consolidation = 'standalone'
    view = display_financial_response(financial_engine(p))
    assert metric(view, 'revenue').consolidation == 'consolidated'
    assert metric(view, 'total_assets').consolidation == 'standalone'
    assert metric(view, 'total_assets').value == 200
    assert metric(view, 'roe').value is None and metric(view, 'roe').status == 'UNQUALIFIED'
    assert metric(view, 'net_margin').value == .1


def test_ytd_and_ttm_keep_every_original_receipt_and_do_not_add_eps():
    p = prepared()
    for kind in ('income', 'cash'):
        for obs in p.reports[kind].observations:
            if obs.frequency == 'quarterly':
                obs.basis = 'ytd'
                for key, value in obs.fields.items():
                    if value is not None:
                        obs.fields[key] = value * int(obs.period[-1])
    result = financial_engine(p, frequency='ttm')
    row = result.rows[-1]
    assert row['revenue'] == 120 and row['eps_reported'] is None
    refs = row['calculations']['revenue']['inputs']
    assert all(ref['source_context']['record_sha256'] for ref in refs)
    assert len({ref['period'] for ref in refs}) == 4
    assert result.source_receipts[0]['periods'][0]['source_context']['fiscal_year'] == 2023
    p.reports['income'].observations = [o for o in p.reports['income'].observations if o.period != '2025-Q2']
    assert financial_engine(p, frequency='ttm').rows[-1]['revenue'] is None


def test_revised_record_has_distinct_hash_without_claiming_restatement_or_filing_time():
    metadata, reports = fixture()
    first = normalize_statement('ABC', 'test:VCI', 'income', reports['income'], metadata, 'non_financial')
    reports['income']['years'][0]['isa3'] = 101
    reports['income']['years'][0]['updateDate'] = '2026-10-19T17:00:00'
    second = normalize_statement('ABC', 'test:VCI', 'income', reports['income'], metadata, 'non_financial')
    assert first.observations[0].source_context.record_sha256 != second.observations[0].source_context.record_sha256
    assert second.observations[0].source_context.restatement_status == 'unknown'
    assert not second.observations[0].source_context.publication_time_qualified


def test_bank_qualified_inputs_do_not_enable_industrial_ratios_or_unqualified_bank_metrics():
    metadata, reports = fixture('NH')
    p = packet(metadata, reports, 'NH')
    result = display_financial_response(financial_engine(p))
    assert result.profile == 'bank'
    for field in ('revenue', 'gross_margin', 'net_margin', 'debt_equity', 'free_cash_flow'):
        assert result.rows[-1][field] is None
    assert metric(result, 'operating_income').status == 'DEMO'
    assert all(m.key not in ('nim', 'npl', 'casa') for m in result.fundamental_summary.metrics)


@pytest.mark.parametrize('value', ['million VND', 'USD', 1000])
def test_unqualified_unit_changes_are_rejected_not_silently_scaled(value):
    metadata, reports = fixture()
    reports['income']['years'][0]['unit'] = value
    with pytest.raises(ValueError, match='unit'):
        normalize_statement('ABC', 'test:VCI', 'income', reports['income'], metadata, 'non_financial')
