"""Restart Manager response fixtures; no canonical service/database is touched."""
import ctypes
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts.windows import runtime_supervisor as s


pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows Restart Manager ABI')


class Call:
    def __init__(self, function):
        self.function = function

    def __call__(self, *args):
        return self.function(*args)


class RestartManager:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.ended = 0
        self.RmStartSession = Call(lambda *args: 0)
        self.RmRegisterResources = Call(lambda *args: 0)
        self.RmEndSession = Call(self.end)
        self.RmGetList = Call(self.get)

    def end(self, *args):
        self.ended += 1
        return 0

    def get(self, session, needed, count, entries, reason):
        capacity = count._obj.value
        response = next(self.responses)
        self.calls.append(capacity)
        needed._obj.value = response['needed']
        count._obj.value = response.get('count', 0)
        for index, pid in enumerate(response.get('pids', [])):
            entries[index].process.pid = pid
            entries[index].process.started.dwLowDateTime = 1
        return response['code']


def install(monkeypatch, tmp_path, responses):
    path = tmp_path/'fixture.ingestion.lock'
    path.write_bytes(b'\0')
    api = RestartManager(responses)
    original = ctypes.WinDLL
    monkeypatch.setattr(ctypes, 'WinDLL', lambda name, *a, **kw:
                        api if name == 'rstrtmgr' else original(name, *a, **kw))
    monkeypatch.setattr(s, '_verify_lock_owner', lambda *args: None, raising=False)
    sleeps = []
    monkeypatch.setattr(s.time, 'sleep', sleeps.append)
    return path, api, sleeps


def test_inventory_grows_between_calls_then_stabilizes(tmp_path, monkeypatch):
    path, api, sleeps = install(monkeypatch, tmp_path, [
        {'code':234, 'needed':1},
        {'code':234, 'needed':2},
        {'code':0, 'needed':2, 'count':2, 'pids':[101,102]},
    ])
    assert s.lock_owners(path) == [101,102]
    assert api.calls == [0,1,2]
    assert sleeps and all(delay > 0 for delay in sleeps)
    assert api.ended == 1


@pytest.mark.parametrize('responses,capacities,owners', [
    ([{'code':0,'needed':0}], [0], []),
    ([{'code':234,'needed':1},{'code':0,'needed':1,'count':1,'pids':[101]}], [0,1], [101]),
    ([{'code':234,'needed':2},{'code':0,'needed':1,'count':1,'pids':[101]}], [0,2], [101]),
    ([{'code':234,'needed':1},{'code':0,'needed':0,'count':0}], [0,1], []),
    ([{'code':234,'needed':1},{'code':234,'needed':2},{'code':234,'needed':3},
      {'code':0,'needed':2,'count':2,'pids':[101,102]}], [0,1,2,3], [101,102]),
])
def test_complete_stable_and_shrinking_snapshots(tmp_path,monkeypatch,responses,capacities,owners):
    path,api,sleeps=install(monkeypatch,tmp_path,responses)
    verified=[]
    monkeypatch.setattr(s,'_verify_lock_owner',lambda owner:verified.append(owner.pid))
    assert s.lock_owners(path)==owners
    assert verified==owners and api.calls==capacities and api.ended==1
    assert len(sleeps)==len(capacities)-1 and sum(sleeps)<=.35+1e-9


def test_persistent_growth_exhausts_fixed_budget_without_empty_inventory(tmp_path,monkeypatch):
    path,api,sleeps=install(monkeypatch,tmp_path,[{'code':234,'needed':n} for n in (1,2,3,4)])
    with pytest.raises(s.InventoryUnverified,match='retry_exhausted') as error:
        s.lock_owners(path)
    assert api.calls==[0,1,2,3] and sleeps==[.05,.1,.2] and api.ended==1
    diagnostic=json.loads(str(error.value).split(' ',1)[1])
    assert diagnostic['code']==234 and len(diagnostic['responses'])==4
    assert diagnostic['responses'][-1]['needed']==4
    assert all(row['utc'] for row in diagnostic['responses'])
    assert str(path) not in str(error.value)


@pytest.mark.parametrize('code',[5,6,14,29,121,160,1223])
@pytest.mark.parametrize('stage',['size','fill'])
def test_native_failure_keeps_exact_code_and_never_returns_partial_owners(tmp_path,monkeypatch,code,stage):
    responses=([{'code':234,'needed':1}] if stage=='fill' else [])+[{'code':code,'needed':0}]
    path,api,_=install(monkeypatch,tmp_path,responses)
    with pytest.raises(s.InventoryUnverified,match='get_list') as error:s.lock_owners(path)
    assert f'"code":{code}' in str(error.value) and api.ended==1


