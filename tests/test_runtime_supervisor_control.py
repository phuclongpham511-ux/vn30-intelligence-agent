"""Deterministic isolated control interleavings; no real roles or databases.

The controller and native Windows file locks are real. All process identities,
launches and shutdowns are simulated; Events select the interleaving, not sleeps.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from scripts.windows import runtime_supervisor as s
REAL_WINDOWS = s.Windows

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows interprocess locks')


@pytest.fixture
def control_fixture(tmp_path, monkeypatch):
    (tmp_path/'config').mkdir()
    cfg = {'canonical_sha':'fixture', 'source_checkout':str(tmp_path/'source'),
           'product_database':str(tmp_path/'unused.db'), 'backend_port':18000,
           'frontend_port':13000}
    s.atomic(tmp_path/'config/runtime.json', cfg)
    store = s.Store(tmp_path); store.path.mkdir(parents=True)
    live = set(); calls = []; hooks = {}; births = []
    monkeypatch.setattr(s, 'alive', lambda row: bool(row and row['pid'] in live))

    def item(pid): return {'pid':pid, 'created':1, 'exe':'FIXTURE'}

    def old_roles():
        rows = {}
        for role, pid in zip(s.ROLES, (1,2,3)):
            live.add(pid)
            rows[role] = {'record':{'identity':item(pid), 'role':role},
                          'members':[item(pid)], 'launches':1, 'phase':'running'}
        s.atomic(store.path/'intent.json', {'running':True})
        s.atomic(store.path/'status.json', {'epoch':'old', 'binding':s.bind(cfg), 'roles':rows})

    class Driver:
        def __init__(self, *args): self.epoch = None
        def validate(self): return cfg
        def vacant(self, role, config):
            if hooks.get('vacant'): hooks['vacant'](role)
            if live & {1,2,3,101}:
                raise s.Conflict('COLLECTOR_ALREADY_OWNED')
        def stop(self, role, record, members):
            calls.append(role)
            if hooks.get('stop_before'): hooks['stop_before'](role)
            live.discard(record['identity']['pid'])
            if hooks.get('stop_after'): hooks['stop_after'](role)

    def launch(*args):
        if hooks.get('launch'): return hooks['launch']()
        state = store.load(); births.append(state['epoch'])
        state['supervisor'] = item(100)
        state.pop('pending_launch', None)
        state['roles'] = {'Collector':{'record':{'identity':item(101), 'role':'Collector'},
                                      'members':[item(101)], 'launches':1}}
        live.update((100,101))
        s.atomic(store.path/'status.json', state)
        if hooks.get('launch_after'): hooks['launch_after']()
        return {'launch_pid':100}

    monkeypatch.setattr(s, 'Windows', Driver)
    monkeypatch.setattr(s, 'independent', launch)
    return tmp_path, store, live, calls, hooks, births, old_roles


def test_original_race_old_stop_cannot_erase_concurrent_start(control_fixture):
    root, store, live, calls, hooks, births, old_roles = control_fixture
    old_roles()
    final_exit = threading.Event(); start_decided = threading.Event()
    def after(role):
        if role == 'Frontend':
            final_exit.set()
            assert start_decided.wait(5)
    hooks['stop_after'] = after
    # Observe the actual competing lock attempt, so this test never depends on
    # how quickly a worker thread happens to be scheduled.
    real_lock = s.file_lock
    from contextlib import contextmanager
    from unittest.mock import patch
    @contextmanager
    def observed_lock(path, wait=0):
        if threading.current_thread().name == 'competing-start' and not start_decided.is_set():
            probe = real_lock(path, 0)
            try:
                probe.__enter__()
            except s.Conflict:
                start_decided.set()  # Start is blocked by Stop's operation lock.
                with real_lock(path, wait): yield
            else:
                try: yield
                finally:
                    probe.__exit__(None, None, None)
                    start_decided.set()  # Old implementation completed Start first.
        else:
            with real_lock(path, wait): yield
    def competing_start():
        threading.current_thread().name = 'competing-start'
        return s.control('start', root, 'FAKE')
    with patch.object(s, 'file_lock', observed_lock), ThreadPoolExecutor(max_workers=2) as pool:
        stop = pool.submit(s.control, 'stop', root, 'FAKE')
        assert final_exit.wait(5)
        start = pool.submit(competing_start)
        stopped = stop.result(timeout=10)
        started = start.result(timeout=10)
    assert not stopped['supervisor_alive'] and not stopped['desired_running']
    assert started['supervisor_alive']
    saved = store.load()
    assert saved['epoch'] == births[0] and saved['epoch'] != 'old'
    assert saved['supervisor']['pid'] == 100
    assert saved['roles']['Collector']['record']['identity']['pid'] == 101
    assert live == {100,101} and calls == ['Collector','Backend','Frontend']


@pytest.mark.parametrize('competing', ['start', 'stop'])
def test_start_serializes_duplicate_start_or_subsequent_stop(control_fixture, monkeypatch, competing):
    root, store, live, calls, hooks, births, _ = control_fixture
    acknowledged = threading.Event(); contender_blocked = threading.Event()
    def launched():
        acknowledged.set()
        assert contender_blocked.wait(5)
    hooks['launch_after'] = launched
    real_lock = s.file_lock
    from contextlib import contextmanager
    @contextmanager
    def observed_lock(path, wait=0):
        if threading.current_thread().name == 'contender' and path.name == 'control.lock':
            with pytest.raises(s.Conflict, match='SUPERVISOR_BUSY'):
                with real_lock(path): pytest.fail('Start must serialize the competing command')
            contender_blocked.set()
        with real_lock(path, wait): yield
    monkeypatch.setattr(s, 'file_lock', observed_lock)
    real_atomic = s.atomic
    def atomic(path, value):
        real_atomic(path, value)
        if path.name == 'intent.json' and not value['running']:
            live.discard(100)  # Simulate daemon exit; recorded child remains for fallback.
    monkeypatch.setattr(s, 'atomic', atomic)
    def contender():
        threading.current_thread().name = 'contender'
        return s.control(competing, root, 'FAKE')
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(s.control, 'start', root, 'FAKE')
        assert acknowledged.wait(5)
        second = pool.submit(contender)
        assert first.result(timeout=10)['supervisor_alive']
        result = second.result(timeout=10)
    assert len(births) == 1
    if competing == 'start':
        assert result['supervisor_alive'] and live == {100,101} and not calls
    else:
        assert not result['supervisor_alive'] and not result['desired_running']
        assert not live and calls == ['Collector']


def test_interrupted_stop_retains_intent_and_ownership_then_recovers(control_fixture):
    root, store, live, calls, hooks, births, old_roles = control_fixture
    old_roles()
    def fail(role):
        if role == 'Backend': raise s.Conflict('SIMULATED_CONTROLLER_FAILURE')
    hooks['stop_before'] = fail
    with pytest.raises(s.Conflict, match='SIMULATED_CONTROLLER_FAILURE'):
        s.control('stop', root, 'FAKE')
    assert not store.desired() and live == {1,2}
    assert store.load()['roles']['Collector']['record'] is None
    assert store.load()['roles']['Backend']['record']['identity']['pid'] == 1
    with pytest.raises(s.Conflict, match='STOP_IN_PROGRESS'):
        s.control('start', root, 'FAKE')
    assert s.control('resume', root, 'FAKE') == {'result':'STOP_INTENT_RETAINED'}
    hooks.clear()
    stopped = s.control('stop', root, 'FAKE')
    assert not stopped['member_alive'] and not live and not births
    assert store.load()['control_phase'] == 'stopped'
    assert not s.control('stop', root, 'FAKE')['desired_running']


def test_uncertain_interrupted_start_never_claims_success_or_replaces_epoch(control_fixture):
    root, store, live, calls, hooks, births, _ = control_fixture
    def interrupted(): raise s.Conflict('SIMULATED_BOOTSTRAP_OUTCOME_UNKNOWN')
    hooks['launch'] = interrupted
    with pytest.raises(s.Conflict, match='SIMULATED_BOOTSTRAP_OUTCOME_UNKNOWN'):
        s.control('start', root, 'FAKE')
    epoch = store.load()['epoch']
    assert store.load()['pending_launch'] == 'supervisor'
    with pytest.raises(s.Conflict, match='LAUNCH_OUTCOME_UNKNOWN'):
        s.control('start', root, 'FAKE')
    with pytest.raises(s.Conflict, match='LAUNCH_OUTCOME_UNKNOWN'):
        s.control('stop', root, 'FAKE')
    assert store.load()['epoch'] == epoch and not store.desired()
    assert not live and not births and not calls


def test_delayed_bootstrap_after_interrupted_stop_obeys_stopped_intent(control_fixture, monkeypatch):
    root, store, live, calls, hooks, births, _ = control_fixture
    s.atomic(store.path/'status.json', {'epoch':'late', 'binding':s.bind(s.read(root/'config/runtime.json')),
                                     'roles':{}, 'pending_launch':'supervisor', 'control_phase':'stopping'})
    s.atomic(store.path/'intent.json', {'running':False})
    monkeypatch.setattr(s, 'identity', lambda pid: {'pid':100, 'created':1, 'exe':'FIXTURE'})
    s.run(root, 'FAKE', 'late')
    assert not store.load().get('pending_launch')
    assert store.load()['phase'] == 'stopped' and not births and not calls
    assert not s.control('stop', root, 'FAKE')['desired_running']
    assert s.control('resume', root, 'FAKE') == {'result':'STOP_INTENT_RETAINED'}


def test_acknowledged_start_survives_controller_failure_without_second_birth(control_fixture):
    root, store, live, calls, hooks, births, _ = control_fixture
    def fail(): raise s.Conflict('SIMULATED_CONTROLLER_FAILURE')
    hooks['launch_after'] = fail
    with pytest.raises(s.Conflict, match='SIMULATED_CONTROLLER_FAILURE'):
        s.control('start', root, 'FAKE')
    hooks.clear()
    assert s.control('start', root, 'FAKE')['supervisor_alive']
    assert len(births) == 1 and store.load()['roles']['Collector']['record']
    live.discard(100)  # Daemon failure; Stop must retain and stop only the recorded child.
    assert not s.control('stop', root, 'FAKE')['member_alive']
    assert not live and calls == ['Collector']


def test_stale_manifest_write_preserves_new_generation(control_fixture):
    root, store, live, calls, hooks, births, _ = control_fixture
    s.control('start', root, 'FAKE')
    before = (store.path/'status.json').read_bytes()
    with pytest.raises(s.Conflict, match='STALE_START_EPOCH'):
        store.publish({'epoch':'old', 'roles':{}})
    assert (store.path/'status.json').read_bytes() == before and live == {100,101}


def test_same_generation_cannot_clear_live_ownership(control_fixture):
    root, store, live, calls, hooks, births, _ = control_fixture
    s.control('start', root, 'FAKE')
    state = store.load(); state['roles'] = {}
    with pytest.raises(s.Conflict, match='LIVE_OWNERSHIP_REPLACEMENT'): store.publish(state)
    assert store.load()['roles']['Collector']['record']['identity']['pid'] == 101


@pytest.mark.parametrize('operation', ['launch', 'stop', 'run'])
def test_stale_generation_cannot_launch_signal_or_publish(control_fixture, monkeypatch, operation):
    root, store, live, calls, hooks, births, _ = control_fixture
    s.control('start', root, 'FAKE')
    before = (store.path/'status.json').read_bytes()
    driver = REAL_WINDOWS(root, 'FAKE', {}, lambda *a,**k: None); driver.epoch = 'old'
    monkeypatch.setattr(driver, 'validate', lambda: {})
    monkeypatch.setattr(driver, 'vacant', lambda *a: None)
    monkeypatch.setattr(s, 'ps', lambda *a,**k: pytest.fail('Stale birth must be refused'))
    monkeypatch.setattr(s.subprocess, 'run', lambda *a,**k: pytest.fail('Stale signal must be refused'))
    with pytest.raises(s.Conflict, match='STALE_START_EPOCH'):
        if operation == 'launch': driver.launch('Collector', 0)
        elif operation == 'stop': driver.stop('Collector', {'identity':{'pid':101}}, [])
        else: s.run(root, 'FAKE', 'old')
    assert (store.path/'status.json').read_bytes() == before and not calls


def test_collector_conflict_preserves_foreign_owner_without_launch_or_stop(control_fixture):
    root, store, live, calls, hooks, births, _ = control_fixture
    live.add(101)  # Unrecorded foreign owner: the process census must refuse adoption.
    with pytest.raises(s.Conflict, match='COLLECTOR_ALREADY_OWNED'):
        s.control('start', root, 'FAKE')
    assert not store.desired() and live == {101} and not calls and not births


def test_stop_never_clears_unknown_or_changed_process_identity(control_fixture):
    root, store, live, calls, hooks, births, old_roles = control_fixture
    old_roles()
    def refuse(role): raise s.Conflict('PROCESS_IDENTITY_UNVERIFIABLE')
    hooks['stop_before'] = refuse
    with pytest.raises(s.Conflict, match='PROCESS_IDENTITY_UNVERIFIABLE'):
        s.control('stop', root, 'FAKE')
    assert live == {1,2,3} and not store.desired()
    assert all(row['record'] for row in store.load()['roles'].values())


def test_pending_role_birth_and_budget_survive_supervisor_failure(control_fixture, monkeypatch):
    root, store, live, calls, hooks, births, _ = control_fixture
    s.atomic(store.path/'status.json', {'epoch':'role-birth', 'roles':{}, 'binding':{}})
    s.atomic(store.path/'intent.json', {'running':True})
    driver = REAL_WINDOWS(root, 'FAKE', {}, lambda *a,**k: None); driver.epoch = 'role-birth'
    driver.roles = {'Collector':s.Role(launches=3)}
    monkeypatch.setattr(driver, 'validate', lambda: {})
    monkeypatch.setattr(driver, 'vacant', lambda *a: None)
    def fail(*a,**k): raise s.Conflict('UNKNOWN_ROLE_LAUNCH')
    monkeypatch.setattr(s, 'ps', fail)
    with pytest.raises(s.Conflict, match='UNKNOWN_ROLE_LAUNCH'): driver.launch('Collector', 0)
    store.publish({'epoch':'role-birth', 'roles':{'Collector':{'record':None, 'launches':3}}})
    assert store.load()['pending_launch'] == 'Collector'
    assert store.load()['roles']['Collector']['launches'] == 3
    with pytest.raises(s.Conflict, match='LAUNCH_OUTCOME_UNKNOWN'):
        s.control('stop', root, 'FAKE')
    assert not store.desired()


def test_old_daemon_exception_path_cannot_overwrite_new_generation(control_fixture, monkeypatch):
    root, store, live, calls, hooks, births, _ = control_fixture
    s.atomic(store.path/'status.json', {'epoch':'old', 'binding':{}, 'roles':{}})
    s.atomic(store.path/'intent.json', {'running':True})
    monkeypatch.setattr(s, 'identity', lambda pid: {'pid':100, 'created':1, 'exe':'FIXTURE'})
    saved = {}
    class Policy:
        def __init__(self, *a, **k): self.roles = {}
        def tick(self, *a):
            # Fault injection of a newer generation during an old daemon tick.
            # Both the normal publish and exception publish must reject it.
            state = {'epoch':'new', 'supervisor':{'pid':200, 'created':1, 'exe':'FIXTURE'},
                     'roles':{'Collector':{'record':{'identity':{'pid':201}}}}}
            live.update((200,201))
            s.atomic(store.path/'status.json', state)
            saved['bytes'] = (store.path/'status.json').read_bytes()
            return False
    monkeypatch.setattr(s, 'Recovery', Policy)
    with pytest.raises(s.Conflict, match='STALE_START_EPOCH'): s.run(root, 'FAKE', 'old')
    assert (store.path/'status.json').read_bytes() == saved['bytes']
    assert live == {200,201} and not calls


def test_interrupted_role_ack_cannot_be_erased_by_error_cleanup(control_fixture, monkeypatch):
    root, store, live, calls, hooks, births, _ = control_fixture
    s.atomic(store.path/'status.json', {'epoch':'birth', 'binding':{}, 'roles':{}})
    s.atomic(store.path/'intent.json', {'running':True})
    driver = REAL_WINDOWS(root, 'FAKE', {}, lambda *a,**k: None); driver.epoch = 'birth'
    monkeypatch.setattr(driver, 'validate', lambda: {})
    monkeypatch.setattr(driver, 'vacant', lambda *a: None)
    monkeypatch.setattr(s, 'ps', lambda *a,**k: {'observer_pid':101, 'run_directory':str(root/'run')})
    monkeypatch.setattr(s, 'identity', lambda pid: {'pid':pid, 'created':1, 'exe':'FIXTURE'})
    live.add(101)
    monkeypatch.setattr(driver, 'verify', lambda *a: (_ for _ in ()).throw(s.Conflict('ROLE_RECEIPT_MISMATCH')))
    with pytest.raises(s.Conflict, match='ROLE_RECEIPT_MISMATCH'): driver.launch('Collector', 0)
    with pytest.raises(s.Conflict, match='LIVE_OWNERSHIP_REPLACEMENT'):
        store.publish({'epoch':'birth', 'roles':{}})
    assert store.load()['roles']['Collector']['record']['identity']['pid'] == 101


def test_control_lock_excludes_a_different_windows_process(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    repo = Path(s.__file__).resolve().parents[2]
    code = '''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.windows.runtime_supervisor import Conflict, file_lock
try:
    with file_lock(Path(sys.argv[2])):
        raise AssertionError('Competing process acquired the control lock')
except Conflict as exc:
    assert str(exc) == 'SUPERVISOR_BUSY'
    print('NATIVE_INTERPROCESS_EXCLUSION_PASS')
'''
    lock = tmp_path/'control.lock'
    with s.file_lock(lock):
        result = subprocess.run([sys.executable,'-B','-c',code,str(repo),str(lock)],
                                capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'NATIVE_INTERPROCESS_EXCLUSION_PASS'
