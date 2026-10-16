"""Native census faults and finite fake Python roles; never product ingestion/DB."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from scripts.windows import runtime_supervisor as s


def driver(): return s.Windows(Path('.'), 'unused-pwsh', {}, lambda *a, **k: None)


def install(monkeypatch, rows, fault=None):
    class Process:
        def __init__(self, pid):
            if pid not in rows: raise s.psutil.NoSuchProcess(pid)
            self.pid = pid
        def get(self, key, default=None):
            if fault: fault(self.pid, key)
            return rows[self.pid].get(key, default)
        def name(self): return self.get('name', 'python.exe')
        def create_time(self): return self.get('created', 123.0)
        def exe(self): return self.get('exe', 'fixture-python.exe')
        def ppid(self): return self.get('parent', 1)
        def cmdline(self): return self.get('args', ['python', '-m', 'scripts.ingest_data', '--watch'])
    monkeypatch.setattr(s.psutil, 'pids', lambda: list(rows))
    monkeypatch.setattr(s.psutil, 'Process', Process)
    monkeypatch.setattr(s.psutil, 'pid_exists', lambda pid: pid in rows)
    monkeypatch.setattr(s, 'native_process_names', lambda: {})


def test_native_stable_empty_and_python_nonworker(monkeypatch):
    install(monkeypatch, {1: {'name': 'node.exe'}, 2: {'args': ['python', 'ordinary.py']}})
    assert s.native_workers() == []


@pytest.mark.parametrize('row',[{'name':''},{'args':[]}])
def test_missing_native_metadata_is_not_a_verified_nonworker(monkeypatch,row):
    install(monkeypatch,{1:row})
    with pytest.raises(s.Conflict,match='COLLECTOR_INVENTORY_UNVERIFIABLE'):
        s.native_workers()


def test_missing_executable_name_can_use_qualified_toolhelp_name(monkeypatch):
    install(monkeypatch,{1:{'name':''}})
    monkeypatch.setattr(s,'native_process_names',lambda:{1:'Secure System'})
    assert s.native_workers()==[]
    monkeypatch.setattr(s,'native_process_names',lambda:{1:'python.exe'})
    assert s.native_workers()[0]['ProcessId']==1  # No broad exclusion.


def test_toolhelp_fallback_still_fences_pid_reuse(monkeypatch):
    rows={1:{'name':''}}
    install(monkeypatch,rows)
    def changed():
        rows[1]['created']=999
        return {1:'Secure System'}
    monkeypatch.setattr(s,'native_process_names',changed)
    with pytest.raises(s.Conflict,match='COLLECTOR_INVENTORY_UNVERIFIABLE'):s.native_workers()


@pytest.mark.skipif(os.name!='nt',reason='Windows Toolhelp ABI')
@pytest.mark.parametrize('fault',['none','open','first','next','empty','duplicate','close'])
def test_toolhelp_native_contract_and_failure_release(monkeypatch,fault):
    import ctypes
    class Call:
        def __init__(self,fn):self.fn=fn
        def __call__(self,*args):return self.fn(*args)
    class Kernel:
        def __init__(self):
            self.closed=[];self.next_calls=0
            self.CreateToolhelp32Snapshot=Call(lambda *a:ctypes.c_void_p(-1).value if fault=='open' else 123)
            self.Process32FirstW=Call(self.first)
            self.Process32NextW=Call(self.next)
            self.CloseHandle=Call(self.close)
        def first(self,h,p):
            if fault=='first':return False
            p._obj.pid=101;p._obj.name='' if fault=='empty' else 'Secure System'
            return True
        def next(self,h,p):
            if fault=='duplicate' and not self.next_calls:
                self.next_calls+=1;return True
            ctypes.set_last_error(5 if fault=='next' else 18);return False
        def close(self,h):self.closed.append(h);return fault!='close'
    kernel=Kernel();monkeypatch.setattr(s.ctypes,'WinDLL',lambda *a,**kw:kernel)
    if fault=='none':assert s.native_process_names()=={101:'Secure System'}
    else:
        with pytest.raises(s.Conflict,match='COLLECTOR_INVENTORY_UNVERIFIABLE'):s.native_process_names()
    assert kernel.closed==([] if fault=='open' else [123])


def test_native_venv_chain_and_news_worker_are_not_collapsed(monkeypatch):
    install(monkeypatch, {1: {}, 2: {'parent': 1}, 3: {'args': ['python', '-m', 'scripts.ingest_news']}})
    rows = s.native_workers()
    assert [r['ProcessId'] for r in rows] == [1, 2, 3]
    assert all(r['CreationTime'] == 123 and r['ExecutablePath'] == 'fixture-python.exe' for r in rows)
    assert all(set(r) == {'ProcessId','ParentProcessId','ExecutablePath','CreationTime'} for r in rows)


@pytest.mark.parametrize('key', ['name','created','exe','parent','args'])
def test_permission_denial_never_returns_partial_success(monkeypatch, key):
    def denied(pid, field):
        if pid == 2 and field == key: raise s.psutil.AccessDenied(pid)
    install(monkeypatch, {1: {}, 2: {}}, denied)
    with pytest.raises(s.Conflict, match='COLLECTOR_INVENTORY_UNVERIFIABLE'):
        s.native_workers()


def test_failed_pid_enumeration_is_not_empty(monkeypatch):
    def denied(): raise s.psutil.AccessDenied()
    monkeypatch.setattr(s.psutil, 'pids', denied)
    with pytest.raises(s.Conflict, match='COLLECTOR_INVENTORY_UNVERIFIABLE'): s.native_workers()


@pytest.mark.parametrize('pids', [None, [1, 1], [True], [-1]])
def test_invalid_native_pid_inventory_fails_closed(monkeypatch, pids):
    monkeypatch.setattr(s.psutil, 'pids', lambda: pids)
    with pytest.raises(s.Conflict, match='COLLECTOR_INVENTORY_UNVERIFIABLE'): s.native_workers()


def test_confirmed_exit_during_observation_is_omitted(monkeypatch):
    rows = {1: {}, 2: {}}
    def exits(pid, key):
        if pid == 2 and key == 'args':
            rows.pop(pid)
            raise s.psutil.NoSuchProcess(pid)
    install(monkeypatch, rows, exits)
    assert [r['ProcessId'] for r in s.native_workers()] == [1]


@pytest.mark.parametrize('reuse', [False, True])
def test_unconfirmed_exit_or_reused_identity_is_not_omitted(monkeypatch, reuse):
    rows={1: {}}
    def changes(pid, key):
        if key == 'args':
            if reuse: rows[pid]['created'] = 999
            else: raise s.psutil.NoSuchProcess(pid)
    install(monkeypatch, rows, changes)
    with pytest.raises(s.Conflict, match='COLLECTOR_INVENTORY_UNVERIFIABLE'): s.native_workers()


def test_native_helper_has_deadline_no_powershell_and_sanitized_environment(monkeypatch):
    monkeypatch.setenv('PATHEXT', '.EXE;.CMD')
    monkeypatch.setenv('SSI_API_KEY', 'synthetic-private-secret')
    monkeypatch.setenv('TECHNICAL_EOD_PILOT', 'true')
    calls=[]
    def result(argv, **kw):
        calls.append((argv,kw)); return SimpleNamespace(returncode=0,stdout='[]')
    monkeypatch.setattr(s.subprocess, 'run', result)
    assert driver().workers() == []
    argv,kw=calls[0]
    assert argv[:2] == [sys._base_executable, '-S'] and argv[3] == 'workers'
    assert kw['timeout'] == 5 and kw['creationflags'] == subprocess.CREATE_NO_WINDOW
    assert not {'SSI_API_KEY','TECHNICAL_EOD_PILOT'} & kw['env'].keys()
    assert not any('Get-CimInstance' in a for a in argv)


@pytest.mark.parametrize('payload', ['', '{}', 'null', 'invalid', '[{}]',
    '[{"ProcessId":1,"ParentProcessId":0,"ExecutablePath":"python.exe","CreationTime":null}]',
    '[{"ProcessId":true,"ParentProcessId":0,"ExecutablePath":"python.exe","CreationTime":1}]'])
def test_incomplete_helper_census_never_means_empty(monkeypatch, payload):
    monkeypatch.setenv('PATHEXT', '.EXE;.CMD')
    monkeypatch.setattr(s.subprocess, 'run', lambda *a, **k:SimpleNamespace(returncode=0,stdout=payload))
    with pytest.raises(s.Conflict, match='COLLECTOR_INVENTORY_UNVERIFIABLE'): driver().workers()


@pytest.mark.parametrize('payload', ['duplicate', 'invalid_parent', 'nonfinite', 'oversized', 'failed'])
def test_invalid_or_failed_census_cannot_qualify_ownership(monkeypatch, payload):
    monkeypatch.setenv('PATHEXT', '.EXE;.CMD')
    row={'ProcessId':1,'ParentProcessId':0,'ExecutablePath':'python.exe','CreationTime':1}
    if payload=='invalid_parent': row['ParentProcessId']=True
    if payload=='nonfinite': row['CreationTime']=float('nan')
    text=json.dumps([row,row] if payload=='duplicate' else [row])
    if payload=='oversized': text=' '*65537
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**kw:SimpleNamespace(
        returncode=1 if payload=='failed' else 0,stdout=text))
    with pytest.raises(s.Conflict,match='COLLECTOR_INVENTORY_UNVERIFIABLE'): driver().workers()


def test_slow_probe_is_identified_without_private_command(monkeypatch):
    monkeypatch.setenv('PATHEXT', '.EXE;.CMD')
    def timeout(*a,**kw): raise subprocess.TimeoutExpired('private-command',kw['timeout'])
    monkeypatch.setattr(s.subprocess, 'run', timeout)
    with pytest.raises(s.Conflict, match='probe=native_collectors timeout_seconds=5') as error:
        driver().workers()
    assert 'private' not in str(error.value)


@pytest.mark.skipif(os.name != 'nt', reason='Finite native Windows fixture')
def test_real_helper_observes_only_temporary_fake_worker(tmp_path):
    # This module never imports Woofi, acquires a lock, opens DB or calls a provider.
    package=tmp_path/'scripts'; package.mkdir(); (package/'__init__.py').write_text('')
    (package/'ingest_data.py').write_text('import time\nfrom pathlib import Path\n'
        'deadline=time.monotonic()+8\nwhile not Path("finish").exists() and time.monotonic()<deadline: time.sleep(.02)\n')
    child=subprocess.Popen([sys._base_executable,'-S','-m','scripts.ingest_data','--watch'],cwd=tmp_path,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        rows=driver().workers()
        row=next(r for r in rows if r['ProcessId']==child.pid)
        assert row['CreationTime'] == s.psutil.Process(child.pid).create_time()
        assert Path(row['ExecutablePath']).samefile(sys._base_executable)
        assert child.poll() is None
    finally:
        (tmp_path/'finish').touch(); child.wait(timeout=10)


@pytest.mark.skipif(os.name != 'nt', reason='Finite native Windows helper timeout')
def test_delayed_native_probe_is_bounded_and_reaped(tmp_path, monkeypatch):
    script=tmp_path/'slow.py'; pid_file=tmp_path/'pid'
    script.write_text('import os,time\nfrom pathlib import Path\n'
        f'Path({str(pid_file)!r}).write_text(str(os.getpid()))\ntime.sleep(10)\n')
    original=s.subprocess.run
    def slow(argv, **kw):
        assert argv[3]=='workers';kw['timeout']=1
        return original([argv[0],'-S',str(script)],**kw)
    monkeypatch.setattr(s.subprocess,'run',slow)
    with pytest.raises(s.Conflict,match='probe=native_collectors'): driver().workers()
    assert pid_file.exists() and not s.psutil.pid_exists(int(pid_file.read_text()))
