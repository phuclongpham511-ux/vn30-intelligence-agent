"""Real saved bank-note arithmetic and company peer API acceptance, no listener."""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
from statistics import median
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.services.personal_financials import saved_research_packet, personal_projection


def validate(bundle, private, report):
    bundle=Path(bundle).resolve(strict=True);private=Path(private);report=Path(report)
    report.mkdir(parents=True,exist_ok=True);(private/'company-peers').mkdir(parents=True,exist_ok=True)
    index=json.loads((bundle/'index.json').read_text(encoding='utf-8'))
    checks=[]
    for ticker in index['reviewed_reports']:
        packet,_=saved_research_packet(bundle,ticker)
        body=personal_projection(packet,authorization_reference='task:v3-real-source-check')
        rows={r['period']:r for r in body['rows']}
        for period,row in rows.items():
            expected={}
            if row.get('demand_deposit_share') is not None:
                expected['demand_deposit_share']=row['customer_demand_deposits']/row['customer_deposits']
            if row.get('npl_classified_ratio') is not None:
                classified_npl=sum(row[f'loan_grade_{i}'] for i in (3,4,5))
                expected['npl_classified_ratio']=classified_npl/row['classified_loans']
                assert row['classified_loans'] <= row['customer_loans'], 'Classified population exceeds consolidated lending'
            if row.get('classified_loan_coverage') is not None:
                expected['classified_loan_coverage']=(row['loan_allowance_general']+row['loan_allowance_specific'])/sum(row[f'loan_grade_{i}'] for i in (3,4,5))
            prior=rows.get(str(int(period)-1))
            if row.get('roe') is not None:
                expected['roe']=row['net_profit']/((row['equity']+prior['equity'])/2)
                expected['roa']=row['net_profit']/((row['total_assets']+prior['total_assets'])/2)
            for key,value in expected.items():assert math.isclose(row[key],value,rel_tol=1e-12)
            checks.append(dict(ticker=ticker,period=period,checked=sorted(expected),status='PASS'))
    env=dict(APP_ENV='development',DATABASE_URL='sqlite://',WOOFI_PERSONAL_RESEARCH='1',
        WOOFI_PERSONAL_BIND='127.0.0.1',WOOFI_PERSONAL_CAPTURES=str(bundle),SSI_API_KEY='',SSI_API_SECRET='')
    cohorts=[]
    with patch.dict(os.environ,env):
        from main import app
        client=TestClient(app,client=('127.0.0.1',1234),base_url='http://127.0.0.1')
        for ticker in sorted(index['captures']):
            url=f'/personal-research/peers/{ticker}?period=2025&frequency=annual'
            r=client.get(url);assert r.status_code==200 and r.headers['cache-control']=='private, no-store'
            assert client.get(url,headers={'Host':'foreign.invalid'}).status_code==404
            data=r.json();(private/'company-peers'/f'{ticker}.json').write_text(json.dumps(data),encoding='utf-8')
            qualified=[]
            for key,m in data['metrics'].items():
                points=[o for o in m['observations'] if o['comparison_eligible']]
                if points:
                    values=[o['value'] for o in points]
                    assert m['distribution']==dict(count=len(values),minimum=min(values),median=median(values),maximum=max(values))
                    for o in points:
                        assert o['rank'] is None and not m['industry_ranking_qualified']
                        assert o['percentile'] is None
                    qualified.append(key)
            cohorts.append(dict(ticker=ticker,industry=data['industry']['id'],members=len(data['members']),qualified_comparison_metrics=qualified))
    with (report/'VERIFIED_METRIC_COVERAGE.csv').open(encoding='utf-8') as f:coverage=list(csv.DictReader(f))
    result=dict(contract='financial-v3-real-acceptance-v1',status='PASS',recorded_at=datetime.now(timezone.utc).isoformat(),
        supported_metric_definitions=len({r['metric_id'] for r in coverage}),
        source_verified_definitions=len({r['metric_id'] for r in coverage if int(r['SOURCE_VERIFIED'])}),
        reported_definitions=len({r['metric_id'] for r in coverage if r['metric_kind']=='reported'}),
        derived_definitions=len({r['metric_id'] for r in coverage if r['metric_kind']=='derived'}),
        original_note_checks=checks,company_peer_api_checks=cohorts,provider_requests=0,
        runtime='PENDING',browser='PENDING',transport='in-process ASGI; no listener')
    (report/'V3_REAL_ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('bundle','private','report'):p.add_argument('--'+key,required=True)
    a=p.parse_args();r=validate(a.bundle,a.private,a.report)
    print(json.dumps({k:r[k] for k in ('status','supported_metric_definitions','source_verified_definitions','reported_definitions','derived_definitions','provider_requests','runtime')}))
