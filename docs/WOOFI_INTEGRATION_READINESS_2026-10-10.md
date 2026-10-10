# WOOFI Technical + Explore integration readiness

Validation date: 2026-10-10, Asia/Ho_Chi_Minh.

This is a local engineering checkpoint. Connected live SSI, News and Community
acceptance is not claimed. No push, deployment, acquisition, credentials transfer,
runtime database copy, or active pilot operation was performed.

## Isolation and exact ancestry

Integration worktree:
`C:/Users/PC/.codex/worktrees/woofi-integration-readiness/vn30-intelligence-agent`.
Branch: `codex/woofi-integration-readiness`.
Integration commit: the commit containing this report; resolve with
`git rev-parse codex/woofi-integration-readiness`.

The app worktree operation could not resolve the nested repository. Git created
the new branch/worktree explicitly at the verified Technical SHA. Before any
integration, all registered worktree HEADs, branches and porcelain states were
recorded in ignored `data/integration_readiness/worktrees-before.json`.

The exact existing ancestry is linear:

```text
84cb2ef5141010b6e6230f3146f5e1e34216adc8  Technical signal checkpoint
  -> e7acc5998504f4e7e2561fee363ecd500063fd6b  Operational EOD persistence
  -> 162d1de8cbaba2358d358ebbd4bdec0834d25184  Technical Stock Detail
  -> beb3b9ab7a01ce299e93064779b5fac2fc28f482  Dependency patches
  -> df5a4569fac70dd9df5cc155aaf6027316d27c4f  Verified Technical base
  -> 3d56bf1fa23eeab6ede48bf3989dcf783c6ddc39  Verified Explore/Home V2
  -> integration checkpoint containing this report
```

`git merge-base` of the two supplied commits is the full Technical SHA.
Explore's sole parent is that same SHA. Integration used `git merge --ff-only`;
there were no conflicts, duplicated commits, cherry-picks or policy choices.
Only the separate integration branch was advanced.

The existing Technical and Explore worktrees were clean. Downloads, the
reconciled Technical worktree and the Technical signal checkpoint contained
unrelated WIP. They were not staged, edited, reset, cleaned or moved. Their Git
HEADs, branches and porcelain states were compared again before checkpointing.
The active SSI supervision checkout was never modified or operated.

## Checksum investigation and exact defect

The Technical baseline was tested at **df5a456** before integration using a new
`uv sync --frozen` environment: **880 passed, 17 failed**. The integrated,
unrepaired **3d56bf1** tree produced **882 passed, the identical 17 failed**.
JUnit failure identities were compared as sets; Explore introduced no failure.

The failures are caused by Git text normalization of two byte-pinned metadata
documents when the operational checkpoint was committed. The repository has
`* text=auto eol=lf`; local `core.autocrlf` is true. Git blobs and fresh checkout
files contained LF, whereas the existing pins and original transfer manifest
describe CRLF bytes. This is a committed packaging defect, rather than a change
to the Technical numerical contracts, stale assertion expectations, an upstream
source revision, or a dependency/runtime behavior difference.

| Qualified evidence | LF Git blob SHA-256 before repair | Original pinned CRLF SHA-256 |
| --- | --- | --- |
| HOSE publication, October 8 | `b39ad06819a33cd3534c1fd4ca330a986f89407807dbb990b2b425fc2650707f` | `416f1fbc0e4cb0f95c2db1174858997b0bfe485480b706fca45d235f4413ad8e` |
| FPT security receipt, October 9 | `3ecc1c7eafbe4b8e0c7b49d42ed75441d2b1f1d32463f8a68d9b77adbbaaa5ae` | `6446ad20e1ab1ff692ae8b3a7799f213d5a46c85fb33bfc3ddf1cd87ccc4f20d` |

Reconstructing CRLF from each LF blob produces its original pin exactly. A
read-only comparison with the corresponding original checkpoint metadata files
independently confirmed exact byte equality. Parsed JSON objects are identical.
The calendar TSV already matches its original
`88b288afa760f13e09522624f17b9fa6dce481047bf2bbfee839d13ebec9bd49` pin and is unchanged.

