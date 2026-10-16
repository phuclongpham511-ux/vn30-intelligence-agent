# Supervisor exit and SSI quote diagnosis — 2026-10-16

Source-only investigation/checkpoint. No integration, push, deployment, service
control, intent change, product SQL write or external SSI acquisition was performed.
Development branch: `codex/woofi-supervisor-listener-native`, based on verified
remote main `eb6125490125a5180f1bcc795024f9a541814a01`. The separate unmerged
Daily Use checkpoint `91da78d` and two untracked frontend instruction files are
preserved and excluded. Production stays on `d2c44fb6289623cb682266ea471fb7fece5f9351`.

## Verified incident timeline (UTC+07)

| Observation | Evidence |
| --- | --- |
| 12:18:49 | Journal records Supervisor PID 20116 starting. |
| 12:19:15 | Last initial role-ready event; all three roles ready. |
| 12:35:16.824608 | Saved pre-closure ownership snapshot; Supervisor and services healthy. |
| 12:44 | Previous successful manual Codex closure acceptance, as reported in this chat. |
| 13:04:30.565057 | `phase3-resume-20261016/final-runtime-safety.json` independently records Supervisor alive and roles ready. |
| 13:59:21.830728 | Exact final persisted Supervisor heartbeat. |
| 13:59:42.410454 | `supervisor_stopped`: `WINDOWS_PROBE_TIMEOUT probe=listeners timeout_seconds=15`. |
| 13:59:42.414482 | `supervisor_exit`, `expected=false`. |
| 16:16:48.986293 | New read-only census: Supervisor absent, both HTTP services 200, all 14 recorded service identities unchanged, one collector root. |

Journal times establish the exception/exit-event time, not an exact kernel process
termination time. No durable OS exit-code receipt or full traceback was found for
this detached daemon. `main()` would return 1 for this exception; that is a code
inference, not an observed exit status. Historical listener data cannot identify
which role's listener query was in progress.

The installed five-file Supervisor package hashes match the pinned d2c44fb source.
The precise failure path is the **critical listener inventory**, previously read
through a new PowerShell `Get-NetTCPConnection` invocation on health ticks. Its
15-second subprocess timeout becomes `Conflict`, which the run-loop containment
handler records before exiting. This is different from optional `power_evidence`
timeouts handled by d2c44fb. Critical ownership failure still must never become
an empty inventory or permission to restart a service.

No timer-gap/power-evidence event appears in this generation's retained journal.
Bounded System-log queries over the launch/incident interval found no matching
sleep/resume or clock-correction records; the event reader was independently
verified against current System events. There is **no affirmative evidence of
Sleep/clock causality**. The reason PowerShell exceeded 15 seconds is unresolved;
historical CPU, CIM internals and probe-child exit evidence were not captured.

Services survived because WMI launches them independently of the daemon's job.
The exception path deliberately preserves their ownership manifest and running
intent, without signalling services. Their survival is intended containment,
not evidence that supervision is healthy.

## Narrow correction and safety review

`Windows.ports()` now uses the already-installed `psutil.net_connections(kind='tcp')`
native owner-table adapter. It selects both IPv4/IPv6 TCP listeners for configured
ports and preserves the existing `LocalPort`/`OwningProcess` contract. Duplicate
address-family rows for the same port/PID are collapsed; different owners remain
visible. Invalid ports, unknown listener PIDs, malformed replies and native read
errors fail closed with a fixed, redacted diagnostic. No PowerShell fallback,
empty-on-error path, retry loop, dependency installation or controller redesign.

PID/creation-time/executable/lineage checks, foreign-port refusal, generation
fences, pending-launch journals, durable intent, Stop serialization, Restart
Manager and collector singleton checks are unchanged. Native inventory failure
still enters the existing blocked path, retaining intent and ownership without
launching or stopping roles. Optional diagnostics and other critical subprocess
timeouts retain their existing behavior.

The new adapter removes the **observed PowerShell timeout dependency**. It does
not prove the historical Windows slowdown's underlying cause, guarantee that
every future probe succeeds, or certify production stability. Native TCP reads
are synchronous OS snapshots, with no newly claimed hard wall-clock deadline.
Ordinary snapshot races still require the existing identity revalidation before
control operations. One read-only live native snapshot took 0.016 seconds; this
is one observation, not a performance guarantee.

