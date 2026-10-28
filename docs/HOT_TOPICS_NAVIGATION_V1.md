# Hot Topics and primary navigation V1

Date: 2026-10-19. Implementation base and verified deployed application:
`e80e36f24e38ac65a109245afbedd6204470ac30`.
Development branch: `codex/woofi-market-board-correction`.

## Implementation

- Public header reuses the existing Next Link, locale/theme controls, original
  logo and ticker search. Three primary destinations remain labelled: Market /
  News / Watchlist; VI: Thị trường / Tin tức / Theo dõi. Desktop is inline;
  ≤900px moves the same navigation to a second full-width header row. Active
  routes include Stock/Index Research and News descendants, with `aria-current`,
  underline and theme tokens. The duplicate primary drawer/sidebar is removed;
  About remains in the footer. News/Watchlist content and routes are unchanged.
- Overview has one compact Hot Topics / Market Focus area immediately after the
  sample summary and before mover tables. Default is Hot Topics. Existing Board
  and Heatmap keep their complete comparison canvas, controls and data logic.
- Hot Topics was extracted from ExploreMarket, which now reuses it. Exact read:
  `GET /api/news/hot?limit=4`. Story-ID dedup preserves server order and original
  representatives. Desktop initially shows up to three, mobile ≤800px up to two;
  explicit expansion exposes the remaining loaded results without another fetch.
- Text-only TopStory reuses safe publisher links, source and original publication
  time/explicit First seen, and separately qualified ticker links. No thumbnail
  requirement, synthesized headline, movement quote consumer or financial value.
  Other TopStory callers keep the original default presentation.
- Hot Topics keeps its backend 72-hour/two-independent-publisher contract;
  Market Focus keeps its exact two feed URLs, issuer qualification, 24-hour compact
  filter and three-story limit. They are separate datasets, never combined or
  reranked. Native labelled buttons with pressed state control named content;
  hidden content cannot participate in layout/tab focus.
- Switching options aborts inactive reads/removes their existing `cacheRefresh`
  listener; each component retains its own data/expansion state. Initial loading,
  genuine empty, initial error/retry and failed refresh with previous headlines
  are distinct. Loading/error in equity metadata does not suppress publisher
  context; its React position remains stable as metadata resolves. One existing
  LivePrices provider is retained; empty symbol demand does not issue quote reads.

No backend/ranking, acquisition cadence, SSI adapter, schema, source qualification,
Watchlist review identity/window/storage key or internal SSI access gate changes.
The read API still has its existing scheduled refresh-intent semantics; this
implementation adds no acquisition worker, provider request or polling mechanism.

## Validation

Commands ran only against development source / synthetic in-memory test data:

| Check | Actual result |
|---|---|
| New focused `node --test tests/hot-topics-navigation.test.mjs` | 16 passed |
| Full frontend `npm test` | 276 total: **275 passed, 1 skipped, 0 failed** |
| `npm run typecheck` | PASS |
| `npm run build` | PASS; optimized production build/static generation |
| Existing backend `test_research_feed.py`, `test_news_relevance_v2.py` | **16 passed**, one dependency deprecation warning |
| `git diff --check` | PASS |
| Cloud Browser rendering/interaction acceptance | **UNAVAILABLE** — no Cloud Browser capability exposed |

The skipped frontend case is the existing optional real persisted-API Stock Detail
replay; it requires an external configured replay and was not enabled. No browser
tests or desktop browser launches were attempted. There are no new screenshots.

The new tests exercise real component SSR and controlled hook/callback execution:
original ordering/dedup, long source titles, safe links/ticker provenance, missing
images/time, loading/error/empty/retained evidence, EN/VI, active navigation,
option switching and inactive cleanup, coalesced cache refresh, separate Focus
feed/window qualification, metadata-independent mounting, Board/Heatmap regression,
responsive CSS caps/visibility and theme/focus tokens. CSS/SSR checks do **not**
establish actual browser layout, touch behavior or light/dark visual acceptance.

Two existing Explore hero/mascot tests had their mocked child import updated from
TopStory to the extracted HotTopics. Their assertions were preserved. A duplicate
translation key was removed in favor of the existing `Show fewer headlines` key.

Backend tests used the existing development Python environment, `APP_ENV=test`,
`DATABASE_URL=sqlite://`, and in-memory fixture sessions/provider callbacks. No
live feed/SSI request or production database was used. The warning is the existing
Starlette TestClient/httpx deprecation, unrelated to this change.

Full test/build logs are in the task-owned evidence directory:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/hot-topics-navigation-implementation-20261019/`.

## Release boundary and remaining work

Production verification was read-only: canonical runtime configuration and release
checkout both pin e80e36f; the production Frontend command points to that checkout
on port 3000. The development branch began clean at that same SHA. Runtime files,
installed P1 Supervisor, Collector, ingestion locks, SQLite and application pin
were not modified. Technical Pilot/FPT settings were not changed. No push, merge,
server start/stop or deployment occurred.

Before a separately authorized release, use Cloud Browser when available to check
1440px/1024px/768px/390px/320px, VI/EN and both themes: first-screen hierarchy, all
three primary labels, 3/2 headline caps/expansion, long title/source wrapping,
keyboard focus, errors/retry, option switching, News/Watchlist navigation and
unchanged review persistence. Then run the existing controlled release gates.
Production still serves e80e36f until an explicitly authorized deployment.
