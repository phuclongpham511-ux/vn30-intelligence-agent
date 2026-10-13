"""Deterministic financial research from period-owned, metadata-qualified statements.

Ratios are fractions. No annualization, valuation proxy, sector inference or forecasts.
Annual reports are never replaced by summed quarters. TTM is separately labelled.
"""
from datetime import datetime, timezone
import math
from src.providers.vnstock.financial_statements import MAP
from src.schemas.financials import FinancialEngineResponse

GROWTH_FIELDS = ('revenue', 'operating_income', 'net_profit', 'profit_parent')
FLOW_FIELDS = set(MAP['income']) - {'eps_reported'} | (set(MAP['cash']) - {'cash_beginning', 'cash_ending'})


def serial(period):
    year = int(period[:4])
    return year * 4 + int(period[-1]) - 1 if '-Q' in period else year


def quarterly(index):
    return f'{index // 4}-Q{index % 4 + 1}'


def previous(period, years=0, quarters=0):
    return quarterly(serial(period) - years * 4 - quarters) if '-Q' in period else str(int(period)-years)


def compatible(*observations):
    present = [item for item in observations if item is not None]
    return bool(present) and len({(item.ticker, item.source, item.currency, item.consolidation) for item in present}) == 1


def finite_result(value):
    return value if value is not None and math.isfinite(value) else None


