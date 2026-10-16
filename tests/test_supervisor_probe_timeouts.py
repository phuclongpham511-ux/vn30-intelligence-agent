"""Finite probe faults, simulated roles and temporary journals; no product runtime."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.windows import runtime_supervisor as s
from tests.test_runtime_supervisor import Fake, policy


def timeout_probe(*args, **kwargs):
    raise subprocess.TimeoutExpired(args[0], kwargs['timeout'],
                                    output='synthetic-private-output')


def diagnostic(driver, monkeypatch):
    events = []
    windows = s.Windows(Path('.'), 'fixture-pwsh', {},
                        lambda name, **data: events.append((name, data)))
    monkeypatch.setattr(s.subprocess, 'run', timeout_probe)
    driver.power_evidence = windows.power_evidence
    return events


def test_optional_diagnostic_timeout_is_unverified_not_fatal(monkeypatch):
    driver = Fake()
    events = diagnostic(driver, monkeypatch)
    driver.power_evidence()
    assert events == [('power_evidence', {
        'result': 'NOT_VERIFIED',
        'reason': 'WINDOWS_PROBE_TIMEOUT probe=power_evidence timeout_seconds=15',
    })]
    assert 'synthetic-private-output' not in json.dumps(events)


def test_resume_diagnostic_timeout_preserves_healthy_roles_without_relaunch(monkeypatch):
    machine, driver, _ = policy()
    machine.tick(0, True); machine.tick(5, True)
    before = {name: row.record for name, row in machine.roles.items()}
    events = diagnostic(driver, monkeypatch)
    assert machine.tick(400, True)
    assert {name: row.record for name, row in machine.roles.items()} == before
    assert all(row.phase == 'running' and row.launches == 1 for row in machine.roles.values())
    assert driver.calls == [('launch', name, 0) for name in s.ROLES]
    assert len(events) == 1


def test_diagnostic_timeout_cannot_prevent_durable_stop(monkeypatch):
    machine, driver, _ = policy()
    machine.tick(0, True); machine.tick(5, True)
    diagnostic(driver, monkeypatch)
    assert machine.tick(400, False) is False
    assert not driver.running
    assert [c[1] for c in driver.calls if c[0] == 'stop'] == ['Collector', 'Backend', 'Frontend']
    assert all(row.record is None for row in machine.roles.values())


def test_diagnostic_timeout_keeps_resume_backoff(monkeypatch):
    machine, driver, _ = policy()
    machine.tick(0, True); machine.tick(5, True)
    driver.running.remove('Backend'); machine.tick(10, True)
    diagnostic(driver, monkeypatch)
    machine.tick(400, True); machine.tick(409, True)
    assert machine.roles['Backend'].record is None
    machine.tick(410, True)
    assert machine.roles['Backend'].launches == 2
    assert all(machine.roles[name].launches == 1 for name in ('Collector', 'Frontend'))


@pytest.mark.parametrize('probe', ['listeners', 'collector_inventory', 'canonical_preflight', 'role_launch'])
def test_critical_timeout_is_identified_and_never_an_empty_inventory(monkeypatch, probe, tmp_path):
    monkeypatch.setattr(s.subprocess, 'run', timeout_probe)
    kwargs = {'output_file': tmp_path/'receipt.json'} if probe == 'role_launch' else {}
    with pytest.raises(s.Conflict, match=f'WINDOWS_PROBE_TIMEOUT probe={probe} timeout_seconds=15') as failure:
        s.ps('fixture-pwsh', 'synthetic-private-command', probe=probe, **kwargs)
    assert 'synthetic-private' not in str(failure.value)


def test_actual_collector_ownership_adapter_propagates_timeout(monkeypatch):
    monkeypatch.setattr(s.subprocess, 'run', timeout_probe)
    driver = s.Windows(Path('.'), 'fixture-pwsh', {}, lambda *a, **k: None)
    with pytest.raises(s.Conflict, match='probe=collector_inventory'):
        driver.workers()


def test_collector_inventory_timeout_refuses_process_birth(monkeypatch, tmp_path):
    driver = s.Windows(tmp_path, 'fixture-pwsh', {}, lambda *a, **k: None)
    monkeypatch.setattr(driver, 'validate', lambda: {'product_database': str(tmp_path/'unused.db')})
    calls = []
    def delayed(*args, **kwargs):
        calls.append(args[0])
        return timeout_probe(*args, **kwargs)
    monkeypatch.setattr(s.subprocess, 'run', delayed)
    monkeypatch.setattr(s, 'lock_owners', lambda *a: pytest.fail('Unverified inventory must abort first'))
    with pytest.raises(s.Conflict, match='probe=collector_inventory'):
        driver.launch('Collector', 0)
    assert len(calls) == 1 and 'Get-CimInstance' in calls[0][-1]
    assert not list(tmp_path.iterdir())  # No birth journal, service, DB or lock.


@pytest.mark.skipif(os.name != 'nt', reason='Windows journal/control locks')
def test_launch_probe_timeout_retains_unknown_birth_journal(monkeypatch, tmp_path):
    store = s.Store(tmp_path); store.path.mkdir(parents=True)
    s.atomic(store.path/'intent.json', {'running': True})
    s.atomic(store.path/'status.json', {'epoch': 'fixture', 'roles': {}})
    driver = s.Windows(tmp_path, 'fixture-pwsh', {}, lambda *a, **k: None)
    driver.epoch = 'fixture'
    monkeypatch.setattr(driver, 'validate', lambda: {})
    monkeypatch.setattr(driver, 'vacant', lambda *a: None)
    monkeypatch.setattr(s.subprocess, 'run', timeout_probe)
    with pytest.raises(s.Conflict, match='probe=role_launch timeout_seconds=25'):
        driver.launch('Collector', 0)
    assert store.load()['pending_launch'] == 'Collector'
    assert store.load()['roles']['Collector']['launches'] == 1
    assert store.desired() is True
    with pytest.raises(s.Conflict, match='LAUNCH_OUTCOME_UNKNOWN'):
        s.control('start', tmp_path, 'fixture-pwsh')


def test_unknown_ownership_is_not_swallowed_after_optional_timeout(monkeypatch):
    machine, driver, _ = policy()
    machine.tick(0, True); machine.tick(5, True)
    diagnostic(driver, monkeypatch)
    before = {name: row.record for name, row in machine.roles.items()}
    def unknown(*args):
        raise s.Conflict('PROCESS_IDENTITY_UNVERIFIABLE')
    driver.inspect = unknown
    with pytest.raises(s.Conflict, match='PROCESS_IDENTITY_UNVERIFIABLE'):
        machine.tick(400, True)
    assert {name: row.record for name, row in machine.roles.items()} == before
    assert len(driver.calls) == 3


@pytest.mark.skipif(os.name != 'nt', reason='Windows journal/control locks')
@pytest.mark.parametrize('fault', ['powershell_timeout', 'native_listener_failure'])
def test_critical_probe_timeout_keeps_manifest_and_intent(monkeypatch, tmp_path, fault):
    store = s.Store(tmp_path); store.path.mkdir(parents=True)
    rows = {name: {'record': {'identity': {'pid': i}, 'role': name},
                   'members': [{'pid': i}], 'phase': 'running', 'launches': 1}
            for i, name in enumerate(s.ROLES, 1)}
    s.atomic(store.path/'intent.json', {'running': True})
    s.atomic(store.path/'status.json', {'epoch': 'fixture', 'binding': {},
                                       'roles': {}, 'resume_roles': rows})
    class Driver(Fake):
        def __init__(self, *args): super().__init__()
        def inspect(self, *args):
            if fault == 'native_listener_failure':
                return native.ports({'backend_port': 18000, 'frontend_port': 13000})
            return s.ps('fixture-pwsh', 'private-command', probe='listeners')
    native = s.Windows(tmp_path, 'fixture-pwsh', {}, lambda *a, **k: None)
    def unavailable(**kwargs): raise OSError('synthetic-private-detail')
    monkeypatch.setattr(s.psutil, 'net_connections', unavailable)
    monkeypatch.setattr(s, 'Windows', Driver)
    monkeypatch.setattr(s, 'alive', lambda *a: False)
    monkeypatch.setattr(s, 'identity', lambda *a: {'pid': 99})
    monkeypatch.setattr(s.subprocess, 'run', timeout_probe)
    reason = 'probe=listeners' if fault == 'powershell_timeout' else 'LISTENER_INVENTORY_UNVERIFIABLE'
    with pytest.raises(s.Conflict, match=reason):
        s.run(tmp_path, 'fixture-pwsh', 'fixture')
    result = store.load()
    assert result['phase'] == 'blocked' and store.desired() is True
    assert all(result['roles'][name]['record'] == row['record'] for name, row in rows.items())
    events = [json.loads(line) for line in (store.path/'events.jsonl').read_text().splitlines()]
    assert events[-1]['event'] == 'supervisor_exit' and events[-1]['expected'] is False
    assert not any(e['event'] in ('role_launched', 'role_stopped') for e in events)


@pytest.mark.parametrize('code,expected', [('ConvertTo-Json -InputObject @()', []),
                                         ('ConvertTo-Json -InputObject @(@{Id=42})', [{'Id': 42}])])
def test_actual_powershell_success_contract(code, expected):
    pwsh = shutil.which('pwsh')
    if os.name != 'nt' or not pwsh: pytest.skip('Windows PowerShell executable')
    assert s.ps(pwsh, code, timeout=5, probe='power_evidence') == expected


def test_real_isolated_powershell_timeout_is_bounded_and_child_is_reaped(tmp_path):
    pwsh = shutil.which('pwsh')
    if os.name != 'nt' or not pwsh: pytest.skip('Windows PowerShell executable')
    pid_file = tmp_path/'probe-pid.txt'
    code = f'[IO.File]::WriteAllText({s.literal(pid_file)},[string]$PID); Start-Sleep -Seconds 10'
    with pytest.raises(s.Conflict, match='probe=power_evidence timeout_seconds=3'):
        s.ps(pwsh, code, timeout=3, probe='power_evidence')
    assert pid_file.exists(), 'Fixture must enter the delayed command before timeout'
    assert not s.psutil.pid_exists(int(pid_file.read_text()))
