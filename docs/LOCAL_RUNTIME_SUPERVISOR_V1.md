# Local Runtime Supervisor V1

2026-10-14. Local implementation checkpoint only. **Not installed or activated.**
Base/app release: `a0c96abdfb8672efd08b1051bd4b2af49e50546e`.
Branch: `codex/woofi-local-runtime-supervisor-v1` in the existing checkout.

## Approach

One small Python controller/daemon, using existing psutil and native Windows
capabilities. `Woofi.ps1` exposes Start, Stop and Status. The canonical
`launch/Invoke-Woofi.ps1`, SSI-only credential reference and DB-scoped collector
mutex remain authoritative. No application/business/ingestion code, dependency,
database schema, Technical policy or FPT automation changes.

Start launches the daemon with local WMI `Win32_Process.Create`, using full paths,
hidden startup and no elevation. Microsoft documents
that WMI-created children do not inherit the calling process job:
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).
The [Create API](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/create-method-in-class-win32-process)
also documents WMI provider job quotas. The startup object selects the documented
`CREATE_BREAKAWAY_FROM_JOB` flag for the newly created process, keeping it outside
the provider job too. No existing job is modified, and there is no attached-launch
fallback if Windows refuses creation. This does not make a process immune to
Windows policy, resource exhaustion, logoff or shutdown.

Bootstrap transfers only executable lookup/Windows directory metadata and UTF-8
mode, since WMI's environment need not match the interactive shell. The daemon
uses the matching base Python interpreter with the existing approved psutil
dependency directory; it avoids the venv redirector's private kill-on-close job
and unrelated global/user site startup hooks. No dependencies are installed. SSI keys,
other credentials, database overrides and pilot flags are excluded; the existing
canonical credential helper remains the only SSI credential exporter.

Real isolated Windows evidence: a WMI child was not in any job, including its
synthetic starter's named job, survived termination of that job and finished a read-only
SQLite integrity/provenance check. This did not close Codex or disturb its job.
Full production survival across closing Codex, logoff or reboot is NOT_VERIFIED.

## Commands (for a separately authorized installation)

The operational package comprises these five sibling files, preserving their
reviewed hashes: `Woofi.ps1`, `runtime_supervisor.py`,
`New-IndependentProcess.ps1`, `Start-WoofiObservedRole.ps1` and
`Invoke-WoofiObservedRole.ps1`. A suggested future installation directory is
`C:\Users\PC\WoofiRuntime\launch\supervisor-v1`. This checkpoint does not copy
them there, alter the application's pin, register tasks or start a daemon.

```powershell
& C:\Users\PC\WoofiRuntime\launch\supervisor-v1\Woofi.ps1 -Action Start
& C:\Users\PC\WoofiRuntime\launch\supervisor-v1\Woofi.ps1 -Action Status
& C:\Users\PC\WoofiRuntime\launch\supervisor-v1\Woofi.ps1 -Action Stop
```

State lives under `state/supervisor-v1`, separately from product data. The absence
of intent defaults to stopped. Status does not create this directory, obtain
either lock, invoke the credential gate, refresh HTTP data or start anything. It
reports recorded managed identities, actual listeners, worker parent/child rows
and read-only Restart Manager resource holders. Healthy unmanaged canonical
services may coexist with `supervisor_alive=false`; this is the current state.

Start refuses occupied ports, existing canonical source processes (including
orphans not yet listening), any acquisition worker or an already-held lock file.
It never adopts current unmanaged services. Activation therefore requires a
separately authorized controlled handoff: preserve newest data, gracefully stop
the current collector/web/API using freshly verified identities, confirm release,
then Start. Do not run Start against the currently healthy runtime to test it.

## Ownership and Stop

Separate control and daemon file locks prevent competing supervisors/commands.
The product ingestion mutex is never acquired, released or deleted by the
supervisor. Read-only file-holder inventory is conservative: an unfamiliar holder
blocks launch. The existing collector alone takes acquisition ownership.

Root identities bind PID, creation time, executable, exact observer script/role,
runtime root and SHA/source/database receipt. Collector readiness requires one
linear execution chain, one native worker, canonical CWD, `scripts.ingest_data
--watch` and one verified lock-file holder. A Windows venv redirector is part of
that chain, not a second worker. Branching or foreign workers block recovery.
Start is asynchronous: daemon startup is acknowledged first; Status reports each
role's separate starting/ready/backoff/blocked phase. It does not claim all three
services are ready merely because the daemon exists.

Stop first persists stopped intent. Each process birth is serialized with that
intent and rechecks it after slow preflight. Stop then handles Collector before
Backend and Frontend. No automatic restart occurs after Stop; only explicit Start
may change the intent. An in-progress Stop refuses a concurrent Start. Repeated
Start while already running is idempotent and does not reset recovery budgets.

Shutdown uses CTRL+C only after rechecking the owned process identities and exact
console membership. Console attach/signalling occurs in a short-lived hidden
helper, never in the persistent daemon/calling terminal. An unrelated console
member, PID reuse, missing proof or foreign port causes refusal, not termination.
No force kill or port/text-based termination is implemented.

A role gets at most one successful stop signal; later waits do not repeat it.
Graceful exit waits are finite (45 seconds per role). The controller waits up to
150 seconds for the daemon, with bounded verified fallback for recorded roots if
it exited. Long in-flight acquisition can therefore yield STOP_NOT_CONFIRMED or
GRACEFUL_STOP_TIMEOUT. Intent remains stopped. Preserve processes/data, inspect
the receipts and let writes finish; do not force-kill or reset a mutex/cooldown.
An orphan without a surviving verified root requires manual ownership recovery.

