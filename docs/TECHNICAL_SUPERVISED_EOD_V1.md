# Supervised Technical EOD pilot V1

## Approved implementation scope

One configured ordinary-equity pilot (initially FPT), no automatic market-wide
activation. Reuse the durable producer, job identities, matching receipts,
snapshot versions and existing D1/D4/D5 consumer. Preserve VERIFIED separation
and both six-hour/24-hour gates. No same-day policy tier.

Discovery extends the previously qualified HOSE calendar by at most one date
per due cycle. Weekends use the independently qualified weekday trading rule.
Weekday occurrence requires a dated official HOSE trading-summary bulletin.
Missing/contradictory evidence stays unknown, never inferred from SSI bars.
Future holidays or exceptional closures need independently qualified official
evidence and an operator-reviewed CalendarEvidence extension. This pilot does
not automatically label missing weekdays as holidays or exceptional closures.

The public HOSE API uses numeric seconds as displayed wall time, as confirmed
by its official formatter. Qualification must corroborate the wall-time basis
against the preserved October 8 bulletin instant and the current official RSS
explicit +0700 offset. These are HOSE publication facts, not SSI publication or
finality. Source retrieval time and response hashes remain distinct.

A durable coordinator lease and minimum ten-minute cycle spacing bound work.
Discovery checks run hourly with persisted backoff; each run acquires at most
one SSI history scope for the configured ticker, at the existing SDK rate.
New jobs and imported evidence retain deterministic identities. Restart between
reads recovers metadata receipts and computes the exact second-read due time.
Missed-run catch-up is bounded, with no parallel SSI crawl. Source/auth failures
halt the pilot until explicit resume; internal retry failures are capped.

Dry run is SELECT-only where a database exists and never accesses SSI or writes
receipts, jobs or snapshots. Controlled fake-clock tests and an official-source
dry run must pass before any recurring live activation. The public API continues
to perform persisted reads only; the UI displays the actual delayed session and
source-check freshness.

## Components and recovery

- `hose_eod_discovery.py`: bounded official-source qualification and adjacent
  calendar extension. Fixed HTTPS endpoints, no redirects, 20-second timeout,
  512 KB response cap, complete single-day index and exact bulletin identity.
- `technical_eod_supervision.py`: one durable configured pilot, fenced ten-minute
  coordinator lease, hourly discovery and a minimum ten-minute cycle interval.
  Calendar/publication metadata commits before enqueue; deterministic job IDs
  recover a crash between those steps. Existing producer publication remains
  fenced and transactional. An expired coordinator cannot acquire its pilot.
- `TechnicalEODSupervision`: additive table in the existing model/schema setup,
  not a second database abstraction. The canonical worker cannot bypass pilot
  scope, halt or coordinator lease. Other pre-existing jobs keep their contract.
- Transient SSI transport/rate/server failures back off 2, 4, 8 hours and halt
  after three consecutive failures. Authentication/permission failure halts
  immediately. No automatic resume. Upstream exception bodies are never stored.
- A revision invalidates affected overlapping active snapshots, removes their
  active pointers and starts a fresh comparison pair. Two matching corrected
  reads are required before publishing the next immutable snapshot version.
  An unchanged recheck appends audit metadata and reuses the existing snapshot.

Only accepted snapshots retain OHLCV. First reads and mismatches retain compact
authenticated metadata/hash receipts only. Owner-reported SSI authorization for
storage, analytics, redistribution and commercial use remains recorded in
TECHNICAL_EOD_PERSISTENCE_V1.md; it is not independently reviewed legal evidence.

## Operating commands

Run from this isolated checkout. Default/no arguments is a no-write dry run.

```powershell
uv run python -m scripts.supervise_technical_eod --dry-run
uv run python -m scripts.supervise_technical_eod --initialize
uv run python -m scripts.supervise_technical_eod --status
uv run python -m scripts.supervise_technical_eod --run-once --credentials-file <existing-authorized-env-file>
```

Initialization imports pinned qualified metadata only, with zero SSI requests.
Status is SELECT-only, performs no network calls, and emits no bars or secrets.
The existing settings loader reads credentials in memory from the authorized
file; the file is not transferred into this checkout. No credentials are stored
in the pilot config or database. `--resume --run-once` is an explicit operator
action after resolving a halted source/authentication/runtime problem.

