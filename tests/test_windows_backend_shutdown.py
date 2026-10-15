"""Windows teardown regressions. No canonical runtime, credentials or provider.

Native TCP controls and deterministic WinError-10054 injection are distinct:
the latter reproduces the exact saved production callback failure reliably.
"""
import asyncio
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
import uvicorn

from src.services.windows_socket_cleanup import (
    _reset_safe_callback, install_windows_socket_cleanup,
)
from src.services import windows_socket_cleanup
from scripts.windows import runtime_supervisor as s


def test_only_socket_shutdown_reset_is_tolerated():
    calls = []
    class Sock:
        def shutdown(self, how):
            calls.append('shutdown')
            raise ConnectionResetError('peer reset')
        def close(self):
            calls.append('close')
    sock = Sock()
    transport = SimpleNamespace(_sock=sock, _called_connection_lost=False)
    def original(t, exc):
        if t._called_connection_lost:
            return
        t._sock.shutdown(socket.SHUT_RDWR)
        t._sock.close()
        t._sock = None
        calls.append('detach')
        t._called_connection_lost = True
    callback = _reset_safe_callback(original)
    callback(transport, None)
    callback(transport, None)
    assert calls == ['shutdown', 'close', 'detach']
    assert transport._sock is None and transport._called_connection_lost