@pytest.mark.parametrize('stage',['start','register'])
def test_session_setup_error_reports_code_and_releases_only_started_session(tmp_path,monkeypatch,stage):
    path,api,_=install(monkeypatch,tmp_path,[])
    setattr(api,'RmStartSession' if stage=='start' else 'RmRegisterResources',Call(lambda *a:5))
    with pytest.raises(s.InventoryUnverified,match=stage):s.lock_owners(path)
    assert api.calls==[] and api.ended==(0 if stage=='start' else 1)


@pytest.mark.parametrize('primary_error',[False,True])
def test_cleanup_failure_is_not_success_and_does_not_mask_original_error(tmp_path,monkeypatch,primary_error):
    path,api,_=install(monkeypatch,tmp_path,[{'code':121 if primary_error else 0,'needed':0}])
    api.RmEndSession=Call(lambda *a:6)
    with pytest.raises(s.InventoryUnverified,match='get_list' if primary_error else 'end'):
        s.lock_owners(path)


@pytest.mark.parametrize('responses,stage',[
    ([{'code':234,'needed':4097}], 'allocation_limit'),
    ([{'code':234,'needed':0}], 'invalid_size'),
    ([{'code':234,'needed':1},{'code':234,'needed':1}], 'invalid_size'),
    ([{'code':0,'needed':1,'count':0}], 'invalid_success'),
    ([{'code':234,'needed':1},{'code':0,'needed':1,'count':2}], 'invalid_success'),
    ([{'code':234,'needed':1},{'code':0,'needed':2,'count':1,'pids':[101]}], 'invalid_success'),
    ([{'code':234,'needed':1},{'code':0,'needed':1,'count':1,'pids':[0]}], 'invalid_owner'),
    ([{'code':234,'needed':2},{'code':0,'needed':2,'count':2,'pids':[101,101]}], 'invalid_owner'),
])
def test_invalid_native_sizes_and_owners_fail_closed(tmp_path,monkeypatch,responses,stage):
    path,api,_=install(monkeypatch,tmp_path,responses)
    with pytest.raises(s.InventoryUnverified,match=stage):s.lock_owners(path)
    assert api.ended==1


def test_unknown_or_exited_identity_cannot_be_dropped_from_inventory(tmp_path,monkeypatch):
    path,api,_=install(monkeypatch,tmp_path,[{'code':234,'needed':1},
        {'code':0,'needed':1,'count':1,'pids':[101]}])
    def unknown(owner):raise s.inventory_error('owner_open',5,pid=owner.pid)
    monkeypatch.setattr(s,'_verify_lock_owner',unknown)
    with pytest.raises(s.InventoryUnverified,match='owner_open'):s.lock_owners(path)
    assert api.ended==1


@pytest.mark.parametrize('operation',['launch','stop','status'])
def test_unverified_inventory_never_authorizes_control_or_success(tmp_path,monkeypatch,operation):
    cfg={'canonical_sha':'fixture','source_checkout':str(tmp_path),'product_database':str(tmp_path/'fixture.db'),
         'backend_port':18000,'frontend_port':13000}
    (tmp_path/'config').mkdir();s.atomic(tmp_path/'config/runtime.json',cfg)
    driver=s.Windows(tmp_path,'pwsh',s.bind(cfg),lambda *a,**k:None)
    monkeypatch.setattr(driver,'validate',lambda:cfg)
    monkeypatch.setattr(driver,'workers',lambda:[])
    def unknown(path):raise s.inventory_error('retry_exhausted',234)
    monkeypatch.setattr(s,'lock_owners',unknown)
    monkeypatch.setattr(s,'ps',lambda *a,**k:pytest.fail('No process launch is permitted'))
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k:pytest.fail('No process signal is permitted'))
    if operation=='launch':
        action=lambda:driver.launch('Collector',0)
    elif operation=='stop':
        monkeypatch.setattr(driver,'verify',lambda *a:True)
        monkeypatch.setattr(driver,'inspect',lambda *a:unknown('fixture'))
        action=lambda:driver.stop('Collector',{'identity':{'pid':101}},[])
    else:
        monkeypatch.setattr(s.Windows,'ports',lambda *a:[])
        monkeypatch.setattr(s.Windows,'workers',lambda *a:[])
        action=lambda:s.control('status',tmp_path,'pwsh')
    with pytest.raises(s.InventoryUnverified):action()
    assert not (tmp_path/'state/supervisor-v1/intent.json').exists()


