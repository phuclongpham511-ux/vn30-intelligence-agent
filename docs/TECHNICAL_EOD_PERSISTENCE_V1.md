# Technical EOD persistence V1

## Authorization and scope

On 2026-10-10 the project owner reported direct SSI confirmation permitting
free authorized API use, historical market-data storage and retention,
processing and derived analytics, third-party redistribution, and commercial
use within Woofi. This is owner-reported authorization, not independently
reviewed legal documentation. The former assumed storage-right blocker is
removed. Credentials remain secret and unchanged.

This slice persists qualified PROVISIONAL operational evidence and packets
through the existing SSI provider and D1/D4/D5 consumer. The existing VERIFIED
completion gate and verified HTTP contract remain separate. Calibration,
certification datasets and protected historical cases are outside this slice.

## Implementation contract

- Reuse the configured application database and canonical ingestion worker.
- Explicit bounded ticker/session jobs carry independently qualified HOSE
  calendar and bulletin publication evidence; no calendar inferred from bars.
- Retain only metadata receipts before acceptance. A fresh first read schedules
  one second read for max(first receipt + 6h, qualified publication + 24h).
- Reuse an accepted cached snapshot until its daily revision check is due.
  Each worker cycle performs at most one bounded fresh SSI history read.
- A database lease fences concurrent workers; expired leases recover after
  interruption. Atomic transactions publish evidence, packet and active pointer
  together. Retryable errors have persisted backoff; SSI failures stop the job
  until an explicit operator resume, without automatic authentication retries.
- Accepted snapshots append immutable versions; unchanged reads reuse the active
  version. Later overlapping source corrections retract affected provisional
  outputs atomically and require a new matching pair before republication.
- HTTP reads only persisted state, without SSI acquisition or scoring. Explicit
  session, assurance, receipt times, version, freshness and diagnostics prevent
  an old session or provisional packet from being presented as verified/current.
- Raw accepted evidence remains inspectable in persisted snapshots. No secrets
  enter evidence or public payloads. Missing evidence remains incomplete.

## Validation plan

Exercise timing and missing-evidence gates, cache hits, matching/revised reads,
cross-session retractions, restart and lease fencing, transaction rollback,
public API separation and real bounded FPT data. Run focused regressions and the
full backend suite. Operational results and UI guidance will be appended after
validation.

## Runtime operation

`scripts.produce_technical_eod` accepts a ticker, explicit session and bounded
JSON definition containing `history_start`, `CalendarEvidence` and
`HosePublicationEvidence`. The caller must independently qualify the cited
official sources before ingress; schema validation does not authenticate an
external document. Missing/future/unqualified evidence causes a diagnostic and
no SSI read. No automatic source qualification or universe-wide job creation is
claimed. A previously audited compact first receipt may be imported.

Example with the preserved, qualified FPT inputs:

```powershell
uv run python -m scripts.produce_technical_eod --ticker FPT --session 2026-10-08 --evidence data/technical_eod/FPT/2026-10-08.qualified.json --first-receipt docs/TECHNICAL_V1_FPT_FIRST_RECEIPT_2026-10-09.json
```

The configured application database is the sole persistence store. Schema setup
adds four Technical EOD tables without rebuilding existing data. Normalized
OHLCV is stored only inside an accepted version, together with the original
full second read, compact first receipt, qualified calendar and publication
evidence, packet, content checksum and policy/source versions. Original
observation/receipt timestamps remain unchanged; preserving a reconstruction
does not certify a historical SSI vendor vintage. Separate append-only compact
receipts audit unchanged later source checks. SSI authentication values and
HTTP authorization material are never stored in these records.

The canonical `uv run python -m scripts.ingest_data --watch` worker services at
most one due Technical EOD job per cycle. It reuses accepted snapshots until a
24-hour revision check is due. Jobs remain durable when the worker stops; source
freshness becomes stale rather than silently refreshed. A single database lease
has a ten-minute expiry and fences expired workers. Interrupted publications
roll back; another worker recovers after lease expiry. SSI acquisition failure
stops the job until an explicit `--resume`; other internal failures back off for
one hour. No operating-system supervisor is installed by this slice.

An accepted snapshot is never overwritten. A changed overlapping source bar,
an added/removed bar within an accepted scope, or changed qualification
definition retracts affected provisional outputs. Matching corrected reads
separated by the unchanged timing gates create the next version. Retractions
and active-pointer updates commit together. Source revisions can be discovered
only when the worker performs its next fresh check; no instantaneous upstream
revision notification is claimed.

## API and future Stock Detail consumption

`GET /technical/{ticker}/daily/operational?session=YYYY-MM-DD` returns a
`provisional_packet` or the existing explicit diagnostic shape. A successful
response carries `assurance=PROVISIONAL`, `safe_to_display_as_verified=false`,
snapshot ID/version, actual persisted/last-checked timestamps, next check due,
freshness and the existing unchanged D5 packet. The packet's provenance also
retains its first and second SSI receipt times, source version, units,
adjustment semantics, HOSE publication source and calendar evidence.

`FRESH` means the source revision check is within its 24-hour cadence. It does
not assert that the requested session is the newest exchange session. The
explicit session date must always be shown. HTTP executes bounded SELECTs and
evidence integrity checks; it never acquires SSI data or recalculates scoring.
Missing inputs, retraction, checksum failure and unavailable infrastructure
return diagnostics without an empty successful packet or invented values.
The existing `/technical/{ticker}/daily` VERIFIED contract remains unchanged
and cannot serve these provisional database snapshots. Research and benchmark
readers do not use the operational tables.

