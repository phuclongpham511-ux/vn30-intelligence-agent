"""Manual Windows lifecycle control. No application imports or database writes.

Start is explicit; Resume (for separately authorized sign-in startup) respects a
durable Stop. Windows WMI launch removes dependence on the caller's process job.
It does not promise survival of Windows shutdown, policy termination or failure
of the supervisor itself. Existing canonical launcher/mutex remain authoritative.
"""
import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes as w
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
import urllib.request
from collections import Counter

import psutil

ROLES = ('Backend', 'Frontend', 'Collector')
BACKOFF = (15, 60, 180)  # Three recoveries per role per explicit Start, never reset by uptime.
TICK = 5
INVENTORY_CALLS = 4  # Includes the zero-capacity sizing call.
INVENTORY_LIMIT = 4096  # Bound native allocation, never truncate the owner list.


class Conflict(RuntimeError):
    """Unknown ownership/pin; fail closed without terminating unrelated processes."""


class IntentStopped(RuntimeError):
    """Stop linearizes before the next process birth, including slow preflight."""


class InventoryUnverified(Conflict):
    """No qualified owner snapshot; never permission to launch or signal."""


def inventory_error(stage, code, **detail):
    # No path, command line or environment values in lifecycle diagnostics.
    return InventoryUnverified('LOCK_INVENTORY_UNVERIFIED '+json.dumps({
        'stage':stage, 'code':code, 'utc':datetime.now(timezone.utc).isoformat(), **detail},
        separators=(',', ':')))


