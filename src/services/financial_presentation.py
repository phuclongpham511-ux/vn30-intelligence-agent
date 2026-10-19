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
    if not fixture and any(not ref.get('source_context') or
            ref['source_context'].get('display_rights') != 'permitted' or
            not (ref['source_context'].get('display_rights_reference') or '').strip() for ref in inputs):
        return 'Financial source display rights are not qualified'
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
    return ('DEMO', 'Synthetic financial evidence') if result.is_fixture else ('QUALIFIED', None)


def financial_research_panels(result):
    """Chart projections of already calculated, individually guarded values.

    No arithmetic, provider calls, residual asset buckets or price joins. A stack
    cannot combine distinct reporting bases or hide a missing point as zero.
    """
    bank = result.profile == 'bank'
    ordinary = result.profile == 'non_financial'
    performance = [('operating_income', 'Operating income', 'VND')] if bank else [
        ('revenue', 'Revenue', 'VND')] if ordinary else []
    performance += [('net_profit', 'Profit after tax', 'VND')]
    growth = [('operating_income_growth_yoy', 'Operating income YoY', 'fraction')] if bank else [
        ('revenue_growth_yoy', 'Revenue YoY', 'fraction')] if ordinary else []
    growth += [('net_profit_growth_yoy', 'Profit after tax YoY', 'fraction')]
    assets = [('customer_loans', 'Customer loans', 'VND')] if bank else [
        ('cash_equivalents', 'Cash and cash equivalents', 'VND'),
        ('inventory', 'Inventory', 'VND')] if ordinary else []
    definitions = [
        ('assets', 'Asset composition', 'stacked', assets, True,
         'Partial components only; receivables, fixed assets, investments and other assets are not reconstructed.'),
        ('funding', 'Funding composition', 'stacked', [
            ('total_liabilities', 'Total liabilities', 'VND'), ('equity', 'Total equity', 'VND'),
            ('liabilities_assets', 'Liabilities / assets', 'fraction')], False,
         'Liabilities and total equity are separate components; borrowings and minority interests are not added again.'),
        ('growth', 'Revenue and profit trends', 'performance', performance + growth, False,
         'Reported period results and comparable YoY rates; no market-price overlay.'),
        ('quarterly', 'Quarterly operating results', 'performance', performance + growth, False,
         'Select Quarterly for standalone quarterly results; annual and TTM values are not relabelled as quarters.'),
        ('pe', 'P/E history', 'unavailable', [('pe', 'P/E', 'multiple')], True,
         'Compatible dated prices, earnings per share and display rights are not qualified.'),
        ('pb', 'P/B history', 'unavailable', [('pb', 'P/B', 'multiple')], True,
         'Compatible dated prices, book value per share and display rights are not qualified.'),
    ]
    panels = []
    for key, title, chart, fields, partial, methodology in definitions:
        points, reasons = [], set()
        enabled = chart != 'unavailable' and (key != 'quarterly' or result.period_type == 'quarterly')
        for row in result.chart_rows:
            values, statuses, bases = {}, {}, {}
            for field, _, _ in fields:
                status, reason = metric_status(row, field, result) if enabled else ('UNAVAILABLE', methodology)
                allowed = status in ('QUALIFIED', 'DEMO')
                values[field] = row.get(field) if allowed else None
                statuses[field] = status
                refs = row.get('calculations', {}).get(field, {}).get('inputs', [])
                bases[field] = refs[0].get('consolidation') if allowed and refs else None
                if reason:
                    reasons.add(reason)
            if len({bases[f] for f, _, _ in fields if values[f] is not None}) > 1:
                reasons.add('Chart series require the same reporting basis.')
                for field, _, _ in fields:
                    values[field], statuses[field], bases[field] = None, 'UNQUALIFIED', None
            if chart == 'stacked':
                amount_fields = [f for f, _, unit in fields if unit == 'VND']
                present = [f for f in amount_fields if values[f] is not None]
                conflict = len({bases[f] for f in present}) > 1
                negative = any(values[f] < 0 for f in present)
                if conflict or negative:
                    reasons.add('Composition requires compatible nonnegative components.')
                    for field, _, _ in fields:
                        values[field], statuses[field], bases[field] = None, 'UNQUALIFIED', None
                elif present:
                    basis = bases[present[0]]
                    for field, _, unit in fields:
                        if unit != 'VND' and values[field] is not None and bases[field] != basis:
                            values[field], statuses[field], bases[field] = None, 'UNQUALIFIED', None
                            reasons.add('Composition requires compatible nonnegative components.')
            points.append(dict(period=row['period'], values=values, statuses=statuses, bases=bases))
        # A historical chart must not imply comparability between separate and
        # consolidated statements. Retain only the latest usable basis; other
        # observations stay inspectable in the original statement evidence.
        anchors = [p for p in points if any(v is not None for v in p['values'].values())]
        if anchors:
            anchor = next(anchors[-1]['bases'][f] for f, v in anchors[-1]['values'].items() if v is not None)
            for point in points:
                for field, _, _ in fields:
                    if point['values'][field] is not None and point['bases'][field] != anchor:
                        point['values'][field], point['statuses'][field], point['bases'][field] = None, 'UNQUALIFIED', None
                        reasons.add('Historical chart periods require the same reporting basis.')
        has_value = any(value is not None for p in points for value in p['values'].values())
        withheld = any(status == 'UNQUALIFIED' for p in points for status in p['statuses'].values())
        panels.append(dict(key=key, title=title, chart=chart, source=result.source,
            frequency=result.period_type,
            status=('DEMO' if result.is_fixture else 'QUALIFIED') if has_value else 'UNQUALIFIED' if withheld else 'UNAVAILABLE',
            partial=partial or any(value is None for p in points for value in p['values'].values()),
            methodology=methodology, reasons=sorted(reasons),
            series=[dict(key=f, label=label, unit=unit) for f, label, unit in fields], rows=points))
    return panels


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
                formula=current.get('calculations', {}).get(key, {}).get('formula', 'No qualified calculation inputs'), reason=reason,
                consolidation=next(iter({ref.get('consolidation') for ref in current.get('calculations', {}).get(key, {}).get('inputs', [])}), None)
                    if status in ('QUALIFIED', 'DEMO') else None))
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
            context = period.get('source_context')
            qualified = (result.is_fixture or period['consolidation'] in ('consolidated', 'standalone') and
                (context is not None and context.get('display_rights') == 'permitted' and
                 bool((context.get('display_rights_reference') or '').strip()))) and period['basis'] in ('annual', 'standalone', 'ytd', 'point_in_time')
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
        'research_panels': financial_research_panels(result),
    })