def test_persistent_inventory_failure_preserves_live_generation_and_never_signals(tmp_path,monkeypatch):
    store=s.Store(tmp_path);store.path.mkdir(parents=True)
    s.atomic(store.path/'intent.json',{'running':True})
    s.atomic(store.path/'status.json',{'epoch':'fixture-generation','binding':{},'roles':{},
                                     'pending_launch':'supervisor'})
    live={1,2,3}
    monkeypatch.setattr(s,'identity',lambda pid:{'pid':pid,'created':1,'exe':'FIXTURE'})
    monkeypatch.setattr(s,'alive',lambda row:bool(row and row['pid'] in live))
    monkeypatch.setattr(s.time,'sleep',lambda seconds:None)
    births=[]
    class Driver:
        def __init__(self,*a):pass
        def launch(self,role,now):
            births.append(role)
            return {'identity':{'pid':s.ROLES.index(role)+1,'created':1,'exe':'FIXTURE'},
                    'role':role,'launched':now}
        def inspect(self,role,record):
            if role=='Collector':raise s.inventory_error('retry_exhausted',234)
            return {'running':True,'ready':True,'members':[record['identity']]}
        def stop(self,*a):pytest.fail('Unverified inventory must never authorize termination')
    monkeypatch.setattr(s,'Windows',Driver)
    with pytest.raises(s.InventoryUnverified):s.run(tmp_path,'FIXTURE','fixture-generation')
    saved=store.load()
    assert saved['epoch']=='fixture-generation' and saved['phase']=='blocked'
    assert set(saved['roles'])==set(s.ROLES) and births==list(s.ROLES)
    assert {row['record']['identity']['pid'] for row in saved['roles'].values()}==live
    assert all(row['launches']==1 for row in saved['roles'].values())
    assert store.desired() and not saved.get('pending_launch')


def collector(tmp_path,monkeypatch):
    cfg={'canonical_sha':'fixture','source_checkout':str(tmp_path),'product_database':str(tmp_path/'fixture.db'),
         'backend_port':18000,'frontend_port':13000}
    (tmp_path/'config').mkdir();s.atomic(tmp_path/'config/runtime.json',cfg)
    class Process:
        def __init__(self,pid):self.pid=pid
        def children(self,recursive):return [Process(102)]
        def name(self):return 'python.exe'
        def cwd(self):return str(tmp_path)
        def cmdline(self):return ['python','-m','scripts.ingest_data','--watch']
    monkeypatch.setattr(s.psutil,'Process',Process)
    monkeypatch.setattr(s,'identity',lambda pid:{'pid':pid,'created':123,'exe':'fixture'})
    driver=s.Windows(tmp_path,'pwsh',s.bind(cfg),lambda *a,**k:None)
    monkeypatch.setattr(driver,'verify',lambda *a:True)
    workers=[{'ProcessId':102,'ParentProcessId':101,'ExecutablePath':'native-python.exe'}]
    monkeypatch.setattr(driver,'workers',lambda:workers)
    return driver,workers,{'identity':{'pid':101},'launched':0}


def test_mutex_changes_to_foreign_owner_are_rejected(tmp_path,monkeypatch):
    driver,_,record=collector(tmp_path,monkeypatch)
    owners=iter(([102],[999]))
    monkeypatch.setattr(s,'lock_owners',lambda path:next(owners))
    assert driver.inspect('Collector',record)['ready']
    with pytest.raises(s.Conflict,match='COMPETING_COLLECTOR'):driver.inspect('Collector',record)


def test_transient_growth_recovers_in_place_without_startup_timeout_or_new_birth(tmp_path,monkeypatch):
    path,api,_=install(monkeypatch,tmp_path,[{'code':234,'needed':1},{'code':234,'needed':2},
        {'code':0,'needed':1,'count':1,'pids':[102]}])
    driver,_,record=collector(tmp_path,monkeypatch)
    cfg=s.read(tmp_path/'config/runtime.json')
    cfg['product_database']=str(path).removesuffix('.ingestion.lock')
    s.atomic(tmp_path/'config/runtime.json',cfg);driver.binding=s.bind(cfg)
    monkeypatch.setattr(driver,'launch',lambda *a:pytest.fail('No new worker birth'))
    monkeypatch.setattr(driver,'stop',lambda *a:pytest.fail('No signal to healthy worker'))
    machine=s.Recovery(driver,lambda *a,**k:None,roles={
        'Collector':s.Role(record=record,launches=1,phase='running',members=[{'pid':101},{'pid':102}])})
    assert machine.tick(100,True)
    assert machine.roles['Collector'].phase=='running' and machine.roles['Collector'].record is record
    assert machine.roles['Collector'].launches==1 and api.calls==[0,1,2]


