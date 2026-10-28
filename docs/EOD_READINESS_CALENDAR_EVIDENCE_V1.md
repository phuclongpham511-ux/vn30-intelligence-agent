# EOD readiness and calendar evidence V1

Status: PARTIAL. Code/test readiness and source qualification are separate.
This report supersedes D5-B1's prior-day-only consumer rule, not its historical
implementation report or the official D2 benchmark cutoff/availability policy.

| Gate | Result | Reason |
|---|---|---|
| CALENDAR_READY | PARTIAL | Typed bounded evidence resolver implemented; no complete verified live venue calendar acquired |
| EOD_COMPLETENESS_READY | PARTIAL | Explicit record-bound completion supported; current SSI adapter supplies no finalization proof |
| LIVE_SSI_VERIFIED | NO | LIVE_VERIFICATION_PENDING: own runtime key and secret both absent |
| CONSUMER_READY | PARTIAL | Deterministic integration verified by synthetic tests; live evidence remains unavailable |

## Evidence discovery

Repository source/metadata inspection found Security.exchange and current
last_synced_at, SSI dated stock OHLC, indexSummary/current intraday caches and
research calendar contracts. No operational persisted exchange-session ledger,
complete venue calendar or vendor-finalization evidence exists. Security metadata
proves current cached identity only; consecutive stock bars do not prove exchange
adjacency. Index metadata identifies venues; a latest index snapshot is not a
complete historical calendar. No protected research records were opened.

Reviewed official SSI documentation:

