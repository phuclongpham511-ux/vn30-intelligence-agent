import json
import pytest
from scripts import collect_financial_vn100 as queue
from src.services.financial_collector import _json
from test_financial_collector import setup, run, packet


def test_complete_contract_supports_tail_without_weakening_legacy(tmp_path):
    journal,backlog,plan=setup(tmp_path)
    ticker=plan['candidates'][0]['ticker']
    plan.update(contract='financial-collector-plan-v513',task_ids=[t['task_id'] for t in backlog['acquisition_backlog'] if t['priority']=='P0' and t['ticker']==ticker])
    plan['candidates']=plan['candidates'][:1]
    result=run(tmp_path,journal,backlog,plan)
    assert len(result['coverage']['resolved_initial_tasks'])==6


def test_entire_queue_continues_and_resume_skips_terminal_sources(tmp_path,monkeypatch):
    tickers=[f'X{i}' for i in range(7)]
    baseline=dict(as_of='2026-10-23',membership=dict(effective_date='2026-08-03'),
        companies=[dict(ticker=t,statements={k:{f:dict(count=0) for f in ('annual','quarterly')} for k in ('income','balance','cash')}) for t in tickers],
        acquisition_backlog=[dict(task_id=t+':'+f+'_'+k,ticker=t,priority='P3',family=f+'_'+k) for t in tickers for f in ('annual','quarterly') for k in ('income','balance','cash')])
    monkeypatch.setattr(queue,'build_coverage',lambda *a,**kw:baseline)
    calls=[];interrupted=[False]
    def collect(plan,backlog,*,root,**kwargs):
        path=root/'state.json';state=json.loads(path.read_text()) if path.exists() else dict(candidates={})
        for c in plan['candidates']:
            if c['ticker']=='X2' and not interrupted[0]:
                interrupted[0]=True
                raise KeyboardInterrupt()
            calls.append(c['ticker'])
            status='ACCESS_RESTRICTED' if c['ticker']=='X0' else 'IMPORTED'
            error=None
            if c['ticker']=='X1' and calls.count('X1')==1:
                status='SOURCE_UNAVAILABLE';error='TimeoutError'
            attempts=state['candidates'].get(c['id'],{}).get('queue_attempts',1)
            state['candidates'][c['id']]=dict(status=status,queue_attempts=attempts,last_result=dict(ticker=c['ticker'],status=status,error=error))
            path.write_bytes(_json(state))
    monkeypatch.setattr(queue,'run_collector',collect)
    with pytest.raises(KeyboardInterrupt):
        queue.run_queue(tmp_path/'db',tmp_path/'queue',as_of=baseline['as_of'],fetch=packet)
    result=queue.run_queue(tmp_path/'db',tmp_path/'queue',as_of=baseline['as_of'],fetch=packet,pause=lambda _:None)
    assert result['status']=='TERMINAL' and result['completed_chunks']==[0,1]
    assert calls==tickers[:5]+['X1']+tickers[5:]  # Only the transport failure retries.
    assert len(result['task_states'])==42
    queue.run_queue(tmp_path/'db',tmp_path/'queue',as_of=baseline['as_of'],fetch=packet)
    assert calls==tickers[:5]+['X1']+tickers[5:]
    with pytest.raises(ValueError,match='same journal'):
        queue.run_queue(tmp_path/'other',tmp_path/'queue',as_of=baseline['as_of'],fetch=packet)


def test_task_states_use_observations_and_keep_missing_families_partial():
    coverage=dict(companies=[dict(ticker='X',financial_data_present=True,statements=dict(
        income=dict(annual=dict(count=4,status='AVAILABLE')),
        cash=dict(quarterly=dict(count=0,status='MISSING'))))])
    tasks=[dict(task_id=f,ticker='X',family=f) for f in ('annual_income','quarterly_cash')]
    states=queue.task_states(tasks,coverage,{'X':dict(status='IMPORTED')})
    assert states['annual_income']['status']=='COMPLETED'
    assert states['quarterly_cash']['status']=='PARTIAL'
