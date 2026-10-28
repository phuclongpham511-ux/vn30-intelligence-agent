"""Finite fixture processes only; never invoke the canonical runtime launcher."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import pytest

pytestmark = pytest.mark.skipif(os.name != 'nt' or not shutil.which('pwsh'), reason='Windows PowerShell lifecycle')
SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/windows/Start-WoofiObservedRole.ps1'


def runtime(tmp_path):
    (tmp_path/'config').mkdir()
    (tmp_path/'launch').mkdir()
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    (tmp_path/'config/runtime.json').write_text(json.dumps({'canonical_sha':'synthetic-checkpoint',
        'source_checkout':str(tmp_path), 'product_database':str(tmp_path/'fixture.db'),
        'backend_port':port, 'frontend_port':port}))
    # The fake gate and role never import the application, read secrets or touch a DB.
    (tmp_path/'launch/Invoke-Woofi.ps1').write_text("""param([string]$Role,[switch]$CheckOnly)
if($CheckOnly){@{Ready=$true}|ConvertTo-Json;return}
Write-Output 'synthetic role'
Start-Sleep -Milliseconds 1200
exit 7
""")
    return port


def start(tmp_path, role='Backend'):
    return subprocess.run(['pwsh','-NoProfile','-File',str(SCRIPT),'-Role',role,'-RuntimeRoot',str(tmp_path)],
        capture_output=True, text=True, timeout=15)


def receipt(path):
    deadline = time.monotonic()+15
    while not path.exists() and time.monotonic()<deadline:
        time.sleep(.05)
    assert path.exists(), 'Finite fixture did not record its exit'
    return json.loads(path.read_text(encoding='utf-8-sig'))


def test_independent_observer_survives_starter_exit_and_records_real_exit_code(tmp_path):
    runtime(tmp_path)
    parent = start(tmp_path)
    assert parent.returncode == 0, parent.stderr
    result = json.loads(parent.stdout)
    run = Path(result['run_directory'])
    # Starting PowerShell has exited; the separate finite role still completes.
    exited = receipt(run/'exit.json')
    started = receipt(run/'started.json')
    assert exited['exit_code'] == 7 and exited['auto_restart'] is False
    assert exited['observer_pid'] == result['observer_pid']
    assert started['credentials_copied'] is False
    assert started['job_membership'] in (True, False, 'UNKNOWN')
    assert 'synthetic role' in (run/'stdout.log').read_text(encoding='utf-8-sig')
    assert not (tmp_path/'fixture.db').exists()


def test_occupied_role_port_is_refused_without_starting_a_child(tmp_path):
    port = runtime(tmp_path)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', port)); listener.listen()
        result = start(tmp_path)
    assert result.returncode != 0
    assert 'already has an owner' in result.stderr
    assert not (tmp_path/'state').exists()


def test_failed_canonical_gate_is_refused_before_receipts_or_child(tmp_path):
    runtime(tmp_path)
    (tmp_path/'launch/Invoke-Woofi.ps1').write_text('param([switch]$CheckOnly)\n@{Ready=$false}|ConvertTo-Json')
    result = start(tmp_path)
    assert result.returncode != 0
    assert not (tmp_path/'state').exists()
