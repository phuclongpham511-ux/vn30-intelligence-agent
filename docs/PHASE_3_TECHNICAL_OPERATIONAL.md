# Phase 3 — Technical Signal operational

Base: 1598bef6af8fcd1b6af7c1fb63324a14443e30ac. Canonical runtime independently
verified at that release with healthy Supervisor/web services and one collector;
SQLite integrity/FK pass, no Technical jobs/snapshots/supervision. Preserve Phase 2.

## Assessment and reconciliation

D1/D4/D5, SSI adjusted daily transport, bounded evidence qualification, immutable
snapshots, receipt audits, revision withdrawal, latest read API, Technical tab and
Watchlist correction-aware receipts already exist. Certification remains BLOCKED:
current reconstructed adjusted histories are not historical PIT vintages.

30fdff2 is one unmerged commit on 9e8943c. Its touched implementation paths are
unchanged on the current base; selected application/test changes transferred by
path-restricted diff after apply --check. No blanket merge, old dependencies,
runtime state or pilot data imported. Reuse its canonical opt-in adapter and
pending-state projection, not its obsolete deployment status/report claims.

## Milestones and gates

| Milestone | User objective / changes | Evidence, risks and acceptance |
| --- | --- | --- |
| M1 reconcile and isolate | Reuse historical canonical adapter, durable existing tables and UI states; add nonsecret opt-in Settings compatible with existing canonical launcher | Fixture first→second read, restart, ownership exclusion, correction/retraction, explicit wait/missing/source-failure states. No numerical engine/policy change, new scheduler or migration. |
| M2 qualify and validate | Inspect one bounded real official prior-day source through supported parser; real-evidence replay if preserved input available; regressions/build/review | No forced SSI, no old packet import to product, no fabricated calendar/publication. Six-hour matching-read and 24-hour publication gates unchanged. Review pacing, memory bounds, leases and UI/Watchlist unread semantics. |
| M3 integrate and release once | Normal FF push, verified online backup/identity/schema, supported Stop/Start; explicit one-ticker pilot only if every safety gate passes | One collector, metadata-only bootstrap while stopped, no credential copying or legacy automation activation. Actual API/browser pending/accepted evidence and bounded 5-minute stability. Live missing evidence means PARTIAL, not manufactured PASS. |

Operational scope is one existing qualified HOSE ordinary stock from the pinned
pilot configuration (FPT); ticker-agnostic algorithms remain unchanged. No HNX
qualification or full-market coverage claim. Discovery extends one adjacent prior
date per existing hourly cadence, one bounded SSI scope per due cycle, persisted
10-minute minimum coordinator cadence and existing cooldown/backoff. A same-day
or six-hour acceptance cannot be simulated as live within this task.

## Progress

- Assessment/preflight complete, 2026-10-16 00:35 ICT: native process identities
  unchanged from Phase 2. Evidence: canonical state/phase3-technical-20261016.
- M1 in progress: selected checkpoint code/tests transferred on focused branch;
  canonical launcher stays unchanged. Untracked frontend/AGENTS.md and CLAUDE.md
  preserved without adopting their instructions. No product writes/controls yet.
- Next: deterministic regressions, evidence qualification, focused final review;
  only then one conditional release. Full final operational report will be saved
  in state/phase3-technical-20261016/FINAL_REPORT.md.

## Implementation and validation evidence

- M1 implemented: selected 30fdff2 adapter/UI/test seams plus two-line default-off
  Settings opt-in read by existing collector main. Canonical launcher, Supervisor,
  SSI adapter, numerical engines, schema, source cadence and existing budgets are
  unchanged. Runtime opt-in can use a release-local nonsecret `.env`; no credential
  file is copied and the database row supplies the bounded ticker identity.
- Corrected presentation gaps reproduced before fixing: unsupported publisher or
  wrong-ticker first receipt could advertise pending eligibility; Watchlist still
  advertised its stored wait flag for those invalid inputs; an incomplete packet
  state could be projected as accepted. These now fail closed through the existing
  assessment, qualified Watchlist state and explicit three-state packet mapping.
  No financial/Technical algorithm was altered to produce acceptance.