The strict single-ticker config is `docs/TECHNICAL_FPT_PILOT_V1.json`; its data
paths must resolve inside this checkout. Runtime SQLite is Git-ignored at
`data/technical_eod/pilot.db`. No original worktree database is written.
Optional `--watch` supports graceful interruption and ten-minute checks, but
no OS service, process supervisor, production deployment or market-wide worker
was installed. The approved local follow-up should invoke one cycle hourly at
minute 05, check the exact committed checkout and pinned evidence, and stay
quiet for unchanged/idle/time-pending states. It must pause on preflight drift
or a halted pilot and must never change policy or auto-resume authentication.
This local scheduling requires the computer on and the app running, as stated
in the [official scheduling documentation](https://learn.chatgpt.com/docs/automations?surface=app).

## Live result — 2026-10-10

The official-source dry run made zero SSI calls and zero database writes.
The October 9 trading bulletin was qualified from official HOSE news 2503357.
Its displayed publication instant is **2026-10-09 16:33:47 +07:00**, corroborated
against the preserved October 8 anchor and the official RSS +0700 time evidence.
The unchanged publication gate is **2026-10-10 16:33:47 +07:00** (09:33:47 UTC).
This proves HOSE bulletin chronology, not SSI bar publication or finality.

One authenticated first FPT history read for **2026-07-01 through 2026-10-09**
completed at **2026-10-10 08:04:58.033323 UTC**. It contains 70 observations,
with adjusted VND prices and volume in shares, current-reconstruction provenance
and cache-bypassed authenticated transport. Durable compact receipt SHA-256:
`1dddb82c5c29ecf0bc360805a0c6894e279562a7bd5c2e2bed1d0b96bef202d9`.
Canonical observations SHA-256:
`1cc89c357bcb29767813e01066e9b3977e4069f06ebbd66fc8fe3f791079f4f1`.
The independently qualified calendar now has 101 contiguous dates: 70 occurred
sessions and 31 closures. Original 100-date seed and evidence reports remain
unchanged, pinned by SHA-256.

The second read is eligible at max(first receipt + 6h, publication + 24h):
**2026-10-10 14:04:58.033323 UTC / 21:04:58.033323 Vietnam time**.
The pilot remains **WAITING_FOR_TIME** and its latest API response is diagnostic;
no October 9 packet, accepted snapshot or raw history has been persisted.
The runtime database contains the recovery receipt and official-source metadata.

The separate, already accepted October 8 FPT packet was displayed through the
patched production UI and a read-only backend harness. Desktop 1440x1000 and
mobile 390x844 passed: PROVISIONAL, evaluated October 8, no meaningful technical
change, no page errors or panel overflow. Synthetic transport cases also covered
loading, obsolete results, four supplied insights capped at three, missing
calendar, unavailable API, retry, corrected version, retraction and stale data.
These synthetic cases are not claimed as real market signals.

## API, Stock Detail and freshness

Existing operational endpoints and their envelopes are unchanged. Set the
existing backend `DATABASE_URL` to the accepted pilot evidence database when
reviewing the pilot API; set frontend `BACKEND_URL` to that backend. This is an
explicit runtime choice, not an automatic change to the original production DB.
No backend was deployed or existing application database reconfigured.

`/technical/{ticker}/daily/operational/latest` selects the newest actually accepted
session, exposes PROVISIONAL assurance, version and source-check freshness, and
reports unavailable/incomplete evidence explicitly. A newer pending job does
not replace an older accepted packet. Retraction produces a diagnostic instead
of silently resurrecting an older packet. HTTP performs persisted validation
only, never SSI acquisition or scoring.

Freshness means the last revision check is within its due interval. It does not
mean same-day coverage or VERIFIED finality. Stock Detail shows the evaluated
session date, retrieval/revision-check times and stale state. The six-hour and
24-hour gates deliberately make review delayed; no same-day tier was introduced.

## Validation and rollout limits

Controlled tests cover eligible/ineligible dates; missing calendar, publication
and SSI data; timezone ambiguity; two-read mismatch; durable first-read recovery;
SQLite disconnect/reconnect; leases and interruption; capped transient retries;
authentication halt; revision/retraction/corrected versions; unchanged cache reuse;
delayed accepted API packets; SELECT-only dry run/status and worker/API separation.
Final validation on 2026-10-10: **897 backend tests**, **73 frontend tests**,
typecheck, optimized production build, desktop/mobile browser integration,
Technical identity guard (9 files) and Git diff checks all passed. The 43 new
controlled tests include parsing, transport classification, CLI scope and durable
supervision. The original 22 milestone source hashes, original HEAD and original
database SHA-256 were verified unchanged. No push or deployment.

The three dependency findings were remediated with compatible patches; see
TECHNICAL_DEPENDENCY_TRIAGE_V1.md. The existing Starlette/httpx test-client
deprecation warning remains, with no behavior failure or unrelated upgrade.

The pilot is intentionally bounded: one configured ticker, at most one history
scope per cycle, six-month/180-day discovery window, at most 128 durable jobs and
731 calendar dates. Older scopes have daily revision checks; this is suitable
for the supervised pilot, not a full-market capacity claim. Before reaching
these caps, a reviewed archival/retention plan and covered-window recheck
coalescing are needed. No automatic deletion or retention change was added.

Weekday gaps block adjacent discovery until official holiday/exceptional-closure
evidence is qualified and imported under operator review. The dynamic bulletin
parser fails closed if schema, timezone anchor, paging or content changes.
Future venue/type/listing changes require refreshing the qualified security
identity evidence; the preserved ordinary-HOSE identity is not universal proof
for every future ticker or listing state. No ticker-specific detector logic.

Remaining live October 9 acceptance depends on a matching time-eligible second
read. Local app availability affects actual run time; missed runs recover from
durable state without inventing retrieval times. Wider ticker activation,
always-on hosting, production API wiring and push/deployment remain separate
rollout milestones. If same-day coverage becomes a product requirement, propose
a separate policy decision; the approved 24-hour gate stays intact.
