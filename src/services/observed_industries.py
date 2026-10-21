"""Private observed-membership research, distinct from historical sector totals."""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
from src.providers.reviewed_reports import pinned_file
from src.services.personal_financials import saved_research_packet, personal_projection
from src.services.financial_intelligence import metric_unit

METRICS = ('revenue','gross_profit','net_profit','profit_parent','total_assets','total_liabilities',
    'equity','operating_income','net_interest_income','customer_loans','customer_deposits',
    'cash_operating','cash_investing','cash_financing','free_cash_flow','inventory',
    'gross_margin','net_margin','roe','roa','current_ratio','quick_ratio','debt_equity','loan_deposit_ratio')


def membership_evidence(directory):
    root=Path(directory).resolve(strict=True)
    if (root/'index.json').stat().st_size > 2_000_000:raise ValueError('Oversized source index')
    index=json.loads((root/'index.json').read_text(encoding='utf-8'))
    entry=index.get('observed_memberships')
    if not entry:raise FileNotFoundError('Observed memberships not configured')
    review=json.loads(pinned_file(root,entry['file'],entry['sha256'],2_000_000))
    if (review.get('contract')!='industry-membership-review-v1'
            or review.get('source')!='SSI:FastConnect:v3:SecuritiesInfo'
            or not isinstance(review.get('entries'),list) or len(review['entries'])>2000):
        raise ValueError('Invalid observed classification review')
    observed=review['receipt']['fetched_at']
    if datetime.fromisoformat(observed).utcoffset() is None:raise ValueError('Missing classification receipt time')
    seen=set()
    for item in review['entries']:
        ticker=item['ticker'];code=item['provider_code']
        if (not re.fullmatch(r'[A-Z0-9]{1,20}',ticker) or ticker in seen
                or item.get('source_status')!='OBSERVED_PAIR_UNQUALIFIED'
                or item.get('observed_at')!=observed or item.get('exchange')!='HOSE'
                or not isinstance(code,str) or not re.fullmatch(r'[0-9]{1,16}',code)
                or not item.get('provider_label')):
            raise ValueError('Ambiguous observed membership')
        seen.add(ticker)
    return index,review


def observed_directory(directory):
    index,review=membership_evidence(directory)
    labels={}
    for item in review['entries']:
        code,label=item['provider_code'],item['provider_label']
        if code in labels and labels[code]!=label:raise ValueError('Conflicting category labels')
        labels[code]=label
    counts=Counter(i['provider_code'] for i in review['entries'])
    available=Counter(i['provider_code'] for i in review['entries'] if i['ticker'] in index['captures'])
    return dict(contract='observed-industry-directory-v1',display_scope='personal_research',
        observed_at=review['receipt']['fetched_at'],source=review['source'],
        taxonomy_family='ICB (SSI provider labels)',taxonomy_version=None,taxonomy_level=None,
        industries=[dict(id=code,label=labels[code],members=counts[code],saved_companies=available[code]) for code in sorted(labels,key=lambda c:(-available[c],labels[c]))],
        historical_aggregation_enabled=False,public_display_eligible=False)


def observed_peers(directory, code, *, period, frequency='annual'):
    if not re.fullmatch(r'\d{1,16}',code) or not re.fullmatch(r'\d{4}' if frequency=='annual' else r'\d{4}-Q[1-4]',period):
        raise ValueError('Invalid observed industry request')
    index,review=membership_evidence(directory)
    members=sorted(i['ticker'] for i in review['entries'] if i['provider_code']==code)
    if not members:raise KeyError('Unobserved category')
    label=next(i['provider_label'] for i in review['entries'] if i['provider_code']==code)
    output={key:dict(unit=metric_unit(key),observations=[],missing={},comparable_companies=0) for key in METRICS}
    for ticker in members:
        if ticker not in index['captures']:
            for metric in output.values():metric['missing'][ticker]='no_saved_financial_evidence'
            continue
        packet,digest=saved_research_packet(directory,ticker,frequency=frequency)
        response=personal_projection(packet,frequency=frequency,limit=20,authorization_reference='task:private-observed-peers:'+digest)
        row=next((r for r in response['rows'] if r['period']==period),None)
        states=next((p['metrics'] for p in response['verification']['periods'] if p['period']==period),{})
        from src.analytics.financial_engine import financial_engine
        raw=next((r for r in financial_engine(packet,frequency=frequency,limit=20).rows if r['period']==period),{})
        for key,metric in output.items():
            state=states.get(key,{})
            if row is None or not state.get('display_eligible'):
                metric['missing'][ticker]='metric_unavailable_for_selected_period'
                continue
            refs=raw['calculations'][key]['inputs']
            scopes={r.get('consolidation') for r in refs}
            signature=sorted({(r['statement'],r['period'],(r.get('source_context')or{}).get('period_start'),(r.get('source_context')or{}).get('period_end')) for r in refs},key=str)
            metric['observations'].append(dict(ticker=ticker,value=row[key],source=packet.source,
                scope=next(iter(scopes)) if len(scopes)==1 else None,
                verification=state['dimensions'],rank=None,percentile=None,
                record_hashes=sorted({r['source_context']['record_sha256'] for r in refs}),
                # Internal comparison key is removed before responding.
                compatibility=[packet.profile,signature]))
    for metric in output.values():
        candidates=[o for o in metric['observations'] if o['verification']['ACCOUNTING_VERIFIED']]
        # No cross-model/basis/period rankings. Unknown membership history is
        # never used for sector totals, historical cohorts or backtests.
        compatible=len({json.dumps([o['compatibility'],o['scope']]) for o in candidates})==1
        if len(candidates)>=2 and compatible:
            points=[o['value'] for o in candidates]
            for o in candidates:
                o['rank']=1+sum(v>o['value'] for v in points)
                o['percentile']=(sum(v<o['value'] for v in points)+.5*sum(v==o['value'] for v in points))/len(points)
            metric['comparable_companies']=len(candidates)
        for o in metric['observations']:o.pop('compatibility')
        metric['covered_companies']=len(metric['observations'])
        metric['expected_companies']=len(members)
    return dict(contract='observed-industry-peers-v1',display_scope='personal_research',
        industry=dict(id=code,label=label),period=period,frequency=frequency,members=members,
        observed_at=review['receipt']['fetched_at'],classification_source=review['source'],
        taxonomy_version=None,taxonomy_level=None,classification_effective_at=None,
        historical_aggregation_enabled=False,sector_totals=None,public_display_eligible=False,metrics=output)
