# Woofi Explore / Home V2

Date: 2026-10-10 (Asia/Ho_Chi_Minh)

## Checkpoint report

| Field | Result |
| --- | --- |
| STATUS | Complete for the Explore/Home scope; all relevant checks pass. Broader baseline failures are recorded below. |
| WORKTREE | `C:\Users\PC\.codex\worktrees\woofi-explore-refresh\vn30-intelligence-agent` |
| BRANCH | `codex/woofi-explore-refresh` |
| STARTING COMMIT | `df5a4569fac70dd9df5cc155aaf6027316d27c4f` |
| COMMIT | This report is included in the Explore/Home checkpoint on the current branch. |
| HOME | Prominent VN-Index, observed movement, source time/session, honest freshness, existing mascot, section navigation. |
| EXPLORE | Ten-row server pages; company/ticker, HOSE/HNX/UPCOM and cached SSI membership filters compose. |
| SEARCH | Six typed matches or eight saved recent identities, empty query valid, browser persistence, individual/full clearing and keyboard navigation. |
| HOT TOPICS | Compact, Story identity deduplication; original representative, publishers, same-Story images and News category availability retained. |
| COMMUNITY PULSE | Home displays existing persisted Today/Last 24 hours evidence, at most three themes, sample/source/time information, original discussions and full News navigation. |
| UI VALIDATION | Existing tokens, wordmark and mascot; English/Vietnamese, dark/light, desktop/mobile; no horizontal page overflow. |
| BACKEND TESTS | 243 relevant tests pass. Broader run: 882 pass, 17 pre-existing Technical fixture failures. |
| FRONTEND TESTS | All 79 Node/component tests pass. |
| TYPECHECK | `npm run typecheck` passes. |
| BUILD | `npm run build` passes. |
| BROWSER CHECKS | Production Next server; headless Chrome at 1440×1000 and 390×844. All checks pass; zero page errors. API transport fixtures are explicitly synthetic, not live market acceptance. |
| REMAINING LIMITATIONS | Worker-dependent freshness, source images and membership coverage; broader Technical fixture integrity issue; connected live acquisition was not exercised in this checkout. |
| NEXT RECOMMENDED MILESTONE | Acceptance with connected SSI metadata/index and the canonical News/Community worker; resolve the separately reproduced Technical fixture issue in its own task. |

No push or deployment. No changes to credentials, Technical EOD/D1/D4/D5 policies,
Stock Detail's Technical Insights, or another worktree.

## Phase 0: audit and preservation

The initial checkout was clean on the expected branch and full starting SHA.
The repository is nested under the supplied `woofi-explore-refresh` working directory.
Git registers `woofi-technical-stock-detail/vn30-intelligence-agent` as a separate
checkout on `codex/woofi-technical-stock-detail`, with shared Git object storage.

Existing behavior was inspected before editing:

- `/` already combined `ExploreMarket` and `TickerPicker`.
- The SSI live-index API already supplied observed levels, point/percent movement,
  trading date, source update time and session/status. Missing aggregate volume/value
  already remained null. Historical daily research had its own route.
- Explore already rendered ten rows, but the global `StockUniverse` downloaded every
  metadata page and filtered/paginated in the browser.
- SSI `indexList` / `securitiesByBoard(index)` membership acquisition already ran in
  the canonical worker, with a separate daily persisted cache and failure retention.
- Search already persisted up to eight recent selections, supported keyboard selection
  and clearing, and bounded suggestions. It depended on the downloaded universe.
- Hot Topics already required independent publisher breadth and usable source images,
  selected the earliest representative and retained category archive Stories.
- Community's existing F319/24HMoney/Chứng Sỹ ingestion, Today/Last 24 hours read APIs,
  source status and shared evidence renderer already worked in News/Stock Detail.
  Home did not show Community Pulse.
- Technical Insights, chart, Stock Detail routes, News archives, browser Watchlist
  membership/review semantics, localization and Woofi's supplied assets were retained.

## Implementation and requirement evidence