@pytest.mark.parametrize('kind',['foreign','duplicate','branching','no_mutex','exited'])
def test_collector_census_mutex_and_identity_still_enforce_single_worker(tmp_path,monkeypatch,kind):
    driver,workers,record=collector(tmp_path,monkeypatch)
    monkeypatch.setattr(s,'lock_owners',lambda path:[102])
    if kind=='no_mutex':
        monkeypatch.setattr(s,'lock_owners',lambda path:[])
        assert not driver.inspect('Collector',record)['ready']
        return
    if kind=='foreign':monkeypatch.setattr(s,'lock_owners',lambda path:[999])
    elif kind in ('duplicate','branching'):
        workers.append({'ProcessId':101,'ParentProcessId':999 if kind=='duplicate' else 101,
                        'ExecutablePath':'native-python.exe'})
    else:
        Process=s.psutil.Process
        def exiting(pid):
            if pid==102:raise s.psutil.NoSuchProcess(pid)
            return Process(pid)
        monkeypatch.setattr(s.psutil,'Process',exiting)
        with pytest.raises(s.psutil.NoSuchProcess):driver.inspect('Collector',record)
        return
    with pytest.raises(s.Conflict,match='COMPETING_COLLECTOR'):driver.inspect('Collector',record)


@pytest.fixture
def native_holder(tmp_path):
    """Real file mutex on an isolated temp path, never a collector process."""
    path=tmp_path/'fixture.db.ingestion.lock'
    child=subprocess.Popen([sys._base_executable,'-u','-c',
        'import msvcrt,sys,os\n'
        'with open(sys.argv[1],"a+b") as h:\n'
        ' h.write(b"x");h.flush();h.seek(0);msvcrt.locking(h.fileno(),msvcrt.LK_NBLCK,1)\n'
        ' print(os.getpid(),flush=True);sys.stdin.readline()\n'
        ' h.seek(0);msvcrt.locking(h.fileno(),msvcrt.LK_UNLCK,1)\n',str(path)],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        # Bound readiness even if the fixture cannot obtain its own temporary lock.
        import queue,threading
        ready=queue.Queue()
        threading.Thread(target=lambda:ready.put(child.stdout.readline()),daemon=True).start()
        pid=int(ready.get(timeout=10))
        yield path,pid
    finally:
        if child.poll() is None:
            child.stdin.write('\n');child.stdin.flush()
        try:child.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill();child.communicate(timeout=5)  # Our isolated fixture only.


def test_native_empty_inventory_ends_cleanly_without_obtaining_mutex(tmp_path):
    path=tmp_path/'unused.lock';path.write_bytes(b'x')
    before=path.read_bytes()
    assert s.lock_owners(path)==[] and path.read_bytes()==before


def test_native_single_owner_and_kernel_mutex_are_preserved(native_holder):
    import msvcrt
    path,pid=native_holder
    assert s.lock_owners(path)==[pid]
    with path.open('r+b') as handle:
        with pytest.raises(OSError):msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
    assert s.lock_owners(path)==[pid]


def test_native_foreign_mutex_owner_blocks_even_without_worker_command_match(native_holder,tmp_path,monkeypatch):
    path,pid=native_holder
    driver=s.Windows(tmp_path,'pwsh',{},lambda *a,**k:None)
    monkeypatch.setattr(driver,'workers',lambda:[])
    with pytest.raises(s.Conflict,match='COLLECTOR_ALREADY_OWNED'):
        driver.vacant('Collector',{'product_database':str(path).removesuffix('.ingestion.lock')})
    assert s.lock_owners(path)==[pid]


def test_native_pid_reuse_and_missing_identity_fail_closed(native_holder):
    path,pid=native_holder
    assert s.lock_owners(path)==[pid]
    owner=SimpleNamespace(pid=pid,started=s.w.FILETIME())
    owner.started.dwLowDateTime=1
    with pytest.raises(s.InventoryUnverified,match='owner_identity_changed'):s._verify_lock_owner(owner)
    owner.pid=0
    with pytest.raises(s.InventoryUnverified,match='owner_open'):s._verify_lock_owner(owner)
