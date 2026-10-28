# D5-B2 gated read-only Technical API V1

Status: PASS for D5-B2 code; LIVE SSI READY: NO / verification pending.
Code validation and live source readiness are separate. This milestone exposes
the existing D5-B1 consumer without changing D1, D4, D5-A or V0 scoring.
Live SSI verification remains PENDING. No operational snapshot, venue evidence
or source finalization proof was acquired or invented in this task.

## API and contract

`GET /technical/{ticker}/daily?session=YYYY-MM-DD` follows the existing root
route convention. OpenAPI declares a `kind`-discriminated union:

- `TechnicalAPIPacket`: `kind=packet`, `safe_to_display_as_verified=true`, and
  the original `TechnicalDailySignalPacket` under `packet`, unchanged.
- `TechnicalAPIDiagnostic`: `kind=diagnostic`, ticker, requested_session,
  server evaluation_as_of, readiness_status, reason_codes, missing_evidence,
  typed available_evidence_summary, nullable source_last_observed_at,
  limitations and `safe_to_display_as_verified=false`.

Only normalized alphanumeric ticker and one literal ISO date are public inputs.
Duplicate dates and all extra query parameters are rejected, including as_of,
history_start, evidence and completion_status. The clock and reader are internal
FastAPI dependencies; public callers cannot inject them. Current UTC server time
defines the cutoff, with Vietnam date checks. No blanket prior-day restriction.
No batch endpoint, accounts or new auth infrastructure were added to this public
API. The existing read APIs have no account authentication requirement.

HTTP semantics:

| Status | Result |
|---|---|
| 200 | Verified operational packet or expected insufficient-evidence diagnostic |
| 404 | Ticker absent from the cached Security universe; typed diagnostic |
| 422 | Bad syntax, extra/duplicate query inputs, future date, unsupported/inactive security or invalid consumer request |
| 429 | Calculation busy or public budget exhausted; typed diagnostic and Retry-After |
| 502 | Consumer SOURCE_UNAVAILABLE diagnostic |
| 503 | Database/file-access/internal infrastructure failure; typed diagnostic |

FastAPI syntax errors retain its standard validation detail. Infrastructure errors
never return a 200 packet. A closed or unverified target session is an expected
calendar-evidence diagnostic, not a fabricated empty success.

## Local read boundary and actual readiness

Inspection found persisted Security and Corporate Action data, but no operational
OHLCV receipt/finalization/calendar store. Existing SSI history uses a process
cache and may invoke external transport; it cannot satisfy a persisted-only HTTP
read. Research manifests are not an operational cache and are never auto-loaded.

The smallest adapter reads exactly one server-controlled input file:

`runtime/technical_eod_evidence/<TICKER>/<YYYY-MM-DD>.json`

It does not create this directory, write snapshots, persist packets, scan other
directories, acquire credentials or open research/holdout datasets. The file
contract wraps existing evidence types:

```text
schema_version: operational-technical-evidence-v1
history_start: ISO date
history: existing EODHistoryRead
calendar: existing CalendarEvidence, or null for an explicit missing-evidence result
```

The directory is fixed in the server dependency. Operators must supply independently
validated operational evidence; merely writing an attestation cannot authenticate
SSI or certify a historical vendor vintage. No producer/archive/scheduler is
implemented here. This worktree has no such directory, own .env or default vn30.db.
Without local evidence the API honestly reports missing_local_history. Cached
identity must also exist; an empty discovery cache reports unknown metadata first.

Files are bounded to 4 MiB, 512 historical observations/completion records and
730 history days. CalendarEvidence retains its 731-record/730-day contract.
Ticker traversal, symlinks at ticker/file level, path escape, malformed/oversized
JSON and unsafe source references fail closed. No exception body is serialized.
Evidence references must be bounded opaque identifiers or public HTTP(S) URLs
without credentials/secret query parameters. Private-path/credential-labelled
output is rejected instead of silently redacting and changing packet evidence.
The store is trusted server input, not a public file-upload interface; this
sanitization is not a detector for arbitrary unlabelled secrets supplied by an
operator. Operators must never include private configuration in source evidence.

## Consumer, evidence gate and unchanged engine

The route reads Security by primary key and calls evaluate_technical_eod_packet
once with an explicitly supplied EODHistoryRead, CalendarEvidence and bounded
history_start. A deny-acquisition provider additionally prevents accidental
fallback from invoking a live SSI provider. The HTTP path has no background task,
ingestion invocation, market-provider dependency or upstream transport.

