# Phase 3 continuation — 2026-10-16

Status: **PARTIAL / BLOCKED at the live preactivation evidence gate**.
Working runtime: `d2c44fb6289623cb682266ea471fb7fece5f9351`.
No application code, provider policy, runtime configuration or product records
were changed by this continuation. Ordinary acquisition remains with the one
healthy canonical Collector. Evidence is saved under canonical
`state/phase3-resume-20261016`; copied databases are isolated, never restored.

## Reconciliation of existing work

- **Complete:** qualified provisional source types, existing SSI adjusted VND /
  shares reader, six-hour matching-read and 24-hour publication gates, D1/D4/D5,
  fenced/idempotent persistence, revision/retraction, API separation, Stock Detail
  and correction-aware Watchlist/review implementation. Prior relevant 415-case
  Technical and 149-case frontend evidence remains applicable to unchanged code.
- **Integrated/deployed but disabled:** canonical single-ticker coordinator,
  default-off opt-in and durable configuration for the approved FPT HOSE scope.
  No parallel worker or scheduler is missing.
- **Time-dependent:** a new qualified comparison pair needs two actual fresh,
  matching, authenticated bounded SSI reads separated by at least six hours.
  Existing snapshot revision check is not due until October 17 04:01:18.209758 UTC.
- **Implementation:** no new production defect or missing capability was
  established; do not introduce speculative clock infrastructure or new policy.
- **External:** historical SSI reconstructed adjusted data still lacks historical
  point-in-time vintages for VERIFIED Materiality/benchmark certification. This is
  separate from PROVISIONAL operation, not its sole activation blocker.
- **Operational acceptance remaining:** independently resolve the interrupted
  receipt chronology, qualify additional sessions on the existing cadence,
  obtain the required real pair, and complete one conditional canonical pilot
  activation/live acceptance. Do not promote fixtures or replay into that proof.

## Bounded plan and result

| Milestone | Evidence and missing capability | User value / scope | Acceptance | Effort | Safety / result |
|---|---|---|---|---|---|
| R1 qualification audit | Existing canonical snapshot, two receipts and calendar through Oct 10; chronology acceptance unresolved | Audit source, hashes, time gates and cooldowns on an isolated backup; one next-weekday official-source check | Every gate explicitly classified; no historical evidence edits | 15–25 min active | COMPLETE assessment; source/time readiness PARTIAL. No SSI or canonical writes. |
| R2 pipeline/delivery acceptance | Existing implementation/tests; canonical snapshot had not had final accepted-view sign-off | Replay current canonical evidence; negative gate probes; focused persistence/retraction/restart tests; actual read-only Stock Detail/Watchlist inspection | Exact deterministic equality, inspectable PROVISIONAL evidence, failed inputs withheld, no VERIFIED promotion | 20–40 min active | PASS within stated replay/fixture/persisted scopes; no fabricated live revisions or review mutations. |
| R3 conditional activation | No new-session pair; interrupted historical chronology not independently signed off | Existing one canonical worker only, one cutover if all gates qualify, then 15-minute live observation | Source/time/ownership/backup/rollback prerequisites all pass | 20–45 min active if ready; real pair >=6h | BLOCKED before activation. Pilot OFF; no unnecessary deployment or repeated stability test. |

Three-hour active-work ceiling was not used as a reason to shorten a live gate.
The evidence prerequisite was reached first. No indefinite command or new
automation is left waiting for it.

## Canonical persisted evidence audit

Snapshot `8496f908c81d4d7ca5cbac0b88ffbd85`, version 1, is for **October 9**,
not the current market session. Its full payload/checksum and append-only
retrieval receipts are retained unchanged. Both receipts bind FPT, July 1–October
9, 70 observations and matching canonical content hash
`1cc89c357bcb29767813e01066e9b3977e4069f06ebbd66fc8fe3f791079f4f1`.

First response: October 15 17:52:52.602354 UTC. Second request: October 16
04:01:16.062394 UTC; second response: 04:01:18.208755 UTC. Recorded request
separation is 36,503.46004 seconds. Qualified October 9 publication is October 9
16:33:47 ICT. The stored policy model passes its chronological, full-content,
scope, calendar, units, authenticated/cache-bypass and nonfixture checks.

