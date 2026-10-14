"""Real Windows observations with finite fake processes and a temporary SQLite DB.

Never invoke the canonical runtime or register a task. Job termination targets
only our own synthetic starter, not any Codex or production process/job.
"""
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
from types import SimpleNamespace
import pytest
from scripts.windows import runtime_supervisor as s
from tests.test_windows_role_observer import runtime, start, receipt

pytestmark = pytest.mark.skipif(os.name!='nt' or not shutil.which('pwsh'), reason='Windows native lifecycle')


def wait_file(path, timeout=15):
    deadline=time.monotonic()+timeout
    while not path.exists() and time.monotonic()<deadline:time.sleep(.05)
    assert path.exists(), 'Finite isolated fixture did not finish'
    return json.loads(path.read_text(encoding='utf-8-sig'))


def test_wmi_child_survives_termination_of_its_own_starter_job(tmp_path):
    with sqlite3.connect(tmp_path/'fixture.db') as db:
        db.execute('CREATE TABLE proof(id INTEGER PRIMARY KEY, payload TEXT)')
        db.execute("INSERT INTO proof VALUES(1,'preserved provenance')")
    before=(tmp_path/'fixture.db').read_bytes()
    job_name='Woofi-fixture-'+tmp_path.name
    child=tmp_path/'child.py'
    child.write_text('''import ctypes,json,os,sqlite3,time
from ctypes import wintypes as w
from pathlib import Path
p=Path(__file__).parent
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenJobObjectW.argtypes=[w.DWORD,w.BOOL,w.LPCWSTR];k.OpenJobObjectW.restype=w.HANDLE
k.GetCurrentProcess.restype=w.HANDLE
k.IsProcessInJob.argtypes=[w.HANDLE,w.HANDLE,ctypes.POINTER(w.BOOL)]
job=k.OpenJobObjectW(4,False,JOB_NAME)
assert job
member=w.BOOL()
assert k.IsProcessInJob(k.GetCurrentProcess(),job,ctypes.byref(member))
starter_member=bool(member.value)
assert k.IsProcessInJob(k.GetCurrentProcess(),None,ctypes.byref(member))
(p/'child-started.json').write_text(json.dumps({'pid':os.getpid(),'in_starter_job':starter_member,'in_any_job':bool(member.value)}))
time.sleep(3)
with sqlite3.connect((p/'fixture.db').as_uri()+'?mode=ro',uri=True) as db:
    result={'integrity':db.execute('PRAGMA quick_check').fetchall(),'fact':db.execute('SELECT payload FROM proof').fetchone()[0]}
(p/'child-finished.json').write_text(json.dumps(result))
'''.replace('JOB_NAME',repr(job_name)))
    starter=tmp_path/'starter.py'
    starter.write_text('''import json,time,sys
from pathlib import Path
sys.path.insert(0,REPO)
from scripts.windows.runtime_supervisor import independent
p=Path(__file__).parent
deadline=time.monotonic()+10
while not (p/'go').exists() and time.monotonic()<deadline:time.sleep(.05)
assert (p/'go').exists()
result=independent(PWSH,[sys.executable,'-B',str(p/'child.py')],p,p/'launch.json')
(p/'starter.json').write_text(json.dumps(result))
time.sleep(10)
'''.replace('REPO',repr(str(Path(__file__).resolve().parents[1]))).replace('PWSH',repr(shutil.which('pwsh'))))
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
    k.TerminateJobObject.argtypes=[w.HANDLE,w.UINT]
    k.CloseHandle.argtypes=[w.HANDLE]
    job=k.CreateJobObjectW(None,job_name);assert job
    info=subprocess.STARTUPINFO();info.dwFlags|=subprocess.STARTF_USESHOWWINDOW;info.wShowWindow=0
    parent=subprocess.Popen([sys.executable,'-B',str(starter)],cwd=tmp_path,stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NEW_CONSOLE,startupinfo=info)
    handle=k.OpenProcess(0x0100|0x0001,False,parent.pid)
    try:
        assert handle and k.AssignProcessToJobObject(job,handle)
        (tmp_path/'go').touch()
        started=wait_file(tmp_path/'child-started.json')
        assert started['in_starter_job'] is False
        assert started['in_any_job'] is False
        assert k.TerminateJobObject(job,7)  # Only the job containing our fixture starter.
        parent.wait(timeout=5)
        result=wait_file(tmp_path/'child-finished.json')
        assert result=={'integrity':[['ok']],'fact':'preserved provenance'}
        assert (tmp_path/'fixture.db').read_bytes()==before
    finally:
        if parent.poll() is None:parent.terminate();parent.wait(timeout=5)
        if handle:k.CloseHandle(handle)
        k.CloseHandle(job)


