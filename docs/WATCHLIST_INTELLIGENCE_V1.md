# Watchlist Intelligence V1

Base: origin/main `2ea10490de0c2120d2b9ddcc44a509868a88079b`.
Existing isolated worktree and branch are reused; other checkouts are untouched.

## Audit findings

- Membership and review IDs were browser-local under `vn30.watchlist.v1`; account
  `Watchlist`/`WatchlistItem` models and CRUD endpoints were scaffolds (501).
- The legacy monitoring endpoint counted exact ticker-tagged Stories from recent
  ingestion; the UI showed three stories but its review action acknowledged the
  entire loaded set. News review replaced old IDs instead of merging them.
- Community used native evidence IDs and content revision records. Its revisions
  include engagement fields, so a content-only Watchlist signature is required.
  Per-ticker Pulse reads also consulted full universe metadata for theme extraction.
- News Article IDs differ from Story IDs. Current Company/Industry/Market Brief
  classification is deterministic headline taxonomy, with partial subject coverage.
  Watchlist reuses that classifier and exact ticker association, without inventing
  sector or macro relevance. A Story keeps one attention identity across publishers.
- Latest Operational EOD reads validated accepted persisted snapshots and preferred
  accepted sessions over pending jobs. Retractions withhold withdrawn packets with
  no older fallback. D1/D4/D5 and acquisition belong outside this read path.
- Stock Detail uses `/stocks/<ticker>` and a Technical section anchor. Watchlist
  preserves those links and adds per-story originals and ticker-filtered News/Pulse.

## Contract

Browser membership and existing review IDs remain compatible. Account CRUD stays
an explicit scaffold. A unified SELECT-only endpoint reads watched metadata,
exact ticker-tagged company reporting (72 hours), public discussions (24 hours),
and the existing accepted Operational EOD projection. It never acquires evidence
or recalculates D1/D4/D5. No sentiment or engagement score is inferred.

Each source has its own identity namespace and content revision. A review records
only displayed items and their current revisions, plus the time of the explicit
action. Reading, navigation, refresh and pagination never review content. New
identities and changed content remain unread. Additional publishers, image retries,
source rechecks and engagement counts do not renew an identity. Reviews are merged
with previously reviewed identities and survive reloads and expiration of windows.
Legacy reviews are retained as a baseline and upgraded to version receipts when
the matching content is next loaded, without reviewing previously unread content.

Counts describe the loaded page, never an uncapped global total. Each ticker has
bounded pages and an explicit more-results indicator. Missing/error source states
are distinct from empty pages. Only the three most recent factual items per source
appear initially; the complete loaded page is available before review.

Technical identities are the accepted event IDs, versioned by their factual
payload rather than snapshot/recheck time. PROVISIONAL stays PROVISIONAL. Empty
accepted packets, incomplete evidence, delayed gates and withdrawals are separate
states. A retracted packet is withheld by the existing reader with no older fallback.
Once a persisted delayed gate has elapsed, the UI says it awaits a source check
instead of claiming the time gate is still pending. Empty checks can be explicitly
reviewed without acknowledging future items. Unread counts become unknown on
corrupt or inaccessible review storage; saved data is never overwritten on failure.

## Bounds and identities

- At most 50 deduplicated, normalized symbols per request.
- At most 12 News stories and 12 Community items per ticker per page.
- A ticker's News discovery scans at most 301 recent matching articles, returning
  a truncation flag when more than 300 exist. A window query returns at most 100
  archived members per selected Story, preserving a stable representative and
  known-source revision signatures; five source articles are disclosed initially.
- Community filters exact ticker membership in SQL before its page limit.
- Technical reads the same accepted packet as Stock Detail and preserves its D5
  order and three-event attention budget; it does not create a second detector.
- Page offsets are bounded to 996. The UI uses pages of 12 and caps navigation at
  that bound. Refresh returns to the first page; focus/minute revalidation cancels
  obsolete requests and clears unavailable evidence.
- Keys are `news:<story_id>`, `community:<native_item_id>` and
  `technical:<event_id>`. Review receipts keep the revision, optional known News
  member hashes and explicit `reviewed_at`; `reviewedAt` stores the latest action
  for a ticker. Legacy `seen` and `communitySeen` stay compatible.

## Source limitations

News has no native correction/retraction ledger. Content changes to known persisted
source evidence are versioned; deleted or no-longer-associated evidence is
withheld. Absence/expiry is never labelled a confirmed retraction. Community has
native content revisions but no deletion ledger; Watchlist hashes factual text and
attribution so reply/view changes alone are not updates. Acquisition coverage and
headline taxonomy remain partial. No cross-device sync is claimed.

## Validation

Tests cover exact ticker matching, bounded SELECTs, identity deduplication,
source freshness, revisions, withdrawn Technical snapshots, empty/incomplete/pending
states, explicit merged review receipts, new arrivals and browser persistence.
The production browser runner uses an isolated synthetic in-memory API. Other
market/ingestion endpoints are disabled in that validation, so it does not acquire
SSI/News evidence or touch the supervised FPT worker. Initial News, Community and
Technical responses travel through the actual Next proxy and FastAPI database
read. Transport fixtures then exercise new arrivals, corrections, withdrawals,
incomplete/no-change states, errors and overlapping requests.

Reproduce from the repository:

1. Run `python tests/watchlist_ui_server.py` (test dependencies installed).
2. Build the frontend with `npm run build`.
3. Start Next on port 3012 with `BACKEND_URL=http://127.0.0.1:8122` in the process
   environment. Do not change operator configuration or another running server.
4. From `frontend`, run `node tests/watchlist-intelligence.browser.mjs`, optionally
   passing the absolute Playwright module path as its first argument.

The runner records JSON and desktop/mobile PNGs under ignored
`data/watchlist_ui_validation/`. Both 1440×1000 and 390×844 layouts, light/dark
themes and English/Vietnamese chrome are covered. No source evidence is translated.

Final validation on 2026-10-10:

| Check | Result |
| --- | --- |
| Full backend `python -m pytest -q` | 911 passed; existing Starlette/httpx deprecation warning |
| Frontend `npm test` | 87 passed |
| Frontend `npm run typecheck` | Passed |
| Frontend `npm run build` | Passed with locked Next 16.3.8; both Watchlist routes included |
| Production browser runner | Passed at 1440×1000 and 390×844; no page errors or horizontal overflow |
| Visual inspection | English/Vietnamese and light/dark screenshots inspected |
| Protected code diff | No changes to D1/D4/D5, EOD production/storage/supervision or supervised worker |

Browser scenarios cover empty/follow, real persisted test News/Community/Technical
reads, explicit review, reload, new arrivals, content revisions, withdrawals, delayed
gate and elapsed gate, no meaningful change, incomplete evidence, obsolete response,
API error/retry, partial review of three visible items, pagination, multiple stocks,
unknown stocks and corrupt storage. Backend cases also cover 305-article truncation,
distinct Story pages, unchanged rechecks, source freshness, corrected snapshot
versions and SELECT-only execution with acquisition/universe readers prohibited.
