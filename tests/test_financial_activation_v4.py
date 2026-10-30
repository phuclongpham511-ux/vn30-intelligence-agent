"""Synthetic qualification boundaries, never provider permission evidence."""
import copy
import pytest
from test_financial_foundation_v2 import prepared, metric
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response


@pytest.mark.parametrize('ticker', ['FPT', 'PNJ', 'VCB', 'ABC'])
def test_independent_basis_and_rights_blockers_are_visible_without_changing_values(ticker):
    packet = prepared()
    packet.ticker = ticker
    for receipt in packet.reports.values():
        for row in receipt.observations:
            row.ticker = ticker
            row.consolidation = None
            row.source_context.display_rights = 'unreviewed'
            row.source_context.display_rights_reference = None
    original = copy.deepcopy(packet)
    result = display_financial_response(financial_engine(packet))
    revenue = metric(result, 'revenue')
    assert revenue.value is None and revenue.status == 'UNQUALIFIED'
    assert 'Reporting basis is not qualified' in revenue.blockers
    assert 'Financial source display rights are not qualified' in revenue.blockers
    assert packet == original


def test_reviewed_rights_alone_do_not_resolve_basis_and_unrelated_fields_stay_visible():
    packet = prepared()
    for row in packet.reports['income'].observations:
        row.consolidation = None
    result = display_financial_response(financial_engine(packet))
    assert metric(result, 'revenue').value is None
    assert metric(result, 'revenue').blockers == ['Reporting basis is not qualified']
    assert metric(result, 'total_assets').value == 200
    assert metric(result, 'total_assets').blockers == []


def test_complete_synthetic_contract_preserves_qualified_value_and_does_not_infer_valuation():
    result = display_financial_response(financial_engine(prepared()))
    assert metric(result, 'revenue').value == 120
    assert metric(result, 'revenue').blockers == []
    assert metric(result, 'pe').value is None
    assert metric(result, 'pe').blockers