def _verify_lock_owner(owner):
    """Fence PID reuse using Restart Manager's native creation FILETIME."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.GetProcessTimes.argtypes = [w.HANDLE,*([ctypes.POINTER(w.FILETIME)]*4)]
    kernel.GetProcessTimes.restype = w.BOOL
    kernel.GetExitCodeProcess.argtypes = [w.HANDLE,ctypes.POINTER(w.DWORD)]
    kernel.GetExitCodeProcess.restype = w.BOOL
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    handle = kernel.OpenProcess(0x1000,False,owner.pid)  # QUERY_LIMITED_INFORMATION only.
    if not handle:
        raise inventory_error('owner_open',ctypes.get_last_error(),pid=owner.pid)
    try:
        created, exited, system, user = (w.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle,ctypes.byref(created),ctypes.byref(exited),
                                      ctypes.byref(system),ctypes.byref(user)):
            raise inventory_error('owner_times',ctypes.get_last_error(),pid=owner.pid)
        if (created.dwLowDateTime,created.dwHighDateTime) != (owner.started.dwLowDateTime,owner.started.dwHighDateTime):
            raise inventory_error('owner_identity_changed',0,pid=owner.pid)
        exit_code = w.DWORD()
        if not kernel.GetExitCodeProcess(handle,ctypes.byref(exit_code)):
            raise inventory_error('owner_exit_query',ctypes.get_last_error(),pid=owner.pid)
        if exit_code.value != 259:  # STILL_ACTIVE
            raise inventory_error('owner_exited',exit_code.value,pid=owner.pid)
    finally:
        kernel.CloseHandle(handle)


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default


def atomic(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def file_lock(path, wait=0):
    """Separate supervisor/control locks, NEVER the product acquisition mutex."""
    import msvcrt
    with path.open('a+b') as handle:
        handle.seek(0, 2)
        if not handle.tell():
            handle.write(b'\0'); handle.flush()
        deadline = time.monotonic() + wait
        while True:
            try:
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError as exc:
                if exc.errno not in (11, 13) or time.monotonic() >= deadline:
                    raise Conflict('SUPERVISOR_BUSY') from None
                time.sleep(.1)
        try:
            yield
        finally:
            handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def identity(pid):
    p = psutil.Process(pid)
    return {'pid':pid, 'created':p.create_time(), 'exe':p.exe()}


def alive(record):
    if not record:
        return False
    try:
        p = psutil.Process(record['pid'])
        return p.create_time() == record['created'] and os.path.samefile(p.exe(), record['exe'])
    except psutil.NoSuchProcess:
        return False
    except (psutil.AccessDenied, OSError):
        raise Conflict('PROCESS_IDENTITY_UNVERIFIABLE') from None


@dataclass
class Role:
    record: dict | None = None
    launches: int = 0
    due: float = 0
    phase: str = 'waiting'
    members: list = field(default_factory=list)


class Recovery:
    """Deterministic policy seam; driver performs verified Windows operations."""
    def __init__(self, driver, emit, roles=None):
        self.driver, self.emit = driver, emit
        self.roles = roles or {name:Role() for name in ROLES}
        self.last_tick = None

    def tick(self, now, desired):
        if self.last_tick is not None and now - self.last_tick > 60:
            self.emit('timer_gap', seconds=round(now-self.last_tick, 2), cause='NOT_VERIFIED')
            self.driver.power_evidence()
            for state in self.roles.values():
                state.due = max(state.due, now + 10)  # No missed-tick catch-up burst.
        self.last_tick = now
        if not desired:
            for name in ('Collector', 'Backend', 'Frontend'):
                state = self.roles[name]
                if state.record:
                    self.driver.stop(name, state.record, state.members)
                    self.emit('role_stopped', role=name, expected=True)
                    state.record = None
                state.phase = 'stopped'
            return False
        for name, state in self.roles.items():
            if state.phase == 'blocked':
                continue
            if state.record:
                observation = self.driver.inspect(name, state.record)
                if observation['running']:
                    state.members = observation['members']
                if observation['running']:
                    if observation['ready']:
                        if state.phase != 'running':
                            self.emit('role_ready', role=name)
                        state.phase = 'running'
                    elif state.phase in ('running','degraded'):
                        if state.phase != 'degraded':
                            self.emit('health_warning',role=name,action='NO_LIVE_PROCESS_RESTART')
                        state.phase = 'degraded'
                    elif now - state.record['launched'] > 45:
                        self.emit('startup_timeout', role=name)
                        self.driver.stop(name, state.record, state.members)
                        state.record = None
                    else:
                        continue
                    if state.record:
                        continue
                else:
                    if any(self.driver.member_alive(m) for m in state.members):
                        raise Conflict('ORPHANED_ROLE_MEMBERS')
                    self.emit('role_exit', role=name, expected=False,
                              pid=state.record['identity'].get('pid'),
                              run_directory=state.record.get('run_directory'),
                              **(self.driver.exit_evidence(state.record) if hasattr(self.driver,'exit_evidence')
                                 else {'exit_code':self.driver.exit_code(state.record)}))
                    state.record = None
                if state.launches > len(BACKOFF):
                    state.phase = 'blocked'
                    self.emit('recovery_stopped', role=name, reason='RESTART_LIMIT')
                    continue
                state.due = now + BACKOFF[state.launches-1]
                state.phase = 'backoff'
                self.emit('backoff', role=name, seconds=BACKOFF[state.launches-1])
            if now >= state.due:
                # The Windows driver serializes process birth with durable intent.
                state.launches += 1
                self.emit('launch_attempt', role=name, number=state.launches)
                state.record = self.driver.launch(name, now)
                state.members = [state.record['identity']]
                state.phase = 'starting'
                self.emit('role_launched',role=name,pid=state.record['identity'].get('pid'),
                          run_directory=state.record.get('run_directory'))
        return True


def ps(pwsh, code, timeout=15, output_file=None):
    # A long-lived Start-Process child can inherit a captured pipe handle. A
    # regular receipt file lets us wait for the starter only, never the service.
    if output_file:
        with output_file.open('x',encoding='utf-8') as output:
            result = subprocess.run([pwsh,'-NoProfile','-Command',code],stdout=output,
                                    stderr=subprocess.DEVNULL,timeout=timeout)
        text = output_file.read_text(encoding='utf-8-sig')
    else:
        result = subprocess.run([pwsh, '-NoProfile', '-Command', code], capture_output=True,
                                text=True, timeout=timeout)
        text = result.stdout
    if result.returncode:
        # Do not echo subprocess text (launcher could contain private diagnostics).
        raise Conflict('WINDOWS_PROBE_FAILED')
    return json.loads(text) if text.strip() else []


def literal(text):
    return "'" + str(text).replace("'", "''") + "'"


def lock_owners(path):
    """Bounded read-only RM snapshot, not a claim to the acquisition mutex.

    RmGetList can return ERROR_MORE_DATA again after sizing. Reallocate only
    within explicit count/call limits; incomplete/failed responses are not empty.
    """
    if not Path(path).exists():
        return []
    class Process(ctypes.Structure):
        _fields_ = [('pid',w.DWORD), ('started',w.FILETIME)]
    class Info(ctypes.Structure):
        _fields_ = [('process',Process), ('app',w.WCHAR*256), ('service',w.WCHAR*64),
                   ('kind',ctypes.c_uint), ('status',w.ULONG), ('session',w.DWORD), ('restartable',w.BOOL)]
    rm = ctypes.WinDLL('rstrtmgr')
    rm.RmStartSession.argtypes = [ctypes.POINTER(w.DWORD),w.DWORD,w.LPWSTR]
    rm.RmRegisterResources.argtypes = [w.DWORD,ctypes.c_uint,ctypes.POINTER(w.LPCWSTR),ctypes.c_uint,ctypes.POINTER(Process),ctypes.c_uint,ctypes.POINTER(w.LPCWSTR)]
    rm.RmGetList.argtypes = [w.DWORD,ctypes.POINTER(ctypes.c_uint),ctypes.POINTER(ctypes.c_uint),ctypes.POINTER(Info),ctypes.POINTER(w.DWORD)]
    rm.RmEndSession.argtypes = [w.DWORD]
    for name in ('RmStartSession','RmRegisterResources','RmGetList','RmEndSession'):
        getattr(rm,name).restype = w.DWORD
    session = w.DWORD(); key = ctypes.create_unicode_buffer(33)
    code = rm.RmStartSession(ctypes.byref(session), 0, key)
    if code:
        raise inventory_error('start',code)
    try:
        code = rm.RmRegisterResources(session,1,(w.LPCWSTR*1)(str(path)),0,None,0,None)
        if code:
            raise inventory_error('register',code)
        capacity = 0
        responses = []
        for attempt in range(1,INVENTORY_CALLS+1):
            needed, count, reason = ctypes.c_uint(), ctypes.c_uint(capacity), w.DWORD()
            try:
                entries = (Info*capacity)() if capacity else None
            except (MemoryError,OverflowError):
                raise inventory_error('allocation',14,capacity=capacity) from None
            code = rm.RmGetList(session,ctypes.byref(needed),ctypes.byref(count),entries,ctypes.byref(reason))
            responses.append(dict(attempt=attempt,code=code,capacity=capacity,needed=needed.value,
                                  returned=count.value,reboot_reasons=reason.value,
                                  utc=datetime.now(timezone.utc).isoformat()))
            detail = dict(responses=responses)
            if code not in (0,234):
                raise inventory_error('get_list',code,**detail)
            if needed.value > INVENTORY_LIMIT:
                raise inventory_error('allocation_limit',code,**detail)
            if code == 234:
                if needed.value <= capacity:
                    raise inventory_error('invalid_size',code,**detail)
                if attempt == INVENTORY_CALLS:
                    raise inventory_error('retry_exhausted',code,**detail)
                capacity = needed.value
                time.sleep(.05 * 2**(attempt-1))  # Total retry delay <= 350 ms.
                continue
            if count.value > capacity or needed.value > capacity:
                raise inventory_error('invalid_success',code,**detail)
            owners = [entries[i].process for i in range(count.value)]
            pids = [owner.pid for owner in owners]
            if (len(set(pids)) != len(pids) or any(not owner.pid or
                    not (owner.started.dwLowDateTime or owner.started.dwHighDateTime) for owner in owners)):
                raise inventory_error('invalid_owner',code,**detail)
            for owner in owners:
                _verify_lock_owner(owner)
            return pids
    finally:
        code = rm.RmEndSession(session)
        if code and sys.exc_info()[0] is None:
            raise inventory_error('end',code)


class Windows:
    def __init__(self, runtime, pwsh, binding, emit):
        self.root, self.pwsh, self.binding, self.emit = runtime, pwsh, binding, emit
        self.epoch = None  # Set only for generation-managed operations.
        self.roles = None

    def validate(self):
        cfg = read(self.root/'config/runtime.json')
        if bind(cfg) != self.binding:
            raise Conflict('RUNTIME_PIN_CHANGED')
        result = subprocess.run(['git','-C',cfg['source_checkout'],'rev-parse','HEAD'],
                                capture_output=True,text=True,timeout=5)
        if result.returncode or result.stdout.strip() != cfg['canonical_sha']:
            raise Conflict('SOURCE_SHA_MISMATCH')
        clean = subprocess.run(['git','-C',cfg['source_checkout'],'diff','HEAD','--quiet'],
                               capture_output=True,timeout=5)
        if clean.returncode:
            raise Conflict('SOURCE_TRACKED_CHANGES')
        gate = ps(self.pwsh, '& '+literal(self.root/'launch/Invoke-Woofi.ps1')+' -CheckOnly', 20)
        if not gate.get('Ready'):
            raise Conflict('CANONICAL_GATE_FAILED')
        return cfg

    def workers(self):
        rows = ps(self.pwsh, "@(Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -match '\\s-m\\s+scripts\\.ingest_(data|news)(?:\\s|$)'} | Select-Object ProcessId,ParentProcessId,ExecutablePath) | ConvertTo-Json -Compress")
        return rows if isinstance(rows,list) else [rows]

    def ports(self, cfg):
        if any(type(cfg[key]) is not int or not 1<=cfg[key]<=65535 for key in ('backend_port','frontend_port')):
            raise Conflict('INVALID_RUNTIME_PORT')
        rows = ps(self.pwsh, '@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {$_.LocalPort -in '+str(cfg['backend_port'])+','+str(cfg['frontend_port'])+'} | Select-Object LocalPort,OwningProcess) | ConvertTo-Json -Compress')
        return rows if isinstance(rows,list) else [rows]

    def vacant(self, role, cfg):
        if role == 'Collector':
            if self.workers() or lock_owners(cfg['product_database']+'.ingestion.lock'):
                raise Conflict('COLLECTOR_ALREADY_OWNED')
        else:
            port = cfg['backend_port' if role == 'Backend' else 'frontend_port']
            if any(row['LocalPort'] == port for row in self.ports(cfg)):
                raise Conflict('PORT_CONFLICT')
            # An orphan can still be starting before its listener appears. Refuse
            # matching canonical source processes; never adopt or terminate them.
            source=Path(cfg['source_checkout']).resolve()
            for process in psutil.process_iter(['name']):
                try:
                    name=(process.info['name'] or '').lower()
                    if role=='Frontend' and name=='node.exe' and Path(process.cwd()).resolve()==source/'frontend':
                        raise Conflict('ROLE_ALREADY_RUNNING')
                    if role=='Backend' and name in ('python.exe','pythonw.exe'):
                        args=process.cmdline()
                        backend=('uvicorn' in args or ('--mode' in args and args[args.index('--mode')+1]=='backend'))
                        if backend and Path(process.cwd()).resolve()==source:
                            raise Conflict('ROLE_ALREADY_RUNNING')
                except psutil.NoSuchProcess:
                    continue
                except psutil.AccessDenied:
                    raise Conflict('ROLE_CENSUS_UNVERIFIABLE') from None

    def launch(self, role, now):
        cfg = self.validate(); self.vacant(role, cfg)
        script = Path(__file__).with_name('Start-WoofiObservedRole.ps1')
        command = '& '+literal(script)+' -Role '+role+' -Supervised -RuntimeRoot '+literal(self.root)
        store = Store(self.root)
        with file_lock(store.path/'command.lock', wait=30):
            if self.epoch is not None:
                state = store.require_epoch(self.epoch)
            if not store.desired():
                raise IntentStopped()
            if self.epoch is not None:
                row = state.setdefault('roles', {}).setdefault(role, {})
                row['launches'] = (self.roles[role].launches if self.roles is not None
                                   else row.get('launches', 0) + 1)
                state['pending_launch'] = role
                atomic(store.path/'status.json', state)
            result = ps(self.pwsh, command, 25,
                        output_file=store.path/('launch-'+uuid.uuid4().hex+'.json'))
            item = identity(result['observer_pid'])
            record = {'identity':item,'role':role,'run_directory':result['run_directory'], 'launched':now}
            if self.epoch is not None:
                row = state.setdefault('roles', {}).setdefault(role, {})
                row.update(record=record, members=[item], phase='starting')
                state.pop('pending_launch', None)
                atomic(store.path/'status.json', state)
        self.verify(record)
        return record

    def verify(self, record):
        if self.epoch is not None:
            Store(self.root).require_epoch(self.epoch)
        if not alive(record['identity']):
            return False
        args = psutil.Process(record['identity']['pid']).cmdline()
        script = str(Path(__file__).with_name('Invoke-WoofiObservedRole.ps1'))
        # The observed launcher resolves its sibling observer path.
        if (script.casefold() not in [a.casefold() for a in args]
                or '-Role' not in args or args[args.index('-Role')+1] != record['role']
                or '-RuntimeRoot' not in args or Path(args[args.index('-RuntimeRoot')+1]).resolve() != self.root):
            raise Conflict('ROLE_IDENTITY_MISMATCH')
        started = read(Path(record['run_directory'])/'started.json')
        if not Path(record['run_directory']).resolve().is_relative_to(self.root/'state/observed-role-runs'):
            raise Conflict('ROLE_RECEIPT_PATH_MISMATCH')
        if started and (started['sha'] != self.binding['sha'] or started['database'] != self.binding['database']
                        or started['source'] != self.binding['source'] or started['observer_pid'] != record['identity']['pid']
                        or started['role'] != record['role']):
            raise Conflict('ROLE_RECEIPT_MISMATCH')
        return True

    def inspect(self, role, record):
        if not self.verify(record):
            return {'running':False,'ready':False,'members':record.get('members',[])}
        root = psutil.Process(record['identity']['pid'])
        members = [identity(p.pid) for p in [root,*root.children(recursive=True)] if p.name().lower() != 'conhost.exe']
        record['members'] = members
        cfg = read(self.root/'config/runtime.json')
        pids = {m['pid'] for m in members}
        if bind(cfg) != self.binding:
            raise Conflict('RUNTIME_PIN_CHANGED')
        if role == 'Collector':
            workers = self.workers()
            if any(row['ProcessId'] not in pids for row in workers):
                raise Conflict('COMPETING_COLLECTOR')
            # A venv redirector and its one child are ONE execution root.
            ids = {row['ProcessId'] for row in workers}
            roots = [row for row in workers if row['ParentProcessId'] not in ids]
            owners = lock_owners(cfg['product_database']+'.ingestion.lock')
            branching = any(n>1 for n in Counter(row['ParentProcessId'] for row in workers).values())
            native = [row for row in workers if '\\.venv\\' not in (row.get('ExecutablePath') or '').casefold()]
            if any(pid not in pids for pid in owners) or len(roots)>1 or branching or len(native)>1:
                raise Conflict('COMPETING_COLLECTOR')
            ready = len(roots) == 1 and len(owners) == 1 and owners[0] in pids
            if ready:
                worker=psutil.Process(owners[0]);args=worker.cmdline()
                if (Path(worker.cwd()).resolve() != Path(cfg['source_checkout']).resolve()
                        or '-m' not in args or args[args.index('-m')+1] != 'scripts.ingest_data' or '--watch' not in args):
                    raise Conflict('COLLECTOR_IDENTITY_MISMATCH')
        else:
            port = cfg['backend_port' if role == 'Backend' else 'frontend_port']
            listeners = [row for row in self.ports(cfg) if row['LocalPort'] == port]
            if any(row['OwningProcess'] not in pids for row in listeners):
                raise Conflict('PORT_CONFLICT')
            ready = bool(listeners)
            if ready:
                route='/health' if role=='Backend' else '/'
                try:
                    with urllib.request.urlopen('http://127.0.0.1:'+str(port)+route,timeout=2) as response:
                        ready=response.status==200
                except OSError:
                    ready=False
        return {'running':True,'ready':ready,'members':members}

    member_alive = staticmethod(alive)

    def exit_code(self, record):
        receipt = read(Path(record['run_directory'])/'exit.json', {})
        return receipt.get('exit_code', 'UNKNOWN')

    def exit_evidence(self, record):
        receipt=read(Path(record['run_directory'])/'exit.json',{})
        return {'exit_code':receipt.get('exit_code','UNKNOWN'),
                'exited_at_utc':receipt.get('exited_at_utc'),'receipt_available':bool(receipt)}

    def stop(self, role, record, members):
        # No TerminateProcess/port-based kills. Never signal an unrelated console.
        if not self.verify(record):
            if any(alive(m) for m in members):
                raise Conflict('ORPHANED_ROLE_MEMBERS')
            return
        observation = self.inspect(role, record)
        current = observation['members']; ids = {m['pid'] for m in current}
        for m in current:
            if not alive(m):
                raise Conflict('PROCESS_CHANGED_DURING_STOP')
        # AttachConsole changes process-wide console/standard handles. Confine it
        # to a short-lived helper, never the daemon or its calling terminal.
        if not record.get('stop_requested'):
            request=Path(record['run_directory'])/('stop-'+uuid.uuid4().hex+'.json')
            atomic(request,{'record':record,'binding':self.binding,'epoch':self.epoch})
            info=subprocess.STARTUPINFO();info.dwFlags|=subprocess.STARTF_USESHOWWINDOW;info.wShowWindow=0
            signal=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'signal',
                '--runtime',str(self.root),'--pwsh',self.pwsh,'--request',str(request)],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,
                creationflags=subprocess.CREATE_NEW_CONSOLE,startupinfo=info)
            if signal.returncode:
                if any(alive(m) for m in current):
                    raise Conflict('GRACEFUL_SIGNAL_REFUSED')
                return
            record['stop_requested']=datetime.now(timezone.utc).isoformat()
            self.emit('role_stop_requested',role=role,expected=True)
        deadline = time.monotonic()+45
        while any(alive(m) for m in current) and time.monotonic() < deadline:
            time.sleep(.2)
        if any(alive(m) for m in current):
            raise Conflict('GRACEFUL_STOP_TIMEOUT')

    def signal(self, record):
        if not self.verify(record):
            return
        root=psutil.Process(record['identity']['pid'])
        current=[identity(p.pid) for p in [root,*root.children(recursive=True)] if p.name().lower()!='conhost.exe']
        ids={m['pid'] for m in current}
        if not all(alive(m) for m in current):
            raise Conflict('PROCESS_CHANGED_DURING_STOP')
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.FreeConsole()
        if not kernel.AttachConsole(record['identity']['pid']):
            raise Conflict('CONSOLE_UNAVAILABLE')
        try:
            clients = (w.DWORD*256)(); count = kernel.GetConsoleProcessList(clients,256)
            if not count or count > 256 or set(clients[:count]) != ids | {os.getpid()}:
                raise Conflict('UNRELATED_CONSOLE_MEMBER')
            if not kernel.SetConsoleCtrlHandler(None,True) or not kernel.GenerateConsoleCtrlEvent(0,0):
                raise Conflict('GRACEFUL_STOP_FAILED')
        finally:
            kernel.FreeConsole()

    def power_evidence(self):
        try:
            events = ps(self.pwsh, "@(Get-WinEvent -FilterHashtable @{LogName='System';Id=1,42;StartTime=(Get-Date).AddMinutes(-30)} -MaxEvents 8 -ErrorAction SilentlyContinue | Where-Object {$_.ProviderName -in @('Microsoft-Windows-Kernel-Power','Microsoft-Windows-Power-Troubleshooter')} | Select-Object Id,ProviderName,TimeCreated) | ConvertTo-Json -Compress")
            self.emit('power_evidence', events=events)
        except Conflict:
            self.emit('power_evidence', result='NOT_VERIFIED')


def bind(cfg):
    return {'sha':cfg['canonical_sha'], 'source':cfg['source_checkout'],
            'database':cfg['product_database'], 'ports':[cfg['backend_port'],cfg['frontend_port']]}


class Store:
    def __init__(self, runtime):
        self.path = runtime/'state/supervisor-v1'
        if not self.path.resolve().is_relative_to(runtime.resolve()):
            raise Conflict('SUPERVISOR_STATE_PATH_MISMATCH')

    def load(self):
        return read(self.path/'status.json', {})

    def desired(self):
        return read(self.path/'intent.json', {}).get('running', False)

    def require_epoch(self, epoch):
        state = self.load()
        if state.get('epoch') != epoch:
            raise Conflict('STALE_START_EPOCH')
        return state

    def publish(self, state):
        """Fenced read-modify-write; callers never hold command.lock here."""
        with file_lock(self.path/'command.lock', wait=30):
            current = self.require_epoch(state.get('epoch'))
            # A failed launch may have saved its root before returning to the
            # policy machine. Never discard that still-live ownership on error.
            for role, row in current.get('roles', {}).items():
                record = row.get('record')
                replacement = state.get('roles', {}).get(role, {}).get('record')
                if record and (not replacement or replacement['identity'] != record['identity']):
                    if alive(record['identity']) or any(alive(m) for m in row.get('members', [])):
                        raise Conflict('LIVE_OWNERSHIP_REPLACEMENT')
            for key in ('pending_launch', 'control_phase'):
                if key in current:
                    state[key] = current[key]
                else:
                    state.pop(key, None)
            atomic(self.path/'status.json', state)

    def event(self, event, **detail):
        path = self.path/'events.jsonl'
        item = {'utc':datetime.now(timezone.utc).isoformat(),'event':event,**detail}
        line=json.dumps(item)+'\n'
        if len(line.encode('utf-8'))>65536:
            line=json.dumps({'utc':item['utc'],'event':event,'detail_truncated':True})+'\n'
        if path.exists() and path.stat().st_size+len(line.encode('utf-8'))>262144:
            os.replace(path, self.path/'events.previous.jsonl')
        with path.open('a', encoding='utf-8') as handle:
            handle.write(line)


def status(runtime):
    """No state-directory creation, gate invocation, mutex or API refresh."""
    store = Store(runtime); result = store.load()
    return {'desired_running':store.desired(), 'supervisor_alive':alive(result.get('supervisor')),
            'recorded':result, 'role_alive':{name:alive(row.get('record',{}).get('identity') if row.get('record') else None)
                                          for name,row in result.get('roles',{}).items()},
            'member_alive':any(alive(m) for row in result.get('roles',{}).values() for m in row.get('members',[]))}


def bootstrap_environment():
    # WMI provider environment is not the interactive shell's environment. Carry
    # executable lookup/Windows paths only, never credentials or pilot flags.
    pathext = os.environ.get('PATHEXT')
    if not pathext:
        raise Conflict('WINDOWS_PATHEXT_MISSING: check PATHEXT in the parent Windows environment before Start')
    extensions = pathext.split(';')
    if (any(not re.fullmatch(r'\.[A-Za-z0-9]+', item) for item in extensions)
            or not {'.EXE', '.CMD'}.issubset({item.upper() for item in extensions})):
        raise Conflict('WINDOWS_PATHEXT_INVALID: expected extension list including .EXE and .CMD; check parent Windows environment')
    # Preserve the approved parent's exact order/value; no default extensions,
    # PATH replacement, extra executable search paths or shell policy override.
    keys=('PATH','PATHEXT','SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA')
    environment=[key+'='+os.environ[key] for key in keys if key in os.environ]
    environment.append('PYTHONUTF8=1')
    environment.append('PYTHONPATH='+str(Path(psutil.__file__).resolve().parents[1]))
    return environment


def independent(pwsh, argv, directory, request_file):
    environment = bootstrap_environment()
    # Windows venv redirectors create a kill-on-close child job. Bootstrap the
    # matching base interpreter directly, with only the approved dependency path;
    # -S excludes unrelated global/user site startup hooks. No packages installed.
    argv=list(argv)
    if Path(argv[0]).exists() and os.path.samefile(argv[0],sys.executable):
        argv=[sys._base_executable,'-S',*argv[1:]]
    atomic(request_file, {'command_line':subprocess.list2cmdline(argv), 'directory':str(directory),
                         'environment':environment})
    result = subprocess.run([pwsh,'-NoProfile','-File',str(Path(__file__).with_name('New-IndependentProcess.ps1')),
                             '-RequestFile',str(request_file)], capture_output=True,text=True,timeout=20)
    if result.returncode:
        raise Conflict('INDEPENDENT_LAUNCH_FAILED')
    return json.loads(result.stdout)


def control(action, runtime, pwsh):
    if action == 'status':
        return _control(action, runtime, pwsh)
    store = Store(runtime); store.path.mkdir(parents=True, exist_ok=True)
    # External operations serialize through completion, including orphan Stop.
    # The daemon never takes this lock; it must still publish/acknowledge/exit.
    with file_lock(store.path/'control.lock', wait=30):
        return _control(action, runtime, pwsh)


def _control(action, runtime, pwsh):
    if action == 'status':
        result = status(runtime)
        cfg = read(runtime/'config/runtime.json')
        driver = Windows(runtime,pwsh,bind(cfg),lambda *a,**k:None)
        result.update(runtime=bind(cfg),listeners=driver.ports(cfg),workers=driver.workers(),
                      lock_file_owners=lock_owners(cfg['product_database']+'.ingestion.lock'))
        return result
    store = Store(runtime); store.path.mkdir(parents=True, exist_ok=True)
    with file_lock(store.path/'command.lock', wait=30):
        existing = status(runtime)
        if action == 'stop':
            atomic(store.path/'intent.json', {'running':False})
            state = store.load()
            stop_epoch = state.get('epoch')
            state['control_phase'] = 'stopping'
            atomic(store.path/'status.json', state)
            store.event('stop_requested', expected=True)
        else:
            if action == 'resume' and not store.desired():
                return {'result':'STOP_INTENT_RETAINED'}
            state = store.load()
            if state.get('control_phase') == 'stopping':
                raise Conflict('STOP_IN_PROGRESS')
            if state.get('pending_launch'):
                raise Conflict('LAUNCH_OUTCOME_UNKNOWN')
            if existing['supervisor_alive']:
                if not store.desired():
                    raise Conflict('STOP_IN_PROGRESS')
                return existing  # Idempotent Start; cannot replenish retry budget.
            if any(existing['role_alive'].values()) or existing['member_alive']:
                raise Conflict('ORPHANED_ROLES_REQUIRE_STOP')
            # Diagnose known environment failure before git preflight or a
            # durable pending-birth journal; no launch has happened yet.
            bootstrap_environment()
            cfg = read(runtime/'config/runtime.json')
            driver = Windows(runtime,pwsh,bind(cfg),store.event)
            driver.validate()
            # Never adopt existing canonical/unknown processes during activation.
            for role in ROLES:
                driver.vacant(role,cfg)
            epoch = uuid.uuid4().hex
            resume_roles = None
            if action == 'resume':
                previous = store.load()
                if previous.get('binding') != bind(cfg):
                    raise Conflict('RUNTIME_PIN_CHANGED')
                resume_roles = {name:vars(Role(launches=row.get('launches',0),
                    due=time.monotonic()+BACKOFF[min(max(row.get('launches',0)-1,0),len(BACKOFF)-1)],
                    phase='blocked' if row.get('launches',0)>len(BACKOFF) else 'waiting'))
                    for name,row in previous.get('roles',{}).items()}
            atomic(store.path/'status.json', {'epoch':epoch,'binding':bind(cfg),'roles':{},
                'resume_roles':resume_roles, 'pending_launch':'supervisor', 'control_phase':'starting'})
            atomic(store.path/'intent.json', {'running':True})
            launched = independent(pwsh,[sys.executable,'-B',str(Path(__file__).resolve()),'run',
                                        '--runtime',str(runtime),'--pwsh',pwsh,'--epoch',epoch],
                                   runtime,store.path/'launch.json')
            store.event('supervisor_launch', **launched)
    if action != 'stop':
        # Release the short state lock for daemon acknowledgement. control.lock
        # still excludes another external Start/Stop, including caller failures.
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            current = status(runtime)
            if current['supervisor_alive']:
                return current
            time.sleep(.1)
        with file_lock(store.path/'command.lock', wait=30):
            store.require_epoch(epoch)
            atomic(store.path/'intent.json', {'running':False})
        raise Conflict('SUPERVISOR_START_NOT_CONFIRMED')
    # A stopped intent is durable before waiting or attempting any shutdown.
    deadline = time.monotonic()+150
    while status(runtime)['supervisor_alive'] and time.monotonic() < deadline:
        time.sleep(.2)
    current = status(runtime)
    store.require_epoch(stop_epoch)
    if not current['supervisor_alive'] and (any(current['role_alive'].values()) or current['member_alive']):
        # Supervisor died; recorded roots still need the same verified graceful stop.
        driver = Windows(runtime,pwsh,current['recorded']['binding'],store.event)
        driver.epoch = stop_epoch
        for role in ('Collector','Backend','Frontend'):
            row = current['recorded'].get('roles',{}).get(role,{})
            if row.get('record'):
                driver.stop(role,row['record'],row.get('members',[]))
                row.update(record=None,members=[],phase='stopped')
                store.publish(current['recorded'])
                store.event('role_stopped',role=role,expected=True,recovery='supervisor_absent')
        current = status(runtime)
    if current['supervisor_alive'] or any(current['role_alive'].values()) or current['member_alive']:
        raise Conflict('STOP_NOT_CONFIRMED')
    with file_lock(store.path/'command.lock', wait=30):
        state = store.require_epoch(stop_epoch)
        if state.get('pending_launch'):
            raise Conflict('LAUNCH_OUTCOME_UNKNOWN')
        state['control_phase'] = 'stopped'
        atomic(store.path/'status.json', state)
    return status(runtime)


def run(runtime, pwsh, epoch):
    store = Store(runtime)
    with file_lock(store.path/'supervisor.lock'):
        with file_lock(store.path/'command.lock', wait=30):
            state = store.require_epoch(epoch)
            if (alive(state.get('supervisor')) or state.get('pending_launch') not in (None, 'supervisor')
                    or any(alive(row.get('record', {}).get('identity') if row.get('record') else None)
                           or any(alive(m) for m in row.get('members', []))
                           for row in state.get('roles', {}).values())):
                raise Conflict('ORPHANED_ROLES_REQUIRE_STOP')
            state['supervisor'] = identity(os.getpid())
            state['phase'] = 'starting'
            if state.get('pending_launch') == 'supervisor':
                state.pop('pending_launch')
            atomic(store.path/'status.json', state)
        driver = Windows(runtime,pwsh,state['binding'],store.event)
        driver.epoch = epoch
        restored = state.get('resume_roles')
        recovery = Recovery(driver,store.event,
            roles={name:Role(**restored.get(name,{})) for name in ROLES} if restored is not None else None)
        driver.roles = recovery.roles
        store.event('supervisor_started', pid=os.getpid())
        try:
            while True:
                store.require_epoch(epoch)
                try:
                    keep = recovery.tick(time.monotonic(), store.desired())
                except IntentStopped:
                    keep = recovery.tick(time.monotonic(), False)
                state.update(phase='running' if keep else 'stopped',
                             heartbeat_utc=datetime.now(timezone.utc).isoformat(),
                             roles={name:vars(row) for name,row in recovery.roles.items()})
                store.publish(state)
                if not keep:
                    break
                time.sleep(TICK)
        except Exception as exc:
            # Unknown ownership never authorizes a signal/restart; keep intent and
            # records for a manual Stop. Failures contain types/codes, never secrets.
            state.update(phase='blocked',reason=str(exc) if isinstance(exc,Conflict) else type(exc).__name__,
                         roles={name:vars(row) for name,row in recovery.roles.items()})
            try:
                store.publish(state)
            except Conflict:
                # Keep the newer/uncertain ownership journal intact, even on
                # the exception path; a stale daemon must not publish anything.
                store.event('manifest_publish_refused', epoch=epoch)
            store.event('supervisor_stopped', reason=state['reason'])
            raise
        finally:
            store.event('supervisor_exit', expected=not store.desired())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('start','stop','status','resume','run','signal'))
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--pwsh',required=True)
    parser.add_argument('--epoch')
    parser.add_argument('--request',type=Path)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Windows is required')
    runtime = args.runtime.resolve()
    try:
        if args.action == 'run':
            run(runtime,args.pwsh,args.epoch)
        elif args.action == 'signal':
            request=read(args.request)
            driver=Windows(runtime,args.pwsh,request['binding'],lambda *a,**k:None)
            driver.epoch = request.get('epoch')
            if driver.epoch is None:
                driver.signal(request['record'])
            else:
                with file_lock(Store(runtime).path/'command.lock', wait=30):
                    driver.signal(request['record'])
        else:
            print(json.dumps(control(args.action,runtime,args.pwsh)))
    except Exception as exc:
        print(json.dumps({'result':'BLOCKED','reason':str(exc) if isinstance(exc,Conflict) else type(exc).__name__}))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
