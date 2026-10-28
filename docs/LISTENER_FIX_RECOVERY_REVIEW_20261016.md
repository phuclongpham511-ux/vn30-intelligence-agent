# Listener checkpoint final safety review — 2026-10-16

Reviewed checkpoint: `0e9743fc6093e2b83a970404860f6e6f7403a89d`, parent
`eb6125490125a5180f1bcc795024f9a541814a01`. Remote main independently matched
that parent. No Daily Use checkpoint, collector/SSI business logic, DB schema,
Technical qualification or credential changes are included.

## Blocking review finding and narrow correction

The checkpoint removed the observed `Get-NetTCPConnection` PowerShell timeout
dependency, but executed native TCP inventory synchronously inside the daemon.
That introduced an unbounded native-call path. A regression explicitly refusing
an in-daemon native read failed on the checkpoint before correction.

The native snapshot now runs in a short-lived **direct base-Python helper** using
the same five-file package, existing psutil dependency path, `-S` and the existing
sanitized bootstrap environment. No venv redirector, PowerShell/CIM, service birth,
database access, intent change or ownership-journal mutation occurs in the helper.
The parent has a five-second subprocess deadline. A timeout reaps only its own
disposable diagnostic process, never a Backend/Frontend/Collector/Supervisor.
It raises a fixed `probe=native_listeners` Conflict, preserving existing blocked
containment and ownership records. This is not a new recovery architecture.

The helper returns a bounded-format JSON listener list. Nonzero exit, malformed,
empty/missing output, unknown owner, unexpected port/type or excess output are
unverified failures; none becomes an empty inventory. Only explicit successful
`[]` is a qualified empty snapshot. PID/creation/executable/lineage checks and
Stop-time revalidation remain outside and unchanged. Both address families are
queried; same-port distinct PIDs remain visible and foreign owners block control.

## Focused validation

202 focused tests passed in one final relevant regression (26.51 seconds),
including native inventory/deadline, listener absence/competition, PID exit/reuse,
Start/Stop serialization/generations, pending births, ownership preservation,
Restart Manager, collector singleton, JSON sharing and PATHEXT. Prior SSI and
frontend evidence remains valid because those sources did not change.

New native Windows evidence uses only ephemeral loopback ports and disposable
processes: IPv4 and IPv6 listeners report the test PID; helper exits without
descendants; a deliberately delayed reader times out and is reaped. The remaining
lifecycle/race tests are simulated, not production acceptance. Multiple listener
owners on the same port are additionally asserted explicitly.

Scope review confirms that collector command inventory, acquisition mutex,
generation fencing, durable intent, launch journals and graceful signalling are
unchanged. The same helper/error contract is used by Status, vacancy and readiness.
No timeout permits launching or terminating a service. No unknown PID is adopted.

## Operational gates

At 16:42 ICT, current d2c44fb services were independently qualified using the
installed controller: Supervisor absent, durable running intent, no pending birth,
all 14 recorded members/receipts verified, Backend/Frontend ready, exactly one
collector root and mutex owner, only known DB holders. Technical Pilot OFF and
legacy FPT PAUSED. Live SQLite integrity/FK passed. Fresh online backup:
`C:\Users\PC\WoofiRuntime\backups\product\20261016T094249250996Z\woofi.db`.
Integrity, schema, counts and provenance were verified on that consistent backup.

Supported Stop can reconcile these recorded live roots after daemon failure; it
persists stopped intent and handles Collector before web/API with identity/console
verification. Proceed only after a confirmed complete Stop, no unknown holders,
final newest-data backup and a qualified source/build/gate. No manual ownership
journal editing, forced service termination, older DB restore or second recovery
attempt is authorized. Production results belong to the separate runtime report
`state/listener-recovery-20261016/FINAL_REPORT.md`, not these source tests.

Historical Windows-level probe delay remains unexplained. Native/deadline tests
do not certify Sleep/Resume, Codex closure, OS policy or indefinite uptime.
