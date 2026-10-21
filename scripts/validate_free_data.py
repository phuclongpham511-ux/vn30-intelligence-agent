"""Offline real-source API/industry/dividend contracts, never runtime startup."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from scripts.validate_financial_activation import validate,require
from src.services.personal_financials import saved_packet,personal_projection
from src.providers.cafef_statements import cafef_packet,SOURCE


def validate_free(captures,report,private,*,probe_directory=None):
    root=Path(captures).resolve(strict=True);report=Path(report);private=Path(private)
    report.mkdir(parents=True,exist_ok=True);private.mkdir(parents=True,exist_ok=True)
    results={}
    for selection in ('preferred','provider'):
        results[selection]=validate(root,report/selection,private/selection,evidence=selection)
    index=json.loads((root/'index.json').read_text(encoding='utf-8'))
    env=dict(APP_ENV='development',DATABASE_URL='sqlite://',WOOFI_PERSONAL_RESEARCH='1',
        WOOFI_PERSONAL_BIND='127.0.0.1',WOOFI_PERSONAL_CAPTURES=str(root),
        WOOFI_FINANCIAL_TAXONOMY='',WOOFI_FINANCIAL_JOURNAL='',SSI_API_KEY='',SSI_API_SECRET='')
    summaries=[];dividends=[]
    with patch.dict(os.environ,env):
        from main import app
        client=TestClient(app,client=('127.0.0.1',1234),base_url='http://127.0.0.1')
        directory=client.get('/personal-research/industries')
        require(directory.status_code==200,'Private observed classification directory failed')
        data=directory.json();(private/'industry-directory.json').write_text(json.dumps(data),encoding='utf-8')
        (private/'industries').mkdir(exist_ok=True)
        for category in data['industries']:
            response=client.get(f"/personal-research/industries/{category['id']}?period=2025&frequency=annual")
            require(response.status_code==200 and response.headers['cache-control']=='private, no-store','Industry observations failed')
            body=response.json()
            require(body['sector_totals'] is None and body['historical_aggregation_enabled'] is False,'Observed classifications cannot enable historical totals')
            for metric in body['metrics'].values():
                require(metric['covered_companies']+len(metric['missing'])==len(body['members']),'Industry coverage denominator changed')
                for point in metric['observations']:
                    require(math.isfinite(point['value']),'Industry value is not finite')
                    if not point['verification']['ACCOUNTING_VERIFIED']:
                        require(point['rank'] is None and point['percentile'] is None,'Unqualified company was ranked')
            (private/'industries'/f"{category['id']}.json").write_text(json.dumps(body),encoding='utf-8')
            summaries.append(dict(code=category['id'],members=len(body['members']),
                saved_companies=category['saved_companies'],
                metrics={k:dict(covered=v['covered_companies'],comparable=v['comparable_companies']) for k,v in body['metrics'].items()}))
        (private/'dividends').mkdir(exist_ok=True)
        for ticker in sorted(index['captures']):
            response=client.get('/personal-research/dividends/'+ticker)
            require(response.status_code==200 and response.headers['cache-control']=='private, no-store','Dividend reader failed')
            body=response.json()
            require(body['coverage']=='INCOMPLETE' and body['public_display_eligible'] is False,'Dividend coverage promoted')
            require(all(r['effective_date'] is None and r['announced_at'] is None for r in body['items']),'Missing date precision invented')
            (private/'dividends'/f'{ticker}.json').write_text(json.dumps(body),encoding='utf-8')
            dividends.append(dict(ticker=ticker,events=len(body['items'])))
        for route in ('/personal-research/industries','/personal-research/industries/'+data['industries'][0]['id']+'?period=2025','/personal-research/dividends/'+next(iter(index['captures']))):
            require(client.get(route,headers={'Host':'foreign.invalid'}).status_code==404,'Private route allowed foreign Host')
    # Independent arithmetic checks against the reviewed original numbers, not
    # a second production financial engine or a provider ratio import.
    calculations=[]
    for ticker in index.get('reviewed_reports',{}):
        packet,_=saved_packet(root,ticker,collection='reviewed_reports')
        response=personal_projection(packet,authorization_reference='task:real-source-validation')
        for row in response['rows']:
            comparisons={}
            if row.get('net_margin') is not None:comparisons['net_margin']=row['net_profit']/row['revenue']
            if row.get('gross_margin') is not None:comparisons['gross_margin']=row['gross_profit']/row['revenue']
            if row.get('free_cash_flow') is not None:comparisons['free_cash_flow']=row['cash_operating']+row['capex_signed']
            if row.get('loan_deposit_ratio') is not None:comparisons['loan_deposit_ratio']=row['customer_loans']/row['customer_deposits']
            if row.get('current_ratio') is not None:comparisons['current_ratio']=row['current_assets']/row['current_liabilities']
            if row.get('quick_ratio') is not None:comparisons['quick_ratio']=(row['current_assets']-row['inventory'])/row['current_liabilities']
            if row.get('debt_equity') is not None:comparisons['debt_equity']=(row['short_debt']+row['long_debt'])/row['equity']
            if row.get('demand_deposit_share') is not None:comparisons['demand_deposit_share']=row['customer_demand_deposits']/row['customer_deposits']
            if row.get('npl_classified_ratio') is not None:comparisons['npl_classified_ratio']=sum(row[f'loan_grade_{i}'] for i in (3,4,5))/row['classified_loans']
            if row.get('classified_loan_coverage') is not None:comparisons['classified_loan_coverage']=(row['loan_allowance_general']+row['loan_allowance_specific'])/sum(row[f'loan_grade_{i}'] for i in (3,4,5))
            if row.get('roe') is not None:
                prior=next(r for r in response['rows'] if r['period']==str(int(row['period'])-1))
                comparisons['roe']=row['net_profit']/((row['equity']+prior['equity'])/2)
                comparisons['roa']=row['net_profit']/((row['total_assets']+prior['total_assets'])/2)
            for key,value in comparisons.items():require(math.isclose(row[key],value,rel_tol=1e-12,abs_tol=1e-9),'Original report calculation mismatch')
            calculations.append(dict(ticker=ticker,period=row['period'],checked=sorted(comparisons),status='PASS'))
    cross=[]
    if probe_directory:
        probes=Path(probe_directory)
        # The FPT amount scale was audited across independently saved endpoints.
        # Numeric agreement does not transfer consolidation or currency metadata.
        reports={}
        for kind in ('income','balance'):
            name='cafef-fpt-'+kind;r=json.loads((probes/(name+'.receipt.json')).read_text(encoding='utf-8'))
            r['body']=(probes/name).read_bytes().decode('utf-8');r['body_sha256']=r.pop('sha256');reports[kind]=r
        capture=dict(contract='cafef-saved-annual-v1',source=SOURCE,ticker='FPT',company_type='CT',observed_at=reports['income']['observed_at'],reports=reports)
        comparison=cafef_packet(capture);original,_=saved_packet(root,'FPT')
        for kind,receipt in comparison.reports.items():
            originals={o.period:o for o in original.reports[kind].observations}
            for obs in receipt.observations:
                for field,value in obs.fields.items():
                    old=originals.get(obs.period)
                    counterpart=old.fields.get(field) if old else None
                    if value is None or counterpart is None:continue
                    delta=abs(value-counterpart)
                    cross.append(dict(period=obs.period,field=field,within_thousand_vnd=delta<=1000,
                        absolute_difference_vnd=delta,scope_transferred=False,original_units_transferred=False))
    result=dict(contract='free-data-application-validation-v2',status='PASS',recorded_at=datetime.now(timezone.utc).isoformat(),
        stock_api_projections=sum(len(r['projections']) for r in results.values()),provider_history_preserved=True,
        observed_industry_categories=len(summaries),observed_memberships=sum(i['members'] for i in summaries),
        industry=summaries,dividends=dividends,calculation_checks=calculations,
        cafef_fpt_cross_checks=cross,provider_requests=0,application_database_access=False,
        runtime='PENDING',browser='PENDING',transport='in-process ASGI; no listener')
    (report/'FREE_DATA_APPLICATION_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('captures','report','private'):p.add_argument('--'+name,required=True)
    p.add_argument('--probe-directory');a=p.parse_args()
    r=validate_free(a.captures,a.report,a.private,probe_directory=a.probe_directory)
    print(json.dumps({k:r[k] for k in ('status','stock_api_projections','observed_industry_categories','observed_memberships','dividends','provider_requests','runtime')}))