Primary API reference: [psutil network connections](https://psutil.readthedocs.io/stable/#psutil.net_connections).
The installed `_pswindows.py` adapter was also inspected; it delegates to the
native extension and does not start PowerShell.

A future Windows-managed service could supply daemon exit/recovery receipts and
remove the custom daemon-lifecycle boundary, but requires separate installation,
credential/intent/collector integration and acceptance. Manual documented control
has fewer automatic recovery paths but no unattended recovery. Neither is
implemented or required for this focused checkpoint.

## SSI findings: expected caching versus unresolved delivery

The 14:36 baseline reports index source time 14:30, PNJ 13:13:42, HPG about 13:13,
and VCB unavailable. These are historical observations, **not fresh provider reads
made by this investigation**. Stock quotes live in Backend memory, separately
from the collector's persisted News/Community data and the Supervisor process.
There is no evidence that the daemon exit itself stopped the quote service.

Code and isolated tests establish:

- Equity demand is the union of unexpired per-client leases (75 seconds), bounded
  to requested symbols. Hidden/unmounted views release leases; visibility/focus/
  pageshow reacquire. Active polling renews leases; unknown-session retries back
  off and may exceed a lease. No permanently active whole-market subscription.
- Expiry unsubscribes/disconnects but retains cached quotes. Receipt/fetch time
  cannot replace the trade's source timestamp. The ordinary stock freshness
  limit is 120 seconds, with existing same-date break/closing allowances.
- The 10-second TTL belongs to the **index response cache**, not equity freshness.
  Index freshness uses its source timestamp and a 180-second limit. A later fetch
  does not make a 14:30 source record a later trade.
- A newly requested symbol can return unavailable before asynchronous subscription
  and bounded initial OHLC bootstrap. Metadata/reference price cannot stand in for
  a quote. Empty/error provider evidence remains missing with existing cooldowns.
- During an active/unknown session, cached symbols rely on stream events; the
  initial bootstrap is for uncached symbols. A renewed lease with no incoming
  event can retain an old, correctly labelled stale price. Tests prove this code
  behavior, not that the production stream was healthy.

The actual Backend log records one `afternoon-monitor-20261016` request for
PNJ/VCB/HPG and several client releases. Access entries lack wall-clock timestamps
and do not capture active lease expiry, per-symbol subscription acknowledgements,
last DATA receipt, stream reconnect/backoff state or missing-quote reason. Thus
historical subscription continuity and a missed healthy refresh are **NOT_VERIFIED**.
VCB, PNJ and HPG are all active HOSE securities in the persisted SSI universe;
VCB is not absent from discovery metadata. This does not prove the provider
returned a usable VCB quote/reference at the incident time.

No SSI source defect is established from these snapshots. No SSI behavior changed.
Do not repair this by forcing requests, extending leases to all symbols, resetting
limits or labelling cached quotes live. A separately scoped, sanitized diagnostic
projection (lease expiry, stream state, last per-symbol receipt, bootstrap outcome,
backoff; no payload/header/token) would be needed to resolve a recurrence.

## Validation and current production safety

- RED: the new fault-injected listener regression failed on the old adapter with
  the exact `probe=listeners timeout_seconds=15` exception. This reproduces the
  exception propagation, not the unknown historical Windows scheduling cause.
- GREEN: 218 focused Python tests passed, no failures/skips (28.92 seconds).
  Includes native adapter, timeout boundaries, Start/Stop control, generation and
  exit races, Restart Manager serialization/ownership, JSON sharing, PATHEXT,
  existing SSI contracts and four new fake-clock/fake-transport demand cases.
- Final bounded review added explicit native response-container validation, so
  malformed empty containers cannot masquerade as a verified empty snapshot.
  The affected native/timeout tests were then run once: **41 passed**, including
  four additional malformed-container cases. No broad suite was repeated.
- Native Windows evidence: a temporary loopback listener bound to an ephemeral
  noncanonical port reported the test PID/identity and disappeared on socket close.
  Lifecycle/control faults use simulated roles and temporary journals, not live
  canonical Start/Stop or production activation acceptance.
- 21 existing frontend market scheduler tests passed, including hidden release,
  reacquisition, cleanup, unknown-session backoff and foreground recovery.
- `git diff --check` clean. No application-wide suite/build repeated: application
  behavior and frontend source were unchanged. One existing Starlette/httpx
  deprecation warning is unrelated to these tests.

Read-only evidence at 16:16 ICT: port 8000/PID 30516, port 3000/PID 14076;
collector redirector 21080 -> native worker 22612 is **one execution root**;
ingestion-lock owner 22612; database resource holders 30516 and 22612, both recorded.
All 14 recorded service PID/creation-time/executable identities match the 12:35
snapshot. Technical Pilot is off in actual worker arguments/environment. Desired
running remains true. Source HEAD equals the runtime pin. Config/intent/status/
launch metadata hashes did not change during inspection. Existing credential
reference files are available; no credential file contents were read/copied.

Explicit read-only SQLite connection: integrity `ok`, zero FK violations. Counts:
4,974 articles, 4,647 stories, 3,377 publisher-text receipts, 2,291 Community items,
24 stocks, 1,522 discovery securities, 30 corporate actions and 25 source documents.
Dividend records/documents have identical content digests to the verified 12:35
baseline. Community has progressed beyond the earlier 2,184-item observation.
No database file replacement, backup restore, cooldown reset or evidence backfill.

Evidence files outside production state:
`C:\Users\PC\.codex\tmp\woofi-supervisor-ssi-20261016\`
contains the read-only census script, `current-safety.json`, identity comparison,
focused pytest log/JUnit and frontend scheduler log. Canonical operational evidence
was only read. No browser visit or quote/index request was used to manufacture
freshness.

## Disposition

Investigation/focused correction PASS; historical SSI delivery cause remains
partially unverified. This local checkpoint is ready for bounded integration
review, **not already integrated or deployed**. Production remains available but
unsupervised. Do not run Start against its occupied ports/live collector; the
controller intentionally refuses adoption. The next operational step requires
separate authorization for a guarded handoff after source review/integration,
preserving the newest database, verifying graceful ownership release, and then
starting exactly one canonical owner. No automatic recovery was attempted here.