- [OHLC tutorial](https://developers.ssi.com.vn/docs/tutorials/ohlc)
- [Python services](https://developers.ssi.com.vn/docs/sdk/python/service-classes)
- [OHLCData models](https://developers.ssi.com.vn/docs/sdk/python/utilities)
- [Operating hours and environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)

The reviewed public OHLC fields contain date/OHLC/volume/value, without a bar-final
flag or audited publication timestamp. The reviewed services do not document a
complete trading-calendar endpoint. This is a documentation finding, not a claim
that SSI could never supply further evidence. The existing pinned 3.2.1 raw
adapter remains unchanged: only bars before actual Vietnam today are acquired.
Market close, fresh receipt or a returned latest row is not finalization proof.

Specific official calendar candidates:

- HNX annual 2026 notice, 5305/TB-SGDHN dated 2025-12-03:
  https://www.hnx.vn/vi-vn/chi-tiet-lich-nghi-gd-60021971.html
- HNX adjustment of New Year closure:
  https://www.hnx.vn/vi-vn/chi-tiet-lich-nghi-gd-60022084.html
- HNX Tet 2026 notice:
  https://datafeed.mobile.hnx.vn/vi-vn/chi-tiet-lich-nghi-gd-60022295.html?_page=1

Official search results identify annual notices and later amendments (including
an added 2026-01-02 closure). Direct HNX page retrieval failed/timeout during this
task. These are identified public evidence candidates, not imported certified
calendars. Annual scope and amendments need manual venue/date verification;
HOSE coverage cannot be inferred from an HNX notice. Holiday notices establish
scheduled closures, not actual occurrence of every other scheduled session.
Emergency closures and ticker suspensions require separate dated evidence.
No blind scraper, repeated external read, inferred weekday calendar or cache was
added. A future acquired calendar should be versioned with actual receipt, updated
on new notices/corrections and explicit unverified dates; no lookup belongs on each
API read. This task makes no complete 2020-2024 calendar claim.

## Bounded contract and continuity

`src.services.session_evidence.CalendarEvidence` declares venue, coverage,
version and at most 731 date records (coverage <=730 days).
`SessionEvidence` distinguishes SCHEDULED, OCCURRED, CLOSED and UNKNOWN,
exchange-session/market-wide/schedule evidence, actual observation/optional
verification timestamps, source references and unresolved reasons. Ticker-specific
OBSERVED, SUSPENDED, NO_TRADE or UNKNOWN states are separately scoped by identity.
SCHEDULED or an official schedule labelled OCCURRED cannot prove actual occurrence.
Caller attestations require real source validation; a typed label or hash alone
does not authenticate the external source.

`resolve_calendar` uses only records for the requested start through T visible
at evaluation_as_of. Verified CLOSED dates alone are omitted. Missing/unknown/
scheduled days become withheld observation slots; suspended/no-trade ticker days
remain venue slots with no admitted ticker bar. These slots break native prefixes
and D4 continuity, even if a raw stock bar was supplied. Raw withheld observations
remain in provenance. Weekends/holidays do not break continuity when independently
proved CLOSED. No weekday inference occurs. Adjacency means every intervening date
is established OCCURRED or CLOSED, not two consecutive returned stock rows.
Cutoff filtering precedes contradiction checks: a later calendar correction
cannot shadow earlier visible evidence. Contradictory/duplicate visible records,
venue mismatch, insufficient declared coverage
or unverified target occurrence return explicit incomplete diagnostics.

The original VerifiedSessionCalendar interface remains accepted as a legacy
caller-attested complete session-list contract, explicitly labelled in provenance.
Its caller still owns independent coverage/closure verification; it is not a new
source qualification. New evidence acquisitions should use CalendarEvidence.
Unknown calendar evidence is propagated to D5 delivery completeness so an empty
result cannot become NO_MEANINGFUL_TECHNICAL_CHANGE. Valid partial events retain
unchanged ranking with explicit limitations.

## Finalization and same-day rule

`EODHistoryRead.completion_evidence` carries at most 512
`EODCompletionEvidence` attestations. Each binds ticker/venue/session/source,
logical read version and the exact normalized MarketBar SHA256, a COMPLETE /
INCOMPLETE / UNKNOWN status, actual available_at/observed_at, source reference and
provider_finalization/verified_snapshot method. Neither method is inferred by
the SSI reader. Caller verification is explicit in packet provenance.

A present target bar requires exactly one COMPLETE, matching attestation:
availability <= proof observation <= actual read receipt <= evaluation cutoff.
A changed bar/read version invalidates an old proof. Invalid, missing, duplicate,
late or incompatible target proof yields INCOMPLETE_EVIDENCE. An absent historical
bar still reaches the existing incomplete D1/D4/D5 packet path; it cannot become
a verified no-change packet. No positive completion is fabricated for absence.
Explicit contrary prior completion evidence withholds the prior bar; absent prior
proofs retain the previously approved labelled daily availability assumption,
without promoting it to verified historical publication. A verified late completion
timestamp overrides an earlier daily assumption and withholds that observation
at its historical EOD boundary.

A verified same-day bar is accepted only with audited/published availability
matching the finalization proof. The operational decision cutoff is the earlier
of evaluation_as_of and the session's existing 23:59:59 Vietnam EOD boundary.
D1 validates the exact completion-bound current bar; D4 transition evidence keeps
that cutoff, and D5 accepts same-day only with validated completion provenance.
Historical behavior retains its original EOD cutoff. The benchmark loader and
D2's official historical evaluation policy are unchanged. No invented market
completion hour, fake tomorrow date, live quote or assumed same-day availability
is used. Actual SSI same-day acquisition remains unavailable through its existing
reader until an independently qualified completion mapping exists.

## Engine preservation and historical boundaries

One consumer invocation continues to call one D4 evaluation (with its existing
D1 runtime) and one D5 packet builder. No separate D1 recomputation, altered q95,
lookback, MA/RSI transition, Bollinger predicate, S/N/C score, episode identity,
ranking, Top 3 or CA context logic was added. The only engine hooks are verified
same-day admission/cutoff propagation and calendar delivery-completeness metadata.
Semantic event/episode identities remain their existing definitions; packet and
calculation/evidence hashes reflect the new declared evidence policy.

Date filtering precedes current/prior values; actual receipt cannot be backdated.
Proofs bind corrected content and version. Finalization attestations received
after the cutoff/read receipt are excluded before their status/correction content
is inspected, so later corrections cannot alter an earlier packet. Current reconstruction and preserved
operational receipt remain distinct from certified historical SSI vendor vintages.
No historical revision recovery, source-retention qualification, calibration,
protected-data access, API, frontend, Watchlist, archive, database or worker added.

## Live SSI and FPT

Only the reconciled worktree's own Settings configuration was checked, printing
presence booleans, never credentials. Its .env is absent; runtime SSI key and
secret are both absent. No other worktree credentials were read/copied and no
SSI request was attempted. LIVE_VERIFICATION_PENDING. No FPT session or outcome
is represented as verified. Synthetic SDK transport tests remain explicitly
synthetic; they now add independently supplied synthetic finalization attestations.

## Validation and preservation

Final commands run from the reconciled worktree:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_eod_readiness.py -q
.venv/Scripts/python.exe -m pytest tests/test_eod_readiness.py tests/test_technical_eod_consumer.py tests/test_d1_runtime.py tests/test_d4_runtime.py tests/test_d5_packet.py -q
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m scripts.check_technical_identity
git diff --check
```

New focused suite: **34 passed**. Combined runtime regression at an intermediate
checkpoint: **188 passed**; subsequent isolation tests and final changes are all
included in final full backend: **885 passed**, one pre-existing Starlette/httpx
deprecation warning. Identity scan: PASS, nine files. Tracked diff whitespace and
all eight milestone files: PASS.

One preceding full run had **884 passed / 1 failed** in the unchanged
`test_cli_import_appends_late_context_through_persisted_service`. Its repeated
CLI call supplied a non-increasing wall-clock timestamp, rejected by the existing
CA append-history guard. Isolated rerun: **1 passed**. Final unmodified full-suite
rerun: **885 passed**. No CA code/assertion was changed to hide the timing-sensitive
failure; this existing test risk is retained in the report.

Fresh baseline: 16 modified tracked, 58 untracked, zero staged; 74 dirty-file
SHA256 values captured before implementation. Final: 16 modified tracked,
61 untracked, zero staged. **69 pre-existing dirty files are byte-identical**;
only the five listed existing milestone source/test files changed, plus three
new listed files. Dividend/frontend/News/calibration WIP is unchanged. Branch
`codex/technical-development-reconciled` and HEAD
`e64986e0cb011d8af40a122e14d5bb47f540ba22` are unchanged.
Own .env and default vn30.db are still absent. No source credentials transferred.
All pre-existing assertions remain. The old invalid-session
fixture now uses a future date, while dedicated same-day tests assert the newly
required incomplete diagnostic and verified-complete success separately. Old
fixture builders add explicit synthetic finalization attestations; assertions on
quantiles, counts, ranking, continuity, CA and missingness are retained.

Milestone-owned files:

- src/services/session_evidence.py (new)
- src/services/technical_eod.py
- src/materiality/factual.py
- src/materiality/episodes.py
- src/materiality/delivery.py
- tests/test_eod_readiness.py (new)
- tests/test_technical_eod_consumer.py
- docs/EOD_READINESS_CALENDAR_EVIDENCE_V1.md (new)

No commit, push, stage, reset, stash, rebase, cleanup or original Downloads worktree
operation. Recommend keeping D5-B2 live packet exposure gated on actual venue and
completion evidence. A later read-only diagnostic API could safely expose pending
readiness, but this task implements no D5-B2 API and grants no live-ready status.
