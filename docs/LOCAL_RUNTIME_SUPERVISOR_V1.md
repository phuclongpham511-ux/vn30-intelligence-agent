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

## Start/Stop race correction — 2026-10-15

The final review of source checkpoint `68df395` reproduced a safety-critical
supervisor-absent Stop race: once the last old role exited, concurrent Start could
publish a new generation, then Stop overwrote it with its old cleanup snapshot.
The reproduction used simulated identities and launches only. Integration was
blocked; the canonical runtime was not changed.

The correction adds a Windows file-backed `control.lock` held for each entire
external Start/Stop/Resume operation, including daemon acknowledgement and
supervisor-absent cleanup. Commands wait at most 30 seconds for it, then fail
closed with SUPERVISOR_BUSY. Status stays read-only and takes no locks. The daemon
never obtains control.lock, so it can acknowledge startup, publish and exit while
a controller waits. The existing shorter `command.lock` coordinates durable
intent, ownership read-modify-write and process birth. The lifetime
`supervisor.lock` still excludes a second daemon. None is the collector mutex.

Ownership publication checks the exact generation while holding command.lock.
Stale daemon startup, recovery launches, stop signals, cleanup and exception-path
writes cannot act on a newer epoch. Cleanup also refuses to replace a still-live
record or its known members. Stop signals retain the existing PID/creation-time,
executable, observer/receipt and exact console-membership validation; the short
signal helper now verifies the generation under command.lock too.

Stop persists stopped intent and a stopping marker before waiting or signalling.
An interrupted Stop therefore blocks Start until a subsequent Stop confirms
cleanup. Successfully stopped roles are journaled individually so another Stop
can continue without forgetting remaining ownership. Resume retains stopped
intent. Old cleanup snapshots cannot erase newer generations.

Supervisor and role births journal a pending-launch marker before creation.
Role attempt counts are persisted before birth; known roots are saved before
post-launch verification and the normal daemon tick. An acknowledged daemon may
continue after its caller exits, and a delayed bootstrap respects stopped intent.
If creation was interrupted before identity acknowledgement, Start and Stop
report LAUNCH_OUTCOME_UNKNOWN rather than claim success or clear the evidence.
This ambiguity requires operator ownership reconciliation; the marker must not
be blindly removed. No automatic acquisition or restart retry is added.

Deterministic temporary-file fixtures exercise the original race in both serial
orders, duplicate Start, supervisor/controller failures, interrupted Start/Stop,
durable intent, stale normal/exception writes, new-generation ownership,
uncertain birth, attempt-budget retention and collector/identity conflicts.
These are simulated lifecycle results, not production activation evidence.
Native Windows fixtures additionally test file-lock exclusion from a separate
process and the existing WMI/console lifecycle using finite fake roles. The
three-role fixture preserves distinct logical ownership names while mapping its
processes to finite Backend consoles; it never starts a real collector/server.

The change is confined to supervisor coordination, focused fixtures and this
report. Canonical services/configuration/product DB, credentials, collector
implementation, Technical policy and paused FPT remain untouched. Production
activation, real sleep/resume and Codex-close/logoff/reboot acceptance are still
NOT_VERIFIED and require separately authorized work.

Validation: the original saved fixture reproduced the lost-manifest race on
`68df395`; the deterministic concurrent regression failed before correction and
passed afterward. **18 new control regressions** pass (17 simulated lifecycle
cases and one native cross-process lock check). The final focused run reported
**45 passed in 53.78 seconds**, covering those new cases, existing supervisor
policy/native fixtures and the ingestion ownership cycle. The earlier combined
run also passed the other ownership/legacy-observer cases; its finite-role
journal mapping failure was corrected, and its first cold-start ownership
barrier timeout passed on the bounded focused rerun. No production timeout or
ownership assertion was relaxed. The entire application suite was not repeated.
Final JUnit evidence: `C:\Users\PC\.codex\tmp\woofi-supervisor-review-20261015\race-fix-focused.xml`.

