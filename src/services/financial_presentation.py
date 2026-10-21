"""Display qualification over the existing engine; no new financial calculations."""
import math
from src.schemas.financials import FinancialEngineResponse, FundamentalSummary
from src.analytics.financial_catalog import specialist_consistency


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


def display_allowed(context, *, internal=False):
    if not context or context.get('display_rights') == 'prohibited':
        return False
    if internal:
        return (context.get('unit_evidence') == 'original_filing'
                and context.get('original_metadata', {}).get('extraction_verified') is True)
    return (context.get('display_rights') == 'permitted'
            and bool((context.get('display_rights_reference') or '').strip()))


def inputs_reasons(inputs, source, *, fixture=False, internal=False):
    """Report independent gates together; never change the qualification decision."""
    if not inputs:
        return ['Unqualified input evidence']
    reasons = []
    if not inputs or any(ref.get('source') != source or ref.get('currency') != 'VND'
            or not ref.get('code') or not ref.get('content_sha256')
            or ref.get('basis') not in ('annual', 'standalone', 'ytd', 'point_in_time') for ref in inputs):
        reasons.append('Unqualified input evidence')
    bases = {ref.get('consolidation') for ref in inputs}
    if len(bases) != 1:
        reasons.append('Conflicting reporting bases')
    if not fixture and not bases <= {'consolidated', 'standalone'}:
        reasons.append('Reporting basis is not qualified')
    if not fixture and any(not display_allowed(ref.get('source_context'), internal=internal) for ref in inputs):
        reasons.append('Financial source display rights are not qualified')
    return reasons


def inputs_reason(inputs, source, *, fixture=False, internal=False):
    reasons = inputs_reasons(inputs, source, fixture=fixture, internal=internal)
    return reasons[0] if reasons else None


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
    refs = evidence.get('inputs', [])
    reported = len(refs) == 1 and refs[0].get('field') == key and refs[0].get('value') == value
    if not reported and any((r.get('source_context') or {}).get('original_metadata', {}).get(check) == 'FAIL'
            for r in refs for check in ('balance_identity', 'cash_flow_identity')):
        return 'UNQUALIFIED', 'Financial statement consistency failed'
    if not reported and not all(specialist_consistency(ref) for ref in refs):
        return 'UNQUALIFIED', 'Loan quality note does not reconcile'
    reason = inputs_reason(evidence.get('inputs', []), result.source, fixture=result.is_fixture, internal=result.display_scope == 'internal_research')
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
        ('cashflow', 'Cash flow and reinvestment', 'performance', [
            ('cash_operating','Operating cash flow','VND'),('cash_investing','Investing cash flow','VND'),
            ('cash_financing','Financing cash flow','VND')] + ([('free_cash_flow','Free cash flow','VND')] if ordinary else []), False,
         'Standalone period flows; YTD is differenced only with compatible prior YTD evidence. Free cash flow is operating cash less reported capital expenditure outflows.'),
        ('profitability', 'Profitability history', 'performance', [
            ('roe','ROE','fraction'),('roa','ROA','fraction')] + ([('gross_margin','Gross Margin','fraction'),
            ('net_margin','Net Margin','fraction')] if ordinary else []), False,
         'ROE and ROA use average opening and closing balances. Quarterly returns are not annualized.'),
        ('liquidity', 'Liquidity and leverage', 'performance', [
            ('current_ratio','Current ratio','multiple'),('quick_ratio','Quick ratio','multiple'),
            ('debt_equity','Debt / equity','multiple')] if ordinary else [], False,
         'Current and quick ratios compare current assets with current liabilities. Debt/equity uses interest-bearing borrowings, not total liabilities.'),
        ('bank_funding', 'Bank lending and deposits', 'performance', [
            ('customer_loans','Customer loans','VND'),('customer_deposits','Customer deposits','VND'),
            ('loan_deposit_ratio','Accounting loans / deposits','fraction')] if bank else [], False,
         'Gross customer loans and customer deposits are period-end amounts. Their accounting ratio is not regulatory LDR. NIM, CASA and NPL are not inferred.'),
        ('bank_quality', 'Bank deposit and credit quality', 'performance', [
            ('demand_deposit_share','Demand-deposit share (accounting)','fraction'),
            ('npl_classified_ratio','NPL / classified customer loans','fraction'),
            ('classified_loan_coverage','Classified loan provision coverage','fraction')] if bank else [], False,
         'Demand deposits divided by customer deposits is an accounting CASA-style share. NPL is grades 3–5 divided by classified loans; coverage uses the matching general and specific allowance. Securities margin lending is excluded from the classified-loan denominators. NIM is unavailable.'),
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