def test_verified_graceful_stop_signals_only_the_isolated_role_console(tmp_path):
    runtime(tmp_path)
    (tmp_path/'launch/Invoke-Woofi.ps1').write_text("""param([string]$Role,[switch]$CheckOnly)
if($CheckOnly){@{Ready=$true}|ConvertTo-Json;return}
Start-Sleep -Seconds 20
exit 0
""")
    command='& '+s.literal(Path(s.__file__).with_name('Start-WoofiObservedRole.ps1'))+' -Role Backend -RuntimeRoot '+s.literal(tmp_path)
    result=s.ps(shutil.which('pwsh'),command,15,output_file=tmp_path/'starter-result.json')
    run=Path(result['run_directory'])
    wait_file(run/'started.json')
    cfg=json.loads((tmp_path/'config/runtime.json').read_text())
    driver=s.Windows(tmp_path.resolve(),shutil.which('pwsh'),s.bind(cfg),lambda *a,**k:None)
    record={'role':'Backend','identity':s.identity(result['observer_pid']),'run_directory':str(run),'launched':time.monotonic()}
    observation=driver.inspect('Backend',record)
    driver.stop('Backend',record,observation['members'])
    assert not s.alive(record['identity'])
    wait_file(run/'exit.json')
    assert not (tmp_path/'fixture.db').exists()


def test_supervised_role_output_rolls_without_losing_exit_receipt(tmp_path):
    runtime(tmp_path)
    (tmp_path/'launch/Invoke-Woofi.ps1').write_text("""param([string]$Role,[switch]$CheckOnly)
if($CheckOnly){@{Ready=$true}|ConvertTo-Json;return}
1..900|ForEach-Object{Write-Output ('finite fixture '+('x'*1000))}
exit 7
""")
    result=subprocess.run(['pwsh','-NoProfile','-File',str(Path(s.__file__).with_name('Start-WoofiObservedRole.ps1')),
        '-Role','Backend','-RuntimeRoot',str(tmp_path),'-Supervised'],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    run=Path(json.loads(result.stdout)['run_directory'])
    assert receipt(run/'exit.json')['exit_code']==7
    assert receipt(run/'started.json')['bounded_log'] is True
    assert 0<(run/'role.log').stat().st_size<=262144
    assert 0<(run/'role.previous.log').stat().st_size<=262144


def test_control_intent_start_stop_resume_and_single_bootstrap(tmp_path,monkeypatch):
    runtime(tmp_path);state={'alive':False,'launches':0}
    monkeypatch.setattr(s.Windows,'validate',lambda self:json.loads((tmp_path/'config/runtime.json').read_text()))
    monkeypatch.setattr(s.Windows,'vacant',lambda *a:None)
    def observed(root):
        return {'supervisor_alive':state['alive'] and s.Store(root).desired(),'role_alive':{},'member_alive':False}
    monkeypatch.setattr(s,'status',observed)
    def launch(*args):state.update(alive=True,launches=state['launches']+1);return {'launch_pid':123}
    monkeypatch.setattr(s,'independent',launch)
    assert s.control('start',tmp_path,'pwsh')['supervisor_alive']
    assert s.control('start',tmp_path,'pwsh')['supervisor_alive']
    assert state['launches']==1
    assert not s.control('stop',tmp_path,'pwsh')['supervisor_alive']
    assert s.control('resume',tmp_path,'pwsh')=={'result':'STOP_INTENT_RETAINED'}
    assert state['launches']==1
    assert s.control('start',tmp_path,'pwsh')['supervisor_alive']
    assert state['launches']==2


def test_second_supervisor_lock_owner_is_refused(tmp_path):
    with s.file_lock(tmp_path/'supervisor.lock'):
        with pytest.raises(s.Conflict,match='SUPERVISOR_BUSY'):
            with s.file_lock(tmp_path/'supervisor.lock'):pytest.fail('Second owner')


def test_slow_graceful_stop_never_sends_a_second_control_signal(tmp_path,monkeypatch):
    driver=s.Windows(tmp_path,'pwsh',{},lambda *a,**k:None)
    record={'identity':{'pid':123},'run_directory':str(tmp_path)}
    monkeypatch.setattr(driver,'verify',lambda row:True)
    monkeypatch.setattr(driver,'inspect',lambda *a:{'members':[{'pid':123}]})
    monkeypatch.setattr(s,'alive',lambda row:True)
    counter=iter(range(0,10000,100))
    monkeypatch.setattr(s.time,'monotonic',lambda:next(counter))
    signals=[]
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k:(signals.append(a),SimpleNamespace(returncode=0))[1])
    for _ in range(2):
        with pytest.raises(s.Conflict,match='GRACEFUL_STOP_TIMEOUT'):
            driver.stop('Backend',record,[])
    assert len(signals)==1 and record['stop_requested']


