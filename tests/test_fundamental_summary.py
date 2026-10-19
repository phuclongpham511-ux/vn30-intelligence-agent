"""Synthetic packets only; no provider reads, persistence or live acceptance."""
import pytest
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response
from test_financial_engine import packet, fixture


def response(*, known_basis=True, demo=False, frequency='annual', mutate=None):
    metadata, reports = fixture()
    if known_basis:
        for report in reports.values():
            for collection in report.values():
                for row in collection:
                    row['consolidation'] = 'consolidated'
    if mutate:
        mutate(reports)
    p = packet(metadata, reports).model_copy(update={'is_fixture': demo})
    # Synthetic permission evidence for this contract test, not provider rights.
    for receipt in p.reports.values():
        for observation in receipt.observations:
            observation.source_context.display_rights = 'permitted'
            observation.source_context.display_rights_reference = 'synthetic-only://permission-test'
    return financial_engine(p, frequency=frequency)


def metric(result, key):
    return next(item for item in result.fundamental_summary.metrics if item.key == key)


def test_existing_engine_units_definitions_and_values_are_not_recalculated():
    full = response()
    before = full.model_dump()
    display = display_financial_response(full)
    assert metric(display, 'eps_reported').unit == 'VND/share'
    assert metric(display, 'eps_reported').value == 2
    assert metric(display, 'revenue').value == 120
    assert metric(display, 'roe').value == pytest.approx(12/90)
    assert metric(display, 'roe').formula == full.rows[-1]['calculations']['roe']['formula']
    assert metric(display, 'roe').status == 'QUALIFIED'
    for key in ('market_cap', 'pe', 'pb', 'bvps'):
        assert metric(display, key).status == 'UNAVAILABLE' and metric(display, key).value is None
    assert full.model_dump() == before


def test_unknown_consolidation_cannot_certify_live_metrics_charts_or_comparisons():
    full = response(known_basis=False)
    display = display_financial_response(full)
    assert metric(display, 'revenue').status == 'UNQUALIFIED'
    assert metric(display, 'revenue').reason == 'Reporting basis is not qualified'
    assert display.rows[-1]['revenue'] is None and display.chart_rows[-1]['revenue'] is None
    assert all(change['current'] is None and change['absolute_change'] is None for change in display.changes)
    line = next(item for item in display.statements['income']['periods'][-1]['items'] if item['code'] == 'isa3')
    assert line['value'] is None and line['semantic_status'] == 'unqualified' and line['raw_value'] == 120
    assert full.rows[-1]['revenue'] == 120, 'full source/calculation API is preserved'


def test_demo_never_becomes_live_qualification():
    display = display_financial_response(response(known_basis=False, demo=True))
    assert display.is_fixture and metric(display, 'revenue').status == 'DEMO'
    assert metric(display, 'revenue').value == 120
    assert not any(item.status == 'QUALIFIED' for item in display.fundamental_summary.metrics)


@pytest.mark.parametrize('prior', [0, -10, None])
def test_growth_rejects_zero_negative_and_missing_base_without_faking_zero(prior):
    def change(reports): reports['income']['years'][-2]['isa3'] = prior
    display = display_financial_response(response(mutate=change))
    assert metric(display, 'revenue_growth_yoy').value is None
    assert metric(display, 'revenue').value == 120


def test_missing_profit_and_division_by_zero_keep_unavailable_ratios():
    def change(reports):
        reports['income']['years'][-1]['isa3'] = 0
        reports['income']['years'][-1]['isa20'] = None
        reports['balance']['years'][-1]['bsa78'] = 0
    display = display_financial_response(response(mutate=change))
    assert metric(display, 'revenue').value == 0
    assert metric(display, 'net_profit').status == 'UNAVAILABLE'
    for key in ('net_profit', 'roe', 'net_margin', 'debt_equity'):
        assert metric(display, key).value is None


def test_consolidation_conflicts_and_missing_exact_prior_period_are_not_comparisons():
    def change(reports):
        reports['balance']['years'][-1]['consolidation'] = 'standalone'
        for report in reports.values():
            report['years'] = [row for row in report['years'] if row['yearReport'] != 2024]
    display = display_financial_response(response(mutate=change))
    assert metric(display, 'roe').value is None
    assert metric(display, 'revenue_growth_yoy').value is None
    assert display.chart_rows[-2]['revenue'] is None
    assert all(change['growth_yoy'] is None for change in display.changes)


def test_unknown_quarter_flow_basis_and_ttm_eps_are_not_qualified():
    def change(reports): reports['income']['quarters'][-1]['flowBasis'] = 'unknown'
    quarter = display_financial_response(response(frequency='quarterly', mutate=change))
    assert metric(quarter, 'revenue').status == 'UNQUALIFIED'
    ttm = display_financial_response(response(frequency='ttm'))
    assert metric(ttm, 'eps_reported').value is None
    assert metric(ttm, 'revenue').value == 120


def test_corrupt_input_units_cannot_become_qualified_even_when_value_is_present():
    full = response()
    full.rows[-1]['calculations']['revenue']['inputs'][0]['currency'] = 'USD'
    display = display_financial_response(full)
    assert metric(display, 'revenue').status == 'UNQUALIFIED'
    assert display.rows[-1]['revenue'] is None


@pytest.mark.parametrize('frequency', ['annual', 'quarterly', 'ttm'])
def test_display_http_contract_is_select_only_and_does_not_change_full_evidence(client, session, frequency):
    from datetime import datetime, timezone
    from sqlalchemy import event
    from main import app
    from src.models import Security
    from src.services.data import get_fundamental_provider
    session.add(Security(symbol='ABC', exchange='HOSE', last_synced_at=datetime.now(timezone.utc)))
    session.commit()
    saved = packet().model_copy(update={'is_fixture': False})
    calls = []
    class Provider:
        source = 'test:VCI'
        def get_reports(self, ticker):
            calls.append(ticker)
            return saved.model_copy(deep=True)
    app.dependency_overrides[get_fundamental_provider] = Provider
    queries = []
    def capture(_conn, _cursor, query, *_args): queries.append(query)
    event.listen(session.get_bind(), 'before_cursor_execute', capture)
    try:
        path = f'/stocks/ABC/financials?frequency={frequency}'
        full = client.get(path).json()
        reply = client.get(path + '&projection=display')
        assert reply.status_code == 200
        display = reply.json()
        assert display['fundamental_summary']['frequency'] == frequency
        assert display['fundamental_summary']['period'] == full['rows'][-1]['period']
        assert display['rows'][-1]['revenue'] is None and full['rows'][-1]['revenue'] is not None
        assert calls == ['ABC', 'ABC'], 'projection introduces no additional provider call'
        assert queries and all(query.lstrip().upper().startswith('SELECT') for query in queries)
    finally:
        event.remove(session.get_bind(), 'before_cursor_execute', capture)
