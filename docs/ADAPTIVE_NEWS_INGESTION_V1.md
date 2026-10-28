# Adaptive News ingestion V1

Base: `10f390de3f4db764be406b78b589afa019a8521c` (main).

## Verified baseline and scope

The working tree already contained the preceding News thumbnail/archive slice plus
unrelated Dividend, Technical/research and UI changes. The News prerequisites are
included with this checkpoint; unrelated changes remain unstaged. Initially all
20 VN RSS sources had fixed 20-minute cadence, the canonical watch loop woke every
60 seconds, acquisition was sequential, and a process-local web thread could run
News. GETs read the database but assembled/tagged all active research rows on each
read. The page API accepted up to 100 despite the frontend requesting 12. Hot Topics
accepted two Articles even from one publisher, contrary to this task's independent
publisher definition. This task restores the independent-group condition and a
server-side 12-Story page cap.

## Scheduling and priorities

`src/news/schedule.json` controls 30-minute priority, 120-minute standard,
240-minute off-hours and 360-minute weekend cadences, two simultaneous fetches,
six sources per iteration, 20-second socket inactivity timeout, 30-minute initial
failure backoff and five-minute refresh-request minimum. Weekday Vietnam sessions
09:00–11:30 and 13:00–15:00 are explicitly a heuristic. No authoritative holiday
calendar exists in the current News implementation; lunch is off-hours.

Priority is configurable per `sources.json` entry: CafeF, VnEconomy, Vietstock,
VietnamBiz, Đầu Tư Chứng Khoán and Thời Báo Tài Chính. All six have verified active
public finance/stock feeds, successful local acquisitions and same-Vietnam-day
publications. Before this change, their stored Article counts were respectively
158/85/59/44/48/34; latest publications ranged from 13:03 to 16:38 Vietnam time.
Selection reflects their finance/stock specialization and observed acquisitions,
not a claim of comprehensive coverage or permanent reliability. All other 14 feeds
are preserved as standard. Alternate legacy registries without scheduling_priority
retain their explicit fixed poll_interval_minutes for compatibility.

Healthy due time is derived from last attempt and the current session cadence,
so a long off-hours timer cannot delay opening. next_due_at stores the last
calculated deadline; the source API exposes the current effective deadline.
Failure deadlines are preserved across session changes. One attempt per claim,
no immediate transport retries; exponential retry delays 30/60/120… minutes cap
at 24 hours. Failed requests preserve last success and all evidence. Errors store
class names only; no provider response bodies or secrets.

## Cache and worker coordination

News GETs and illustrated Quick News never fetch upstream. News/Hot Topics and
`/top?require_image=true` read persisted `NewsReadCache` research rows. Due access
records intent in the existing NewsSourceState; GET completion does not depend
on external fetch completion. POST /news/refresh returns requested/deduplicated
counts and explicitly says pending_worker. /sources exposes pending timestamps,
cadence, counters, duration, inserted count and worker requirement.

The existing web-open refresh records durable News intent and excludes News from
its convenience thread for other domains. The canonical worker must run:

```powershell
uv run python -m scripts.ingest_data --watch
```

Worker stopped: persisted rows remain readable; intent waits durably. No API
claims that News refresh completed. No OS supervisor or new infrastructure is
added. Worker restart restores cadence and pending intent. --force-news remains
a one-off override and cannot combine with --watch; it still respects bounds.

Database source leases and two shared fetch slots commit atomically, bounding
acquisition across processes as well as threads. Tokens fence evidence writes;
expired owners discard results. Ten-minute expiry allows recovery after a crash.
Duplicate visitors cannot acquire a source; repeat pending requests are suppressed
with a conditional database update. The process-local convenience mutex is not
News's coordination mechanism. Configure/migrate schema before starting multiple
production workers; simultaneous first-time DDL is not a deployment coordinator.

## Stories, Hot Topics and UI

Existing matching, identities, raw Articles and publisher-group provenance remain.
Incremental writes mark changed Stories dirty. Projection updates occur in the
worker and are serialized in the database. Dirty flags survive a crash between
evidence and projection commits. Only touched Stories are rebuilt, except initial
bootstrap or a changed successful SSI universe snapshot, which reclassifies the
projection. Empty cycles do not rebuild. Duplicate observations only update image
retry revision timestamps in cached payloads; they do not renew Story activity or
rebuild Hot ranking. Failing source transactions do not publish those revisions.

Hot eligibility requires two independent publisher groups within the active 72-hour
window and an actual same-Story thumbnail. At read time lightweight filtering
handles exact expiry, publisher counts, earliest representative and recency ordering.
No matching, taxonomy rebuild or upstream fetch runs in HTTP. The read cache retains
96 hours for ordinary snapshots crossing expiry and caps at 10,000 Stories. This
is a bounded product cache, not an arbitrary historical replay API. Original
Articles/Stories are never deleted. Raw latest, unillustrated top and detail remain
inspectable database evidence reads; they have different performance from visual
cache routes. Minute UI polling is retained because cached reads are inexpensive.

EN/VI, thumbnails, missing/broken-image hiding, source evidence, taxonomy, actual
Load More and snapshot paging remain. Hot explanatory chrome now names independent
publishers. No redesigned screens, recommendations or Materiality changes.

## Measurements

**Deterministic simulation**, not production: a cold-start Thursday 2026-10-08,
minute scheduler checks, successful instantaneous acquisitions, no holidays or
failures, six sources per cycle. Fixed 20-minute cadence: 1,440 source attempts/day.
Adaptive: 182 (14 for each priority source, seven for each standard source), an
87.36% reduction. Failure/backoff and real fetch durations were not simulated.

