"""Simulated lifecycle policy. No canonical runtime, acquisition or DB changes."""
import json
from pathlib import Path
import pytest
from scripts.windows import runtime_supervisor as s


class Fake:
    def __init__(self):
        self.running = set(); self.ready = True; self.calls = []; self.power = 0
        self.orphans = False

    def launch(self, role, now):
        self.calls.append(('launch',role,now)); self.running.add(role)
        return {'identity':{'role':role},'role':role,'launched':now}

    def inspect(self, role, record):
        return {'running':role in self.running,'ready':self.ready,'members':[{'role':role}]}

    def member_alive(self, member):
        return self.orphans or member['role'] in self.running

    def stop(self, role, record, members):
        self.calls.append(('stop',role)); self.running.discard(role)

    def exit_code(self, record): return 7
    def power_evidence(self): self.power += 1


def policy():
    events = []; driver = Fake()
    return s.Recovery(driver,lambda name,**data:events.append((name,data))),driver,events


def test_start_ready_and_explicit_stop_never_restart_on_later_ticks():
    machine,driver,events = policy()
    assert machine.tick(0,True)
    machine.tick(5,True)
    assert all(row.phase=='running' for row in machine.roles.values())
    assert machine.tick(10,False) is False
    assert [call[1] for call in driver.calls if call[0]=='stop']==['Collector','Backend','Frontend']
    machine.tick(1000,False)
    assert len([call for call in driver.calls if call[0]=='launch'])==3
    assert all(item[1]['expected'] for item in events if item[0]=='role_stopped')


@pytest.mark.parametrize('role',s.ROLES)
def test_unexpected_exit_has_backoff_and_three_additional_attempts(role):
    machine,driver,events = policy(); machine.tick(0,True); machine.tick(1,True)
    for death, delay in [(2,15),(18,60),(79,180)]:
        driver.running.remove(role); machine.tick(death,True)
        for heartbeat in range(death+1,death+delay-1,5):
            machine.tick(heartbeat,True)
        machine.tick(death+delay-1,True)
        assert machine.roles[role].record is None
        machine.tick(death+delay,True)
        assert role in driver.running
    driver.running.remove(role); machine.tick(260,True)
    machine.tick(500,True)
    assert machine.roles[role].phase=='blocked'
    assert machine.roles[role].launches==4
    assert ('recovery_stopped',{'role':role,'reason':'RESTART_LIMIT'}) in events
    assert all(item[1]['exit_code']==7 for item in events if item[0]=='role_exit')


def test_healthy_uptime_does_not_replenish_retry_budget():
    machine,driver,_ = policy(); machine.tick(0,True); machine.tick(5,True)
    driver.running.remove('Backend'); machine.tick(10,True); machine.tick(25,True)
    machine.tick(30,True); machine.tick(10000,True)
    assert machine.roles['Backend'].launches==2


def test_later_health_failure_does_not_kill_a_live_service():
    machine,driver,events=policy();machine.tick(0,True);machine.tick(5,True)
    driver.ready=False;machine.tick(50,True);machine.tick(55,True)
    assert all(row.phase=='degraded' for row in machine.roles.values())
    assert not any(call[0]=='stop' for call in driver.calls)
    assert len([name for name,_ in events if name=='health_warning'])==3
    driver.ready=True;machine.tick(60,True)
    assert all(row.phase=='running' for row in machine.roles.values())


def test_startup_failure_stops_verified_process_then_backs_off():
    machine,driver,events = policy(); driver.ready=False
    machine.tick(0,True); machine.tick(45,True)
    assert machine.roles['Backend'].record
    machine.tick(46,True)
    assert not machine.roles['Backend'].record
    assert ('stop','Backend') in driver.calls
    machine.tick(60,True); assert not machine.roles['Backend'].record
    machine.tick(61,True); assert machine.roles['Backend'].record
    assert any(name=='startup_timeout' for name,_ in events)


def test_resume_gap_delays_pending_restart_without_catchup_or_claiming_sleep():
    machine,driver,events = policy(); machine.tick(0,True); machine.tick(5,True)
    driver.running.remove('Backend'); machine.tick(10,True)
    machine.tick(400,True)
    assert not machine.roles['Backend'].record
    machine.tick(409,True); assert not machine.roles['Backend'].record
    machine.tick(410,True); assert machine.roles['Backend'].record
    assert driver.power==1
    assert ('timer_gap',{'seconds':390,'cause':'NOT_VERIFIED'}) in events
    assert machine.roles['Backend'].launches==2


def test_orphan_after_root_exit_blocks_instead_of_starting_competing_worker():
    machine,driver,_ = policy(); machine.tick(0,True); machine.tick(5,True)
    driver.running.remove('Collector'); driver.orphans=True
    with pytest.raises(s.Conflict,match='ORPHANED'):
        machine.tick(6,True)
    assert machine.roles['Collector'].launches==1


def test_port_and_collector_lock_conflicts_are_not_retried_or_signalled():
    for role,reason in [('Backend','PORT_CONFLICT'),('Collector','COLLECTOR_ALREADY_OWNED')]:
        cfg={'backend_port':123,'frontend_port':456,'product_database':'fixture.db'}
        driver=s.Windows(Path('.'),'pwsh',{},lambda *a,**k:None)
        driver.ports=lambda cfg:[{'LocalPort':123,'OwningProcess':999}]
        driver.workers=lambda:[{'ProcessId':111}]
        with pytest.raises(s.Conflict,match=reason): driver.vacant(role,cfg)


