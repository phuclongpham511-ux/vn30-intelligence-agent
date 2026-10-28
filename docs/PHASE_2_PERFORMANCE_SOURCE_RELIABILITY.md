# Phase 2 — performance and source reliability

Base/runtime: ef5e3fec07441a61f32fbcf620561e1d0f0ea9ae. Phase 1 closure test
passed with unchanged process identities. Existing checkout reused on
`codex/woofi-phase2-performance-reliability`; unrelated untracked frontend
instruction files preserved. No Supervisor architecture/EOD/provider policy work.

## Baseline and priorities

Bounded ordinary LIVE reads, 2026-10-15 16:42 UTC; no forced refresh/cache reset.
First-observed cache temperature is unknown, so it is not labelled proven cold.

| Path | First observed | Subsequent observations | Payload |
| --- | ---: | ---: | ---: |
| FPT financial display | 487 ms | 315 / 605 ms | 670,911 B |
| PNJ financial display | 4,154 ms | 432 / 273 ms | 648,709 B |
| VCB financial display | 3,805 ms | 176 / 201 ms | 639,830 B |
| Explore / search | 20 / 20 ms | 20 / 27 ms | 4,756 / 2,216 B |
| News / Community | 131 / 216 ms | 102 / 222 ms | 24,185 / 12,438 B |

20 enabled News and three Community sources healthy; disabled FireAnt excluded.
No current F319/Money24 outage demonstrated. SQLite/query fast paths are not a
confirmed high-impact bottleneck. Cold upstream constructor/handshake remains an
external dependency; no speculative parallelism, rate-limit or cache-expiry change.

Seven-sample paired REPLAY of captured annual financial packets found recursive
Pydantic deepcopy 21–27 ms versus validated Python-dict roundtrip 9–11 ms. Replay
contains only the selected annual observations, not a complete live provider packet.
Calculation itself ~8–12 ms; an additional derived-response cache would cost more
copying than it saves and is rejected. Preserve numerical formulas/provenance.

| Milestone | Impact/evidence and benefit | Complexity/risk | Validation/acceptance |
| --- | --- | --- | --- |
| M1 packet copy + frequency reuse | Packet deepcopy dominates local replay; repeated annual→quarterly→annual re-downloads ~0.65 MB | Low/medium; mutable isolation, ticker/period ownership, freshness and cancellation | >=40% paired replay copy reduction; deep equality/isolation/nonfinite checks; returning to a successful frequency within 60 s makes no request; expired/error/manual retry still read normally |
| M2 Community diagnostics/quiet source | Confirmed source code treats no recent sitemap posts as parse failure; generic ValueError hides cause | Low; source health must not hide genuine parse/network/access failures | Deterministic pre-fix failure then pass; empty valid old sitemap succeeds, malformed/recent unparsable fails; sanitized error codes/next due; unchanged persisted cadence and singleton |
| M3 integration/local release | Ship validated changes together once | Operational; protect Phase 1 | Focused tests then one relevant regression run/build/review; normal FF push verified; exact pin/owners/integrity/online backup before one cutover; canonical browser smoke + bounded five-minute identity/HTTP observation |

Dependencies: existing Python/Node packages, approved canonical launch procedures.
No new dependencies/schema/financial indicators. Frontend changes reuse current
layout, VI/EN and themes; data displayed from a cached read retains original read
and source timestamps. Cache lifetime 60 seconds, at most three frequency entries
per mounted Fundamentals component; no background/prefetch/retry acquisition.

## Progress record

- Assessment/baseline complete; raw evidence in
  `C:/Users/PC/.codex/tmp/woofi-phase2-20261015` (LIVE vs REPLAY labelled).
- M1 source PASS: validated Python-mode packet copy keeps detached mutable graphs,
  numeric/date semantics and all provenance. Nonfinite input fails closed. Paired
  11-sample REPLAY medians (baseline deepcopy → actual candidate get_reports):
  FPT 21.323 → 8.165 ms (61.71%); PNJ 17.646 → 6.997 ms (60.35%);
  VCB 19.925 → 8.718 ms (56.25%). No new derived-response cache was added.
  Fundamentals reuses at most three validated frequency reads for 60 seconds,
  preserving read/source times; expiry, clock reversal, failures, explicit retry
  and navigation cancellation are covered. A round-trip uses two requests, not
  three. Live end-to-end improvement remains a post-release measurement.
- M2 source PASS: original quiet-sitemap regression failed (1 FAIL/3 PASS), then
  passed after correction. A qualified old sitemap now succeeds with zero new
  items; recent unparseable/missing/future-only evidence still fails. Stable
  HTTP/timeout/access/format codes omit upstream messages, credentials and bodies.
  Source API exposes additive `next_due_at` from existing persisted attempt cadence.
  No source interval, retry budget, schema or collector ownership change.
- Validation: initial focused backend 53 PASS; final relevant backend run
  188 PASS/2 FAIL in 116.50 s. Both failures were unchanged subprocess-fixture
  startup preconditions (10-second first.called wait), not ownership assertions.
  Filesystem evidence shows first.called was created 1.378 / 0.401 seconds after
  cleanup release, with DB/lock creation at that late stage. Heavy dependency
  startup overlapped webpack; CPU contention is plausible, not directly proven.
  After build completion, the whole unchanged ownership file passed 9/9 in
  68.19 s. No assertions/timeouts were changed, tests skipped, or broad loops run.
  All 190 unique relevant backend cases therefore have current passing evidence,
  reported as split validation rather than one clean 190-test run.
- Frontend: 147/147 PASS; typecheck PASS; webpack production build PASS. One
  bounded self-review checked ticker/period ownership, copy isolation, finite
  values, source errors, cancellation, bounded caches, API compatibility and
  unchanged source scheduling/mutex policy; no blocking finding.
- M3 integration/release pending. Canonical runtime is still the protected Phase 1
  release at this checkpoint. Operational acceptance will be recorded in
  `C:/Users/PC/WoofiRuntime/state/phase2-performance-20261015/FINAL_REPORT.md`.
- Deferred: persistent financial cache, SDK handshake rewrite, source concurrency,
  new supervisor/autostart, database migrations and page redesign: insufficient
  benefit/evidence or unnecessary risk. Reconsider only with new measurements.

Final acceptance must report live/replay/fixture differences, external latency,
all correctness and operational gates, exact commits, and measured limitations.