Bounded critical-section review: external lock order is control.lock then
command.lock; the daemon takes supervisor.lock then only brief command.lock
sections. Controller acknowledgement/shutdown waits hold no command.lock, and
the signal helper never takes control.lock. Cleanup and exception publications
are fenced. Pending births and incomplete Stop retain their safety markers.
No unrelated termination, forced retry, mutex manipulation or application/data
policy change was introduced. This correction is ready for separate integration;
installation/activation remains unauthorized in this task.

## PATHEXT bootstrap correction — 2026-10-15

The first approved controlled activation of `4a5f519` failed before creating any
service role. The daemon reported WINDOWS_PROBE_FAILED in Backend preflight.
Its sanitized WMI environment omitted PATHEXT, so the canonical PowerShell
launcher could not resolve `git`. Read-only comparison demonstrated that adding
only the parent PATHEXT made the gate pass. Activation was stopped and runtime
source/config restored to a0c96ab without replacing the database. Failure evidence:
`C:\Users\PC\WoofiRuntime\state\supervisor-v1-activation-20261015T011203Z\FINAL_REPORT.md`.
The installed operational package remains stopped; it is not updated by this fix.

`bootstrap_environment()` now includes the approved parent's PATHEXT in the
existing whitelist. PATH and PATHEXT retain their exact values/order/case. There
are no machine-specific search paths, default extension substitutes, execution
policy changes, credential keys or pilot flags added. The existing canonical
credential helper/reference is unchanged. This single environment bootstraps the
daemon and is inherited by the Backend, Frontend and Collector PowerShell
launchers; no separate per-role workaround is needed.

Missing/empty PATHEXT reports WINDOWS_PATHEXT_MISSING. Malformed lists report
WINDOWS_PATHEXT_INVALID: entries must be simple dot-prefixed alphanumeric
extensions and include .EXE and .CMD, compared case-insensitively. Empty entries,
paths, whitespace and control characters are rejected. Diagnostics direct the
operator to the parent Windows environment and never echo the rejected value.
Validation occurs before request creation/process birth and, for a new Start,
before git preflight or pending-launch journaling. Stop, read-only Status and
stopped-intent Resume retain their existing behavior.

The new native regression calls the actual `independent()` WMI bootstrap. It
compares child Git/npm resolution to the approved parent executables, preserves
PATH/PATHEXT, runs npm --version, and validates a temporary Git checkout through
the actual Windows.validate seam. It uses an unchanged canonical Invoke-Woofi.ps1
fixture (SHA256 CE419D770661BF7046DF7B04F1E37220D38AEA8E3721D48EFE77766F42B24AD9)
and invokes -CheckOnly for all three roles. Its credential reference/helper are
explicit synthetic fixtures. Its dummy database-existence file is never opened
or modified, no application is imported, and no service/collector/provider is
started. This qualifies command resolution and the gate contract, not production
credential recognition or service health.

Both retention and detached-WMI regressions failed against the previous source
and passed after correction. Thirteen new checks cover exact environment
retention, secret/pilot exclusion, approved command resolution, isolated canonical
preflight and missing/malformed diagnostics before launch or intent changes.
Existing lifecycle/native, Start/Stop generation and collector-ownership checks
are the focused regression scope; no full application suite is required.
Final focused validation: **58 passed in 45.94 seconds**, including all 13 new
checks. Logs and JUnit evidence:
`C:\Users\PC\.codex\tmp\woofi-pathext-fix-20261015\focused.log` and `focused.xml`.

Focused review: the only new forwarded key is PATHEXT; PATH, dependency bootstrap,
WMI flags, control lock order, generation writes, identity checks, collector mutex,
retry limits/cooldowns and Technical policy remain unchanged. Runtime configuration,
services, product SQLite, credential references, FPT PAUSED state and unrelated
instruction files/WIP are preserved. After integration, a separately authorized
release must install the corrected package and repeat actual service/lifecycle
and bounded stability acceptance. Codex-close and real sleep remain unverified.

## Restart Manager inventory correction — 2026-10-15

Base: `100f79f123f242e3ae69e1b5878691115519c421`.
Local branch: `codex/woofi-supervisor-lock-inventory-fix`. This source correction
is not installed, pushed or activated.

