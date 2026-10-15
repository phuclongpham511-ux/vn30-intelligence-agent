"""RM serialization only; mocked API failures and isolated native processes."""
import ctypes
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts.windows import runtime_supervisor as s

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows named mutex ABI')


class Call:
    def __init__(self, function):
        self.function = function

    def __call__(self, *args):
        return self.function(*args)


def kernel(monkeypatch, *, handle=123, wait=0, release=True, close=True):
    calls=[]
    def call(name,result):
        def invoke(*args):
            calls.append((name,args))
            return result
        return Call(invoke)
    api=SimpleNamespace(CreateMutexW=call('open',handle), WaitForSingleObject=call('wait',wait),
                        ReleaseMutex=call('release',release), CloseHandle=call('close',close))
    monkeypatch.setattr(s.ctypes,'WinDLL',lambda *a,**k:api)
    monkeypatch.setattr(s.ctypes,'get_last_error',lambda:5)
    return calls


@pytest.mark.parametrize('wait',[258,0x80,0xffffffff,1])
def test_wait_failure_or_abandonment_never_runs_inventory(monkeypatch,tmp_path,wait):
    calls=kernel(monkeypatch,wait=wait)
    monkeypatch.setattr(s,'_lock_owners',lambda *a:pytest.fail('Unqualified mutex must not query RM'))
    with pytest.raises(s.InventoryUnverified,match='serialization_wait'):
        s.lock_owners(tmp_path/'unused.lock')
    assert [n for n,_ in calls]==['open','wait']+(['release'] if wait==0x80 else [])+['close']
    assert calls[0][1]==(None,False,s.INVENTORY_MUTEX)
    assert calls[1][1]==(123,5000)  # One bounded native wait, no polling/retry loop.


def test_open_failure_does_not_wait_or_query(monkeypatch,tmp_path):
    calls=kernel(monkeypatch,handle=0)
    monkeypatch.setattr(s,'_lock_owners',lambda *a:pytest.fail('No valid handle'))
    with pytest.raises(s.InventoryUnverified,match='serialization_open'):s.lock_owners(tmp_path)
    assert [n for n,_ in calls]==['open']


@pytest.mark.parametrize('failure',[False,True])
def test_lock_encloses_complete_inventory_and_releases_on_exception(monkeypatch,tmp_path,failure):
    calls=kernel(monkeypatch)
    def inventory(path):
        assert [n for n,_ in calls]==['open','wait']
        assert path==tmp_path
        if failure:raise s.inventory_error('fixture_rm_failure',121)
        return [999]  # Foreign owners are returned unchanged, never filtered.
    monkeypatch.setattr(s,'_lock_owners',inventory)
    if failure:
        with pytest.raises(s.InventoryUnverified,match='fixture_rm_failure'):s.lock_owners(tmp_path)
    else:assert s.lock_owners(tmp_path)==[999]
    assert [n for n,_ in calls]==['open','wait','release','close']


@pytest.mark.parametrize('release,close',[(False,True),(True,False),(False,False)])
@pytest.mark.parametrize('primary',[False,True])
def test_cleanup_failure_is_not_success_or_loss_of_primary_failure(monkeypatch,release,close,primary):
    calls=kernel(monkeypatch,release=release,close=close)
    with pytest.raises(s.InventoryUnverified,match='original' if primary else 'serialization_cleanup'):
        with s.inventory_lock():
            if primary:raise s.inventory_error('original',234)
    assert [n for n,_ in calls]==['open','wait','release','close']


def native(code):
    return subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True,timeout=15,
                          cwd=str(s.Path(s.__file__).resolve().parents[2]))


def test_native_mutex_excludes_independent_observer_then_allows_after_release():
    # Child reaches a bounded wait while the parent actually owns the mutex.
    # No sleep, timing-based assertion, canonical file or collector invocation.
    code=('from scripts.windows import runtime_supervisor as s\n'
          's.INVENTORY_WAIT_MS=50\n'
          'with s.inventory_lock(): print("acquired")\n')
    with s.inventory_lock():
        blocked=native(code)
        assert blocked.returncode!=0 and 'serialization_wait' in blocked.stderr
        assert '"code":258' in blocked.stderr and 'acquired' not in blocked.stdout
    acquired=native(code)
    assert acquired.returncode==0,acquired.stderr
    assert acquired.stdout.strip()=='acquired'


def test_native_abandoned_mutex_fails_current_observation_and_releases():
    # Keep a non-owning handle so Windows retains the abandoned object after
    # the temporary owner's normal process exit. No live process is killed.
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes=[s.w.LPVOID,s.w.BOOL,s.w.LPCWSTR]
    kernel.CreateMutexW.restype=s.w.HANDLE
    kernel.CloseHandle.argtypes=[s.w.HANDLE]
    handle=kernel.CreateMutexW(None,False,s.INVENTORY_MUTEX)
    assert handle
    try:
        child=native('import os\nfrom scripts.windows import runtime_supervisor as s\n'
                     'with s.inventory_lock(): os._exit(0)\n')
        assert child.returncode==0,child.stderr
        with pytest.raises(s.InventoryUnverified,match='"code":128'):
            with s.inventory_lock():pytest.fail('Abandoned inventory cannot qualify ownership')
        with s.inventory_lock():pass  # Previous uncertain query released ownership.
    finally:kernel.CloseHandle(handle)