| Requirement | Current implementation / evidence |
| --- | --- |
| Actual index and both movements; positive/negative/zero/missing | Existing `useLiveIndex`, `indexMovement`, `signedIndex` and `ExploreMarket`; backend live-market regression, formatting tests and browser up/down/zero/unavailable cases. |
| Evaluated date/session, freshness; stale never labelled current | Trading date and source timestamp remain visible in Vietnam time. `indexDisplayStatus` honors unavailable/stale/failure, checks source date, invalid/future time, and ages active/unconfirmed snapshots. A 30-second UI clock ages a page left open; tests cover midnight and expiry. Stale data uses uncertain mascot and does not assert an active session. |
| Useful index loading/unavailable and supportive mascot | Existing scanning/uncertain/directional assets, loading status and retry; browser missing/read-error/retry cases and component loading test. |
| Approximately ten stocks; avoid full universe on Explore | `useEquityPage` makes a single `limit=10&offset=...` request. Home/News/Stock Detail no longer activate full-universe loading; Watchlist preserves its existing context. Browser request inspection confirms discovery limits ≤10. |
| Exchange and trustworthy index filters | `/stocks/universe` composes `q`, `exchange`, `index_group`, `symbols`, `limit` and `offset` on cached data. Missing group membership yields no evidence of inclusion and disabled UI options; inactive securities are excluded. SSI source/as-of/status survive cached refresh failure. Backend tests check composition, bounds, stale retained cache and missing membership. |
| Dynamic ticker/company navigation, efficient mobile | Exact/prefix ticker search precedes broad company matches, using the existing Vietnamese normalization. Both lists and searches link to encoded Stock Detail routes. Mobile rows keep ticker/exchange and price together with company text below; section links let users jump straight to browsing. |
| Loading/empty/failure, unknown versus zero | Abortable, debounced metadata reads clear obsolete results when query/page changes. Loading skeleton, filtered empty state, retry and stale cache messages are explicit. An unacquired empty cache does not display zero universe/result counts. Component and browser tests cover each state and obsolete responses. |
| Empty search and durable history; no unrelated default suggestions | Only saved symbols are looked up for an empty query; an empty history requests nothing. Typed search requests six matches after 200 ms. Browser reload retains history and tests individual removal, full clearing, unavailable identity removal, Arrow keys/Enter/Escape and search retry. The existing browser storage key/format is preserved. |
| Compact Hot Topics without archive loss | `uniqueHotTopics` deduplicates only the promotion response by Story ID, preserving first representative/order and source counts. Compact `TopStory`/`NewsThumbnail` variants are opt-in. Existing category News remains unchanged; browser checks the same three Stories in Company/Industry/Market. |
| Publisher attribution, trustworthy thumbnails, direct story links | Original publisher/date/count evidence and original article links remain. Existing `storyImages` uses images belonging to the same Story; unsafe/missing images are withheld. Broken image browser test hides affected items; a source-image note explains the visible rule. No generated imagery, importance/popularity score or replacement story is introduced. |
| Community remains present with real sample evidence | Home opts into the existing `CommunityPulse` and shared `CommunityDiscussions` compact view. It shows up to three existing extractive themes and six active ticker entries, not a new score/ingestion pipeline. Activity counts are explicitly distinguished from sentiment. Representative original URLs, complete bounded theme evidence, source coverage/status/attempt/success time and sample evaluation time remain inspectable. |
| Community stale/error/empty; no fabricated FOMO/sentiment | Source warning and coverage disclosure, exact Today/Last 24 hours choice, unknown counts on read failure and an empty-window explanation without silent fallback. Browser and backend Community tests exercise windows, source status, empty/read error/retry. |
| UI identity, responsive behavior, no extra framework | Existing Next/React/Tailwind tokens, supplied logo/mascots, calm market color, visible focus and responsive shell. No added packages or decorative charts. Screenshots were visually reviewed; desktop/mobile EN/VI dark/light checks pass. |
| Protect Technical Stock Detail and related flows | Existing Technical component tests and backend latest/daily/Bollinger tests pass; browser navigation reaches the Technical diagnostic section. Technical algorithms, operational endpoints, chart and pilot evidence remain untouched. Watchlist retains local membership/review behavior and full metadata context. |

## Reproducible validation