Existing consumer verification remains authoritative for:

- active cached ordinary-equity identity, SSI source, HOSE/HNX/UPCOM venue,
  metadata observation time and requested session;
- SSI adjusted basis, VND prices, shares volume, logical source version,
  normalized identities/duplicates, actual receipt/fetch timestamps and cutoff;
- requested venue coverage and actual occurrence, every intervening calendar
  date, independently verified closures and unresolved suspension/no-trade slots;
- exactly one visible COMPLETE target proof bound to ticker, venue, session,
  source/version and normalized bar hash, with availability <= proof observation
  <= history receipt <= cutoff;
- same-day published availability matching that proof; current/prior observations
  and later corrections remain filtered by the existing knowledge policy.

The API additionally withholds ordinary verified delivery when either critical
D1 price/volume check is unresolved or delivery-incomplete, fixture flags are
present, calendar continuity remains unresolved, packet_state is incomplete or
public provenance is unsafe. These yield diagnostics. Insufficient lookback
retains the existing insufficient_history code; calendar, completion, incompatible
basis, cutoff and infrastructure codes are reused from the consumer.

Valid events can coexist with unresolved noncritical MA/RSI/Bollinger checks or
an unverified bounded episode left anchor. These limitations are preserved, not
converted to continuity or closure. A no-change packet requires the original
D5 fully resolved/delivery-complete empty-state policy. Missing CA coverage stays
UNKNOWN/INCOMPLETE; there is no invented NO_ACTION.

Success preserves all current events, episode IDs/relationships, family checks,
evidence, complete deterministic ranking, Top 3, overflow, S/N/C/Base V0, CA context,
versions, source provenance and limitations. It is an operational technical
assessment with explicitly retained historical availability assumptions and
`source_receipt_not_certified_historical_vendor_vintage`, not a certified PIT
benchmark or calibrated investment recommendation. Public-input gating does not
solve historical source revision recovery.

## Corporate Action read and resource cost

The existing CA repository loads all revisions for each context lookup. The HTTP
adapter subclasses it only to provide a bounded request-local known-action view;
the existing context/revision/verification rules remain in use.

Two SELECTs at most find <=512 identities ever assigned this ticker before cutoff,
then <=512 latest visible revisions of those identities. Symbol/effective-date
filtering happens AFTER revision selection, preserving corrections away from
the ticker/date. Later revisions cannot shadow visible earlier evidence.
Oversized/ambiguous/failed optional CA reads remain UNKNOWN and are not retried for
every historical session. No database write, new table, migration or index is added.

Result materialization is bounded, but SQL work still depends on existing table
size/indexes, particularly JSON symbol lookup; there is no constant-cost claim.
Existing database deployment/startup behavior in main.py is unchanged. HTTP reads
perform only SELECTs: Security PK lookup plus at most two CA queries, no full
universe loading and no per-session SQL loop. One 4 MiB file is read; existing
bounded D4 prefix reconstruction remains quadratic within the 512-record cap.

A process-wide sliding-window budget permits 12 accepted calculations per 60
seconds, one active calculation, no waiting queue. It runs before database/file
reads and also covers missing-data requests. Storage is bounded to 12 timestamps.
Rate/busy rejection uses 429 with Retry-After. This is a small public endpoint
guard, shared by clients within each process, not distributed/per-user quotas;
multiple server processes have separate budgets. No Redis, queue, full-market
computation or packet cache added.

## Fixture examples

Persisted generated evidence for XYZ/2020-03-02 with two facts returns, in outline:

```json
{"kind":"packet","safe_to_display_as_verified":true,"packet":{
  "ticker":"XYZ","trading_session":"2020-03-02",
  "packet_state":"HAS_INSIGHTS","score_version":"v0"}}
```

This excerpt omits the full retained inventory/evidence only for readability.
It is synthetic integration evidence, not live SSI proof. A dedicated test compares
the complete response packet with the exact existing consumer model dump.

An existing cached ticker without the local file returns:

```json
{"kind":"diagnostic","ticker":"XYZ","requested_session":"2020-03-02",
 "evaluation_as_of":"2021-01-01T00:00:00Z",
 "readiness_status":"INCOMPLETE_EVIDENCE",
 "reason_codes":["missing_local_history"],"missing_evidence":["local_history"],
 "available_evidence_summary":{"local_history_present":false,"observation_count":0,
   "calendar_present":false,"completion_count":0,"source":null,"venue":null},
 "source_last_observed_at":null,
 "limitations":["source_receipt_not_certified_historical_vendor_vintage",
   "local_operational_evidence_required_not_acquired_by_api"],
 "safe_to_display_as_verified":false}
```

