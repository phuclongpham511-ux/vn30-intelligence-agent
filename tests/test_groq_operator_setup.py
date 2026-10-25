"""Local operator setup: no account secret, provider or network access."""
import hashlib
import json
import os
from pathlib import Path
import ssl
import subprocess
import socket
import threading
import time
from decimal import Decimal

import pytest

from scripts import groq_trial_operator as operator
from src.services.financial_model_adapter import EvaluationStopped, config_digest
from test_financial_groq_gateway import groq_config

ROOT = Path(__file__).resolve().parents[1]
TLS_HELPER = ROOT / 'docs/operator-readiness/groq-first-trial/prepare-loopback-tls.ps1'
WINDOWS_POWERSHELL = Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')


def local_environment():
    return {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'USERPROFILE', 'LOCALAPPDATA', 'PROGRAMFILES'}}


def memory_tls_handshake(directory):
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(directory / 'loopback-cert.pem', directory / 'loopback-key.pem')
    client_context = ssl.create_default_context(cafile=str(directory / 'loopback-ca.pem'))
    incoming_c, outgoing_c, incoming_s, outgoing_s = (ssl.MemoryBIO() for _ in range(4))
    client = client_context.wrap_bio(incoming_c, outgoing_c, server_hostname='127.0.0.1')
    server = server_context.wrap_bio(incoming_s, outgoing_s, server_side=True)
    completed = set()
    for _ in range(12):
        for name, endpoint in [('client', client), ('server', server)]:
            try:
                endpoint.do_handshake()
                completed.add(name)
            except ssl.SSLWantReadError:
                pass
        incoming_s.write(outgoing_c.read())
        incoming_c.write(outgoing_s.read())
        if len(completed) == 2:
            assert ('IP Address', '127.0.0.1') in client.getpeercert()['subjectAltName']
            return
    pytest.fail('loopback TLS handshake did not complete')


@pytest.mark.skipif(os.name != 'nt' or not WINDOWS_POWERSHELL.exists(), reason='Windows 5.1 entry point required')
def test_windows_51_entry_discovers_modern_runtime_and_preserves_existing_tls(tmp_path):
    directory = tmp_path / 'tls'
    command = [str(WINDOWS_POWERSHELL), '-NoLogo', '-NoProfile', '-NonInteractive',
        '-File', str(TLS_HELPER), '-OutputDirectory', str(directory)]
    first = subprocess.run(command, capture_output=True, text=True, env=local_environment(), timeout=30)
    assert first.returncode == 0, first.stderr
    paths = json.loads(first.stdout)
    assert int(paths['PowerShellVersion'].split('.')[0]) >= 7
    memory_tls_handshake(directory)
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()}
    second = subprocess.run(command, capture_output=True, text=True, env=local_environment(), timeout=30)
    assert second.returncode != 0
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()}


def test_key_stays_out_of_evaluator_environment_and_requires_hidden_input(monkeypatch):
    secret = 'synthetic-provider-key-only'
    assert operator.read_gateway_key({'WOOFI_GROQ_API_KEY': secret}) == secret
    assert operator.read_gateway_key({}, reader=lambda: secret) == secret
    monkeypatch.setattr('sys.stdin.isatty', lambda: False)
    with pytest.raises(EvaluationStopped, match='hidden_input'):
        operator.read_gateway_key({})
    environment = operator.evaluator_environment(dict(SystemRoot='C:/Windows', WOOFI_GROQ_API_KEY=secret,
        WOOFI_LLM_GATEWAY_TLS_KEY='private-key.pem', ANOTHER_API_KEY='private'), 'synthetic-caller-token', 'ca.pem')
    assert secret not in json.dumps(environment)
    assert set(environment) == {'SystemRoot', 'WOOFI_LLM_GATEWAY_TOKEN', 'WOOFI_LLM_GATEWAY_CA_FILE',
        'PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING'}


def one_request_config():
    config = groq_config()
    config.budget.max_requests = 1
    config.budget.max_input_tokens = 6656
    config.budget.max_output_tokens = 1280
    config.budget.max_cost_usd = Decimal('.0017664')
    return config


def test_fixed_budget_and_independent_live_authorization_are_required(tmp_path):
    config = one_request_config()
    path = tmp_path / 'gateway-config.json'
    path.write_text(config.model_dump_json(), encoding='utf-8')
    assert operator.load_approved_config(path).budget.max_requests == 1
    command = dict(operation='serve_only', nonce='test-one', config_sha256=config_digest(config),
        approval_reference=config.approval.reference)
    operator.approve_command(command, config, live=False)
    command['operation'] = 'run_once'
    with pytest.raises(EvaluationStopped, match='explicit_matching'):
        operator.approve_command(command, config, live=True)
    command['live_invocation_approved'] = True
    operator.approve_command(command, config, live=True)
    config.budget.max_requests = 2
    path.write_text(config.model_dump_json(), encoding='utf-8')
    with pytest.raises(EvaluationStopped, match='one_request_trial'):
        operator.load_approved_config(path)