**Real local HTTP**, 12 requests/route against persisted local data on 127.0.0.1:8000:

| Route | Median ms | Maximum ms |
|---|---:|---:|
| News Industry page, limit 12 | 39.97 | 163.26 |
| Hot Topics, limit 4 | 43.81 | 64.22 |
| Illustrated Quick News, limit 6 | 56.92 | 208.19 |

The raw top evidence route measured 1,488.17 ms median before moving illustrated
Quick News to the cache; raw evidence endpoints are intentionally not claimed to
share visual-cache latency. Figures reflect this machine/dataset, not production.
A focused API test also returns stale persisted News while a provider is blocked
on an unreleased event, demonstrating HTTP independence from fetch completion.

**Real public RSS**: four explicit bounded batches (6/6/6/2) succeeded for all
20 sources, receiving 1,399 items and inserting 21 new Articles. This was a manual
qualification override; it does not represent normal adaptive crawl frequency.

## Tests and review

Focused tests cover session/priority/standard/weekend cadence, fresh skip, durable
stale intent, simultaneous visitors, separate worker sessions, global concurrency,
lease expiry, backoff/recovery, transport timeout/no immediate retry, restart,
empty cycles, dirty-projection crash recovery, duplicate image retry revisions,
cache-only HTTP, page cap and snapshot expiry. Existing tests preserve 72-hour
publication age, source isolation, earliest representative, hidden thumbnails,
independent publisher counts, raw evidence and frontend localization.

Full working-tree regression includes pre-existing uncommitted work; a separate
staged-tree check verifies the commit does not depend on that work.

| Check | Result |
|---|---|
| `uv run --no-sync pytest -q --tb=short` (working tree) | 692 passed |
| News/worker focused suite | 69 passed |
| `python -m pytest -q --tb=short` (staged export with original Git ancestry) | 567 passed |
| `npm test` (working tree / staged export) | 67 / 63 passed |
| `npx tsc --noEmit` (working tree) | passed |
| `npm run build` (working tree, Turbopack) | passed |
| `npm run build -- --webpack` (staged export) | passed |
| `git diff --cached --check` | passed |

The staged frontend uses a junction to existing node_modules; Turbopack cannot
follow that dependency junction outside its root, so only the isolated export
uses webpack. The original workspace's normal Turbopack build passes. The staged
export was given the original commit ancestry for existing governance tests;
no frozen authority, original Git ref, test assertion or repository file was
changed to bypass those checks. One existing Starlette deprecation warning remains.

Review covered scheduling, shared claims, fenced recovery, stale HTTP behavior,
evidence/Hot semantics, cache expiry, scope and staged dependency completeness.

## Operational limitations

The worker must remain running for continuous freshness; no automatic restart
supervisor is supplied. Weekdays are not a holiday calendar. Socket timeout is
inactivity-based, not an absolute wall-clock budget for a server sending a trickle
of bytes; feed size is bounded. SQLite serializes writes, so very large evidence
transactions may briefly contend with intent writes. PostgreSQL leases use portable
conditional updates, but this checkpoint's concurrency execution tests use SQLite.
The bounded cache is for current research and ordinary Show more sessions, not
arbitrary historical snapshots. Missing images and classification gaps still hide
visual rows without removing evidence. No claim of complete News coverage.


## Exact checkpoint files

- `CONTEXT.md`
- `docs/ADAPTIVE_NEWS_INGESTION_V1.md`
- `docs/NEWS_REFRESH_V2.md`
- `frontend/app/api/ingestion/refresh/route.ts`
- `frontend/app/components/ExploreMarket.tsx`
- `frontend/app/components/app-shell/AppShell.tsx`
- `frontend/app/components/news/ArticleRow.tsx`
- `frontend/app/components/news/NewsThumbnail.tsx`
- `frontend/app/components/news/TopStory.tsx`
- `frontend/app/components/stock/NewsFeed.tsx`
- `frontend/app/components/stock/StockNews.tsx`
- `frontend/app/news/page.tsx`
- `frontend/app/watchlist/page.tsx`
- `frontend/lib/news.ts`
- `frontend/lib/translations.ts`
- `frontend/lib/useNewsArchive.ts`
- `frontend/tests/localization.test.mjs`
- `frontend/tests/research-presentation.test.mjs`
- `main.py`
- `routers/ingestion.py`
- `routers/news.py`
- `scripts/ingest_data.py`
- `src/db/session.py`
- `src/news/adapters.py`
- `src/news/models.py`
- `src/news/read.py`
- `src/news/read_cache.py`
- `src/news/registry.py`
- `src/news/schedule.json`
- `src/news/scheduling.py`
- `src/news/service.py`
- `src/news/sources.json`
- `src/services/ingestion.py`
- `tests/test_data_reliability.py`
- `tests/test_ingestion.py`
- `tests/test_news.py`
- `tests/test_news_adaptive.py`
- `tests/test_news_correction.py`
- `tests/test_news_pagination.py`
- `tests/test_news_refinement.py`
- `tests/test_research_feed.py`


## Checkpoint result

STATUS: PASS. Commit message: `perf: add adaptive low-resource news ingestion`.
No push. Follow-up: run the canonical --watch worker during normal usage and
inspect source cadence/status across the next Vietnam session. Unrelated local
Dividend/Technical/UI work remains uncommitted and preserved. `.env` is unchanged.