From `frontend`:

```powershell
npm ci --no-audit --no-fund
npm run typecheck
npm test
npm run build
npm run start -- --port 3012
# In a second shell; use an installed or bundled Playwright module path:
node tests/explore-home.browser.mjs <playwright-module-path> http://127.0.0.1:3012
```

From the repository root:

```powershell
uv sync --frozen
uv run pytest tests/test_market_universe.py tests/test_stocks_api.py tests/test_display_metadata.py tests/test_live_market.py tests/test_research_feed.py tests/test_news.py tests/test_news_refinement.py tests/test_news_pagination.py tests/test_news_adaptive.py tests/test_news_discovery.py tests/test_community.py tests/test_community_daily.py tests/test_watchlist_monitoring.py tests/test_technical_daily_api.py tests/test_technical_operational_latest.py tests/test_bollinger.py -q
```

The browser runner intercepts acquisition/market/news/community APIs using labelled
synthetic fixtures. It never acquires SSI data, runs the ingestion worker or alters
stored evidence. The actual backend discovery/API semantics are independently tested
through FastAPI and a disposable SQL database. Runtime/browser evidence is saved in
ignored `data/explore_home_v2/browser-report.json` and four desktop/mobile EN-dark and
VI-light screenshots. These synthetic screenshots are QA evidence, not market reports.

`git diff --check` passes. The final diff was reviewed against the supplied mission,
AGENTS.md, CONTEXT.md and frontend/DESIGN.md.

## Data and validation limitations

1. SSI universe/index membership refresh continues to belong to the canonical worker.
   HTTP reads do not acquire or invent membership. Stale retained groups remain visibly
   labelled cached/incomplete; missing groups are unavailable.
2. SSI index aggregate volume/value may be absent. They remain unavailable; previous
   session totals are never borrowed. Current presentation does not enter completed
   daily analytics or Technical policies.
3. News coverage and clustering remain approximate. Hot Topics represents publisher
   attention, not corroborated truth or a numerical importance score. Source images
   may be unavailable or fail; the existing image-only visibility preference is retained.
4. Community is a bounded persisted sample, with source isolation and partial coverage.
   Original discussions and counts do not measure sentiment, FOMO or momentum. Stopped
   workers can leave stale/empty windows; switching to Last 24 hours is explicit.
5. Recent searches remain in this browser with a maximum of eight. Storage failures
   still permit in-memory operation. No account synchronization is introduced.
6. This checkout has no configured connected SSI runtime/database for live-data acceptance.
   Browser validation proves rendering/interactions and contract handling using fixtures;
   it does not certify today's market observations or upstream acquisition freshness.

## Pre-existing broader backend failures

`uv run pytest -q`: **882 passed, 17 failed**. All failures are in
`test_hose_eod_discovery.py` (15) and `test_supervised_eod_cli.py` (2), caused by
pinned Technical evidence checksums that already disagree with their starting-commit
files. An archive of the exact starting commit was extracted inside this worktree's
ignored QA directory and the two unchanged suites rerun: **4 passed, the same 17 failed**.
The current files are byte-identical to that commit, so this is not a Windows checkout
line-ending change or an Explore/Home regression.

| Evidence | Pinned SHA-256 | Starting commit and current SHA-256 |
| --- | --- | --- |
| `TECHNICAL_V1_HOSE_PUBLICATION_2026-10-08.json` | `416f1fbc0e4cb0f95c2db1174858997b0bfe485480b706fca45d235f4413ad8e` | `b39ad06819a33cd3534c1fd4ca330a986f89407807dbb990b2b425fc2650707f` |
| `TECHNICAL_V1_FPT_SECURITY_RECEIPT_2026-10-09.json` | `6446ad20e1ab1ff692ae8b3a7799f213d5a46c85fb33bfc3ddf1cd87ccc4f20d` | `3ecc1c7eafbe4b8e0c7b49d42ed75441d2b1f1d32463f8a68d9b77adbbaaa5ae` |

The calendar seed matches its pinned digest. No evidence was edited, and no integrity
check was weakened. Requalification/repair of those protected fixtures is separate
from this Explore/Home checkpoint.