### Incident and qualified cause

The second controlled activation passed actual PATHEXT preflight and
Start/Stop/Start acceptance. At 04:52:29.560667 UTC / 11:52:29 ICT the daemon
recorded `supervisor_stopped: LOCK_INVENTORY_CHANGED` and exited unexpectedly.
Its live roles and ownership records remained available. The authorized recovery
stopped those verified roles and restored source/config to a0c96ab, retaining
the newest product database, writes and receipts. Full incident report:
`C:\Users\PC\WoofiRuntime\state\supervisor-v1-retry-20261015T043849Z\FINAL_REPORT.md`.

The old second RmGetList call mapped **every nonzero result** to the same error;
its return code, needed/returned counts and capacity were discarded. The saved
incident cannot establish a duplicate collector, ERROR_MORE_DATA specifically,
or another Windows error. That uncertainty is retained.

Microsoft's [RmGetList contract](https://learn.microsoft.com/en-us/windows/win32/api/restartmanager/nf-restartmanager-rmgetlist)
documents ERROR_MORE_DATA (234) for an undersized process array. The list can
outgrow the sizing result before the next call. An isolated mocked response
sequence (234 needing one slot, 234 needing two, then success) reproduced the
exact old LOCK_INVENTORY_CHANGED exception before correction. This proves the
implementation failed to handle a supported condition; it does not recover the
missing native code from the production incident. The native structures' sizes
and field layout are unchanged; explicit DWORD return types and EndSession
signature are now specified.

### Minimal inventory correction

Only `lock_owners()` and its direct diagnostic/identity helpers change. All three
callers retain their existing behavior: Collector vacancy before launch,
Collector readiness/Stop inspection, and read-only Status. No application,
collector, launcher, lifecycle policy or manifest-lock architecture change.

- At most **four RmGetList calls**, including zero-capacity sizing. Retry only
  ERROR_MORE_DATA with an increasing required capacity. Delays are 50, 100 and
  200 ms, at most 350 ms total; no tight loop or background retry service.
- Allocate at most 4,096 entries; refuse larger requirements instead of truncating.
  Allocation failure, impossible success counts, inconsistent size responses,
  invalid/duplicate PIDs and zero creation timestamps fail closed.
- Read only the filled count on success, including legitimate shrink-to-empty.
  Never read partial failed buffers or convert an API failure to an empty list.
- Every returned PID is checked against the exact native creation FILETIME via
  query-only OpenProcess/GetProcessTimes; reused, inaccessible or exited owners
  remain unverified. Query handles are closed. No acquisition byte-lock is taken.
- Diagnostics include stage, native code, UTC time and up to four call results
  with capacity/needed/returned/reboot-reason fields. No resource paths, commands,
  environment or credential values are added. Sessions end on all started paths;
  a cleanup failure cannot return a successful inventory or mask an earlier error.

Transient size changes that stabilize recover within the original inspection:
healthy verified processes are neither signalled nor relaunched. Exhausted or
otherwise unqualified inventory raises InventoryUnverified (a Conflict), so it
cannot authorize a birth, successful ownership verification or Stop signal.
The existing fail-closed daemon error boundary preserves role identities and the
generation manifest, leaves live processes untouched and requires operator
reconciliation/Stop. Persistent failure can still stop the daemon; this fix adds
no automatic resurrection or indefinite retries. Durable Stop intent and
incomplete-Stop guards, control/command/lifetime locks, generation fencing,
console identity validation and the collector's kernel mutex are unchanged.

### Validation and review

`tests/test_supervisor_lock_inventory.py` adds **49 passing cases** covering empty,
single, increasing/decreasing and transient inventories, exhausted retry budgets,
native failures, setup/cleanup errors, invalid sizes/owners, PID reuse, unknown
owners, collector exit/ownership changes, duplicate/branching worker rejection,
control refusal, generation preservation and in-place healthy recovery.
Four are native Windows fixtures on temporary file resources: empty inventory,
real single holder plus kernel-lock exclusion, foreign-holder launch refusal,
and exact native creation-time/missing-identity qualification. These are not
canonical collector or production stability acceptance.