An isolated Git archive of Explore reproduced **17 failed, 4 passed** in the two
affected suites. Restoring only the two original byte representations made
the same archive pass **21 tests**, without any code or test change.

The integration repair restores those exact original CRLF bytes and marks just
the two documents `binary` in `.gitattributes` (`-text -diff -merge`). They are
archival, byte-qualified evidence and must not be automatically normalized or
merged. All other files retain the repository's LF rule. The documents' semantic
contents, original expected hashes, qualification algorithms and tests remain
unchanged. The binary diff is independently explained by the hash table above;
the only added bytes are carriage returns at the existing 16 and 11 line breaks.

Fresh `git checkout-index` export of the staged tree retained the exact pins and
passed the **21 affected tests**. Additional negative checks changed bytes in
disposable metadata only: `seed_calendar`, `publication_anchor`, and CLI
`configuration` all continued rejecting changed evidence.

### Exact failing tests and assertions before repair

These tests are unchanged; the 15 HOSE cases stop at evidence loading before
their intended publication/parser assertions can run.

| Test in `test_hose_eod_discovery.py` | Observed failure |
| --- | --- |
| `test_qualified_seed_has_69_sessions_31_closures_and_no_gap` | `ValueError: Qualified seed checksum mismatch` |
| `test_official_bulletin_separates_publication_client_time_and_ssi_unknown` | `ValueError: Publication anchor changed` |
| `test_ambiguous_or_missing_publication_fails_closed[anchor]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[timezone]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[stale-rss]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[pagination]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[duplicate]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[title]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[summary]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[published]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[approval]` | Same publication anchor exception |
| `test_ambiguous_or_missing_publication_fails_closed[deleted]` | Same publication anchor exception |
| `test_no_bulletin_is_unknown_not_a_holiday_and_current_day_is_ineligible` | Same publication anchor exception |
| `test_growing_calendar_does_not_change_prior_job_definition_or_fabricate_weekday` | Same publication anchor exception |
| `test_source_bytes_and_entity_expansion_are_bounded` | Same publication anchor exception |

| Test in `test_supervised_eod_cli.py` | Observed failure |
| --- | --- |
| `test_checked_in_configuration_pins_only_isolated_pilot_paths` | `ValueError: Qualified pilot evidence checksum mismatch` |
| `test_default_is_public_source_dry_run_without_bootstrap` | `assert cli.main([]) == 0` receives 1; CLI reports `BLOCKED / supervised_eod_preflight_failed / ValueError` when the seed loader rejects the anchor |

Raw baseline logs, JUnit XML, hash analysis and exact failure messages remain
in ignored `data/integration_readiness/`. The historical Explore report is
preserved: its observation that current files match the starting Git commit is
correct; this investigation traces the mismatch further back to normalization
when the qualified source bytes entered Git.

## Data contract review

| Contract | Independently checked behavior | Acceptance boundary |
| --- | --- | --- |
| VN-Index freshness and units | `test_live_market.py`, provider index tests and `market-index.test.mjs` preserve direct index levels and point/percent movement without price scaling. UI rejects stale/failed, prior Vietnam dates, invalid/future times and expired active snapshots. Missing current aggregate volume/value stay null; no previous-session totals are borrowed. Browser exercises up/down/zero/stale/unavailable/error/retry. | Controlled clocks and synthetic transport; current live SSI levels, timestamps and aggregates were not acquired. |
| VN30/VN100 membership provenance | SSI `indexList` + `securitiesByBoard(index)` validates ordinary Stock instrument, board and identity. Persisted source `SSI:FastConnect`, successful refresh time and status remain visible. Failed refresh retains dated memberships; absent memberships do not imply inclusion. `test_market_universe.py` covers composition, retention and inactive exclusion. | Provider-reported cache provenance, not independently audited live constituent lists. |
| Explore pagination | Public `/stocks/universe` composes query/exchange/group/symbols with bounded offset/limit. Ten-row page requests, later pages, exact/prefix ticker precedence, missing group, empty/error and obsolete response behavior pass backend and browser tests. | No HTTP metadata acquisition or full-universe load on Explore. |
| Search history | Existing browser storage identity persists at most eight recent tickers; typed search is limited to six. Reload, individual/all clearing, unavailable identity removal, empty history, keyboard navigation and retry pass. | Browser-local history; no account synchronization. |
| Hot Topics | Promotion-only Story-ID dedup retains first representative/order/counts; publisher breadth, same-Story thumbnails, broken-image withholding and category archive availability pass. Re-ingestion does not create publisher mentions. | Publisher attention, not corroborated truth or Materiality. No live publisher coverage claim. |
| Community Pulse | Explicit Today/Last 24 hours, bounded extractive evidence, original source links, sample/source/time details, stale/error/empty and unknown counts pass. News/Community acquisition and persistence code match Technical base. | Bounded persisted sample, partial coverage, no sentiment/FOMO/momentum inference. Canonical worker live freshness untested. |
| Technical Stock Detail API | Full latest/daily/operational/persistence regressions retain SELECT-only accepted-session lookup, newer-pending behavior, no fallback after retraction, null unknown session, PROVISIONAL versus VERIFIED, no-store, sanitized failures and query rejection. Synthetic in-memory FastAPI evidence traverses the actual Next proxy into desktop/mobile Stock Detail. | Synthetic accepted evidence only; no existing accepted SSI database copied or used. No live pilot acceptance claim. |