This model result is not the outstanding independent operational chronology
sign-off. Retained Windows events show the two resume/RTC corrections between
the reads. They support the user's confirmed Sleep event and do not establish
that either receipt is false or that the six-hour gate was bypassed. There is
no separate elapsed observation bound to the complete pair in the available
incident record. No new clock-attestation schema requirement is being imposed;
the existing unresolved acceptance gate is simply not silently declared PASS.
Neither original timestamps nor accepted data were rewritten or relabelled.

The API currently returns `FRESH` because its source recheck is still within the
existing daily cadence. This means neither newest-session coverage nor a new
SSI acquisition in this continuation. The explicit October 9 session remains
visible. Next due time was preserved, not reset to manufacture fresh evidence.

## New independent source evidence

One bounded four-request read through the existing official parser qualified
the [October 12 HOSE bulletin](https://api.hsx.vn/n/api/v1/1/news/2503652).
Publication: **October 12 16:34:30 ICT**; observed/qualified October 16
05:54:47.219111 UTC. Response, index, pinned-anchor and current official +0700
RSS hashes and original public response bytes are saved in the operational
evidence directory. Metadata hash:
`3a19a9eb89a9909e4278527d63f4c258a5b9de84bc60d393c64384cf34a26078`.

An isolated metadata-only extension through the already-qualified Sunday rule
and October 12 bulletin validates successfully. This is not a canonical calendar
update, SSI publication/finality proof or historical PIT certificate. With both
new-session SSI receipts absent, the actual assessment returns
`INCOMPLETE_EVIDENCE / authenticated_fresh_read_unavailable`. No new session is
claimed accepted. The existing hourly discovery/minimum-cycle/cooldown policy
was not changed; no catch-up crawl was run.

## Validation and actual product boundary

- **Canonical-data REPLAY PASS:** fresh isolated online backup of the actual
  product snapshot, exact D1/D4/D5 output, API equality and Watchlist projection
  equality; source copy hash unchanged, zero Technical SSI requests.
- **Six synthetic negative probes PASS:** missing calendar/publication, wrong
  ticker, fixture input, early second request and altered full-content digest
  all produce incomplete evidence. These are in-memory negative mutations only.
- **Nine focused regressions PASS:** independent time boundaries, correction/
  retraction and version append, durable reopen, SELECT-only API with acquisition/
  scoring forbidden, unchanged snapshot reuse/freshness and latest-retraction
  withholding. The Starlette/httpx deprecation warning is unchanged.
- **Actual canonical Stock Detail PASS for persisted display:** FPT Technical
  tab shows PROVISIONAL, evaluated October 9, source check October 16 11:01 ICT,
  one MA state-change insight and expandable original metrics/source/as-of facts.
  The ordinary completed chart separately covers October 15. No recommendation
  or VERIFIED assurance is claimed.
- **Actual Watchlist API PASS:** SELECT-only FPT intelligence returns the same
  snapshot/version/insight. Existing browser-local membership and explicit review
  receipts were not edited. Actual production retraction/correction transitions
  remain NOT_VERIFIED; isolated tests are not labelled live transitions.
- Existing build/typecheck/full relevant suites are reused for unchanged
  application code. Documentation-only checkpoint requires no production cutover.

## Decision and safe continuation

Keep Technical Pilot OFF and the separate legacy FPT automation PAUSED. Ordinary
Woofi remains available. Qualification is incomplete under the user's explicit
preactivation gate, so activation is not authorized merely by these tests/model
results. The normal due window was not forced early; a clean new matching pair
cannot be fabricated or completed within a three-hour active run.

Resume only after the outstanding chronology/source/time prerequisites can be
qualified. Use the same canonical architecture and its normal schedules; any
later cutover needs fresh ownership, integrity, verified online backup, source/
build compatibility and rollback checks, followed by its own >=15-minute awake
observation. Preserve all later News/Community/product writes. Do not restore the
isolated backup, activate legacy FPT, relax VERIFIED/PIT requirements or claim
current Technical coverage from this persisted October 9 snapshot.