def test_non_windows_import_does_not_install_transport_hook(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(windows_socket_cleanup.sys, 'platform', 'linux')
        assert install_windows_socket_cleanup() is False


@pytest.mark.parametrize('stage', ['shutdown', 'close', 'protocol'])
def test_other_errors_propagate_and_socket_identity_is_restored(stage):
    class Sock:
        def shutdown(self, how):
            if stage == 'shutdown':
                raise PermissionError('unknown shutdown failure')
        def close(self):
            if stage == 'close':
                raise ConnectionResetError('close is not shutdown')
    sock = Sock()
    transport = SimpleNamespace(_sock=sock, _called_connection_lost=False)
    def original(t, exc):
        if stage == 'protocol':
            raise ConnectionResetError('protocol failure')
        t._sock.shutdown(socket.SHUT_RDWR)
        t._sock.close()
    with pytest.raises(OSError):
        _reset_safe_callback(original)(transport, None)
    assert transport._sock is sock
    assert not transport._called_connection_lost


@pytest.mark.skipif(os.name != 'nt', reason='native Windows transport')
def test_recorded_reset_releases_actual_cpython_server_attachment():
    from asyncio.proactor_events import _ProactorSocketTransport, _ProactorBasePipeTransport
    pipe_callback = _ProactorBasePipeTransport._call_connection_lost
    assert install_windows_socket_cleanup()
    callback = _ProactorSocketTransport._call_connection_lost
    assert install_windows_socket_cleanup()
    assert _ProactorSocketTransport._call_connection_lost is callback
    assert _ProactorBasePipeTransport._call_connection_lost is pipe_callback
    async def scenario():
        loop = asyncio.get_running_loop()
        server = await loop.create_server(asyncio.Protocol, '127.0.0.1', 0)
        left, right = socket.socketpair()
        left.setblocking(False)
        class Paused(asyncio.Protocol):
            def connection_made(self, t):
                t.pause_reading()
        transport = _ProactorSocketTransport(loop, left, Paused(), server=server)
        await asyncio.sleep(0)
        class ResetSocket:
            def __getattr__(self, key):
                return getattr(left, key)
            def shutdown(self, how):
                raise ConnectionResetError(10054, 'recorded peer reset')
        transport._sock = ResetSocket()
        try:
            transport._call_connection_lost(None)
            server.close()
            await asyncio.wait_for(server.wait_closed(), .2)
            assert server._active_count == 0
            assert transport._called_connection_lost and transport._sock is None
            assert left.fileno() == -1
        finally:
            # Only fixture-owned socket/bookkeeping cleanup on a failed assertion.
            left.close(); right.close(); transport._sock = None
            if transport._server is not None:
                transport._server._detach(); transport._server = None
            transport._called_connection_lost = True
            server.close()
    asyncio.run(scenario())


BACKEND = r'''
import asyncio,json,os,sqlite3,time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from uvicorn import Config,Server
from uvicorn.protocols.http.httptools_impl import HttpToolsProtocol
from src.services.windows_socket_cleanup import install_windows_socket_cleanup
p=Path(__file__).parent
def record(event,**fields):
    with (p/'events.jsonl').open('a') as f:f.write(json.dumps(dict(event=event,pid=os.getpid(),at=time.time(),**fields))+'\n')
install_windows_socket_cleanup()
pending=[]
class ResetSocket:
    def __init__(self,sock):self.sock=sock
    def __getattr__(self,key):return getattr(self.sock,key)
    def shutdown(self,how):raise ConnectionResetError(10054,'recorded peer reset')
class HTTP(HttpToolsProtocol):
    def connection_made(self,t):
        super().connection_made(t)
        original=t._call_connection_lost
        def lost(exc):
            if self.scope and self.scope.get('path')=='/reset' and not t._called_connection_lost:
                raw=t._sock;t._sock=ResetSocket(raw);record('injected_reset')
                pending.append((t,raw))
                try:return original(exc)
                finally:
                    if t._sock is not None:t._sock=raw
            return original(exc)
        t._call_connection_lost=lost
@asynccontextmanager
async def lifespan(app):
    db=sqlite3.connect(p/'fixture.db')
    db.execute('create table proof(value text)');db.execute("insert into proof values('original')");db.commit()
    db.execute("insert into proof values('in-flight write')")
    record('startup',parent=os.getppid())
    try:yield
    finally:
        record('lifespan_shutdown')
        if (p/'delayed').exists():
            end=time.monotonic()+6
            while not (p/'release').exists() and time.monotonic()<end:await asyncio.sleep(.02)
            assert (p/'release').exists(),'fixture shutdown release missing'
        db.commit();db.close();record('database_closed')
app=FastAPI(lifespan=lifespan)
@app.get('/reset')
def reset():return {'fixture':True}
@app.get('/normal')
def normal():return {'fixture':True}
class Probe(Server):
    def handle_exit(self,sig,frame):
        record('signal',sig=sig);super().handle_exit(sig,frame)
    async def on_tick(self,counter):
        if counter==0:record('listening',port=self.servers[0].sockets[0].getsockname()[1])
        if time.monotonic()-start>20:self.should_exit=True
        return await super().on_tick(counter)
    async def shutdown(self,*a,**kw):
        record('shutdown_enter');await super().shutdown(*a,**kw);record('shutdown_exit')
start=time.monotonic()
async def run():
    async def rescue():
        # Bounded fixture-only teardown if a regression strands a transport.
        # Any use is a test FAILURE, never a successful shutdown or product fix.
        await asyncio.sleep(12)
        for t,raw in pending:
            if t._server is not None:
                record('fixture_rescue');raw.close();t._sock=None
                t._server._detach();t._server=None;t._called_connection_lost=True
    task=asyncio.create_task(rescue())
    try:await Probe(Config(app,host='127.0.0.1',port=0,http=HTTP)).serve()
    finally:task.cancel();record('process_finally')
asyncio.run(run())
'''


def _events(root):
    path = root/'events.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def _until(predicate, seconds=10):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(.02)
    assert predicate(), 'bounded isolated lifecycle deadline exceeded'


@pytest.mark.skipif(os.name != 'nt' or not shutil.which('pwsh'), reason='native Windows WMI lifecycle')
@pytest.mark.parametrize('route,delayed', [('/normal', False), ('/reset', False), ('/reset', True)])
def test_real_backend_launch_tree_repeated_graceful_shutdown(tmp_path, route, delayed):
    """Actual WMI/observer/venv/helper/Uvicorn; only temporary SQLite and ports."""
    import urllib.request
    python = Path(uvicorn.__file__).parents[3]/'Scripts/python.exe'
    assert python.is_file(), 'existing approved development venv required'
    repo = Path(__file__).resolve().parents[1]
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]; k.OpenProcess.restype = w.HANDLE
    k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    k.CloseHandle.argtypes = [w.HANDLE]
    for cycle in range(2):
        root = tmp_path/str(cycle)
        for folder in ('config', 'launch', 'state/observed-role-runs/probe'):
            (root/folder).mkdir(parents=True)
        cfg = dict(canonical_sha='fixture', source_checkout=str(root),
                   product_database=str(root/'fixture.db'), backend_port=0, frontend_port=0)
        (root/'config/runtime.json').write_text(json.dumps(cfg))
        (root/'backend.py').write_text(BACKEND)
        (root/'helper.py').write_text("import subprocess,sys\ntry: code=subprocess.call([sys.executable,'-B','backend.py'])\nexcept KeyboardInterrupt: code=130\nsys.exit(code)\n")
        # Credential-free stub of the canonical helper contract, not its gate.
        (root/'launch/Invoke-Woofi.ps1').write_text(
            'param([string]$Role)\n$env:PYTHONPATH='+s.literal(str(repo)+os.pathsep+os.environ.get('PYTHONPATH',''))+
            '\nSet-Location -LiteralPath '+s.literal(root)+'\n& '+s.literal(python)+' -B '+s.literal(root/'helper.py'))
        if delayed:
            (root/'delayed').touch()
        run = root/'state/observed-role-runs/probe'
        launched = s.independent(shutil.which('pwsh'), [shutil.which('pwsh'), '-NoProfile', '-File',
            str(repo/'scripts/windows/Invoke-WoofiObservedRole.ps1'), '-Role', 'Backend',
            '-RuntimeRoot', str(root), '-RunDirectory', str(run), '-BoundedLog'], root, root/'launch.json')
        _until(lambda:any(x['event']=='listening' for x in _events(root)))
        port = next(x['port'] for x in _events(root) if x['event']=='listening')
        assert port not in (3000, 8000)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}'+route, timeout=3) as response:
            assert response.status == 200
        if route == '/reset':
            _until(lambda:any(x['event']=='injected_reset' for x in _events(root)))
        record = dict(role='Backend', identity=s.identity(launched['launch_pid']), run_directory=str(run), members=[])
        driver = s.Windows(root, shutil.which('pwsh'), s.bind(cfg), lambda *a, **kw:None)
        members = driver.observe_members(record)['members']
        assert len(members) == 5  # observer, helper redirector/native, backend redirector/native
        helper_members = [x for x in members if str(root/'helper.py') in s.psutil.Process(x['pid']).cmdline()]
        assert len(helper_members) == 2
        handles = [k.OpenProcess(0x101000, False, x['pid']) for x in members]
        assert all(handles)
        request = root/'signal.json'
        s.atomic(request, dict(record=record, binding=s.bind(cfg)))
        info = subprocess.STARTUPINFO(); info.dwFlags |= subprocess.STARTF_USESHOWWINDOW; info.wShowWindow = 0
        try:
            with (root/'signal.log').open('w') as output:
                result = subprocess.run([sys.executable, '-B', s.__file__, 'signal', '--runtime', str(root),
                    '--pwsh', shutil.which('pwsh'), '--request', str(request)], stdout=output, stderr=output,
                    creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=info, timeout=15)
            assert result.returncode == 0
            if delayed:
                _until(lambda:any(x['event']=='lifespan_shutdown' for x in _events(root)))
                _until(lambda:not any(s.alive(x) for x in helper_members), seconds=3)
                assert any(s.alive(x) for x in members)
                assert not any(x['event']=='database_closed' for x in _events(root))
                (root/'release').touch()
            _until(lambda:not any(s.alive(x) for x in members))
            events = _events(root); names = [x['event'] for x in events]
            assert len([x for x in events if x['event']=='signal']) == 1
            assert 'database_closed' in names and 'shutdown_exit' in names and 'fixture_rescue' not in names
            assert names.index('lifespan_shutdown') < names.index('database_closed') < names.index('shutdown_exit')
            assert s.read(run/'exit.json')['auto_restart'] is False
            import sqlite3
            with sqlite3.connect(root/'fixture.db') as db:
                assert db.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
                assert db.execute('PRAGMA foreign_key_check').fetchall() == []
                assert db.execute('SELECT value FROM proof').fetchall() == [('original',), ('in-flight write',)]
            codes=[]
            for handle in handles:
                code=w.DWORD(); assert k.GetExitCodeProcess(handle, ctypes.byref(code))
                assert code.value != 259; codes.append(code.value)
            s.atomic(root/'exit-codes.json', codes)
            assert not [x for x in s.psutil.process_iter(['cmdline'])
                        if str(root/'helper.py') in (x.info['cmdline'] or [])]
        finally:
            # Release only the fixture's explicit graceful delay. Never kill.
            (root/'release').touch()
            for handle in handles:
                k.CloseHandle(handle)
