"""Native read-only listener snapshots; synthetic owners and isolated sockets only."""
import os
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace as Row

import pytest

from scripts.windows import runtime_supervisor as s


CFG = {'backend_port': 18000, 'frontend_port': 13000}


def driver():
    return s.Windows(Path('.'), 'fixture-pwsh', {}, lambda *a, **k: None)


def listener(port=18000, pid=123, status=s.psutil.CONN_LISTEN):
    return Row(status=status, laddr=Row(port=port), pid=pid)


def test_listener_snapshot_does_not_depend_on_timed_out_powershell(monkeypatch):
    def timed_out(*args, **kwargs):
        raise subprocess.TimeoutExpired('synthetic-private-command', 15)
    monkeypatch.setattr(s.subprocess, 'run', timed_out)
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: [listener()])
    assert driver().ports(CFG) == [{'LocalPort': 18000, 'OwningProcess': 123}]


def test_native_snapshot_filters_tcp_listeners_and_deduplicates_dual_stack(monkeypatch):
    calls = []
    def inventory(**kw):
        calls.append(kw)
        return [listener(), listener(), listener(13000, 456), listener(12000),
                listener(status=s.psutil.CONN_ESTABLISHED)]
    monkeypatch.setattr(s.psutil, 'net_connections', inventory)
    assert driver().ports(CFG) == [
        {'LocalPort': 13000, 'OwningProcess': 456},
        {'LocalPort': 18000, 'OwningProcess': 123},
    ]
    assert calls == [{'kind': 'tcp'}]


def test_verified_native_empty_inventory(monkeypatch):
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: [])
    assert driver().ports(CFG) == []


@pytest.mark.parametrize('pid', [None, 0, -1, True, '123'])
def test_unknown_owner_never_becomes_empty_inventory(monkeypatch, pid):
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: [listener(pid=pid)])
    with pytest.raises(s.Conflict, match='LISTENER_INVENTORY_UNVERIFIABLE'):
        driver().ports(CFG)


@pytest.mark.parametrize('error', [s.psutil.AccessDenied(), OSError('synthetic-private-detail'),
                                  ValueError('synthetic-private-detail')])
def test_native_failure_is_fail_closed_and_redacted(monkeypatch, error):
    def failed(**kw): raise error
    monkeypatch.setattr(s.psutil, 'net_connections', failed)
    with pytest.raises(s.Conflict, match='LISTENER_INVENTORY_UNVERIFIABLE') as failure:
        driver().ports(CFG)
    assert 'private' not in str(failure.value)


def test_malformed_native_response_is_not_accepted(monkeypatch):
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: [Row(status=s.psutil.CONN_LISTEN)])
    with pytest.raises(s.Conflict, match='LISTENER_INVENTORY_UNVERIFIABLE'):
        driver().ports(CFG)


@pytest.mark.parametrize('rows', [None, {}, (), ''])
def test_malformed_empty_response_cannot_look_like_a_verified_empty_snapshot(monkeypatch, rows):
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: rows)
    with pytest.raises(s.Conflict, match='LISTENER_INVENTORY_UNVERIFIABLE'):
        driver().ports(CFG)


@pytest.mark.parametrize('port', [True, 0, -1, 65536, '8000'])
def test_invalid_configuration_refused_before_native_query(monkeypatch, port):
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: pytest.fail('Invalid configuration'))
    with pytest.raises(s.Conflict, match='INVALID_RUNTIME_PORT'):
        driver().ports(dict(CFG, backend_port=port))


def test_foreign_listener_still_blocks_launch_before_process_census(monkeypatch):
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: [listener(pid=999)])
    monkeypatch.setattr(s.psutil, 'process_iter', lambda *a: pytest.fail('Must refuse first'))
    with pytest.raises(s.Conflict, match='PORT_CONFLICT'):
        driver().vacant('Backend', CFG)


def test_foreign_listener_still_blocks_inspection(monkeypatch):
    win = driver()
    monkeypatch.setattr(win, 'observe_members', lambda record: {
        'running': True, 'members': [{'pid': 123}]})
    monkeypatch.setattr(s, 'read', lambda *a: CFG)
    monkeypatch.setattr(s, 'bind', lambda *a: {})
    monkeypatch.setattr(s.psutil, 'net_connections', lambda **kw: [listener(pid=999)])
    with pytest.raises(s.Conflict, match='PORT_CONFLICT'):
        win.inspect('Backend', {})


@pytest.mark.skipif(os.name != 'nt', reason='Real Windows native TCP inventory')
def test_real_windows_isolated_listener_reports_own_pid_and_releases():
    with socket.socket() as server:
        server.bind(('127.0.0.1', 0))
        server.listen()
        port = server.getsockname()[1]
        cfg = {'backend_port': port, 'frontend_port': port}
        assert driver().ports(cfg) == [{'LocalPort': port, 'OwningProcess': os.getpid()}]
        assert s.alive(s.identity(os.getpid()))
    assert driver().ports(cfg) == []