One combined focused run covered inventory, supervisor policy, concurrent
Start/Stop, WMI bootstrap/lifecycle, role observer and ingestion ownership:
**117 passed, 1 failed in 98.51 s**. The unchanged finite WMI end-to-end fixture
logged NoSuchProcess during its short-lived process census, before its expected
second launch. Its fixture adapter bypasses Restart Manager. A single bounded
rerun of that exact unchanged test **passed in 9.10 s**. Both outcomes are retained;
the combined run is not represented as an all-green first run. No production
assertion, timeout or existing test was weakened, and no broad suite was repeated.
The original red regression and its subsequent green result are saved too.

Evidence: `C:\Users\PC\.codex\tmp\woofi-lock-inventory-fix-20261015\`
contains red.log, green-original.log, new-regressions.log, focused.log/xml,
finite-wmi-failure-events/status, finite-wmi-rerun.log/xml and scope-preservation.json.
The final checkpoint SHA is recorded in the handoff report and local Git history.

Bounded safety review found no blocker in the correction. RM describes registered
resource users, not exclusive byte-range lock ownership; its list is not an atomic
snapshot with process census, identity checks or later launch/signal. Native API
duration also depends on Windows; only call count, allocation and added retry
delay are bounded here. Existing process/console fences and the actual ingestion
mutex remain necessary. The finite-fixture NoSuchProcess timing limitation and
actual production/Codex-close/sleep acceptance remain explicit risks.

Canonical config/source remains a0c96ab and stopped; installed operational code
is still the previous approved 100f79f bytes. No product DB, credentials, source
cooldowns, Technical policy, FPT PAUSED state, startup tasks or Downloads WIP were
modified. Both unrelated untracked frontend instruction files retain their hashes.
Next action is separate integration review, then separately authorized activation;
this checkpoint does not authorize either.

## Production process-exit correction — 2026-10-15

This correction continues `cc1efe3e9d9650f202472bcec3aaa6dae1c38758` and retains
the PATHEXT and bounded Restart Manager fixes. The separately authorized final
review found a production blocker, not merely a flaky finite-role fixture. See
`C:\Users\PC\.codex\tmp\woofi-lock-inventory-final-20261015\FINAL_REPORT.md`.

### Root cause and scope

The failed legacy assertion expected Backend launch count >= 2 but observed 1.
Its Backend observer exit receipt preceded the daemon's NoSuchProcess event by
about 113 ms. A synchronized native fixture then proved the production path:
actual PID/time/executable/script/receipt verification succeeds, the finite
observer exits naturally, and `psutil.Process()` in `Windows.inspect()` raises
before Recovery can record the exit and apply backoff. The daemon's error boundary
therefore exits while other services may remain alive. Simply passing an unchanged
rerun did not qualify integration.

The same non-atomic census pattern appeared in verification, descendant reads
and console signalling. Stop also needed to retain identities newly discovered
during a failed partial census or by its separate signal helper. The change is
confined to those existing Windows lifecycle seams, tests and this report; no
new supervisor layer, application feature, worker policy or database change.

### Corrected behavior and ownership protection

- Root lookup distinguishes absence from PID/creation-time/executable mismatch
  and inaccessible metadata. Command-line verification handles confirmed natural
  exit and rechecks identity after reading the existing role receipt.
- `observe_members()` is the shared production census for readiness and signal
  validation. It qualifies each child's creation identity, tolerates only
  confirmed departed processes, and retries transient enumeration churn at most
  three times with 50/100 ms delays. PID reuse, access denial and persistent
  uncertainty remain conflicts. No blanket NoSuchProcess suppression.
- Newly qualified members are remembered before a later read can fail. Live
  known members missing from the current tree remain orphan conflicts. Only
  confirmed departed identities are pruned after successful reconciliation, so
  history does not grow without bound. Confirmed root exit with all known members
  gone reaches the existing exit receipt/backoff/attempt-budget policy.
- Recovery copies discovered members into its Role state on both inspection and
  Stop error paths. Supervisor-absent Stop publishes partial discoveries through
  the existing generation fence before returning an error. Durable stopped intent
  and incomplete-Stop markers stay intact; unknown ownership never authorizes Start.
- The existing signal request also carries the helper's latest qualified members.
  The helper persists them before native control and on failure; the parent checks
  binding/epoch/root identity and waits for the union of those members, including
  on helper refusal or timeout. A new surviving child cannot produce successful Stop.
- Exact console membership and process identities are rechecked after AttachConsole
  and before control. A reused/departed identity or foreign console member refuses
  signalling. Stop on an already-finished complete tree requires no signal;
  surviving or unknown children still block cleanup.
- A collector exiting after the mutex snapshot is unready, not fabricated ready.
  Reuse/access failure remains a conflict; process identity is checked again after
  command/CWD reads. The real acquisition mutex, one-root/one-native-worker rule,
  canonical CWD/command checks and existing Start/Stop locks are unchanged.
- Restart Manager success with fewer filled entries than its stated requirement
  is now rejected as invalid, including a contradictory nonzero requirement with
  zero returned owners. The earlier bounded retries/limits and native diagnostics
  are preserved; inventory failures never become empty success.

### Regression and bounded safety review

The original native gate failed again before this correction and passed afterward.
`tests/test_runtime_supervisor_exit_races.py` adds 30 cases: native verified-root
exit, exits during command/tree reads, child exit, bounded census churn, PID reuse,
access denial, detached/surviving children, partial discoveries, worker projection
exit/reuse, already-exited Stop/signal, stale generations, post-attach validation,
signal-helper fresh members/refusal/timeout and durable incomplete Stop journaling.
Native cases use temporary fake roles; deterministic process maps cover adversarial
interleavings. None starts a production service/collector or opens the product DB.

The existing finite WMI adapter now reuses production `observe_members()` instead
of duplicating the unsafe census. Only its fake readiness remains simulated.
Launch-count, exit/backoff, Stop, Resume and ownership assertions/timeouts are
unchanged. Inventory process fakes now provide real creation/executable identity
fields; their unreadable-PID case asserts a qualified fail-closed Conflict instead
of accepting an unhandled NoSuchProcess. No assertion or timeout was weakened.

Final single focused regression: **149 passed, zero failures/skips, 78.37 seconds**.
It includes all 50 inventory cases, 30 exit-race cases, supervisor policy/control,
real isolated WMI/observer/bootstrap checks, and ingestion ownership/cooldown tests.
One existing Starlette/httpx deprecation warning remains. Development red/green
evidence and the earlier diagnostic-assertion correction are preserved. No full
application/frontend suite or unchanged-test retry loop was run.

Evidence: `C:\Users\PC\.codex\tmp\woofi-supervisor-exit-fix-20261015\`
contains red.log, green-original.log, focused-development.log/xml,
native-development.log/xml, stop-development.log/xml and final.log/xml.
The final handoff report records the checkpoint, integration result and exact SHA.

Own safety review covered normal and exception journals, helper handoff, native
identity checks, lock order and stale generations. No blocking finding remains
in this scope. Windows snapshots still cannot be atomic with future process
changes; uncertain ownership continues to fail closed and may require manual
reconciliation. Persistent inventory failure may still stop the daemon while
preserving managed processes. Production activation/stability, actual Codex
closure and sleep/resume are not certified by isolated fixtures.

This task authorizes source integration after validation only. Canonical runtime
remains the stopped a0c96ab release; installed package, product DB/data/cooldowns,
credentials, FPT PAUSED state, Technical policy/checkpoint 30fdff2, startup tasks,
Downloads WIP and unrelated instruction files are unchanged. Controlled activation
requires a separate fresh ownership/data-safety handoff; it was not performed.

## Autonomous local stability Phase 1 — execution plan, 2026-10-15

Scope: restore safe daily Windows operation using the integrated supervisor and
existing canonical launch/data paths. User authorization permits one controlled
activation, not autostart or repeated production retries. This section is the
living plan/progress record, extending this existing implementation document.

Evidence directory: `C:\Users\PC\WoofiRuntime\state\local-stability-phase1-20261015`.
Starting source main: df05ccd4dc29bc33b6b717126185a482bdf92c3d.
Starting runtime: a0c96abdfb8672efd08b1051bd4b2af49e50546e, all roles stopped.

| Milestone | Dependency and acceptance | Execution status |
| --- | --- | --- |
| M0 — establish safe baseline | Fresh source/pin, clean release, native ownership/ports/locks, credential reference, SQLite integrity/FK/provenance and verified online backup; no unknown owner | PASS — 09:34–09:35 UTC: no live roles/owners, 29-table integrity/FK PASS, online backup verified; all identities/static provenance preserved |
| M1 — prepare approved release | M0; independent release directory, unchanged dependency contracts, production build, hashes and actual detached canonical three-role preflight; retain old release/config | PASS — clean df05ccd, unchanged app/dependency/schema contracts, build 2Ar6rJtxBmDOjBqYYnsxA, package hashes and both real WMI/preflights qualified |
| M2 — single controlled activation | M1; install matching package/pin, actual Start/readiness, explicit Stop with durable intent and no restart, Start again; exactly one supervisor/API/frontend/collector root | PASS — Start/readiness, graceful Stop, >60 seconds stopped with Resume retaining intent, then explicit second Start/readiness; one verified native collector owner; no activation failure/retry |
| M3 — product/data/stability | M2; real Home/Explore/Detail/Fundamentals/News/Community/Watchlist, correct serving artifact and labels, 15-minute bounded ownership/HTTP/lifecycle observation, final integrity/provenance/identities preserved | FAIL — daemon exited 09:54:03 UTC with COMPETING_COLLECTOR after 366.97 seconds; product/serving checks passed before failure; data preserved; cleanup blocked on remaining Backend members |
| M4 — independent operation/handoff | M3; detached native job evidence, simple Start/Stop/Status and rollback instructions; actual user Codex-close acceptance | NOT_READY / MANUAL_TEST_PENDING — activation failed; never close Codex or force Windows sleep/logoff/reboot |

Priority/risk decisions: reuse the corrected architecture and today's 149 passing
isolated tests where source is unchanged. The historical unknown outage cause is
not invented or expanded into unrelated investigation. Actual role disappearance,
unknown ownership, duplicate acquisition, data/provenance loss or a critical API
regression fails activation. Persisted/provider/fixture evidence must remain distinct;
ordinary collection follows existing due times and cooldowns, without force flags.

Failure procedure: stop further attempts, preserve failure state/events and any
post-update writes; stop only freshly verified owned collector then web/API roles
through the documented controller. Create a new consistent backup, retain the same
newest live DB, and restore compatible old source/config/gate only after ownership
release. Unknown ownership fails closed. No retry of production activation after
failure without separate user authorization; a scoped source diagnosis/fix may follow.

Phase status remains PARTIAL until every mandatory acceptance gate is proven.
Codex closure is a human gate; native job independence is supporting evidence,
not a substitute. Real sleep/resume remains NOT_VERIFIED unless the user performs it.


### Phase 1 activation result and bounded source correction

The single production activation attempt failed at 2026-10-15 09:54:03 UTC
(16:54:03 ICT). Initial Start/Stop/Start and product smoke passed, but the second
supervisor exited with COMPETING_COLLECTOR. Three observation samples passed;
the 15-minute stability gate failed after 366.97 seconds. Never report the
pre-failure Home screenshot/product checks as current runtime availability.

A simultaneous read-only inventory saw the supervisor PID itself, then reported
owner_exited as that process ended. This is not proof of a duplicate collector.
A finite isolated native reproduction used two temporary file-mutex holders and
four independent Restart Manager readers. Before the correction, 40 of 48
queries included another reader PID or its exit; the complete stdout was observed
in the task transcript. No canonical service/database was involved.

Correction: a separate Windows named mutex serializes complete Restart Manager
sessions, including the initial path probe and RmEndSession, across cooperating
processes/Windows sessions. It does not obtain the ingestion mutex. One bounded
5-second native wait; no spin/retry loop. Missing access, timeout, abandonment,
wait or cleanup failure remain InventoryUnverified. WAIT_ABANDONED releases the
ownership Windows grants but fails the current observation. No PID is filtered
out; foreign holders, incomplete inventories, PID reuse and persistent failures
still fail closed. Lock order remains control/command -> inventory; inventory
never acquires control/command locks. Other tools/older versions that do not use
this protocol can still cause unverified inventories, never permission to launch.

The same 48-query isolated probe returned zero anomalies after the correction.
New regressions cover native cross-process exclusion/release, abandoned-owner
crash release, all wait outcomes, access/open failure, error cleanup and retained
primary errors, plus concurrent native file-owner reads. Existing process, Stop
intent, generation, collector and inventory tests remain mandatory. This is source
validation only: the correction is NOT installed in the canonical package and no
production activation retry is authorized after the failed attempt.

Failure handling: stopped intent persisted. Collector exited gracefully, no
worker/mutex holder remains; Frontend was then independently verified and stopped
using the same driver, under the control lock with generation-fenced publishing.
Backend Stop timed out at 45 seconds. Its observer remains plus recorded uvicorn
redirector/native members whose credential-helper parent exited; subsequent
inspection reports ORPHANED_ROLE_MEMBERS. Both ports are vacant, but the native
Backend still holds the DB. Ownership records are retained; no force kill, old DB
restore, pin rollback or new Start was performed. Current pin stays df05ccd until
remaining ownership can be safely reconciled. The backend hang root cause is not
established by available stack evidence; do not invent one or weaken the guard.

Latest verified backup after collector shutdown:
`C:\Users\PC\WoofiRuntime\backups\product\20261015T095655634196Z\woofi.db`,
SHA256 c7a0e8a098ca929611626e3d77287d62baf8dd7bc3daf47f89b0ac2462e66763.
Live full integrity/FK, schema, all original identities and static provenance PASS.
Articles 4535, stories 4244, text receipts 2933; Community evidence 1933, revisions
1976. Dividend records/documents remain 30/25. Preserve this newest live database.

Phase 1 remains BLOCKED for production acceptance/reconciliation. Source correction
may be checkpointed after focused validation, but integration/activation readiness
must not be inferred. A separate user authorization is needed for another live
activation; safe resolution of remaining Backend ownership comes first. Actual
Codex closure/sleep acceptance cannot run against the stopped/blocked application.


### Source validation after activation failure

The 165-case focused run exposed a separate real Windows file-sharing failure:
Status could hold a normal JSON reader while a controller atomically replaced
status.json (WinError 5). A held-reader fixture reproduced it without timers.
A share-delete-only experiment still failed and was discarded. The correction
uses a second independent named mutex for physical JSON read/write only, retaining
atomic replacement and the existing control/command generation transactions.
No lock is held across a process operation by the physical-I/O helper. Missing
files keep their documented default; invalid JSON/access/coordination failure
remain errors. It never opens the product DB or modifies app API/data logic.

Final focused run: 165 PASS / 3 FAIL, all three from an existing console fake
missing the new CreateMutexW ABI, before its existing identity assertions could
run. The fixture now delegates only CreateMutexW/WaitForSingleObject/ReleaseMutex/
CloseHandle to the real kernel, leaving console attach/control fake and every
assertion unchanged. The entire affected exit-race file plus both new test files
then passed: 48 PASS / 0 FAIL. Combined with the unchanged 165 passing results,
all 168 unique relevant cases have passing current evidence; this is explicitly
split-run validation, not a claimed single 168-test run. XML/logs and calculated
coverage are in the Phase 1 evidence directory. No failed case was skipped,
assertion weakened or timeout extended; no further unchanged broad suite repeated.

The two source corrections were reviewed for lock order, error/abandonment release,
unknown-owner fail-closed behavior, manifest preservation and bounded waits. They
are eligible for a normal source checkpoint/integration only, not proof that live
activation/cleanup has passed. Runtime package remains df05ccd, launch gate disabled,
Backend records retained. No new production activation or force cleanup is permitted
by this failed attempt. Product availability and manual acceptance remain BLOCKED.
