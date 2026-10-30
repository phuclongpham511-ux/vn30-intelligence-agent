"""One resumable VN100 acquisition queue, through the existing bounded collector."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from scripts.ingest_financial_intelligence import private_destination
from src.providers.vnstock import sdk
from src.providers.vnstock.financial_packet import fetch_packet
from src.services.financial_batch import _atomic_bytes
from src.services.financial_collector import _json, _sha, run_collector
from src.services.financial_coverage import build_coverage
from src.services.financial_journal import MetricJournal


def task_states(tasks, coverage, receipts):
    companies={c['ticker']:c for c in coverage['companies']}
    result={}
    for task in tasks:
        frequency,kind=task['family'].split('_',1)
        cell=companies[task['ticker']]['statements'][kind][frequency]
        receipt=receipts[task['ticker']]
        status=('COMPLETED' if cell['count'] and cell.get('status')=='AVAILABLE' else
            'PARTIAL' if cell['count'] or companies[task['ticker']].get('financial_data_present') else
            'ACCESS_RESTRICTED' if receipt['status']=='ACCESS_RESTRICTED' else
            'VALIDATION_FAILED' if receipt['status']=='EXTRACTION_FAILURE' else
            'RETRY_EXHAUSTED' if receipt.get('queue_attempts',1)>=2 else 'SOURCE_UNAVAILABLE')
        result[task['task_id']]=dict(ticker=task['ticker'],family=task['family'],status=status,
            periods=cell['count'],source_status=receipt['status'],error=receipt.get('error'))
    return result


def run_queue(journal_path, root, *, as_of, fetch, industry=None, private_root=None, pause=time.sleep):
    """Pin the full initial queue; terminal source receipts are never fetched again."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    checkpoint = root / 'queue.json'
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding='utf-8'))
        if state['journal'] != str(Path(journal_path).resolve()) or state['as_of'] != as_of:
            raise ValueError('Resume must use the same journal and date')
        before = json.loads((root / 'before.json').read_text(encoding='utf-8'))
        if state['baseline_sha256'] != _sha(_json(before)):
            raise ValueError('Queue baseline fingerprint differs')
    else:
        before = build_coverage(journal_path, as_of=as_of, industry_snapshot=industry)
        if before['membership']['effective_date'] != '2026-08-03':
            raise ValueError('This queue requires the preserved August 2026 snapshot')
        tasks = [t for t in before['acquisition_backlog'] if t['priority'] in ('P0', 'P3')
            and t['family'] in {f'{f}_{k}' for f in ('annual','quarterly') for k in ('income','balance','cash')}
            and next(c for c in before['companies'] if c['ticker']==t['ticker'])['statements'][t['family'].split('_',1)[1]][t['family'].split('_',1)[0]]['count']==0]
        state = dict(contract='financial-queue-v513', journal=str(Path(journal_path).resolve()),
            as_of=as_of, baseline_sha256=_sha(_json(before)), tasks=tasks,
            tickers=sorted({t['ticker'] for t in tasks}), completed_chunks=[], status='RUNNING')
        _atomic_bytes(root/'before.json', _json(before))
        _atomic_bytes(checkpoint, _json(state))
    for offset in range(0,len(state['tickers']),5):
        number = offset//5
        if number in state['completed_chunks']:
            continue
        group = state['tickers'][offset:offset+5]
        chunk = root / f'batch-{number+1:02}'
        chunk.mkdir(exist_ok=True)
        plan_path = chunk/'plan.json'
        if plan_path.exists():
            plan=json.loads(plan_path.read_text(encoding='utf-8'))
        else:
            candidates=[dict(id=t.lower()+'-vci',ticker=t,issuer=t,kind='vci',
                url=f'https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{t}/financial-statement',
                discovery_url='https://vnstocks.com/docs/huong-dan/bao-cao-tai-chinh',
                title='Bounded installed VCI Finance methods',reporting_period='All periods exposed by the approved SDK path',
                document_type='sdk_canonical_capture',access='public_no_login',published_date=None,
                access_notes='Serial six-second pacing; private research; public rights unreviewed') for t in group]
            plan=dict(contract='financial-collector-plan-v513',as_of=as_of,backlog_sha256=_sha(_json(before)),
                task_ids=[t['task_id'] for t in state['tasks'] if t['ticker'] in group], candidates=candidates)
            _atomic_bytes(plan_path,_json(plan))
        prior=json.loads((chunk/'state.json').read_text(encoding='utf-8'))['candidates'] if (chunk/'state.json').exists() else {}
        pending=[c for c in plan['candidates'] if prior.get(c['id'],{}).get('status') in (None,'ACQUIRING','INTERRUPTED')
            and prior.get(c['id'],{}).get('queue_attempts',1)<2]
        if pending:
            print('CHUNK',number+1,'PENDING',[c['ticker'] for c in pending],flush=True)
            run_collector(dict(plan,candidates=pending),before,journal_path=journal_path,root=chunk,
                industry_snapshot=industry,fetch_packet=fetch,private_root=private_root)
        receipts=json.loads((chunk/'state.json').read_text(encoding='utf-8'))['candidates']
        transient={'TimeoutError','ConnectionError','ConnectTimeout','ReadTimeout','ConnectError','ReadError','RemoteProtocolError'}
        retry=[c for c in plan['candidates'] if receipts[c['id']]['last_result'].get('error') in transient
            and receipts[c['id']].get('queue_attempts',1)<2]
        if retry:
            # Persist the retry budget before a source request, including interruption.
            for c in retry:receipts[c['id']]['queue_attempts']=2
            _atomic_bytes(chunk/'state.json',_json(dict(contract='financial-collector-state-v57',candidates=receipts)))
            pause(12)
            run_collector(dict(plan,candidates=retry),before,journal_path=journal_path,root=chunk,
                industry_snapshot=industry,fetch_packet=fetch,private_root=private_root)
            receipts=json.loads((chunk/'state.json').read_text(encoding='utf-8'))['candidates']
        rows=[dict(receipts[c['id']]['last_result'],queue_attempts=receipts[c['id']].get('queue_attempts',1)) for c in plan['candidates']]
        _atomic_bytes(chunk/'result.json',_json(rows))
        coverage=build_coverage(journal_path,as_of=as_of,industry_snapshot=industry)
        _atomic_bytes(chunk/'coverage.json',_json(coverage))
        own_tasks=[t for t in state['tasks'] if t['ticker'] in group]
        state.setdefault('task_states',{}).update(task_states(own_tasks,coverage,{r['ticker']:r for r in rows}))
        state['completed_chunks'].append(number)
        _atomic_bytes(checkpoint,_json(state))
        print('CHECKPOINT',number+1,'/',(len(state['tickers'])+4)//5,flush=True)
    after=build_coverage(journal_path,as_of=as_of,industry_snapshot=industry)
    _atomic_bytes(root/'after.json',_json(after))
    state['status']='TERMINAL'
    _atomic_bytes(checkpoint,_json(state))
    return state


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal',required=True)
    parser.add_argument('--root',required=True)
    parser.add_argument('--as-of',default='2026-10-23')
    parser.add_argument('--industry-snapshot')
    args=parser.parse_args(argv)
    journal=private_destination(args.journal);root=private_destination(args.root)
    if not journal.is_file():parser.error('Existing financial journal required')
    industry=json.loads(private_destination(args.industry_snapshot).read_text(encoding='utf-8')) if args.industry_snapshot else None
    root.mkdir(parents=True,exist_ok=True)
    if not (root/'safety.json').exists():
        saved=root/'before.sqlite';restored=root/'restore-test.sqlite'
        j=MetricJournal(journal,readonly=True)
        with j.connect() as db:
            if db.execute('pragma integrity_check').fetchone()[0]!='ok':raise ValueError('Journal integrity failed')
        if not saved.exists():j.backup(saved)
        if not restored.exists():MetricJournal(saved,readonly=True).backup(restored)
        with MetricJournal(saved,readonly=True).connect() as db:
            db.execute('ATTACH DATABASE ? AS restored',(str(restored.resolve()),))
            for table in ('financial_capture','financial_statement','financial_selection','financial_metric'):
                for a,b in [('main','restored'),('restored','main')]:
                    if db.execute(f'SELECT count(*) FROM (SELECT * FROM {a}.{table} EXCEPT SELECT * FROM {b}.{table})').fetchone()[0]:raise ValueError('Restore differs')
        files=[p for p in Path('.local').rglob('*') if p.is_file() and not p.resolve().is_relative_to(root.resolve()) and p.resolve()!=journal.resolve()]
        files += [Path(p) for p in ('CONTEXT.md','frontend/app/components/stock/FinancialAnalysisPanel.tsx','frontend/app/components/stock/FinancialResearchCharts.tsx','frontend/next-env.d.ts','docs/FINANCIAL_DATA_INFRASTRUCTURE_FEASIBILITY_2026_10_22.md') if Path(p).is_file()]
        _atomic_bytes(root/'preservation.json',_json({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}))
        _atomic_bytes(root/'safety.json',_json(dict(backup=str(saved),restore=str(restored),status='VERIFIED')))
    def acquire(ticker):
        print('ACQUIRE',ticker,flush=True)
        try:return fetch_packet(ticker,sdk,request_pause_seconds=6)
        except SystemExit as exc:raise RuntimeError('SDK stopped; no automatic access retry') from exc
    result=run_queue(journal,root,as_of=args.as_of,fetch=acquire,industry=industry)
    print('QUEUE',result['status'],len(result['tickers']),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