## Recovery and sleep/resume

- Initial launch plus at most three additional launches per role.
- Backoff: 15, 60, 180 seconds. Healthy uptime does not replenish the budget.
- Startup readiness deadline: 45 seconds. Web readiness uses owned listeners
  and small read-only HTTP checks; Collector readiness uses ownership evidence.
- An already-ready live process with a failing health response is labelled
  degraded, not automatically killed. Process exit remains the recovery trigger.
- Ownership, source-pin changes, tracked source changes, failed launch gate,
  unknown launch outcome or unknown members fail closed. No retry spiral.
- Five-second lifecycle checks. No market/provider freshness polling or forced
  acquisition is added. Collector restarts retain normal persistent scheduling,
  fenced writes and cooldowns; they do not use force flags.
- A timer gap over 60 seconds records a gap with cause NOT_VERIFIED and obtains
  at most eight recent Windows power events. A gap alone never proves sleep.
- Pending launches receive a ten-second resume grace; missed checks do not
  generate catch-up bursts. Existing healthy processes are retained. Actual
  sleep/resume was simulated, not induced on the live machine.

The daemon is itself one process, not a second watchdog hierarchy. If it exits,
managed roles may remain alive; Status reports stale/absent daemon evidence and
Stop can handle still-verifiable recorded roots. There is no automatic daemon
resurrection while signed in. Unknown/orphan ownership requires operator action.

## Optional Windows sign-in design — NOT registered

Only after separate authorization, a per-user Task Scheduler logon trigger could
run the installed `Woofi.ps1 -Action Resume`. Use the normal user token and one
task instance; no elevation, service install or task-level rapid restart loop.
Resume respects stopped/absent intent and does nothing after intentional Stop.
It preserves role launch budgets and introduces backoff, rather than resetting
exhausted budgets. Explicit Stop followed by Start resets them. Resume refuses
changed runtime bindings or orphaned roles. No task XML/registration, Windows
service, registry Run entry or Codex automation was created or modified here.

## Diagnostics

`status.json` records binding, current supervisor identity, role identities,
attempts, phases and heartbeat. `events.jsonl` records launches, ready/exit,
observed exit receipts, expected stops, backoff/limit, timer gaps, bounded power
evidence and reasons recovery stopped. Missing exit receipt gives UNKNOWN; an
observation timestamp is not invented as the exact exit time.

Events rotate at 256 KiB with one previous file; oversized details are marked
truncated. Supervised role streams rotate at 256 KiB with one previous file and
bounded individual lines. Legacy manual launches retain their prior default;
the supervisor explicitly selects bounded logging. Per-launch receipts are
retained rather than silently deleting historical evidence. Manual epochs can
accumulate bounded run folders; operator archiving is a separate future action.

Only metadata, types/codes and existing canonical output are recorded. No
credentials are placed in command lines/state or copied. Existing canonical
credential-helper behavior remains; this task does not read secret values.

## Validation evidence and scope

Real native observations: independent WMI child vs starter-job termination,
temporary SQLite bytes/provenance unchanged, verified console shutdown, bounded
role-log rotation, separate supervisor lock exclusion, and an end-to-end WMI
controller/daemon/stop fixture. Its three role adapters are explicitly simulated
finite PowerShell roles; no actual collector, server or provider is launched.

Deterministic simulations cover each role's unexpected exit, startup timeout,
backoff/limits, healthy uptime, later health failure, sleep gap, explicit Stop,
Stop during preflight, optional Resume budget/intent, conflicts/orphans and pin
change. Existing ingestion ownership/forced-command refusal, graceful stop,
cooldown and corporate-action provenance regressions are included.

Validation found and corrected two operational defects before checkpointing:
captured starter pipes could wait on a long-lived child (now uses a receipt file),
and console attachment in the long-lived controller could affect subsequent
children (now isolated in a signal helper). These were not hidden by longer
timeouts or weakened assertions.

Bootstrap hardening additionally checks WMI startup-object property construction,
the Windows venv redirector's private job, exclusion of credentials/pilot flags
and use of approved executable/dependency paths. Independence is asserted on the
actual isolated child, not inferred from a successful WMI return code.

Relevant regression after these fixes: 51 passed. Subsequent diagnostics and
single-stop-signal hardening: 24 lifecycle tests passed. Final source validation
after orphan-start guards: **53 relevant tests passed**. After final bootstrap
hardening, **26 lifecycle/native tests passed**, including the no-job-membership
assertion, real WMI daemon fixture and environment whitelist. Local logs are under
`C:\Users\PC\.codex\tmp\woofi-supervisor-v1-20261014`.

Canonical preflight/Status confirms app SHA a0c96ab, backend/frontend healthy,
one collector root with real worker 11856 owning its lock. No supervisor state
directory was created on the live runtime. No canonical process was signalled,
restarted or adopted. Live database checks are read-only; ordinary existing
collector writes may continue. Historical October 14 exit cause remains UNKNOWN.

Activation readiness: staged implementation, pending integration/installation and
a separately authorized controlled handoff. Production handoff, sign-in startup,
full Codex close/logoff/reboot survival and real sleep are NOT_VERIFIED.

The two unrelated untracked frontend instruction files, Downloads WIP and the
unmerged Technical checkpoint 30fdff2 are preserved. No Git push, runtime cutover,
cloud work, Technical/FPT activation or unrelated application changes.