Stock Detail should request one explicit accepted session, label PROVISIONAL
and display the session and receipt age, then reuse `packet_state`,
`top_insights`, `all_current_session_events`, family checks and provenance.
`NO_MEANINGFUL_TECHNICAL_CHANGE` is a valid result; it is distinct from missing
or retracted evidence. Cache identity must include ticker, session, snapshot
version and assurance. A diagnostic/retraction must clear the displayed cached
packet. Preserve existing scores/order and offer original evidence links;
preferences may affect presentation only. No frontend changes are included.

## Real operational result — 2026-10-10

The owner-reported permission update enabled one bounded fresh SSI FPT history
read for 2026-07-01 through 2026-10-08. All four preserved evidence file hashes,
the exact worktree, HEAD, settings loader and both original timing gates passed.
The independently reconstructed calendar still contains 69 occurred sessions
and 31 qualified closures across 100 dates with no gaps.

The fresh read completed at **2026-10-10 06:30:27.705427 UTC**
(**13:30:27 Asia/Ho_Chi_Minh**). Its full canonical content hash remained
`4bdfe85b7b7c7bdb8dc9c13c520887922fcf54660bd1a3b47099617676536a22`.
The producer atomically stored version 1, snapshot
`3c596852c76a4850ac229606c3aa75ee`, as PROVISIONAL with
`NO_MEANINGFUL_TECHNICAL_CHANGE`. A database reconnect preserved the accepted
evidence and both receipt audits. The actual FastAPI route, exercised through
its ASGI test client against the configured persistent database, returned
HTTP 200 with PROVISIONAL assurance and only SELECT statements. The VERIFIED route
returned a diagnostic. A repeat worker cycle reused cached state without any
SSI request. The next source revision check is due at
**2026-10-11 06:30:27.716638 UTC**; it requires the canonical worker to be running.
No protected benchmark inputs or certification data were written.

## Freshness decision before same-day product rollout

The approved provisional policy cannot produce accepted same-day insights: the
second request must start at least 24 hours after the independently qualified
post-session bulletin publication. For the qualified 2026-10-08 bulletin at
16:34:41 UTC+7, the earliest possible publication gate was 2026-10-09 16:34:41
UTC+7. A later first read can delay acceptance further because the six-hour gate
also applies. Worker downtime and missing publication/calendar evidence add
further delay. The accepted live snapshot is explicitly for October 8; it does
not establish October 9 coverage.

Recommended product decision: launch this slice as delayed provisional session
review with the visible session date and assurance. Same-day charts/live quotes
continue under their existing market-data contracts. If same-day Technical
insights are required, define a separately approved informational tier or obtain
provider finalization evidence sufficient for VERIFIED admission. Such a tier
would need explicit evidence rules, revision handling, UI labels and exclusions;
it is not implemented or treated as approved here. The existing 24-hour and
six-hour provisional rules remain unchanged.

Remaining wider-rollout issues: independently qualified calendar/publication
acquisition for future sessions, an explicit bounded ticker/job selection
policy, worker process supervision, operational monitoring and Stock Detail UI
integration. SSI finality and historical vendor-vintage certification remain
outside this provisional acceptance claim. No SSI licensing approval is being
requested again.

## Final validation and changed files

- New persistence/recovery tests: **23 passed**. They cover accepted storage,
  cache reuse, receipt audits, both time gates, missing calendar/publication,
  source basis failure, source revisions and cross-session retraction,
  corrected version creation, stopped acquisition, expired-worker fencing,
  publication interruption/rollback, definition changes during acquisition,
  actual file-database reopen, sanitized API failures and SELECT-only serving.
- Full backend suite: **849 passed**, including existing V0, V1, SSI, EOD,
  Technical API, News, Community and worker regression contracts. One existing
  Starlette/httpx deprecation warning remains.
- Technical identity scan: **PASS (9 files)**. D1/D4/D5 algorithm files and
  scoring/detection policies were not edited. `git diff --check` passed.
- This phase changed `CONTEXT.md`, `routers/technical.py`,
  `scripts/ingest_data.py`, `src/db/session.py`,
  `src/services/technical_api.py` (HTTPS provenance filter correction),
  `tests/test_data_reliability.py`, and the provisional progress report.
  It added `src/models/technical_eod.py`,
  `src/services/technical_eod_store.py`, `scripts/produce_technical_eod.py`,
  `tests/test_technical_eod_persistence.py`, and this document.
- Accepted local evidence is in the configured Git-ignored application SQLite
  database; the qualified input definition is under Git-ignored
  `data/technical_eod/FPT/2026-10-08.qualified.json`. Raw market history was not
  added to tracked files. The preserved receipt/index files and older evidence
  investigation remain unchanged.
- Existing provisional WIP is retained. HEAD remains
  `84cb2ef5141010b6e6230f3146f5e1e34216adc8`. No commit, push or deployment was
  performed, and no unrelated worktree was modified.

The approved delayed operational backend milestone is implemented and validated.
Wider rollout and same-day Technical delivery remain the next product boundary;
the recommendation above preserves the approved evidence policy.
