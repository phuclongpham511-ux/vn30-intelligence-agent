# Local Stability & Performance V1

Date: 2026-10-14. Development checkpoint only; no runtime cutover or push.

## Scope and release state

Base and freshly verified origin/main: `9e8943cac9f61be77bf7cb5a8fb274aebb8c1fbf`.
Branch: `codex/woofi-local-stability-performance-v1`, in the existing development
checkout. No additional worktree was created. The canonical runtime remains pinned
to the base release, with backend/frontend stopped and zero collectors. Nothing in
this checkpoint has been installed in the canonical runtime.

Untracked `frontend/AGENTS.md` and `frontend/CLAUDE.md` are preserved instruction
artifacts (generated Next.js guidance and its pointer). They are excluded from the
commit; their SHA-256 values remain, respectively:

- `63F2C50380ED6303237CCE215CE27AF1D620D094C215E28D1B1538A3C070E3BB`
- `336CC4FBF19BEAADA7CCF9986414FA91851A8D7A07DFB3CCBE800A69EED0AB49`

## P0: what the evidence establishes

The historical service exit cause is **UNKNOWN**. The incident observed around
16:01 ICT cannot be attributed to an application crash, sleep, or Codex cleanup
with the available evidence.

Observed Windows and launcher evidence:

- Last boot was October 13 at 18:29:41 ICT; no incident-time reboot was found.
- Kernel-Power event 42 records sleep at October 14 12:25:55 ICT, reason
  `Application API`. Event 187 records a user-mode suspend request.
- Power-Troubleshooter event 1 records sleep at
  `2026-10-14T05:25:55.053939700Z` and wake at
  `2026-10-14T08:55:46.090617500Z` (12:25:55 to 15:55:46 ICT).
- Backend stdout last activity: 12:23:30 ICT. Collector stdout/stderr last
  activity: 12:25:07 ICT, normal idle/skipped work. Frontend startup reported
  ready in 8.7 seconds. These logs contain no recorded service exit codes.
- Backend stderr contains a VCB history RateLimitError at 11:34:55, followed by
  subsequent successful requests; it does not establish the later shutdown cause.
- Bounded Application event queries returned no matching Python/node/PowerShell/
  Codex crash. Security process-exit auditing was unavailable.
- Fresh census confirms no 3000/8000 listeners or canonical acquisition process.

Sleep explains a monitoring/acquisition gap while the machine was suspended. It
does **not** prove that sleep terminated the processes. Earlier same-day sleep was
followed by continued service activity.

Existing `start-role.ps1` already uses Windows `Start-Process` with hidden windows
and redirected logs. Microsoft documents that the ordinary Windows child is
independent of the starting shell:
<https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/start-process?view=powershell-7.5>.
This does not establish independence from an enclosing process job.

### Small staged reliability improvement

`scripts/windows/Start-WoofiObservedRole.ps1` and
`Invoke-WoofiObservedRole.ps1` provide a **manual**, opt-in wrapper around the
unchanged canonical `launch/Invoke-Woofi.ps1`. The wrapper records role, observer
PID, release/source/database reference, UTC start/exit times, native exit code,
exception type, job membership and console presence. It refuses occupied service
ports, an existing acquisition process, a failed canonical launch gate and
overwriting existing receipts. The canonical collector mutex remains authoritative.

A finite fake-role test proves the observer completes after its starting
PowerShell exits and retains exit code 7. The observed test child was nevertheless
in a Windows job. **Survival after closing Codex/session or killing that job remains
NOT_VERIFIED.** Abrupt process/job termination can prevent `finally` from writing an
exit receipt; a missing receipt means UNKNOWN, never successful shutdown.

No watchdog, scheduler, automatic restart, job breakaway, elevation, service
installation or autostart was added. Existing ownership tests cover graceful stop,
exclusive acquisition, release after process death and persisted cooldowns. The
wrapper was tested only against temporary fake runtimes, never the canonical one.

For a separately authorized recovery/release, an operator can use the wrapper
with one explicitly selected role and the canonical runtime root. It is not an
automatic deployment entry point. The current runtime was not restarted here.

## P1: findings and narrow changes

1. **Warm financial cache readers waited for unrelated cold provider work.** The
   old global lock enclosed both fetching and cached-packet copying. A bounded
   barrier regression reproduced this. A separate short LRU lock now lets warm
   reads proceed while the existing single acquisition lock serializes all cold
   reads. Same-key misses coalesce; the 128-entry/hour-bucket policy, deep-copy
   isolation and provider error semantics remain. Upstream concurrency was not
   increased.
2. **The financial response repeated calculation-input graphs.** An optional
   `projection=display` removes historical calculation graphs and duplicate chart
   graphs, keeping all displayed numeric facts, original statement tables, receipt
   metadata, reconciliation, source/freshness fields and latest calculation
   evidence. The default `projection=full` API remains complete and unchanged.
   Fundamentals uses the display projection; Python formulas are unchanged.
3. **The financial UI aborted at 20 seconds despite prior observed cold requests
   exceeding 25 seconds.** Its budget is now a finite 60 seconds, within the
   existing 90-second proxy budget. Independent page sections keep loading
   separately. Errors stay visible, retries remain manual, and navigation/unmount
   aborts obsolete requests. This is timeout handling, not faster provider fetches;
   aborting a browser request does not guarantee cancellation of upstream work.
