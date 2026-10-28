# Runtime compatibility and ingestion ownership V1

Baseline: `ed9862cb35e82279c2c6c143a535907a9839371e`.
Scope approved by the operator: remove the minimum reader and acquisition ownership
blockers before a canonical runtime migration. No cutover, deployment, expanded
Technical EOD coverage, Dividend product completion or UI redesign is included.

## Dividend contract decision: A, lossless reader compatibility

The consistent read-only product backup contains 30 `corporateactionrecord` payloads
from VSDC, all explicitly non-fixture. Twenty-six observations are verified; one
unverified observation represents an unresolved source correction. Normal revision
selection yields 24 latest observations, not a deletion of the 30 stored versions.
These are real observations produced by unpublished Dividend acquisition/UI work.
Canonical repository reads must parse resident rows even when a particular ticker
or date is not eligible for corporate-action context. Deferring the entire reader
would keep rejecting this otherwise compatible product database.

Three rejected extensions are provenance-critical: `source_updated_at` records
source revision timing; `source_title` preserves original source identity/evidence;
`evidence_text` retains the inspected announcement terms. The narrow adapter adds
only these typed optional fields to the existing frozen, extra-forbidden notice.
It accepts their original values without stripping whitespace, truncation or
reconstructing terms. Unknown extensions still fail explicitly. Absent extensions
are omitted during serialization, preserving older payload/packet identities;
explicit nulls remain present. The existing evidence maximum is 6,000 characters.
All 30 captured payloads satisfy the contract and round-trip exactly.

No table/column migration is required for these fields: they already reside in
the JSON payload. Stored payload bytes, 30 provenance triples and the counts in
all 23 existing tables remain identical after canonical `create_tables` on a
copy. Five existing canonical EOD tables are added to that copy only, with no
pilot evidence imported. SQLite integrity and foreign-key checks pass.
Missing effective dates are never inferred. An unresolved correction returns the
existing `pending_verification` context state after its receipt instead of exposing
an earlier version as confirmed context. Earlier as-of evidence remains unchanged.

Full Dividend acquisition, additional WIP tables/UI, approval of announcement dates
as ex-dates, and historical calibration remain deferred. No source input from the
preservation package or pilot database is copied into the product database.

## Exactly one acquisition owner

`scripts.ingest_data --watch` is the sole continuous product collector. It already
handles universe, index memberships, adaptive News, Community and the existing
EOD queue consumer. This change creates no EOD jobs or additional ticker coverage.
The collector mutex covers the entire process watch lifetime, including idle waits.
Public News/Community/metadata ingestion seams and legacy CLI smoke/force/watch
commands obtain the same mutex, so a separate process cannot bypass ownership.
Same-thread nested calls are reentrant; independent threads/processes are excluded.

For local file-backed SQLite, the mutex is a one-byte OS lock alongside the resolved
absolute database path. It has no expiring TTL, and process death releases it.
Do not unlink it: deleting a locked file can create competing ownership domains.
The file contains no credentials or source data. In-memory test engines use an
engine-scoped thread mutex. PostgreSQL uses a dedicated session advisory lock;
PostgreSQL and shared/network filesystems are not qualified by this local Windows
SQLite acceptance. SQLite URI acquisition fails closed. Migration must use the
same absolute DB path and local volume; hardlink aliases are not supported.

This outer owner does not replace persisted News source leases, lease-token fencing,
two fetch slots, adaptive intervals, retry/backoff or refresh coalescing. Those
continue unchanged. Community retains its enabled sources, bounded acquisition,
robots restrictions and existing 15-minute cadence. Its attempt timestamp is
committed before network work, including the legacy seam, preserving cooldown when
a process is interrupted. Errors retain previous evidence and last-success time.

HTTP `/ingestion/refresh` obtains no acquisition ownership and calls no collector.
It records due-News refresh intent and returns 202 `pending_worker`; repeated intent
is coalesced by the existing durable scheduler. News reads remain cached; Community
reads remain SELECT-only. Metadata is refreshed only by the collector's existing
schedule. Stopping the collector leaves honest stale/never-attempted states, not
request-process acquisition. `/news/refresh` remains the existing intent-only seam.

## Validation and acceptance limits

Public-seam tests first reproduced rejection of provenance fields, stale correction
context, HTTP background acquisition, competing collectors during an idle watch,
and lost Community cooldown after interruption. Controlled independent-process tests
then verify all collector entry points, owner release on forced process death,
persisted universe cooldown on restart and Community cooldown after reconnect.
Existing News durable lease/fencing, source freshness and bounded slot tests pass.

Final checks on the isolated branch: 74 focused backend tests, 934 full backend
tests and 87 frontend tests pass; typecheck and production build pass. Commands:
`python -B -m pytest -q --tb=short -p no:cacheprovider` for the full backend;
the focused invocation adds test_runtime_compatibility, test_ingestion,
test_ingestion_ownership, test_data_reliability, test_news_adaptive,
test_news_correction, test_community_daily, test_market_universe and
test_corporate_action_context modules from `tests/`. Frontend commands are
`npm run test`, `npm run typecheck` and `npm run build`. The existing FastAPI
test-client/httpx deprecation warning does not fail tests. Independent Standards
and Spec reviews found no actionable defects.

All 30 original cases were validated on an isolated copy outside Git. Evidence is
in `C:/Users/PC/Woofi-runtime-compatibility-v1-20261010-4b60d7e2/`:
`dividend-compatibility.json`, test command/result logs and `shadow-results.json`.
Original raw payloads are deliberately excluded from Git.

Shadow acceptance uses backend 8130 and production Next.js 3013, an isolated product
DB copy, blank credential environment overrides and blocked backend outbound
connections. There is no shadow collector. News/Hot Topics, Community, metadata
discovery/search and Watchlist read captured product cache. Market/chart seams are
explicitly synthetic; VN-Index/live quotes deliberately return unavailable, and
missing fundamentals/operational evidence stay missing. Home, News, Watchlist and
Stock Detail routes, direct backend and proxy responses, HTTP intent-only refresh,
backend restart recovery and unchanged Dividend hashes are checked. This is cached
and fixture acceptance, not a fresh SSI/public-source acceptance claim.

## Future handoff, not executed

1. Review this local checkpoint and integrate it into canonical main separately.
2. Select one durable product DB and absolute URL; take a consistent verified backup
   before a separately authorized schema deployment. Retain all Dividend WIP rows.
3. Configure a clean pinned runtime without moving or copying credentials in this task.
   Keep the FPT pilot DB, automation, checkpoint and EOD evidence contracts separate.
4. Stop the existing old News collector before starting the new canonical collector;
   the old code does not participate in the new mutex. Check old process-tree exit.
5. Start one `uv run python -m scripts.ingest_data --watch` against the product DB.
   Start the API and frontend on their agreed ports; keep this worker in an explicit
   terminal or authorized external supervisor. No supervisor is added here.
6. Validate bounded real-source freshness, last-attempt/last-success and collector
   health independently of the already completed offline acceptance. Do not use
   `--force-news` to defeat adaptive cooldown or run parallel legacy collectors.
7. Rollback must stop the new owner before restoring the old collector/API/frontend.
   Retain the same product DB and compatible provenance; never reset it to fixtures.

The dirty Downloads checkout and all original worktrees are preserved. FPT supervision,
D1/D4/D5, EOD admission policy and pilot database are outside the implementation diff.
No push or active service cutover is performed by this checkpoint.