def test_optional_resume_preserves_exhausted_budget_until_explicit_start(tmp_path,monkeypatch):
    runtime(tmp_path);store=s.Store(tmp_path);store.path.mkdir(parents=True)
    cfg=json.loads((tmp_path/'config/runtime.json').read_text())
    s.atomic(store.path/'intent.json',{'running':True})
    s.atomic(store.path/'status.json',{'binding':s.bind(cfg),'roles':{'Backend':{'launches':4}}})
    monkeypatch.setattr(s.Windows,'validate',lambda self:cfg)
    monkeypatch.setattr(s.Windows,'vacant',lambda *a:None)
    state={'alive':False}
    monkeypatch.setattr(s,'status',lambda root:{'supervisor_alive':state['alive'],'role_alive':{},'member_alive':False})
    def launch(*args):state['alive']=True;return {'launch_pid':123}
    monkeypatch.setattr(s,'independent',launch)
    s.control('resume',tmp_path,'pwsh')
    restored=store.load()['resume_roles']['Backend']
    assert restored['launches']==4 and restored['phase']=='blocked'


def test_wmi_supervisor_end_to_end_with_only_finite_fake_roles(tmp_path,monkeypatch):
    """Real controller/daemon/stop; role adapters simulate all three services.

    No collector module, network server or production DB is ever launched. The
    fixture adapter maps roles to finite fake Backend PowerShell scripts, so the
    live canonical collector's global mutex/preflight is never bypassed for a real
    worker. Separate tests cover the production adapter's ownership rejection.
    """
    runtime(tmp_path)
    (tmp_path/'launch/Invoke-Woofi.ps1').write_text("""param([string]$Role,[switch]$CheckOnly)
if($CheckOnly){@{Ready=$true}|ConvertTo-Json;return}
Write-Output 'finite simulated role, no acquisition'
Start-Sleep -Seconds 3
exit 7
""")
    fixture_code='''class FixtureWindows(s.Windows):
    def validate(self):return s.read(self.root/'config/runtime.json')
    def vacant(self,*args):pass
    def launch(self,role,now):return super().launch('Backend',now)
    def inspect(self,role,record):
        if not self.verify(record):return {'running':False,'ready':False,'members':record.get('members',[])}
        root=s.psutil.Process(record['identity']['pid'])
        members=[s.identity(p.pid) for p in [root,*root.children(recursive=True)] if p.name().lower()!='conhost.exe']
        record['members']=members
        return {'running':True,'ready':True,'members':members}
'''
    namespace={'s':s};exec(fixture_code,namespace)
    monkeypatch.setattr(s,'Windows',namespace['FixtureWindows'])
    runner=tmp_path/'fixture-supervisor.py'
    runner.write_text('import sys,threading\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(Path(__file__).resolve().parents[1]))+')\nfrom scripts.windows import runtime_supervisor as s\n'+fixture_code+'''
s.Windows=FixtureWindows
s.TICK=.2;s.BACKOFF=(.3,.6,1)
timer=threading.Timer(40,lambda:s.atomic(s.Store(Path(__file__).parent).path/'intent.json',{'running':False}))
timer.daemon=True;timer.start()
sys.exit(s.main())
''')
    launch=s.independent
    def fixture_launch(pwsh,argv,directory,request):
        return launch(pwsh,argv[:2]+[str(runner)]+argv[3:],directory,request)
    monkeypatch.setattr(s,'independent',fixture_launch)
    try:
        state=s.control('start',tmp_path,shutil.which('pwsh'))
        assert state['supervisor_alive']
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            saved=s.Store(tmp_path).load()
            if saved.get('roles',{}).get('Backend',{}).get('launches',0)>=2:break
            time.sleep(.1)
        assert saved['roles']['Backend']['launches']>=2
        stopped=s.control('stop',tmp_path,shutil.which('pwsh'))
        assert not stopped['supervisor_alive'] and not stopped['desired_running']
        assert not any(stopped['role_alive'].values())
        log=(s.Store(tmp_path).path/'events.jsonl').read_text()
        assert 'role_exit' in log and 'backoff' in log and '"expected": true' in log
        assert s.control('resume',tmp_path,shutil.which('pwsh'))=={'result':'STOP_INTENT_RETAINED'}
        assert not (tmp_path/'fixture.db').exists()
    finally:
        if s.Store(tmp_path).path.exists():
            s.atomic(s.Store(tmp_path).path/'intent.json',{'running':False})