- Official-source LIVE preflight qualified October 9 via four bounded official
  HOSE metadata/RSS reads at 00:38 ICT October 16. No SSI request or product write.
  Seed calendar covers July 1–October 8; no weekday-only occurrence inference.
- Preserved SSI pilot REPLAY: 70 actual observations, October 9 PROVISIONAL
  HAS_INSIGHTS version 1; exact D1/D4/D5 replay/API/Watchlist equality, STALE source
  check, source database hash unchanged, zero SSI requests. Copy is isolated in
  ignored data/technical_eod/phase3-acceptance-20261016, never imported to product.
- Focused initial 40 PASS; final projection/Watchlist subset 32 PASS. Frontend
  149/149 PASS including preserved packet render, zero skips; typecheck PASS.
  Identity guard PASS (9 files); engine/policy/dependency/Supervisor diff empty.
- Final broader Technical regression: 415 PASS in 201.69 s; final projection/
  Watchlist subset after the last state-mapping correction: 32 PASS. Collector
  process-ownership regression 9/9 PASS in 48.94 s (run without webpack overlap).
  Existing Starlette/httpx deprecation warning only. One bounded diff review found
  no remaining blocker: exclusive/reentrant owner, unchanged durable leases,
  single-ticker scope, bounded requests, no HTTP acquisition, qualified states,
  immutable/revision-aware packets and explicit review receipts are preserved.
- Source checkpoint is ready for the exact-path production build and conditional
  integration/cutover. Operational progress and final source/runtime SHAs will be
  recorded in the report above; a source checkpoint does not claim activation.

Live acceptance cannot bypass time: a new first receipt requires a matching fresh
read at least six hours later, and at least 24 hours after qualified publication.
Deployment with an honestly pending pilot is PARTIAL live acceptance. Certification
stays BLOCKED and the separate legacy FPT automation stays PAUSED.

## Continuation after Supervisor recovery — 2026-10-16

Ordinary runtime is now healthy at `d2c44fb`, including 907.34 seconds of awake
stability and the user's subsequently completed Codex closure test. The old
STOPPED description in the original Phase 3 failure report is historical.

The continuation audited the actual canonical October 9 snapshot and both
receipts on a fresh isolated SQLite online backup. Exact D1/D4/D5 replay,
persisted API and Watchlist agreement passed with zero Technical SSI calls.
Actual production Stock Detail displays the delayed October 9 PROVISIONAL
insight, its October 16 11:01 ICT source check and inspectable metric evidence;
the separate price chart correctly covers October 15. This completes the
previously missing persisted accepted-view smoke, not a new live generation.

One bounded public HOSE qualification obtained the October 12 bulletin and
stored its original public responses outside product data. Canonical calendar
coverage remains October 10; an isolated October 11/12 extension is not imported.
October 12 has no first/matching second SSI receipt. The original October 9
snapshot passes the unchanged stored policy model, but the earlier interruption's
independent chronology acceptance remains NOT_VERIFIED. Kernel RTC correction
fields corroborate suspend/resume; they neither prove a gate bypass nor supply
a separate receipt-bound elapsed-time observation. No new mandatory receipt
field or qualification policy was introduced.

Pilot activation is withheld under the user's explicit preactivation evidence
gate. Existing daily recheck is due October 17 04:01:18.209758 UTC; it was not
forced early. A new comparison pair requires at least six real hours, plus the
independently qualified publication gate. Tests cannot satisfy that live wait.
No missing application capability or code defect was established in this run;
no speculative clock/scheduler/collector changes or runtime cutover were made.

See [continuation acceptance](PHASE_3_RESUME_ACCEPTANCE_2026-10-16.md) and
`C:\Users\PC\WoofiRuntime\state\phase3-resume-20261016\FINAL_REPORT.md`.
Phase 3 remains PARTIAL/BLOCKED for complete live operational acceptance;
Technical Pilot remains OFF and the legacy FPT automation PAUSED.
