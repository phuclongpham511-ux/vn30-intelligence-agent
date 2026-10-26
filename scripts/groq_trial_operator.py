"""Local hidden-key host for the existing gateway and one explicitly approved run.

No account declarations or egress approval are generated here. Control/config
files are trusted operator input inside the private trial directory. The caller
token remains in memory and is passed only to the evaluator's process environment.
"""
import argparse
import getpass
import hashlib
import http.client
import json
import os
from pathlib import Path
import secrets
import ssl
import subprocess
import sys
import threading
import warnings

from scripts import serve_financial_llm_gateway
from src.schemas.financial_evaluation import LiveEvaluationConfig
from src.services.financial_evaluation import load_dataset
from src.services.financial_groq_adapter import GroqChatTransport
from src.services.financial_model_adapter import (
    EvaluationStopped, SyntheticEgressGate, SyntheticGatewayModel, config_digest,
)

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://127.0.0.1:8765/evaluate'
RUNTIME_ENVIRONMENT = {'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE',
    'LOCALAPPDATA', 'LANG', 'LC_ALL'}


def read_gateway_key(environment, *, reader=None):
    key = environment.get('WOOFI_GROQ_API_KEY', '')
    if key.strip():
        return key.strip()
    if reader is None:
        if not sys.stdin.isatty():
            raise EvaluationStopped('interactive_hidden_input_required')
        def reader():
            with warnings.catch_warnings():
                warnings.simplefilter('error', getpass.GetPassWarning)
                return getpass.getpass('Groq API key (hidden; never written to disk): ')
    key = reader().strip()
    if not key:
        raise EvaluationStopped('gateway_key_missing')
    return key