4. Production validation exposed unsupported named exports from the existing
   Watchlist route. Two helper functions are now private; the SSR test harness
   exposes them only in its test compilation. No Watchlist behavior/UI changed.
5. A full-backend test hit Windows wall-clock resolution in a synthetic late
   corporate-action update. That test now advances an explicit fixture clock.
   Production corporate-action/history code and strict chronological guards were
   not modified.

No numerical formulas, financial indicators, News/Community schedules, SSI
adapter, Technical EOD policy, source cooldowns or ingestion ownership logic were
changed. Existing Stock Detail section independence and lazy-tab loading were
retained; no speculative request-waterfall redesign was made.

## Measurements and evidence labels

Raw local logs/JSON are retained in
`C:\Users\PC\.codex\tmp\woofi-local-stability-v1-20261014`.
`scripts/benchmark_local_performance.py` uses ASGI TestClient, in-memory SQLite and
synthetic provider overrides, with external socket connections forbidden. It
starts no preview server or collector. Replay uses a previously saved public FPT
API response from the prior release acceptance, with zero new provider calls.

| Measurement | Before | After | Evidence |
| --- | ---: | ---: | --- |
| Warm packet while an unrelated cold read sleeps 250 ms | 261.01 ms | 7.27 ms | SYNTHETIC, one bounded contention measurement |
| Synthetic financial response | 196,106 bytes | 69,855 bytes | SYNTHETIC |
| Saved FPT annual financial response | 1,079,231 bytes | 670,911 bytes | REPLAY, 37.8% smaller |
| Saved FPT JSON serialization, five-sample median | 8.80 ms | 4.30 ms | REPLAY |
| Financial browser request deadline | 20 s | 60 s | FIXTURE contract; not a speed measurement |

Five-sample isolated API medians (milliseconds):

| API supporting page | Before | After | Coverage limitation |
| --- | ---: | ---: | --- |
| Home | 1.36 | 1.28 | Unavailable synthetic index |
| Explore | 3.87 | 4.23 | One synthetic security |
| Stock Detail | 3.92 | 4.41 | Empty synthetic history |
| Fundamentals full | 9.01 | 11.32 | Synthetic financial packet |
| Fundamentals display | 9.35 | 9.78 | Before implementation, parameter returned full response |
| News | 15.90 | 25.07 | Empty synthetic cache |
| Watchlist | 13.55 | 13.55 | Synthetic symbol |

These tiny fixtures do **not** demonstrate overall page-load gains or a regression
in unchanged News/Explore code. They report reproducible request-processing
samples, including framework overhead. Browser rendering/hydration, production
network transfer and new external-provider latency are NOT_VERIFIED. The 250 ms
provider wait is synthetic and unchanged. Prior live FPT/PNJ cold waits over
25 seconds are historical evidence, not measurements from this task.

## Validation

- Initial focused backend validation: **27 passed**, including finite Windows
  lifecycle fixtures, financial cache/display and ownership checks.
- Full backend, run once: **1,019 passed, 1 failed** in 274.18 seconds. The failure
  was the synthetic corporate-action timestamp collision described above.
- After fixture correction, affected provenance/ownership/ingestion/data-reliability/
  financial-display checks: **28 passed**. A first correction targeted the wrong
  clock module, failed and was corrected. No second full-backend run was claimed.
- Frontend suite: **144 passed**. After the production-export correction,
  **13 focused tests passed**, covering financial loading/evidence and Watchlist
  helper rendering.
- Typecheck: PASS. Production `npm run build -- --webpack`: **PASS**, including
  TypeScript, static generation and build traces. Initial build exposed the invalid
  Watchlist route exports; the final build verifies their correction. Webpack was
  used for the existing external dependency junction; no preview was launched.
- Loading fixtures verify one bounded request, honest timeout error, no automatic
  retry, removed timers and discarded post-navigation results.
- Optional display projection passes annual/quarterly/TTM fact/evidence equality,
  original API compatibility, invalid-parameter rejection and SELECT-only reads.
- One focused final diff review: no blocking correctness/data-safety finding.
- Actual production-browser acceptance: **NOT_VERIFIED**; runtime stopped. No
  policy-denied preview was retried or bypassed.

## Canonical safety and remaining limitations

Final read-only inspection: runtime pin and checkout HEAD remain the base SHA;
tracked source is clean. Ports 3000/8000 remain unowned, with zero canonical
collectors and no duplicate ingestion. Existing credential references are
available in SSI-only mode; secrets were not read, copied or changed. The FPT
automation remains PAUSED; no automation configuration was changed.

The existing product SQLite database was opened with `mode=ro` and `query_only`;
`quick_check` returned `ok`, bounded foreign-key check returned no failures,
and 29 tables remain available. Tests use isolated fixture databases. No live
database writes, backup restores, migrations, provenance rewrites or acquisitions
were performed. Downloads WIP and unrelated source checkpoints were untouched.

The live runtime is still unavailable. Historical exit cause and survival of
processes after Codex job/session termination remain unresolved. Manual exit
instrumentation improves future evidence, not guaranteed uptime. Slow cold
provider requests can still exceed the finite UI budget; cancelling a request
does not kill a provider call. Production speed and browser acceptance require a
separately authorized local release/recovery followed by bounded real checks.

Next safe action: review/integrate this local checkpoint, then authorize a
controlled local release and service recovery preserving the current database,
credentials/cooldowns and exactly one collector owner. No deployment is implied
by this report.