def test_one_attempt_sentinel_prevents_retry_and_child_receives_no_provider_key(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setenv('WOOFI_GROQ_API_KEY', 'synthetic-provider-key-only')
    monkeypatch.setenv('WOOFI_LLM_GATEWAY_TOKEN', 'synthetic-caller-token')
    def fake_run(args, **kwargs):
        calls.append((args, kwargs['env']))
        assert 'WOOFI_GROQ_API_KEY' not in kwargs['env']
        assert '--enable-real' in args and '--authorize-synthetic-egress' in args
        json.dump(dict(stopped_reason='run_budget_exhausted', usage=dict(requests=1, usage_complete=True)),
            kwargs['stdout'])
        return type('Result', (), {'returncode': 1})()
    monkeypatch.setattr(operator.subprocess, 'run', fake_run)
    exit_code, report = operator.evaluate_once(tmp_path, one_request_config(), 'synthetic-explicit-approval')
    assert exit_code == 1 and report['usage']['requests'] == 1
    with pytest.raises(FileExistsError):
        operator.evaluate_once(tmp_path, one_request_config(), 'must-not-retry')
    assert len(calls) == 1


def test_operator_host_waits_without_creating_approval_or_egress(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Unapproved operator host attempted network access')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(operator, 'read_gateway_key', lambda env: 'synthetic-provider-key-only')
    monkeypatch.setenv('WOOFI_GROQ_API_KEY', 'synthetic-provider-key-only')
    monkeypatch.setenv('WOOFI_LLM_GATEWAY_TOKEN', 'synthetic-temporary-caller')
    result = []
    thread = threading.Thread(target=lambda: result.append(operator.run(tmp_path)), daemon=True)
    thread.start()
    status_path = tmp_path / 'operator-status.json'
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if status_path.exists() and json.loads(status_path.read_bytes()).get('key_present'):
            break
        time.sleep(.02)
    else:
        pytest.fail('operator did not reach waiting state')
    assert not (tmp_path / 'gateway-config.json').exists()
    assert not (tmp_path / 'free-plan-review.json').exists()
    assert 'synthetic-provider-key-only' not in status_path.read_text()
    operator.write_json(tmp_path / 'operator-command.json', dict(operation='shutdown', nonce='test-shutdown'))
    thread.join(5)
    assert result == [0] and not thread.is_alive()
    assert not (tmp_path / 'operator-session.lock').exists()
    assert not (tmp_path / 'live-attempt-started.json').exists()
    closed = json.loads(status_path.read_bytes())
    assert closed['key_present'] is False and closed['operator_process_closed'] is True


@pytest.mark.skipif(os.name != 'nt' or not WINDOWS_POWERSHELL.exists(), reason='Windows TLS setup required')
def test_serve_only_command_checks_real_loopback_tls_auth_without_upstream(tmp_path, monkeypatch):
    probe = socket.socket()
    try:
        probe.bind(('127.0.0.1', 8765))
    except OSError:
        pytest.skip('Operator loopback port is already in use')
    finally:
        probe.close()
    directory = tmp_path / 'private-trial'
    setup = subprocess.run([str(WINDOWS_POWERSHELL), '-NoLogo', '-NoProfile', '-NonInteractive',
        '-File', str(TLS_HELPER), '-OutputDirectory', str(directory)], env=local_environment(),
        capture_output=True, text=True, timeout=30)
    assert setup.returncode == 0, setup.stderr
    connect = socket.socket.connect
    def loopback_only(sock, address):
        assert address[0] == '127.0.0.1', 'unexpected external network attempt'
        return connect(sock, address)
    monkeypatch.setattr(socket.socket, 'connect', loopback_only)
    monkeypatch.setattr(operator, 'read_gateway_key', lambda env: 'synthetic-provider-key-only')
    monkeypatch.setenv('WOOFI_GROQ_API_KEY', 'synthetic-provider-key-only')
    monkeypatch.setenv('WOOFI_LLM_GATEWAY_TOKEN', 'synthetic-caller-only')
    class NoUpstream:
        def preflight(self): return dict(rpm=30, rpd=1000, tpm=8000, tpd=200000)
        def send(self, payload): pytest.fail('serve_only must not invoke upstream')
    monkeypatch.setattr(operator.GroqChatTransport, 'from_environment', lambda config: NoUpstream())
    config = one_request_config()
    (directory / 'gateway-config.json').write_text(config.model_dump_json(), encoding='utf-8')
    operator.write_json(directory / 'operator-command.json', dict(operation='serve_only', nonce='synthetic-serve',
        config_sha256=config_digest(config), approval_reference=config.approval.reference))
    results = []
    thread = threading.Thread(target=lambda: results.append(operator.run(directory)), daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            status_path = directory / 'operator-status.json'
            if status_path.exists():
                state = json.loads(status_path.read_bytes())
                if state.get('state') == 'gateway_ready_waiting_for_live_approval':
                    break
            time.sleep(.02)
        else:
            pytest.fail('serve_only did not reach verified loopback readiness')
        assert state['authentication_http_status'] == 401 and state['tls_verified']
        assert state['real_llm_requests'] == 0
        assert not (directory / 'live-attempt-started.json').exists()
        assert not (directory / 'usage.json').exists()  # Wrong caller cannot consume a reservation.
    finally:
        operator.write_json(directory / 'operator-command.json', dict(operation='shutdown', nonce='synthetic-stop'))
        thread.join(15)
    assert results == [0] and not thread.is_alive()
