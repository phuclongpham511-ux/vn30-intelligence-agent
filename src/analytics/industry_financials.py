"""Coverage-aware industry arithmetic over qualified canonical metric facts."""
from collections import defaultdict
from datetime import date
import math
from src.services.financial_intelligence import metric_unit

ADDITIVE = ('revenue','gross_profit','net_profit','profit_parent','total_assets','total_liabilities',
    'equity','cash_operating','cash_investing','cash_financing','free_cash_flow',
    'operating_income','net_interest_income','customer_loans','customer_deposits','inventory')
RATIOS = {'roe':('net_profit','average_equity'), 'roa':('net_profit','average_assets'),
    'gross_margin':('gross_profit','revenue'), 'net_margin':('net_profit','revenue'),
    'loan_deposit_ratio':('customer_loans','customer_deposits')}
MODEL_TYPES = {'non_financial':('CT','non_financial'), 'real_estate':('CT','non_financial'),
    'bank':('NH','bank'), 'securities':('CK','financial_other'), 'insurance':('BH','financial_other')}
BALANCES = {'total_assets','total_liabilities','equity','customer_loans','customer_deposits','inventory','average_assets','average_equity'}


def finite_sum(values):
    try:
        result=math.fsum(values)
        return result if math.isfinite(result) else None
    except OverflowError:
        return None


def industry_snapshot(taxonomy, observations, industry_id, *, period, frequency, membership_on:date, report_scope='consolidated'):
    industry = next((i for i in taxonomy.industries if i.id==industry_id), None)
    if industry is None:
        raise KeyError('Unknown industry')
    members = sorted(m.ticker for m in taxonomy.memberships if m.industry_id==industry_id
        and m.effective_from<=membership_on and (m.effective_to is None or membership_on<=m.effective_to))
    expected = len(members)
    indexed = defaultdict(list)
    for item in observations:
        if item.ticker in members and item.period==period and item.period_type==frequency and item.report_scope==report_scope:
            indexed[(item.ticker,item.metric_id)].append(item)

    def select(ticker, metric):
        choices = indexed.get((ticker,metric), [])
        if len(choices)>1:
            return None,'conflicting_observations'
        if not choices:
            return None,'missing_observation'
        item = choices[0]
        if item.quality_status!='QUALIFIED' or item.value is None or item.is_fixture:
            return None,'unqualified_observation'
        if (item.company_type,item.profile)!=MODEL_TYPES[industry.model]:
            return None,'incompatible_issuer_model'
        if item.unit!=metric_unit(metric) or item.currency!='VND':
            return None,'incompatible_unit'
        if not item.period_end or metric not in BALANCES and not item.period_start:
            return None,'unqualified_fiscal_boundaries'
        return item,None

    ordinary=industry.model in ('non_financial','real_estate')
    additive=[m for m in ADDITIVE if (m not in ('revenue','gross_profit','free_cash_flow','inventory') or ordinary)
        and (m not in ('operating_income','net_interest_income','customer_loans','customer_deposits') or industry.model=='bank')]
    ratios=[m for m in RATIOS if (m not in ('gross_margin','net_margin') or ordinary)
        and (m!='loan_deposit_ratio' or industry.model=='bank')]
    output = {}
    for metric in (*additive,*ratios):
        inputs = RATIOS.get(metric,(metric,))
        included,excluded = {},{}
        for ticker in members:
            selected = [select(ticker,key) for key in inputs]
            reason = next((r for _,r in selected if r),None)
            if not reason and len({i.period_end for i,_ in selected})>1:
                reason='incompatible_fiscal_intervals'
            if not reason and len({i.period_start for i,_ in selected if i.metric_id not in BALANCES})>1:
                reason='incompatible_fiscal_intervals'
            if not reason and len({i.source for i,_ in selected})>1:
                reason='incompatible_input_sources'
            if not reason and len(inputs)>1 and selected[1][0].value<=0:
                reason='nonpositive_denominator'
            if not reason and len(inputs)>1 and not math.isfinite(selected[0][0].value/selected[1][0].value):
                reason='nonfinite_peer_result'
            if reason:
                excluded[ticker]=reason
            else:
                included[ticker]=[i for i,_ in selected]
        # Never combine different fiscal year ends or different flow intervals.
        intervals={(items[0].period_start if inputs[0] not in BALANCES else None,items[0].period_end) for items in included.values()}
        if len(intervals)>1:
            excluded.update({t:'incompatible_fiscal_intervals' for t in included});included={}
        count=len(included)
        numerator=finite_sum(items[0].value for items in included.values()) if count else None
        denominator=finite_sum(items[1].value for items in included.values()) if count and len(inputs)>1 else None
        value=numerator/denominator if numerator is not None and denominator and denominator>0 else numerator if len(inputs)==1 else None
        if value is not None and not math.isfinite(value):
            value=None
        points={t:items[0].value/items[1].value if len(inputs)>1 else items[0].value for t,items in included.items()}
        peers=[]
        for ticker,point in sorted(points.items(),key=lambda pair:(-pair[1],pair[0])):
            less=sum(v<point for v in points.values());equal=sum(v==point for v in points.values())
            contribution=point/numerator if len(inputs)==1 and numerator and numerator>0 else None
            if contribution is not None and not math.isfinite(contribution):
                contribution=None
            peers.append(dict(ticker=ticker,value=point,rank=1+sum(v>point for v in points.values()),
                percentile=(less+.5*equal)/count,
                contribution=contribution,
                sources=sorted({i.source for i in included[ticker]}),revisions=[i.revision for i in included[ticker]]))
        output[metric]=dict(value=value,unit=metric_unit(metric),
            status='UNAVAILABLE' if value is None else 'COMPLETE' if count==expected else 'PARTIAL',
            included_companies=count,expected_companies=expected,coverage=count/expected if expected else None,
            method=f'sum({inputs[0]}) / sum({inputs[1]}) on the same companies' if len(inputs)>1 else 'sum of observed compatible companies',
            excluded=excluded,peers=peers,
            period_start=str(next(iter(intervals))[0]) if len(intervals)==1 and next(iter(intervals))[0] else None,
            period_end=str(next(iter(intervals))[1]) if len(intervals)==1 else None)
    # Share/vintage-qualified price joins are not available in the current engine.
    for metric in ('pe','pb'):
        output[metric]=dict(value=None,unit='multiple',status='UNAVAILABLE',included_companies=0,
            expected_companies=expected,coverage=0 if expected else None,peers=[],
            excluded={t:'unqualified_price_share_and_earnings_basis' for t in members},
            method='Requires a matched capitalization/earnings or capitalization/equity cohort; company multiples are never averaged.')
    represented={t for metric in output.values() for t in members if t not in metric['excluded']}
    return dict(contract='industry-financials-v1',industry=industry.model_dump(),
        taxonomy=dict(name=taxonomy.name,version=taxonomy.version,source_reference=taxonomy.source_reference),
        period=period,frequency=frequency,membership_on=membership_on.isoformat(),report_scope=report_scope,
        expected_companies=expected,represented_companies=len(represented),
        missing_tickers=sorted(set(members)-represented),metrics=output,point_in_time_qualified=False,
        limitations=['Totals describe the classified observed cohort, not the entire market.',
            'Each ratio uses the same companies in its numerator and denominator. Coverage is metric-specific.',
            'Rank 1 is the largest numerical value, not an investment recommendation. Percentile uses empirical midrank.',
            'Membership is effective-dated; its historical publication vintage is not certified.',
            'Bank loan/deposit ratio is an accounting comparison, not regulatory LDR.'])
