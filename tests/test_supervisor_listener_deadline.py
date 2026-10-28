"""Bound the native Windows reader without running services or acquiring DB locks."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from types import SimpleNamespace

import pytest
from scripts.windows import runtime_supervisor as s

CFG = {'backend_port': 18000, 'frontend_port': 13000}


def driver(): return s.Windows(Path('.'), 'unused-pwsh', {}, lambda *a, **k: None)


def test_native_listener_must_run_outside_daemon_with_deadline(monkeypatch):
    calls = []
    monkeypatch.setenv('PATHEXT', '.COM;.EXE;.BAT;.CMD')
    monkeypatch.setenv('SSI_API_KEY', 'synthetic-private-key')
    monkeypatch.setenv('TECHNICAL_EOD_PILOT', 'true')
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: pytest.fail('Unbounded in-daemon native call'))
    def completed(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout='[{"LocalPort":18000,"OwningProcess":123}]')
    monkeypatch.setattr(s.subprocess, 'run', completed)
    assert driver().ports(CFG) == [{'LocalPort':18000,'OwningProcess':123}]
    argv, kwargs = calls[0]
    assert argv[:2] == [s.sys._base_executable, '-S']
    assert Path(argv[2]).samefile(s.__file__)
    assert argv[3] == 'listeners' and 'unused-pwsh' in argv
    assert kwargs['timeout'] == 5 and kwargs['capture_output'] and kwargs['text']
    assert kwargs['env']['PYTHONPATH'] == str(Path(s.psutil.__file__).resolve().parents[1])
    assert not {'SSI_API_KEY','TECHNICAL_EOD_PILOT'} & kwargs['env'].keys()


def test_native_timeout_is_not_empty_inventory(monkeypatch):
    monkeypatch.setenv('PATHEXT', '.EXE;.CMD')
    def timeout(*args, **kwargs): raise subprocess.TimeoutExpired('synthetic-private-command',kwargs['timeout'])
    monkeypatch.setattr(s.subprocess, 'run', timeout)
    with pytest.raises(s.Conflict, match='WINDOWS_PROBE_TIMEOUT probe=native_listeners timeout_seconds=5') as error:
        driver().ports(CFG)
    assert 'private' not in str(error.value)


@pytest.mark.parametrize('code,payload', [(1,'synthetic-private-error'),(0,''),(0,'{}'),
    (0,'null'),(0,'invalid-json'),(0,'[{"LocalPort":18000,"OwningProcess":null}]'),
    (0,'[{"LocalPort":18000,"OwningProcess":true}]'),
    (0,'[{"LocalPort":12000,"OwningProcess":123}]'),
    (0,'[{"LocalPort":true,"OwningProcess":123}]')])
def test_incomplete_or_failed_helper_never_verifies_ownership(monkeypatch, code, payload):
    monkeypatch.setenv('PATHEXT', '.EXE;.CMD')
    monkeypatch.setattr(s.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=code,stdout=payload))
    with pytest.raises(s.Conflict, match='LISTENER_INVENTORY_UNVERIFIABLE') as error:
        driver().ports(CFG)
    assert 'private' not in str(error.value)


@pytest.mark.skipif(os.name != 'nt', reason='Windows native helper')
def test_real_helper_sees_ipv4_and_ipv6_and_leaves_no_child():
    sockets = []
    try:
        for family, address in [(socket.AF_INET,'127.0.0.1'),(socket.AF_INET6,'::1')]:
            server=socket.socket(family,socket.SOCK_STREAM)
            sockets.append(server)
            server.bind((address,0)); server.listen()
        cfg=dict(zip(('backend_port','frontend_port'),(p.getsockname()[1] for p in sockets)))
        before={p.pid for p in s.psutil.Process().children()}
        rows=driver().ports(cfg)
        assert {(r['LocalPort'],r['OwningProcess']) for r in rows} == {(p,os.getpid()) for p in cfg.values()}
        assert {p.pid for p in s.psutil.Process().children()} == before
    finally:
        for server in sockets: server.close()


@pytest.mark.skipif(os.name != 'nt', reason='Real isolated native-reader timeout')
def test_delayed_isolated_reader_is_bounded_and_only_probe_is_reaped(tmp_path, monkeypatch):
    script=tmp_path/'reader.py'
    pid_file=tmp_path/'probe-pid.txt'
    script.write_text('import os,time\nfrom pathlib import Path\n'
        f'Path({str(pid_file)!r}).write_text(str(os.getpid()))\ntime.sleep(30)\n',encoding='utf-8')
    real_run=s.subprocess.run
    def delayed(argv, **kwargs):
        assert argv[3]=='listeners'
        kwargs['timeout']=1  # Speed up only the deliberately delayed isolated fixture.
        return real_run([argv[0],'-S',str(script)],**kwargs)
    monkeypatch.setattr(s.subprocess,'run',delayed)
    started=time.monotonic()
    with pytest.raises(s.Conflict,match='probe=native_listeners'):
        driver().ports(CFG)
    assert time.monotonic()-started<5
    assert pid_file.exists(), 'Probe must enter the delayed path'
    assert not s.psutil.pid_exists(int(pid_file.read_text()))