## Tests and review

51 focused API cases pass. They use actual temporary persisted JSON files,
in-memory SQL, internal clock/reader dependencies and the real D1 -> D4 -> D5
consumer. Synthetic indicators are controlled only for targeted 3/overflow cases.
They do not serve as vendor authentication. Existing HTTP tests block SSI reader,
provider acquisition, SDK transport, HTTPX HTTPTransport, Requests transport and
ingestion callback; teardown asserts zero acquisition attempts, even if an engine
exception would otherwise become a diagnostic. TestClient's in-process transport
remains available. Repeated reads capture only bounded SELECTs and identical
fixed-clock packet JSON; budget rejection happens before reading the local file.

Coverage includes 0/1/2/3/5 events, Top 3/overflow, continuation/unresolved episodes,
CA score/ranking neutrality, revision/cutoff selection, no local history, insufficient
lookback, missing/closed/late calendar, missing/invalid/late completion, same-day
proof, incompatible basis/source, late metadata/receipt, missing target, fixture
exclusion, bounded file/history, sensitive source/CA provenance, request validation,
429 budget/busy behavior and sanitized 503 database/file faults.

Exact commands (worktree Python, no frontend change):

```powershell
.venv/Scripts/python.exe -m pytest tests/test_technical_daily_api.py -q --tb=short
.venv/Scripts/python.exe -m pytest tests/test_technical_daily_api.py tests/test_technical_eod_consumer.py tests/test_eod_readiness.py tests/test_d1_runtime.py tests/test_d4_runtime.py tests/test_d5_packet.py tests/test_stocks_api.py tests/test_data_api.py tests/test_news.py tests/test_news_discovery.py tests/test_news_pagination.py tests/test_news_adaptive.py tests/test_news_correction.py tests/test_news_refinement.py -q --tb=short
.venv/Scripts/python.exe -m pytest -q --tb=short
.venv/Scripts/python.exe -m scripts.check_technical_identity
git diff --check
```

Focused final: 51 passed. Combined API/runtime/News regression: 316 passed at the
preceding 47-case API checkpoint; the four additional API cases pass in the final
focused suite. Final full backend regression: **936 passed**, one existing warning,
149.88 seconds. No unexpected regression or pre-existing timing failure occurred
in this full run.
Identity scan PASS (9 files). Tracked whitespace check PASS; existing CRLF notices
are conversion notices, not introduced whitespace errors. One existing Starlette
httpx deprecation warning remains. Manual standards/spec review confirms one
root app, one added GET route, unchanged algorithms/source schemas/scoring,
public-input/evidence/network boundaries and no frontend/News modification.

Initial red collection proved the missing route/service. Expanded tests initially
blocked TestClient's own HTTPX request as well as external requests; the guard was
corrected to block actual external transport without lowering network assertions.
The correction fixture initially changed symbol without a stable component_id,
which represents a new identity in the existing CA repository; it now uses the
existing explicit component identity to test real revisions. No engine rule or
pre-existing assertion was changed for these fixture issues.

## Owned files and Git preservation

- main.py: import/register one router only.
- routers/technical.py: new GET route and server dependencies.
- src/services/technical_api.py: new bounded local reader, gate/envelopes,
  request budget and read-only CA adapter.
- tests/test_technical_daily_api.py: new public-seam tests.
- docs/D5_B2_GATED_READ_ONLY_API_V1.md: this report.

Baseline: 16 modified tracked, 61 untracked, zero staged. SHA256 verification
confirmed all 77 pre-existing dirty files byte-identical. Final status
after this report: 17 modified tracked, 65 untracked, zero staged. All pre-existing
Technical, Dividend, frontend, News and calibration WIP is preserved. No commit,
push, staging, reset, stash, rebase, cleanup or Downloads repository operation.
Branch codex/technical-development-reconciled and HEAD
e64986e0cb011d8af40a122e14d5bb47f540ba22 are unchanged.

Next smallest task: qualify one recent completed operational ticker/session using
independent venue and bar-bound completion evidence plus an actual SSI receipt,
then verify this local-only endpoint on that evidence. Source acquisition/storage
rights and historical-vintage limits remain separate; do not infer live readiness
or implement a production scheduler from these tests.
