"""Native finite observer, production inspect/recovery, deterministic exit barrier.

No canonical service, supervisor daemon, collector, provider or SQLite is started.
This review-only gate deliberately asserts normal recovery, not an expected crash.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import time

import pytest

from scripts.windows import runtime_supervisor as s
from tests.test_windows_role_observer import runtime, receipt
from tests.test_runtime_supervisor_control import control_fixture


pytestmark = pytest.mark.skipif(os.name != 'nt' or not shutil.which('pwsh'),
                                reason='Native Windows finite observer fixture')


def test_verified_native_root_exit_is_handled_by_production_recovery(tmp_path,monkeypatch):
    runtime(tmp_path)
    release = tmp_path/'allow-exit'
    (tmp_path/'launch/Invoke-Woofi.ps1').write_text('''param([string]$Role,[switch]$CheckOnly)
if($CheckOnly){@{Ready=$true}|ConvertTo-Json;return}
$release=Join-Path (Split-Path $PSScriptRoot) 'allow-exit'
$deadline=(Get-Date).AddSeconds(15)
while(-not (Test-Path -LiteralPath $release) -and (Get-Date) -lt $deadline){Start-Sleep -Milliseconds 20}
exit 7
''')
    cfg=s.read(tmp_path/'config/runtime.json')
    driver=s.Windows(tmp_path.resolve(),shutil.which('pwsh'),s.bind(cfg),lambda *a,**kw:None)
    command='& '+s.literal(Path(s.__file__).with_name('Start-WoofiObservedRole.ps1'))
    command+=' -Role Backend -Supervised -RuntimeRoot '+s.literal(tmp_path)
    launched=s.ps(shutil.which('pwsh'),command,15,output_file=tmp_path/'starter.json')
    run=Path(launched['run_directory'])
    receipt(run/'started.json')
    record={'role':'Backend','identity':s.identity(launched['observer_pid']),
            'run_directory':str(run),'launched':time.monotonic()}
    observer=s.psutil.Process(record['identity']['pid'])
    original_verify=driver.verify
    timeline={'observer':record['identity'],'isolated_runtime':str(tmp_path),'steps':[]}
    def save(event,**detail):
        timeline['steps'].append({'event':event,'utc':datetime.now(timezone.utc).isoformat(),**detail})
        (tmp_path/'production-exit-timeline.json').write_text(json.dumps(timeline,indent=2))
    def verify_then_exit(item):
        verified=original_verify(item)  # Actual PID/time/exe/script/receipt checks.
        assert verified
        save('production_identity_verified',alive=s.alive(item['identity']))
        release.touch()  # Allow only this finite fixture to exit naturally.
        observer.wait(timeout=10)
        assert not s.alive(item['identity'])
        save('verified_root_exited_before_census',exit_receipt=receipt(run/'exit.json'))
        return verified
    monkeypatch.setattr(driver,'verify',verify_then_exit)
    monkeypatch.setattr(driver,'launch',lambda *a:pytest.fail('No immediate process birth allowed'))
    monkeypatch.setattr(driver,'stop',lambda *a:pytest.fail('No process termination allowed'))
    events=[]
    machine=s.Recovery(driver,lambda event,**detail:events.append((event,detail)),roles={
        'Backend':s.Role(record=record,launches=1,phase='running',members=[record['identity']])})
    try:
        # A natural verified root exit should reach the existing exit/backoff
        # policy. A raw NoSuchProcess here would instead terminate run().
        try:
            keep=machine.tick(time.monotonic(),True)
        except Exception as exc:
            save('production_recovery_raised',type=type(exc).__name__)
            raise
        assert keep and machine.roles['Backend'].record is None
        assert machine.roles['Backend'].phase=='backoff'
        assert any(event=='role_exit' for event,detail in events)
    finally:
        release.touch()
        observer.wait(timeout=10)
        save('fixture_cleanup_complete',alive=s.alive(record['identity']),
             database_created=(tmp_path/'fixture.db').exists())


@pytest.fixture
def census(tmp_path,monkeypatch):
    """Real adapter and identity validation with deterministic process events."""
    executable=tmp_path/'identity.exe';executable.write_bytes(b'never executed')
    (tmp_path/'config').mkdir()
    cfg={'canonical_sha':'fixture','source_checkout':str(tmp_path),'product_database':str(tmp_path/'unused.db'),
         'backend_port':18000,'frontend_port':13000}
    s.atomic(tmp_path/'config/runtime.json',cfg)
    run=tmp_path/'state/observed-role-runs/fixture';run.mkdir(parents=True)
    s.atomic(run/'started.json',{'sha':'fixture','source':str(tmp_path),'database':cfg['product_database'],
                                'observer_pid':1,'role':'Backend'})
    args=['pwsh','-File',str(Path(s.__file__).with_name('Invoke-WoofiObservedRole.ps1')),
          '-Role','Backend','-RuntimeRoot',str(tmp_path)]
    rows={1:{'created':10,'parent':0},2:{'created':20,'parent':1}}
    hooks={};calls=[]
    def event(name,pid):
        if name in hooks:hooks[name](pid)
    class Process:
        def __init__(self,pid):
            if pid not in rows:raise s.psutil.NoSuchProcess(pid)
            self.pid=pid;self.birth=rows[pid]['created']
        def create_time(self):return self.birth
        def value(self,name,value):
            event(name,self.pid)
            if self.pid not in rows:raise s.psutil.NoSuchProcess(self.pid)
            return value
        def exe(self):return self.value('exe',str(executable))
        def name(self):return self.value('name','pwsh.exe' if self.pid==1 else 'python.exe')
        def cmdline(self):return self.value('cmdline',args if self.pid==1 else ['python','-m','scripts.ingest_data','--watch'])
        def cwd(self):return self.value('cwd',str(tmp_path))
        def children(self,recursive):
            event('children',self.pid)
            if self.pid not in rows:raise s.psutil.NoSuchProcess(self.pid)
            return [Process(pid) for pid,row in rows.items() if row['parent']==self.pid]
    monkeypatch.setattr(s.psutil,'Process',Process)
    monkeypatch.setattr(s.psutil,'pid_exists',lambda pid:pid in rows)
    driver=s.Windows(tmp_path.resolve(),'FIXTURE',s.bind(cfg),lambda *a,**kw:None)
    monkeypatch.setattr(driver,'ports',lambda *a:[])
    monkeypatch.setattr(driver,'workers',lambda:[])
    monkeypatch.setattr(driver,'launch',lambda *a:pytest.fail('Unverified census must never admit process birth'))
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**kw:pytest.fail('No real process signal allowed'))
    record={'identity':s.identity(1),'role':'Backend','run_directory':str(run),'launched':0,
            'members':[s.identity(1),s.identity(2)]}
    sleeps=[];monkeypatch.setattr(s.time,'sleep',sleeps.append)
    return driver,record,rows,hooks,calls,sleeps


@pytest.mark.parametrize('stage',['cmdline','children'])
def test_natural_root_exit_during_metadata_read_reaches_existing_backoff(census,stage):
    driver,record,rows,hooks,events,_=census
    def exit_tree(pid):
        if pid==1:rows.clear()
    hooks[stage]=exit_tree
    machine=s.Recovery(driver,lambda event,**kw:events.append(event),roles={
        'Backend':s.Role(record=record,launches=1,phase='running',members=list(record['members']))})
    assert machine.tick(100,True)
    assert machine.roles['Backend'].phase=='backoff' and machine.roles['Backend'].record is None
    assert machine.roles['Backend'].due==115 and events==['role_exit','backoff']


def test_confirmed_child_exit_is_not_an_empty_or_unknown_tree(census):
    driver,record,rows,hooks,_,_=census
    def child_exits(pid):
        if pid==2:rows.pop(2)
    hooks['name']=child_exits
    observed=driver.inspect('Backend',record)
    assert observed['running'] and not observed['ready']
    assert [m['pid'] for m in observed['members']]==[1]
    assert [m['pid'] for m in record['members']]==[1]


def test_transient_children_enumeration_retries_are_bounded(census):
    driver,record,_,hooks,_,sleeps=census
    attempts=[]
    def transient(pid):
        attempts.append(pid)
        if len(attempts)==1:raise s.psutil.NoSuchProcess(999)
    hooks['children']=transient
    assert driver.inspect('Backend',record)['running']
    assert attempts==[1,1] and sleeps==[.05]


def test_persistent_enumeration_failure_keeps_members_without_admitting_recovery(census):
    driver,record,_,hooks,_,sleeps=census
    def churn(pid):raise s.psutil.NoSuchProcess(999)
    hooks['children']=churn
    with pytest.raises(s.Conflict,match='PROCESS_CENSUS_UNVERIFIABLE'):driver.inspect('Backend',record)
    assert sleeps==[.05,.1] and len(record['members'])==2


@pytest.mark.parametrize('kind',['reused_root','reused_child','inaccessible_root','inaccessible_child'])
def test_reused_or_inaccessible_process_identity_is_never_downgraded_to_exit(census,kind):
    driver,record,rows,hooks,_,_=census
    if kind=='reused_root':rows[1]['created']=1000
    elif kind=='reused_child':
        def reuse(pid):
            if pid==2:rows[2]['created']=1000
        hooks['name']=reuse
    else:
        target=1 if kind=='inaccessible_root' else 2
        def denied(pid):
            if pid==target:raise s.psutil.AccessDenied(pid)
        hooks['exe' if target==1 else 'name']=denied
    with pytest.raises(s.Conflict):driver.inspect('Backend',record)
    assert record['identity']['created']==10
    assert all(item['created']!=1000 for item in record['members'])


@pytest.mark.parametrize('root_alive',[False,True])
def test_live_orphan_member_blocks_recovery_and_is_not_forgotten(census,monkeypatch,root_alive):
    driver,record,rows,hooks,_,_=census
    if root_alive:
        monkeypatch.setattr(s.psutil.Process,'children',lambda *a,**kw:[])
    else:rows.pop(1)
    machine=s.Recovery(driver,lambda *a,**kw:None,roles={
        'Backend':s.Role(record=record,launches=1,phase='running',members=list(record['members']))})
    with pytest.raises(s.Conflict,match='ORPHANED_ROLE_MEMBERS'):machine.tick(100,True)
    assert machine.roles['Backend'].record is record
    assert any(item['pid']==2 for item in machine.roles['Backend'].members)


def test_partial_failed_census_preserves_newly_discovered_live_member(census):
    driver,record,rows,hooks,_,_=census
    record['members']=[record['identity']]
    rows[3]={'created':30,'parent':1}
    def denied(pid):
        if pid==3:raise s.psutil.AccessDenied(pid)
    hooks['name']=denied
    machine=s.Recovery(driver,lambda *a,**kw:None,roles={
        'Backend':s.Role(record=record,launches=1,phase='running',members=[record['identity']])})
    with pytest.raises(s.Conflict,match='PROCESS_IDENTITY_UNVERIFIABLE'):machine.tick(100,True)
    assert {m['pid'] for m in machine.roles['Backend'].members}=={1,2}
    assert machine.roles['Backend'].record is record


@pytest.mark.parametrize('change',['exited','reused','denied'])
def test_collector_exit_or_identity_change_after_mutex_snapshot_cannot_certify_readiness(census,monkeypatch,change):
    driver,record,rows,hooks,_,_=census
    monkeypatch.setattr(driver,'workers',lambda:[{'ProcessId':2,'ParentProcessId':1,'ExecutablePath':'native-python.exe'}])
    monkeypatch.setattr(s,'lock_owners',lambda path:[2])
    def change_worker(pid):
        if pid!=2:return
        if change=='exited':rows.pop(2)
        elif change=='reused':rows[2]['created']=2000
        else:raise s.psutil.AccessDenied(pid)
    hooks['cmdline']=change_worker
    if change=='exited':
        observed=driver.inspect('Collector',record)
        assert observed['running'] and not observed['ready']
    else:
        with pytest.raises(s.Conflict):driver.inspect('Collector',record)
    assert all(m['created']!=2000 for m in record['members'])


@pytest.mark.parametrize('action',['stop','signal'])
@pytest.mark.parametrize('orphan',[False,True])
def test_exit_before_stop_or_signal_never_targets_surviving_or_unrelated_processes(census,action,orphan):
    driver,record,rows,_,_,_=census
    rows.pop(1)
    if not orphan:rows.pop(2)
    call=(lambda:driver.stop('Backend',record,record['members'])) if action=='stop' else lambda:driver.signal(record)
    if orphan:
        with pytest.raises(s.Conflict,match='ORPHANED_ROLE_MEMBERS'):call()
    else:call()


def test_stale_generation_cannot_census_or_signal_new_owned_processes(census):
    driver,record,_,_,_,_=census
    store=s.Store(driver.root);store.path.mkdir(parents=True,exist_ok=True)
    s.atomic(store.path/'status.json',{'epoch':'new'})
    driver.epoch='old'
    with pytest.raises(s.Conflict,match='STALE_START_EPOCH'):driver.signal(record)


@pytest.mark.parametrize('change',['root_reused','child_exited','foreign_console'])
def test_signal_rechecks_identity_after_console_attach_before_any_control_event(census,monkeypatch,change):
    driver,record,rows,_,calls,_=census
    real_kernel=s.ctypes.WinDLL('kernel32',use_last_error=True)
    class Kernel:
        def __getattr__(self,name):
            # Mock console signalling only. State reads now use the real native
            # JSON-I/O mutex; do not replace that unrelated ABI with a stub.
            if name not in ('CreateMutexW','WaitForSingleObject','ReleaseMutex','CloseHandle'):
                raise AttributeError(name)
            return getattr(real_kernel,name)
        def FreeConsole(self):calls.append('free');return 1
        def AttachConsole(self,pid):calls.append('attach');return 1
        def GetConsoleProcessList(self,clients,capacity):
            pids=[1,2,os.getpid()]+([999] if change=='foreign_console' else [])
            for i,pid in enumerate(pids):clients[i]=pid
            if change=='root_reused':rows[1]['created']=1000
            if change=='child_exited':rows.pop(2)
            return len(pids)
        def SetConsoleCtrlHandler(self,*a):pytest.fail('No handler change on unverified identity')
        def GenerateConsoleCtrlEvent(self,*a):pytest.fail('No unrelated process signal')
    monkeypatch.setattr(s.ctypes,'WinDLL',lambda *a,**kw:Kernel())
    with pytest.raises(s.Conflict):driver.signal(record)
    assert calls==['free','attach','free']


@pytest.mark.parametrize('failure',['success_but_child_alive','refused','timeout'])
def test_stop_waits_for_members_discovered_by_the_separate_signal_helper(census,monkeypatch,failure):
    from types import SimpleNamespace
    driver,record,rows,_,_,_=census
    def helper(argv,**kw):
        request=Path(argv[argv.index('--request')+1]);value=s.read(request)
        rows[3]={'created':30,'parent':1}
        value['record']['members'].append(s.identity(3));s.atomic(request,value)
        rows.pop(1);rows.pop(2)
        if failure=='timeout':raise s.subprocess.TimeoutExpired(argv,15)
        return SimpleNamespace(returncode=1 if failure=='refused' else 0)
    monkeypatch.setattr(s.subprocess,'run',helper)
    clock=iter((0,100,200));monkeypatch.setattr(s.time,'monotonic',lambda:next(clock))
    if failure=='timeout':
        with pytest.raises(s.subprocess.TimeoutExpired):driver.stop('Backend',record,record['members'])
    else:
        reason='GRACEFUL_SIGNAL_REFUSED' if failure=='refused' else 'GRACEFUL_STOP_TIMEOUT'
        with pytest.raises(s.Conflict,match=reason):driver.stop('Backend',record,record['members'])
    assert any(m['pid']==3 for m in record['members']) and 3 in rows


def test_stop_error_journals_new_members_and_keeps_durable_intent(control_fixture,monkeypatch):
    root,store,live,calls,hooks,births,old_roles=control_fixture
    old_roles()
    def partial(self,role,record,members):
        live.add(4)
        record['members']=[*members,{'pid':4,'created':1,'exe':'FIXTURE'}]
        raise s.Conflict('PROCESS_IDENTITY_UNVERIFIABLE')
    monkeypatch.setattr(s.Windows,'stop',partial)
    with pytest.raises(s.Conflict,match='PROCESS_IDENTITY_UNVERIFIABLE'):
        s.control('stop',root,'FIXTURE')
    saved=store.load()
    assert saved['epoch']=='old' and saved['control_phase']=='stopping' and not store.desired()
    assert {m['pid'] for m in saved['roles']['Collector']['members']}=={3,4}
    assert live=={1,2,3,4} and births==[]
    with pytest.raises(s.Conflict,match='STOP_IN_PROGRESS'):s.control('start',root,'FIXTURE')


@pytest.mark.parametrize('desired',[True,False])
def test_recovery_remembers_members_discovered_by_a_failing_stop(census,monkeypatch,desired):
    driver,record,rows,_,_,_=census
    def partial(*args):
        rows[3]={'created':30,'parent':1}
        record['members'].append(s.identity(3))
        raise s.Conflict('PROCESS_IDENTITY_UNVERIFIABLE')
    monkeypatch.setattr(driver,'stop',partial)
    state=s.Role(record=record,launches=1,phase='starting',members=list(record['members']))
    machine=s.Recovery(driver,lambda *a,**kw:None,roles={name:s.Role() for name in s.ROLES})
    machine.roles['Backend']=state
    with pytest.raises(s.Conflict,match='PROCESS_IDENTITY_UNVERIFIABLE'):
        machine.tick(100,desired)
    assert state.record is record and any(m['pid']==3 for m in state.members)
