"""Pin existing real captures for the local research server; no acquisition.

python -m scripts.prepare_personal_financials NEW_PRIVATE_FOLDER CAPTURE.json ...
No overwrite, SQL, provider request, ticker hardcoding or public artifact output.
"""
import argparse
import hashlib
import json
from pathlib import Path
from src.services.personal_financials import saved_packet, personal_projection

def prepare(destination, captures):
    destination.mkdir(parents=True, exist_ok=False)
    index = {'contract':'personal-saved-captures-v1', 'captures':{}}
    for path in captures:
        data = path.read_bytes()
        raw = json.loads(data)
        ticker = raw['ticker']
        import re
        if not re.fullmatch(r'[A-Z0-9]{1,20}', ticker) or ticker in index['captures']:
            raise ValueError('Invalid or duplicate capture owner')
        name = ticker + '.json'
        (destination / name).write_bytes(data)
        index['captures'][ticker] = dict(file=name, sha256=hashlib.sha256(data).hexdigest())
    (destination/'index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
    results=[]
    for ticker in index['captures']:
        packet, digest = saved_packet(destination, ticker)
        views={frequency:personal_projection(packet,frequency=frequency,authorization_reference='task:financial-v6:'+digest)
               for frequency in ('annual','quarterly','ttm')}
        for frequency,view in views.items():
            (destination/f'{ticker}-{frequency}-personal.json').write_text(json.dumps(view,ensure_ascii=False,indent=2),encoding='utf-8')
        results.append(dict(ticker=ticker,profile=packet.profile,capture_sha256=digest,
            source_version=packet.source_version,
            statements={kind:dict(status=r.status, annual=sum(o.frequency=='annual' for o in r.observations),
                quarterly=sum(o.frequency=='quarterly' for o in r.observations),
                unknown_basis=sum(o.consolidation is None for o in r.observations),
                missing_original_unit=sum(o.source_context.original_unit is None for o in r.observations),
                periods=[o.period for o in r.observations]) for kind,r in packet.reports.items()},
            views={f:dict(periods=len(v['rows']),reported_statement_values=sum(i['value'] is not None for s in v['statements'].values() for p in s['periods'] for i in p['items']),
                chart_values=sum(x is not None for p in v['research_panels'] for row in p['rows'] for x in row['values'].values())) for f,v in views.items()}))
    (destination/'COVERAGE.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    parser.add_argument('captures',type=Path,nargs='+')
    args=parser.parse_args()
    result=prepare(args.destination,args.captures)
    print(json.dumps({'tickers':[r['ticker'] for r in result], 'provider_requests':0}))