def evaluator_environment(environment, token, ca_file):
    result = {name: value for name, value in environment.items() if name.upper() in RUNTIME_ENVIRONMENT}
    result.update(WOOFI_LLM_GATEWAY_TOKEN=token, WOOFI_LLM_GATEWAY_CA_FILE=str(ca_file),
        PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    return result


def load_approved_config(path, *, trial_profile='baseline'):
    raw = path.read_bytes()
    if len(raw) > 16384:
        raise EvaluationStopped('configuration_too_large')
    config = LiveEvaluationConfig.model_validate_json(raw)
    b = config.budget
    profiles = {'baseline': (6656, 1280, '0.0017664'),
        'trial3-completion': (5888, 2048, '0.002112')}
    if trial_profile not in profiles:
        raise EvaluationStopped('one_request_trial_limits_required')
    input_cap, output_cap, cost_cap = profiles[trial_profile]
    if (config.provider != 'groq' or config.model != 'openai/gpt-oss-120b' or
            config.endpoint != ENDPOINT or config.input_token_overhead != 2048 or
            b.max_requests != 1 or b.max_input_tokens != input_cap or b.max_output_tokens != output_cap or
            b.per_request_input_tokens != input_cap or b.per_request_output_tokens != output_cap or
            str(b.max_cost_usd) != cost_cap):
        raise EvaluationStopped('one_request_trial_limits_required')
    # Reuse all original dataset, prompt, expiry and destination gates. No send.
    SyntheticGatewayModel(config, SyntheticEgressGate(load_dataset()),
        operator_enabled=True, egress_authorized=True)
    return config


def approve_command(command, config, *, live):
    expected = 'run_once' if live else 'serve_only'
    if (command.get('operation') != expected or not isinstance(command.get('nonce'), str) or
            not 1 <= len(command['nonce']) <= 100 or
            command.get('config_sha256') != config_digest(config) or
            command.get('approval_reference') != config.approval.reference or
            (live and command.get('live_invocation_approved') is not True)):
        raise EvaluationStopped('explicit_matching_operator_command_required')


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def authentication_check(ca_file):
    context = ssl.create_default_context(cafile=str(ca_file))
    connection = http.client.HTTPSConnection('127.0.0.1', 8765, timeout=5, context=context)
    try:
        connection.request('POST', '/evaluate', body=b'{}', headers={
            'Content-Type': 'application/json', 'Authorization': 'Bearer deliberately-wrong-operator-token',
            'X-Woofi-Run-ID': 'deliberately-wrong-run'})
        response = connection.getresponse()
        if response.status != 401:
            raise EvaluationStopped('caller_authentication_check_failed')
        response.read(1024)
    finally:
        connection.close()


def evaluate_once(directory, config, nonce):
    # Persist before starting the child: even an uncertain launch is never retried.
    with (directory / 'live-attempt-started.json').open('x', encoding='utf-8') as handle:
        json.dump(dict(config_sha256=config_digest(config), approval_reference=config.approval.reference,
            nonce=nonce), handle)
    environment = evaluator_environment(os.environ, os.environ['WOOFI_LLM_GATEWAY_TOKEN'],
        directory / 'loopback-ca.pem')
    args = [sys.executable, '-B', '-m', 'scripts.evaluate_financial_llm', '--mode', 'real',
        '--config', str(directory / 'gateway-config.json'), '--enable-real', '--authorize-synthetic-egress',
        '--request-interval-seconds', '0']
    with (directory / 'first-report.json').open('x', encoding='utf-8') as output, \
            (directory / 'evaluator-errors.txt').open('x', encoding='utf-8') as errors:
        result = subprocess.run(args, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
            stdout=output, stderr=errors, timeout=60)
    report_path = directory / 'first-report.json'
    report = json.loads(report_path.read_bytes()) if report_path.stat().st_size else {}
    return result.returncode, report


def run(directory, *, trial_profile='baseline'):
    directory = directory.resolve(strict=True)
    if directory == ROOT or ROOT in directory.parents:
        raise EvaluationStopped('private_directory_outside_git_required')
    state_path = directory / 'operator-status.json'
    config_path = directory / 'gateway-config.json'
    command_path = directory / 'operator-command.json'
    ca_file = directory / 'loopback-ca.pem'
    status = dict(pid=os.getpid(), endpoint=ENDPOINT, real_llm_requests=0)
    server_box = {}
    server_thread = None
    stopped = threading.Event()
    lock_path = directory / 'operator-session.lock'
    lock = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.write(lock, str(os.getpid()).encode())
    try:
        status['state'] = 'awaiting_hidden_key'
        write_json(state_path, status)
        key = read_gateway_key(os.environ)
        os.environ['WOOFI_GROQ_API_KEY'] = key
        os.environ['WOOFI_LLM_GATEWAY_TOKEN'] = secrets.token_urlsafe(48)
        status.update(state='waiting_for_verified_account_and_owner_approval', key_present=True,
            credential_sha256=hashlib.sha256(key.encode()).hexdigest())
        del key
        os.environ.update(WOOFI_GROQ_FREE_PLAN_REVIEW=str(directory / 'free-plan-review.json'),
            WOOFI_LLM_GATEWAY_CONFIG=str(config_path), WOOFI_LLM_GATEWAY_STATE=str(directory / 'usage.json'),
            WOOFI_LLM_GATEWAY_TLS_CERT=str(directory / 'loopback-cert.pem'),
            WOOFI_LLM_GATEWAY_TLS_KEY=str(directory / 'loopback-key.pem'))
        write_json(state_path, status)
        print('Key is held in this gateway process. Waiting for reviewed account/config and explicit operator commands.')
        seen = set()
        while not stopped.wait(.5):
            if not command_path.exists():
                continue
            command = json.loads(command_path.read_bytes()[:16385])
            nonce = command.get('nonce')
            if not isinstance(nonce, str) or nonce in seen:
                continue
            seen.add(nonce)
            if command.get('operation') == 'shutdown':
                return 0
            try:
                config = load_approved_config(config_path, trial_profile=trial_profile)
                GroqChatTransport.from_environment(config).preflight()  # No provider request.
                if command.get('operation') == 'serve_only':
                    approve_command(command, config, live=False)
                    if server_thread is not None:
                        raise EvaluationStopped('gateway_already_started')
                    ready = threading.Event()
                    def on_ready(server):
                        server_box['server'] = server
                        ready.set()
                    def serve():
                        server_box['exit_code'] = serve_financial_llm_gateway.run(on_ready=on_ready)
                    server_thread = threading.Thread(target=serve, daemon=True)
                    server_thread.start()
                    if not ready.wait(10) or server_box['server'].server_address != ('127.0.0.1', 8765):
                        raise EvaluationStopped('loopback_gateway_start_failed')
                    authentication_check(ca_file)
                    server_box['config_sha256'] = config_digest(config)
                    status.update(state='gateway_ready_waiting_for_live_approval', authentication_http_status=401,
                        tls_verified=True, config_sha256=config_digest(config))
                    write_json(state_path, status)
                else:
                    approve_command(command, config, live=True)
                    if server_box.get('config_sha256') != config_digest(config):
                        raise EvaluationStopped('gateway_preflight_required')
                    status.update(state='one_live_attempt_started', real_llm_requests=None)
                    write_json(state_path, status)
                    exit_code, report = evaluate_once(directory, config, nonce)
                    usage = report.get('usage') or {}
                    status.update(state='one_attempt_finished_no_retry', evaluator_exit_code=exit_code,
                        real_llm_requests=usage.get('requests') if usage.get('usage_complete') is True else None,
                        stopped_reason=report.get('stopped_reason'), usage=report.get('usage'),
                        raw_model_metrics=report.get('raw_model_metrics'),
                        verified_delivery_rate=report.get('verified_delivery_rate'))
                    write_json(state_path, status)
                    return 0
            except Exception:
                # Never write raw exceptions or command/config content to a log.
                status['state'] = 'operator_action_refused_check_review_and_limits'
                write_json(state_path, status)
                if (directory / 'live-attempt-started.json').exists():
                    return 2
        return 0
    finally:
        if 'server' in server_box:
            server_box['server'].shutdown()
        if server_thread is not None:
            server_thread.join(15)
        os.environ.pop('WOOFI_GROQ_API_KEY', None)
        os.environ.pop('WOOFI_LLM_GATEWAY_TOKEN', None)
        status.update(key_present=False, operator_process_closed=True)
        if not (directory / 'live-attempt-started.json').exists():
            status['state'] = 'closed_without_live_attempt'
        write_json(state_path, status)
        os.close(lock)
        lock_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description='Hidden-key host for one separately approved Groq trial')
    parser.add_argument('--trial-directory', type=Path, required=True)
    parser.add_argument('--trial-profile', choices=('baseline', 'trial3-completion'), default='baseline',
        help='Opt in to an exact separately approved budget; default remains the original trial')
    args = parser.parse_args()
    try:
        return run(args.trial_directory, trial_profile=args.trial_profile)
    except KeyboardInterrupt:
        return 0
    except Exception:
        print('Operator host refused setup. Check private paths and hidden terminal input.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