def financial_engine(packet, *, frequency='annual', limit=8, sector=None, industry=None):
    if frequency not in ('annual', 'quarterly', 'ttm') or not 1 <= limit <= 20:
        raise ValueError('Unsupported financial projection')
    indexed = {}
    for kind, receipt in packet.reports.items():
        if receipt.statement != kind or kind not in MAP:
            raise ValueError('Invalid financial receipt ownership')
        indexed[kind] = {}
        for obs in receipt.observations:
            if obs.ticker != packet.ticker or obs.source != packet.source or obs.currency != 'VND' or obs.statement != kind:
                raise ValueError('Wrong financial observation ownership')
            if obs.period in indexed[kind] or obs.frequency != ('quarterly' if '-Q' in obs.period else 'annual'):
                raise ValueError('Invalid financial period ownership')
            if any(value is not None and not math.isfinite(value) for value in obs.fields.values()):
                raise ValueError('Non-finite financial input')
            indexed[kind][obs.period] = obs
    for kind in MAP:
        indexed.setdefault(kind, {})

    def input_ref(obs, field):
        receipt = packet.reports[obs.statement]
        return dict(statement=obs.statement, period=obs.period, field=field,
            code=obs.field_codes.get(field), value=obs.fields.get(field), source=obs.source,
            currency=obs.currency, basis=obs.basis, consolidation=obs.consolidation,
            content_sha256=receipt.content_sha256)

    def value_at(kind, period, field):
        obs = indexed[kind].get(period)
        if obs is None:
            return None, [], 'missing_statement'
        value, refs = obs.fields.get(field), [input_ref(obs, field)]
        if value is None:
            return None, refs, 'missing_or_unqualified_input'
        if field == 'eps_reported' and obs.basis not in ('annual', 'standalone'):
            return None, refs, 'eps_not_additive'
        if kind == 'balance' or field in ('cash_beginning', 'cash_ending', 'eps_reported'):
            return value, refs, None
        if obs.basis in ('annual', 'standalone'):
            return value, refs, None
        if obs.basis == 'ytd' and '-Q' in period:
            if period.endswith('Q1'):
                return value, refs, None
            prior = indexed[kind].get(previous(period, quarters=1))
            if prior and prior.basis == 'ytd' and compatible(obs, prior) and prior.fields.get(field) is not None:
                return value - prior.fields[field], refs + [input_ref(prior, field)], None
            return None, refs, 'missing_compatible_prior_ytd'
        return None, refs, 'unknown_flow_basis'

    periods = sorted({period for rows in indexed.values() for period in rows
                      if ('-Q' in period) == (frequency != 'annual')})
    results = {}
    for period in periods:
        observations = [indexed[kind].get(period) for kind in MAP]
        values, evidence, provenance = {}, {}, {}
        coherent = compatible(*observations)
        for kind, fields in MAP.items():
            for field in fields:
                value, refs, reason = value_at(kind, period, field)
                if frequency == 'ttm' and field in FLOW_FIELDS:
                    window = [previous(period, quarters=offset) for offset in range(3, -1, -1)]
                    parts = [value_at(kind, key, field) for key in window]
                    owners = [indexed[kind].get(key) for key in window]
                    if all(item is not None for item in owners) and compatible(*owners) and all(p[0] is not None for p in parts):
                        value, refs, reason = sum(p[0] for p in parts), [ref for p in parts for ref in p[1]], None
                    else:
                        value, refs, reason = None, [ref for p in parts for ref in p[1]], 'incomplete_or_incompatible_ttm'
                elif frequency == 'ttm' and field == 'eps_reported':
                    value, reason = None, 'eps_not_additive'
                elif frequency == 'ttm' and field in ('cash_beginning', 'cash_ending'):
                    # These are source-period point values, not TTM cash endpoints.
                    value, reason = None, 'not_ttm_flow'
                if value is not None and not math.isfinite(value):
                    value, reason = None, 'nonfinite_result'
                values[field] = value
                provenance[field] = refs
                evidence[field] = dict(formula='sum(four contiguous standalone quarters)' if frequency == 'ttm' and field in FLOW_FIELDS else 'reported; YTD flows differenced against previous same-year YTD where required', inputs=refs, reason=reason)

        def calculate(name, formula, fields, fn, *, positive=(), ordinary=False, extra=None):
            args = [values.get(field) for field in fields]
            refs = [ref for field in fields for ref in provenance.get(field, [])]
            reason = ('not_applicable_to_issuer' if ordinary and packet.profile != 'non_financial' else
                      'incompatible_statement_basis' if not coherent else
                      'missing_input' if any(arg is None for arg in args) else
                      'nonpositive_denominator' if any(values.get(field) is None or values[field] <= 0 for field in positive) else None)
            if extra:
                refs += extra[1]
                reason = reason or extra[2]
            if len({(ref['source'],ref['currency'],ref['consolidation']) for ref in refs}) > 1:
                reason = 'incompatible_statement_basis'
            output = fn(*args) if reason is None else None
            if output is None and reason is None:
                reason = 'invalid_input_sign'
            if output is not None and not math.isfinite(output):
                output, reason = None, 'nonfinite_result'
            values[name] = output
            provenance[name] = refs
            evidence[name] = dict(formula=formula, inputs=refs, reason=reason)

        calculate('gross_margin', 'gross_profit / revenue', ['gross_profit', 'revenue'], lambda a,b:a/b, positive=('revenue',), ordinary=True)
        calculate('net_margin', 'total profit after tax / revenue', ['net_profit','revenue'], lambda a,b:a/b, positive=('revenue',), ordinary=True)
        calculate('total_debt', 'short_debt + long_debt', ['short_debt','long_debt'], lambda a,b:a+b if a>=0 and b>=0 else None, ordinary=True)
        calculate('debt_equity', 'total_debt / total equity', ['total_debt','equity'], lambda a,b:a/b, positive=('equity',), ordinary=True)
        calculate('liabilities_assets', 'total_liabilities / total_assets', ['total_liabilities','total_assets'], lambda a,b:a/b, positive=('total_assets',))
        calculate('current_ratio', 'current_assets / current_liabilities', ['current_assets','current_liabilities'], lambda a,b:a/b, positive=('current_liabilities',), ordinary=True)
        calculate('quick_ratio', '(current_assets - inventory) / current_liabilities', ['current_assets','inventory','current_liabilities'], lambda a,b,c:(a-b)/c, positive=('current_liabilities',), ordinary=True)
        calculate('cash_conversion', 'cash_operating / total profit after tax', ['cash_operating','net_profit'], lambda a,b:a/b, positive=('net_profit',), ordinary=True)
        calculate('capex_cash_outflow', '-capex_signed (only reported outflows)', ['capex_signed'], lambda a:-a if a<=0 else None, ordinary=True)
        calculate('free_cash_flow', 'cash_operating - capex_cash_outflow', ['cash_operating','capex_cash_outflow'], lambda a,b:a-b, ordinary=True)
        calculate('balance_residual', 'total_assets - total_liabilities - total equity', ['total_assets','total_liabilities','equity'], lambda a,b,c:a-b-c)
        for metric, field in (('roe','equity'),('roa','total_assets')):
            prior_period = previous(period, years=1) if frequency != 'quarterly' else previous(period, quarters=1)
            prior_obs = indexed['balance'].get(prior_period)
            current_obs = indexed['balance'].get(period)
            prior_value, prior_refs, prior_reason = value_at('balance', prior_period, field)
            if prior_value is None or prior_value <= 0:
                prior_reason = prior_reason or 'nonpositive_prior_balance'
            if current_obs and prior_obs and not compatible(current_obs, prior_obs):
                prior_reason = 'incompatible_prior_balance'
            calculate(metric, f'total profit after tax / mean(current {field}, {prior_period} {field}); period return, not annualized',
                ['net_profit',field], lambda p,b: p/((b+prior_value)/2), positive=(field,), extra=(prior_value,prior_refs,prior_reason))

        for field in GROWTH_FIELDS:
            for suffix, prior_period in (('growth_yoy', previous(period, years=1)), ('growth_qoq', previous(period, quarters=1) if '-Q' in period else None)):
                name = field + '_' + suffix
                prior_row = results.get(prior_period)
                before = prior_row[field] if prior_row else None
                after = values.get(field)
                all_refs = provenance[field] + (prior_row['calculations'][field]['inputs'] if prior_row else [])
                comparable = prior_row and len({(ref['source'],ref['currency'],ref['consolidation']) for ref in all_refs}) <= 1
                reason = 'missing_comparable_period' if before is None or after is None or not comparable else 'nonpositive_base' if before <= 0 else None
                values[name] = finite_result((after-before)/before) if reason is None else None
                if reason is None and values[name] is None:
                    reason = 'nonfinite_result'
                evidence[name] = dict(formula='(current - exact comparable prior period) / prior; positive base required',
                    inputs=all_refs, reason=reason)

        # Old history contract remains available to the existing presentation layer.
        for field in ('gross_margin','net_margin','roe'):
            prior_row = results.get(previous(period, years=1))
            refs = provenance[field] + (prior_row['calculations'][field]['inputs'] if prior_row else [])
            comparable = prior_row and len({(ref['source'],ref['currency'],ref['consolidation']) for ref in refs}) <= 1
            before = prior_row[field] if comparable else None
            values[field+'_change'] = finite_result(values[field]-before) if values[field] is not None and before is not None else None
            evidence[field+'_change'] = dict(formula='current ratio - exact prior-year ratio (fraction difference)',
                inputs=refs, reason=None if values[field+'_change'] is not None else 'missing_comparable_period')
        dates = {o.source_dates.get('publicDate') for o in observations if o and o.source_dates.get('publicDate')}
        row = dict(ticker=packet.ticker,source=packet.source,currency='VND',period=period,frequency=frequency,
            **values, calculations=evidence, statement_periods={o.statement:o.period for o in observations if o},
            publication_date=next(iter(dates)) if len(dates)==1 else None,
            consolidation=next((o.consolidation for o in observations if o),None) if coherent else None,
            is_fixture=packet.is_fixture)
        results[period] = row

    rows = list(results.values())[-limit:]
    changes = []
    if rows:
        latest = rows[-1]
        prior_period = previous(latest['period'], years=1)
        prior = results.get(prior_period)
        for field in (('operating_income','net_profit') if packet.profile == 'bank' else ('revenue','net_profit')):
            current = latest[field]
            comparable_refs = latest['calculations'][field]['inputs'] + (prior['calculations'][field]['inputs'] if prior else [])
            before = prior[field] if prior and len({(ref['source'],ref['currency'],ref['consolidation']) for ref in comparable_refs}) <= 1 else None
            if current is not None:
                changes.append(dict(metric=field,current_period=latest['period'],prior_period=prior_period,
                    current=current,previous=before,absolute_change=finite_result(current-before) if before is not None else None,
                    growth_yoy=latest[field+'_growth_yoy']))
    chart_rows = []
    if rows:
        for index in range(serial(rows[0]['period']), serial(rows[-1]['period'])+1):
            key = str(index) if frequency == 'annual' else quarterly(index)
            chart_rows.append(results.get(key) or dict(period=key,**{field:None for field in rows[0] if field not in ('period','calculations')}))
    statements = {}
    for kind, receipt in packet.reports.items():
        selected = [obs for obs in receipt.observations if obs.period in {row['period'] for row in rows}]
        statements[kind] = dict(status=receipt.status, basis='reported source periods; not summed TTM statements',
            periods=[obs.model_dump(mode='json') for obs in selected])
    available = [kind for kind,receipt in packet.reports.items() if receipt.observations]
    period_types = [kind for kind, pattern in (('annual', False), ('quarterly', True))
                   if any(('-Q' in p)==pattern for data in indexed.values() for p in data)]
    if any(all(previous(p, quarters=offset) in indexed['income'] for offset in range(4))
           for p in indexed['income'] if '-Q' in p):
        period_types.append('ttm')
    reconciliations = []
    for kind in ('income','cash'):
        for year, annual in indexed[kind].items():
            if '-Q' in year:
                continue
            quarters = [indexed[kind].get(f'{year}-Q{q}') for q in range(1,5)]
            if not all(quarters) or not compatible(annual,*quarters):
                continue
            for field in MAP[kind]:
                if field not in FLOW_FIELDS or annual.fields.get(field) is None:
                    continue
                parts = [value_at(kind, obs.period, field) for obs in quarters]
                if all(part[0] is not None for part in parts):
                    quarter_sum = sum(part[0] for part in parts)
                    difference = quarter_sum - annual.fields[field]
                    if math.isfinite(difference) and math.isfinite(quarter_sum) and difference != 0:
                        reconciliations.append(dict(statement=kind,period=year,field=field,
                            annual_reported=annual.fields[field],quarter_sum=quarter_sum,difference=difference,
                            inputs=[input_ref(annual,field)]+[ref for part in parts for ref in part[1]]))
    return FinancialEngineResponse(ticker=packet.ticker,source=packet.source,period_type=frequency,
        profile=packet.profile,rows=rows,chart_rows=chart_rows,changes=changes,statements=statements,
        available_period_types=period_types,available_statements=available,
        source_receipts=[dict(**receipt.model_dump(mode='json',exclude={'observations'}),
            periods=[dict(period=o.period,basis=o.basis,source_dates=o.source_dates,diagnostics=o.diagnostics) for o in receipt.observations])
            for receipt in packet.reports.values()],source_version=packet.source_version,
        metadata_sha256=packet.metadata_sha256,financial_identity_guard=packet.profile!='non_financial',
        read_at=datetime.now(timezone.utc),sector=sector,industry=industry,is_fixture=packet.is_fixture,
        reconciliations=reconciliations,
        limitations=['Current source versions, not historical point-in-time vintages.',
            'Source publication dates are unqualified local strings; read time is not publication time.',
            'Consolidation is unknown unless explicitly supplied; matching unknown bases do not certify consolidation.',
            'Quarterly ROE/ROA are period returns, not annualized. TTM needs four contiguous qualified quarters.',
            'Valuation, NIM, NPL and CASA lack qualified inputs and remain unavailable.',
            'Annual and quarterly reports retain their independent source versions; differences are not reconciled by overwriting.'])
