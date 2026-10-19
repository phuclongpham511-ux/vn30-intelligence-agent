"""Synthetic financial panel contracts; no acquisition or production database."""
import copy
import pytest
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response
from test_financial_foundation_v2 import prepared
from test_financial_engine import packet


def panels(p=None, frequency='annual'):
    return {x['key']: x for x in display_financial_response(financial_engine(p or prepared(), frequency=frequency)).research_panels}


def test_all_six_panels_exist_and_use_individually_qualified_values_without_new_math():
    output = panels()
    assert set(output) == {'assets', 'funding', 'growth', 'quarterly', 'pe', 'pb'}
    funding = output['funding']['rows'][-1]['values']
    assert funding == {'total_liabilities': 120, 'equity': 100, 'liabilities_assets': .6}
    assert output['growth']['rows'][-1]['values']['revenue'] == 120
    assert output['growth']['rows'][-1]['values']['revenue_growth_yoy'] == pytest.approx(.2)
    assert output['assets']['partial']
    assert 'other_assets' not in output['assets']['rows'][-1]['values']
    for key in ('pe', 'pb', 'quarterly'):
        assert output[key]['status'] == 'UNAVAILABLE'
        assert all(v is None for p in output[key]['rows'] for v in p['values'].values())


def test_unknown_basis_and_missing_rights_never_reappear_through_panel_projection():
    p = prepared()
    for receipt in p.reports.values():
        for obs in receipt.observations:
            obs.source_context.display_rights = 'unreviewed'
    before = p.model_dump()
    output = panels(p)
    for key in ('assets', 'funding', 'growth'):
        assert output[key]['status'] == 'UNQUALIFIED'
        assert all(v is None for row in output[key]['rows'] for v in row['values'].values())
    assert p.model_dump() == before


@pytest.mark.parametrize('negative', [False, True])
def test_conflicted_or_negative_stack_is_withheld_without_hiding_unrelated_growth(negative):
    p = prepared()
    latest = next(o for o in p.reports['balance'].observations if o.period == '2025')
    if negative:
        latest.fields['equity'] = -10
    else:
        # A corrupt calculation receipt simulates a cross-basis composition.
        result = financial_engine(p)
        result.rows[-1]['calculations']['equity']['inputs'][0]['consolidation'] = 'standalone'
        output = {x['key']: x for x in display_financial_response(result).research_panels}
        assert all(v is None for v in output['funding']['rows'][-1]['values'].values())
        assert output['growth']['rows'][-1]['values']['revenue'] == 120
        return
    output = panels(p)
    assert all(v is None for v in output['funding']['rows'][-1]['values'].values())
    assert output['funding']['rows'][-1]['statuses']['equity'] == 'UNQUALIFIED'
    assert output['growth']['rows'][-1]['values']['revenue'] == 120


def test_missing_periods_are_explicit_chart_gaps_not_connected_or_zero_filled():
    p = prepared()
    for receipt in p.reports.values():
        receipt.observations = [o for o in receipt.observations if o.period != '2024']
    growth = panels(p)['growth']
    assert [r['period'] for r in growth['rows']] == ['2023', '2024', '2025']
    assert all(v is None for v in growth['rows'][1]['values'].values())
    assert growth['partial']


def test_quarterly_and_ttm_modes_never_relabel_each_other():
    assert panels(frequency='quarterly')['quarterly']['rows'][-1]['values']['revenue'] == 30
    assert panels(frequency='ttm')['growth']['rows'][-1]['values']['revenue'] == 120
    assert panels(frequency='ttm')['quarterly']['status'] == 'UNAVAILABLE'


def test_bank_projection_uses_loans_and_operating_income_not_industrial_metrics():
    output = panels(packet(company_type='NH'))
    assert [s['key'] for s in output['assets']['series']] == ['customer_loans']
    keys = {s['key'] for s in output['growth']['series']}
    assert 'operating_income' in keys and 'revenue' not in keys
    assert output['growth']['status'] == 'DEMO'
    assert not any(x['status'] == 'QUALIFIED' for x in output.values())


def test_only_qualified_partial_components_are_used_and_zero_is_not_missing():
    p = prepared()
    latest = next(o for o in p.reports['balance'].observations if o.period == '2025')
    latest.fields['inventory'] = 0
    output = panels(p)
    assert output['assets']['rows'][-1]['values'] == {'cash_equivalents': None, 'inventory': 0}
    assert output['assets']['partial']


def test_historical_chart_never_connects_consolidated_and_separate_periods():
    p = prepared()
    for receipt in p.reports.values():
        for obs in receipt.observations:
            if obs.period.startswith('2023'):
                obs.consolidation = 'standalone'
    output = panels(p)
    assert output['growth']['rows'][0]['values']['revenue'] is None
    assert output['growth']['rows'][-1]['values']['revenue'] == 120
    assert 'Historical chart periods require the same reporting basis.' in output['growth']['reasons']
