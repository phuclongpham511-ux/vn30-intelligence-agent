"""Display qualification over the existing engine; no new financial calculations."""
import math
from src.schemas.financials import FinancialEngineResponse, FundamentalSummary


# Units describe engine outputs, not guesses from a provider's arbitrary columns.
METRICS = {
    'valuation': [('market_cap', 'Market capitalization', 'VND'), ('pe', 'P/E', 'multiple'),
        ('pb', 'P/B', 'multiple'), ('eps_reported', 'Reported basic EPS', 'VND/share'), ('bvps', 'BVPS', 'VND/share')],
    'performance': [('revenue', 'Revenue', 'VND'), ('net_profit', 'Profit after tax', 'VND'),
        ('revenue_growth_yoy', 'Revenue YoY', 'fraction'), ('net_profit_growth_yoy', 'Profit after tax YoY', 'fraction')],
    'profitability': [('roe', 'ROE', 'fraction'), ('roa', 'ROA', 'fraction'),
        ('gross_margin', 'Gross Margin', 'fraction'), ('net_margin', 'Net Margin', 'fraction')],
    'health': [('total_assets', 'Total assets', 'VND'), ('total_liabilities', 'Total liabilities', 'VND'),
        ('equity', 'Total equity', 'VND'), ('debt_equity', 'Debt / equity', 'multiple'),
        ('cash_operating', 'Operating cash flow', 'VND'), ('free_cash_flow', 'Free cash flow', 'VND')],
}


def inputs_reason(inputs, source, *, fixture=False):
    if not inputs or any(ref.get('source') != source or ref.get('currency') != 'VND'
            or not ref.get('code') or not ref.get('content_sha256')
            or ref.get('basis') not in ('annual', 'standalone', 'ytd', 'point_in_time') for ref in inputs):
        return 'Unqualified input evidence'
    bases = {ref.get('consolidation') for ref in inputs}
    if len(bases) != 1:
        return 'Conflicting reporting bases'
    if not fixture and not bases <= {'consolidated', 'standalone'}:
        return 'Reporting basis is not qualified'
    return None


def metric_status(row, key, result):
    value = row.get(key)
    evidence = row.get('calculations', {}).get(key, {})
    reason = evidence.get('reason')
    if value is None:
        if reason == 'missing_or_unqualified_input' and evidence.get('inputs') and all(ref.get('code') for ref in evidence['inputs']):
            return 'UNAVAILABLE', 'Required inputs are unavailable'
        return ('UNQUALIFIED' if reason and any(word in reason for word in ('unqualified', 'incompatible', 'unknown')) else 'UNAVAILABLE',
                reason or 'Required inputs are unavailable')
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not evidence or reason:
        return 'UNQUALIFIED', reason or 'Unqualified input evidence'
    reason = inputs_reason(evidence.get('inputs', []), result.source, fixture=result.is_fixture)
    if reason:
        return 'UNQUALIFIED', reason
    if not result.is_fixture and row.get('consolidation') not in ('consolidated', 'standalone'):
        return 'UNQUALIFIED', 'Reporting basis is not qualified'
    return ('DEMO', 'Synthetic financial evidence') if result.is_fixture else ('QUALIFIED', None)


def display_financial_response(result: FinancialEngineResponse) -> FinancialEngineResponse:
    """Conservative display only; full API/source evidence and math are unchanged.

    Unknown consolidation cannot certify comparisons or live overview metrics.
    DEMO can demonstrate known source units with an explicitly unknown basis.
    """
    projected = []
    for row in result.rows:
        projected.append({**row, **{key: None for key in row.get('calculations', {})
            if metric_status(row, key, result)[0] not in ('QUALIFIED', 'DEMO')}})
    by_period = {row['period']: row for row in projected}
    current = result.rows[-1] if result.rows else {}
    metrics = []
    for group, definitions in METRICS.items():
        for key, label, unit in definitions:
            if result.profile == 'bank' and key in ('revenue', 'revenue_growth_yoy'):
                key, label = ('operating_income', 'Operating income') if key == 'revenue' else ('operating_income_growth_yoy', 'Operating income YoY')
            status, reason = metric_status(current, key, result)
            metrics.append(dict(key=key, group=group, label=label, unit=unit, status=status,
                value=current.get(key) if status in ('QUALIFIED', 'DEMO') else None,
                formula=current.get('calculations', {}).get(key, {}).get('formula', 'No qualified calculation inputs'), reason=reason))
    changes = []
    for change in result.changes:
        evidence = current.get('calculations', {}).get(change['metric'] + '_growth_yoy', {})
        allowed = inputs_reason(evidence.get('inputs', []), result.source, fixture=result.is_fixture) is None
        value = by_period[current['period']].get(change['metric'])
        changes.append({**change, 'current': value,
            **({} if allowed and value is not None else dict(previous=None, absolute_change=None, growth_yoy=None))})
    statements = {}
    for kind, statement in result.statements.items():
        periods = []
        for period in statement['periods']:
            qualified = (result.is_fixture or period['consolidation'] in ('consolidated', 'standalone')) and period['basis'] in ('annual', 'standalone', 'ytd', 'point_in_time')
            periods.append({**period, 'items': [line if qualified and line['unit'] in ('VND', 'VND/share') or line['value'] is None else
                {**line, 'value': None, 'semantic_status': 'unqualified'} for line in period['items']]})
        statements[kind] = {**statement, 'periods': periods}
    latest = len(result.rows) - 1
    return result.model_copy(update={
        'rows': [row if index == latest else {k:v for k,v in row.items() if k != 'calculations'}
                 for index, row in enumerate(projected)],
        'chart_rows': [{k:v for k,v in by_period.get(row['period'], row).items() if k != 'calculations'} for row in result.chart_rows],
        'changes': changes, 'statements': statements,
        'fundamental_summary': FundamentalSummary(period=current.get('period'), frequency=result.period_type,
            consolidation=current.get('consolidation'), publication_date=current.get('publication_date'), metrics=metrics),
    })