def test_lock_owner_without_commandline_match_still_blocks(monkeypatch):
    driver=s.Windows(Path('.'),'pwsh',{},lambda *a,**k:None);driver.workers=lambda:[]
    monkeypatch.setattr(s,'lock_owners',lambda path:[999])
    with pytest.raises(s.Conflict,match='COLLECTOR_ALREADY_OWNED'):
        driver.vacant('Collector',{'product_database':'fixture.db'})


def test_orphaned_backend_before_listen_is_refused_without_signalling(tmp_path,monkeypatch):
    class Process:
        info={'name':'python.exe'}
        def cmdline(self):return ['python','-m','uvicorn','main:app']
        def cwd(self):return str(tmp_path)
    driver=s.Windows(tmp_path,'pwsh',{},lambda *a,**k:None);driver.ports=lambda cfg:[]
    monkeypatch.setattr(s.psutil,'process_iter',lambda *a:[Process()])
    with pytest.raises(s.Conflict,match='ROLE_ALREADY_RUNNING'):
        driver.vacant('Backend',{'backend_port':123,'frontend_port':456,'source_checkout':str(tmp_path)})


def test_runtime_pin_change_fails_before_launch_or_gate(monkeypatch,tmp_path):
    (tmp_path/'config').mkdir();s.atomic(tmp_path/'config/runtime.json',{'canonical_sha':'new','source_checkout':'source','product_database':'db','backend_port':1,'frontend_port':2})
    driver=s.Windows(tmp_path,'pwsh',{'sha':'old'},lambda *a,**k:None)
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k:pytest.fail('Must not launch'))
    with pytest.raises(s.Conflict,match='RUNTIME_PIN_CHANGED'): driver.validate()


def test_status_without_supervisor_is_read_only_and_reports_unmanaged_roles(tmp_path,monkeypatch):
    (tmp_path/'config').mkdir();s.atomic(tmp_path/'config/runtime.json',{'canonical_sha':'sha','source_checkout':'source','product_database':'db','backend_port':1,'frontend_port':2})
    monkeypatch.setattr(s.Windows,'ports',lambda *a:[{'LocalPort':1,'OwningProcess':99}])
    monkeypatch.setattr(s.Windows,'workers',lambda *a:[{'ProcessId':123}])
    monkeypatch.setattr(s,'lock_owners',lambda path:[123])
    before=list(tmp_path.rglob('*'));result=s.control('status',tmp_path,'pwsh')
    assert result['supervisor_alive'] is False and result['desired_running'] is False
    assert result['listeners'][0]['OwningProcess']==99 and result['lock_file_owners']==[123]
    assert list(tmp_path.rglob('*'))==before


def test_intent_defaults_stopped_and_event_logs_are_bounded(tmp_path):
    store=s.Store(tmp_path);store.path.mkdir(parents=True)
    assert store.desired() is False
    s.atomic(store.path/'intent.json',{'running':False})
    for i in range(1000):store.event('fixture',sample='x'*500)
    assert (store.path/'events.jsonl').stat().st_size<=262144
    assert (store.path/'events.previous.jsonl').stat().st_size<=262144
    assert not store.desired()


def test_no_production_concurrency_or_data_policy_is_modified():
    # Scope guard supplements behavioral tests: adapter imports no ORM/app/collector.
    source=Path(s.__file__).read_text()
    assert 'from main' not in source and 'sqlmodel' not in source
    assert 'TerminateProcess' not in source.replace('No TerminateProcess/port-based kills.', '')
    assert 'CREATE_BREAKAWAY' not in source and 'Register-ScheduledTask' not in source


def test_wmi_bootstrap_carries_only_windows_paths_not_credentials_or_pilot_flags(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setenv('SSI_API_KEY','synthetic-secret-do-not-copy')
    monkeypatch.setenv('TECHNICAL_EOD_PILOT','synthetic-pilot-do-not-copy')
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='{"launch_pid":123}'))
    assert s.independent('pwsh',['python','fixture.py'],tmp_path,tmp_path/'request.json')['launch_pid']==123
    value=(tmp_path/'request.json').read_text()
    assert 'synthetic-secret' not in value and 'synthetic-pilot' not in value
    allowed={'PATH','SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PYTHONUTF8','PYTHONPATH'}
    assert all(line.split('=',1)[0] in allowed for line in s.read(tmp_path/'request.json')['environment'])


@pytest.mark.skipif(__import__('os').name!='nt',reason='Windows command lock')
def test_stop_during_slow_preflight_prevents_process_birth(tmp_path,monkeypatch):
    store=s.Store(tmp_path);store.path.mkdir(parents=True)
    s.atomic(store.path/'intent.json',{'running':True})
    driver=s.Windows(tmp_path,'pwsh',{},store.event)
    def preflight():
        s.atomic(store.path/'intent.json',{'running':False})
        return {}
    monkeypatch.setattr(driver,'validate',preflight)
    monkeypatch.setattr(driver,'vacant',lambda *a:None)
    monkeypatch.setattr(s,'ps',lambda *a,**k:pytest.fail('Stop must prevent process creation'))
    with pytest.raises(s.IntentStopped):driver.launch('Backend',0)
    assert store.desired() is False
