# Supervisor resume timeout — isolated investigation, 2026-10-16

Base: `30991dcaa4d4fc3f207ad1b5914432d5a489c7d7`.
Local correction only. No integration, activation or canonical runtime changes.

## Incident evidence and limits

The preserved Phase 3 report and `state/supervisor-v1/events.jsonl` record:

- Last published heartbeat: October 15 17:54:08 UTC.
- Windows sleep/resume evidence includes Kernel-Power 42/107 and the clock
  correction from 17:54:20.3670782 to 20:54:17.500 UTC.
- At 20:54:21.262583 UTC (October 16 03:54:21 ICT), the daemon recorded
  `supervisor_stopped reason=TimeoutExpired`, then `supervisor_exit expected=false`.
- No `timer_gap` or `power_evidence` event precedes this failure in the retained
  journal. `Recovery.tick()` emits `timer_gap` synchronously before calling
  `power_evidence()`. The historical failure therefore does not establish that
  the optional diagnostic was its source.
- All three roles had reached readiness, with no intervening launch/restart/Stop
  event. The normal running loop's PowerShell subprocesses are listener inventory
  (`Get-NetTCPConnection`) and collector inventory (`Get-CimInstance Win32_Process`),
  each with a 15-second deadline. Their raw timeouts previously had the same name.
- The bootstrap does not preserve a per-probe traceback/command receipt. Available
  PowerShell/WMI event queries supplied no additional command correlation for the
  incident window. Exact historical subprocess/role: **NOT_VERIFIED**. An in-flight
  ownership probe across suspension is consistent with the evidence, not proven.

Sleep contributed an observation/time discontinuity. Neither a wall-clock change
nor the four-second proximity alone identifies the timed-out command or proves an
application failure. No forced sleep, live acquisition or product database read
was used in this investigation.

## Confirmed defect and minimal correction

An isolated replay of the approved base proves a separate concrete defect:
`power_evidence()` catches `Conflict`, but `ps()` used to propagate raw
`subprocess.TimeoutExpired`. An optional event-log timeout can therefore escape
`Recovery.tick()` and terminate the daemon before its otherwise healthy roles are
checked. This is a proven defect, **not a claimed identification of this incident**.

`ps()` now converts its existing finite timeout to a sanitized `Conflict` carrying
a fixed caller label and configured deadline. Labels cover `listeners`,
`collector_inventory`, `canonical_preflight`, `role_launch` and `power_evidence`.
No command, captured output or environment is included. Timeout budgets and native
process-launch semantics are unchanged; there are no retries or timeout extensions.

Only the existing optional `power_evidence()` catch downgrades that error to
`NOT_VERIFIED`, now with its sanitized reason. Healthy role inspection, resume
backoff and durable Stop processing continue. Critical probe timeouts still escape
to the existing blocked daemon path, preserving desired intent, generation-fenced
ownership and pending launch outcomes. Unknown ownership never becomes an empty
inventory, permission to launch, a successful Stop or permission to signal.

## Validation and boundaries

The new focused file covers optional timeout, healthy resume, explicit Stop,
pending-restart grace, critical probe labels and redaction, both actual inventory
adapters, collector birth refusal, unknown identities, pending launch preservation
and daemon manifest preservation. Native isolated PowerShell cases cover empty and
single-row JSON responses and an actual finite delayed command whose timeout
reaps that fixture process. All role lifecycle faults are simulated, not canonical
service acceptance; no Windows sleep is induced.

Validation results:

- Approved-base reproduction: raw `TimeoutExpired(timeout=15)`, no diagnostic
  result event. The two new optional-timeout regressions failed before correction.
- New focused file: **17 PASS** (including real isolated PowerShell commands).
- One final relevant regression: **117 PASS**, zero failures/skips, 28.98 seconds:
  `test_runtime_supervisor.py`, `test_runtime_supervisor_control.py`,
  `test_supervisor_lock_inventory.py`, `test_supervisor_pathext.py` and
  `test_supervisor_probe_timeouts.py`. This includes simulated lifecycle/control,
  native Restart Manager fixtures and isolated WMI bootstrap/preflight, never
  canonical service activation. Existing Starlette/httpx deprecation warning only.
- Focused diff review: no critical probe catch added; no empty-inventory fallback;
  no lock, generation, termination, retry budget or acquisition-policy changes.

Existing Technical policy,
collector mutex, control locks, generation fencing, credentials, launch gate and
runtime configuration are unchanged. Unrelated untracked instruction files remain
untouched. No application-wide regression or browser suite is needed for this diff.

## Recovery implication

This correction removes a demonstrated optional-diagnostic failure mode and makes
future PowerShell timeout failures identifiable. It does not certify production
sleep/resume, or make a critical inventory timeout safe to ignore. The historical
exact command remains unresolved. Canonical runtime remains STOPPED with
`desired_running=false`, launch authorization false and Technical Pilot OFF.
Final supported read-only Status confirms no live supervisor/role/member,
listener, acquisition worker or collector-lock owner. The installed supervisor
SHA256 still matches the Phase 3 package (`d28f9d32dafeee01cdf4cfe1c2b865d3e`
`bcdfd1bea6bdb0b426081e831b42215`); this correction is not deployed.
Review this local checkpoint before separately authorized integration or a single
controlled recovery attempt; preserve all existing evidence and Technical records.