def display_financial_response(result: FinancialEngineResponse, *, internal_authorization_reference=None) -> FinancialEngineResponse:
    """Conservative display only; full API/source evidence and math are unchanged.

    Unknown consolidation cannot certify comparisons or live overview metrics.
    DEMO can demonstrate known source units with an explicitly unknown basis.
    """
    # Only explicit offline callers can opt in; no HTTP parameter enables this.
    # Internal source verification is independent of public display permission.
    if internal_authorization_reference is not None:
        if not isinstance(internal_authorization_reference, str) or not internal_authorization_reference.strip() or result.is_fixture:
            raise ValueError('Invalid internal financial review authorization')
        result = result.model_copy(update={'display_scope': 'internal_research',
            'internal_authorization_reference': internal_authorization_reference,
            'read_kind': 'saved_filing_review'})
    elif result.display_scope != 'public':
        raise ValueError('Internal financial response cannot be republished as public')
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
            blockers = list(dict.fromkeys(([reason] if reason else []) + inputs_reasons(
                current.get('calculations', {}).get(key, {}).get('inputs', []),
                result.source, fixture=result.is_fixture, internal=result.display_scope == 'internal_research'))) if status in ('UNQUALIFIED', 'UNAVAILABLE') else []
            metrics.append(dict(key=key, group=group, label=label, unit=unit, status=status,
                blockers=blockers,
                value=current.get(key) if status in ('QUALIFIED', 'DEMO') else None,
                formula=current.get('calculations', {}).get(key, {}).get('formula', 'No qualified calculation inputs'), reason=reason,
                consolidation=next(iter({ref.get('consolidation') for ref in current.get('calculations', {}).get(key, {}).get('inputs', [])}), None)
                    if status in ('QUALIFIED', 'DEMO') else None))
    changes = []
    for change in result.changes:
        evidence = current.get('calculations', {}).get(change['metric'] + '_growth_yoy', {})
        allowed = inputs_reason(evidence.get('inputs', []), result.source, fixture=result.is_fixture, internal=result.display_scope == 'internal_research') is None
        value = by_period[current['period']].get(change['metric'])
        changes.append({**change, 'current': value,
            **({} if allowed and value is not None else dict(previous=None, absolute_change=None, growth_yoy=None))})
    statements = {}
    for kind, statement in result.statements.items():
        periods = []
        for period in statement['periods']:
            context = period.get('source_context')
            qualified = (result.is_fixture or period['consolidation'] in ('consolidated', 'standalone') and
                display_allowed(context, internal=result.display_scope == 'internal_research')) and period['basis'] in ('annual', 'standalone', 'ytd', 'point_in_time')
            periods.append({**period, 'items': [line if qualified and line['unit'] in ('VND', 'VND/share', 'shares') or line['value'] is None else
                {**line, 'value': None, 'semantic_status': 'unqualified'} for line in period['items']]})
        statements[kind] = {**statement, 'periods': periods}
    latest = len(result.rows) - 1
    from src.services.financial_verification import verification_assessment
    return result.model_copy(update={
        'rows': [row if index == latest else {k:v for k,v in row.items() if k != 'calculations'}
                 for index, row in enumerate(projected)],
        'chart_rows': [{k:v for k,v in by_period.get(row['period'], row).items() if k != 'calculations'} for row in result.chart_rows],
        'changes': changes, 'statements': statements,
        'fundamental_summary': FundamentalSummary(period=current.get('period'), frequency=result.period_type,
            consolidation=current.get('consolidation'), publication_date=current.get('publication_date'), metrics=metrics),
        'research_panels': financial_research_panels(result),
        'verification': verification_assessment(result, projected, audience=result.display_scope),
    })