## Validation and preservation

| Check | Result |
| --- | --- |
| Full Technical backend baseline | 880 passed, 17 failed |
| Full Explore backend before repair | 882 passed, the same 17 failed |
| Full integrated backend after repair | 899 passed, zero failures/skips, one existing deprecation warning |
| Technical frontend baseline | 73 passed |
| Full integrated frontend | 79 passed, zero failures/skips |
| Frontend typecheck | PASS |
| Optimized production build | PASS, Next.js 16.3.8 |
| Fresh staged-tree checkout | 21 affected tests pass; original evidence pins retained |
| Technical identity guard | PASS, 9 files |
| Protected source identity against df5a456 | PASS, 62 Git blobs including analytics/materiality, providers, models, provisional/persistence/supervision, News/Community, canonical ingestion, Technical UI/proxy and both lockfiles |
| Browser smoke | PASS at 1440x1000 and 390x844, zero page errors |
| Git whitespace/identity | Configured author identity present; working/staged diff checks pass |

Explore browser coverage includes server pagination, exchange/index filters,
search/history/keyboard, Home/Stock Detail/News/index navigation, Hot Topics,
Community, loading/empty/errors, EN/VI, dark/light and no horizontal overflow.
Technical checks additionally cover accepted insights/evidence, actual proxy
headers/query rejection/unknown session, no-change, cap-three, loading, obsolete
response, retraction, corrected/stale output, missing calendar, failure and retry.
Screenshots were visually inspected. The first new Technical smoke attempt had
an overly exact selector for a metric inside JSON `<pre>` text; the test selector
was corrected, the initial log retained, and the complete rerun passed. Product
code was unchanged.

Browser evidence is saved in `data/explore_home_v2/` and
`data/integration_readiness/`. The extra Technical harness creates only an
in-memory synthetic database and blocks acquisition/scoring after setup. Its
temporary local proxy configuration and both servers are removed/stopped after
validation. Generated output is ignored; no runtime data enters the commit.

Core commands were `uv sync --frozen`, `uv run pytest -q`, `npm ci --no-audit
--no-fund`, `npm test`, `npm run typecheck`, `npm run build`, and
`uv run python scripts/check_technical_identity.py`. Explore smoke uses
`node tests/explore-home.browser.mjs <playwright-module-path> <production-url>`.

## Remaining limitations and push readiness

No integration conflict or policy blocker remains. This validates local code,
packaging, deterministic contracts and rendering; connected SSI acquisition,
current VN-Index observations, live membership coverage and live News/Community
worker freshness still require operational acceptance in an authorized runtime.
The existing supervised pilot remains single-ticker and delayed by the unchanged
six-hour matching-read and 24-hour post-publication gates. Wider coverage,
always-on hosting, source schema changes and capacity/retention decisions remain
separate rollout work. The Starlette/httpx TestClient deprecation warning remains.

The local checkpoint may be reviewed for a future push. No remote ref was
changed, no push/deployment was attempted, and this report does not authorize a
live rollout or describe synthetic results as verified market evidence.
