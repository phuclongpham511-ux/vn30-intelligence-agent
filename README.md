# VN30 Intelligence Agent

Help active retail investors know which changes deserve attention across Vietnamese equities.
The eventual product will rank material changes and show only the top 1–3 insights with inspectable evidence.

## Status: News refinement + Community Pulse V1; browser-local Watchlist monitoring

News Top Stories shows one registry-selected representative per Story, with other
reporting behind a disclosure. Independent publisher counts and ranking are unchanged.
Filters select Stories and matching representatives; disclosures retain the other
publishers' reporting for the selected Story.
Optional thumbnails use explicit RSS/Atom media metadata only; absent or failed
images render no placeholder. Sector tags remain available under Advanced filters
with a partial-coverage label; the current company universe lacks sector metadata.

Community Pulse is a separate News workspace view and separate database evidence
layer. It samples one public F319 listing at `https://newf319.com/`, at most 50
listing entries, every 30 minutes. Robots restrictions are checked before each
acquisition; failed checks stop acquisition. Only public thread metadata is stored.
Ticker relevance requires registered company identity or explicit ticker context,
not bare uppercase tokens. Counts measure distinct observed threads, and activity
ordering uses lifetime replies then public last-activity time; it is not a growth
rate, sentiment or Materiality score. Six discussions appear by default.

The read-only `/community/pulse` and `/community/sources` endpoints never crawl
during a page request. Browser Refresh only reads persisted data and source status.
Run `create_tables()` during explicit production schema deployment for the additive
Community tables and nullable News thumbnail fields. Local development does this
at startup. News and Community ingestion failures remain independent.

## Data Update Reliability V1 — canonical collection worker

Run one worker alongside the FastAPI/web processes, against the same DATABASE_URL:

```powershell
uv run python -m scripts.ingest_data
uv run python -m scripts.ingest_data --watch
```

One-off mode evaluates both domains and exits nonzero if either reports a failure.
Watch mode reevaluates every 60 seconds; existing persisted News source intervals
and Community's 30-minute interval determine due work. Each domain uses its own
session; source/domain failures are reported by exception type only and do not
terminate the watch loop. Ctrl+C/SIGTERM stops cleanly; in-flight bounded acquisition
may finish first. Restart does not reset timestamps or force fetches. Skipped work
does not change last-success state. Run only one collector: do not also run the
legacy domain-specific `--watch` commands. These remain available for targeted
diagnostics; News `--smoke` does not persist data. `--force-news` is an explicit
one-off News override, forbidden with `--watch`; it does not bypass Community cadence.

This worker does not start inside FastAPI. Automatic launch/process restart is
the responsibility of a future external deployment supervisor, not implemented here.
The worker is sequential and the 60-second wait follows completion of each cycle.

Successful Community acquisitions append one CommunityThreadObservation per sampled
thread (thread ID, actual observation time, nullable lifetime replies/views), alongside
the latest thread state in one transaction. History starts with this feature; no
backfill, retention job, velocity or momentum score exists. Failed/skipped cycles
create no observations. Freshness APIs expose healthy (successful within twice the
source interval), stale, latest-attempt error, never attempted and News disabled
states. The UI displays last successful fetch, not a claim of complete market coverage.

Source verification on 2026-10-05: F319 public listing parsed 20 threads, with stable
URLs, dates and reply/view counts; `f319.com` itself did not resolve here. Chứng Sỹ
returned a public shell without thread metadata and disallows `/api/` in robots;
FireAnt returned a public shell without usable discussion metadata. Both are
deferred; no authenticated or internal API was used. Community coverage is a
bounded sample, and ticker matches depend on the registered company universe.

The canonical [project checkpoint in CONTEXT.md](CONTEXT.md#current-architecture-stage)
records completed capabilities, blockers and the next direction (2026-10-05).
Foundation/data analytics, financial visualization, News V1, connected stock/news
discovery, market briefing usability/readiness and Mascot UI V1 are complete.
News uses 10 Vietnamese and 5 global sources without full article persistence or
an LLM dependency.

Technical Materiality is **PAUSED**, not abandoned, pending external historical-data
and provenance evidence. SSI product Market Data qualification has passed;
product integration does not certify PIT vintage, historical revisions or the full
adjustment methodology. Existing research/evaluation infrastructure
remains available, but further calibration/deployment must wait for new evidence.

**Watchlist Intelligence V1** now reuses the existing Watchlist page for browser-local
membership, ticker-matched Story developments, source evidence and explicit review
state, answering “What changed for what I follow?” This is deterministic Personalized
Relevance + Monitoring, not Materiality scoring or cross-device personalization.
The AI Product Layer and Unified Materiality /
Personalized Attention Budget are later directions.

## Run locally

Requirements: Python 3.12+, uv, Node.js 24+ and npm (Node 24.16 tested; frontend tests use native TypeScript support). From repository root:

```powershell
uv --system-certs sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The `.env` copy runs only on first setup. It preserves existing SSI credentials when you
restart the backend or repeat these commands. Edit `.env` to add credentials after first
setup; never copy `.env.example` over an existing `.env`. The backend loads `.env` from the
repository root and creates or updates the local schema during development startup. No
OpenAI key is required.

In a second terminal:

```powershell
cd frontend
$env:NODE_OPTIONS='--use-system-ca'
npm ci
npm run dev
```

Open http://127.0.0.1:3000 and select a stock, or enter another ticker to validate and add it.
Backend API docs: http://127.0.0.1:8000/docs.
The browser only calls the Next.js backend proxy. Its optional server-side BACKEND_URL
environment variable defaults to http://127.0.0.1:8000. No browser CORS workaround is required.

## Interface and language

The responsive dashboard uses Tailwind CSS, shadcn/ui, Lucide, Recharts and persistent
dark/light themes and a neutral blue research identity. Lightweight Charts 5.2.1 renders
real candlesticks, MA20/MA50, volume and RSI in synchronized panes. Global search can validate and add new tickers. Stock detail includes
3M/6M/1Y/2Y history, compact market context, annual revenue/profit/growth/profitability
charts, raw technical and financial tables, and connected ingested news. Recharts renders
financial trends; all indicators come from deterministic Python analytics.

Technical and annual-history panels have independent loading/retry/empty states.
Technical indicators initialize inside the selected window: warm-up stays null and
changing the range can slightly change Wilder RSI initialization. The default 6M
series matches the existing snapshot window. TradingView attribution is retained.

The interface is permanently English-only. Only trusted display_name_en metadata is
shown as a company name; otherwise the ticker is displayed. Raw company_name is retained
in the backend but is never a UI fallback. New tickers do not require frontend branches.
Development startup applies the additive display-name migration idempotently.

## Architecture

Exactly one root main.py and one FastAPI app.

```text
Explore UI → Next.js API proxy → FastAPI routers → services
                                                ↓
                existing provider interfaces → SSI market / vnstock fundamentals
                                                ↓
                      normalized schemas → pure analytics → API
```

Stack: Python, FastAPI, SQLModel/SQLAlchemy, Pydantic, psycopg, pandas, numpy, uv;
Next.js, React, TypeScript; pytest and pytest-asyncio; backend Dockerfile.

- MarketDataProvider: SSI FastConnect securities metadata validates symbols and
  supplies company names; daily historical OHLCV uses `ssi-sdk==3.2.1`.
  `MARKET_DATA_PROVIDER=ssi` is the default. Set `SSI_API_KEY` and `SSI_API_SECRET`
  locally; missing credentials fail safely with no silent fallback.
  Explicit `MARKET_DATA_PROVIDER=vnstock` retains the temporary KBS/VCI adapter.
- FundamentalDataProvider: VCI annual income statements, up to four periods in the
  verified community package. vnstock is pinned to 4.0.2 because mappings are version-specific.
  Its original official wheel and transitive vnai wheel remain pinned in uv settings
  because their PyPI version index entries are no longer available.
- News V1: metadata-only ingestion, deterministic Article → Story normalization,
  tagging and deduplication, configurable polling, source telemetry and failure isolation.
- Stock keeps the existing symbol/company_name fields (equivalent to ticker/name).
  updated_at and a case-insensitive unique index were added. The HTTP input accepts ticker or symbol.
- Bounded process-local caches: 5-minute market history, 1-hour fundamentals and listings.
  Cache expiration retries upstream; there is no stale/fake fallback.
- Legacy SDK import is lazy. SDK telemetry and automatic agent-guide installation default off.
  System TLS certificates are used without disabling certificate verification.

## Data contracts and formulas

All price and financial amounts use **VND**, volume uses shares. SSI prices are already
VND (×1), volume is shares (×1), and historical prices are treated as adjusted.
Required raw OHLC/volume fields are validated before SDK model zero coercion.
Only bars dated strictly before today in `Asia/Ho_Chi_Minh` enter analytics:
today is excluded even after close, becoming eligible on the next Vietnam calendar
day. This intentional freshness delay creates no synthetic sessions or forward fill.
VCI SDK OHLC prices (explicit legacy selection only) are in thousands of VND and
are multiplied by 1,000 exactly once in the adapter.
Statement amounts are already VND and are not scaled.

MarketBar: ticker, date, open/high/low/close, volume, source, currency.
MarketSnapshot: ticker, as_of, close, source, currency and the metrics below.
Non-finite/invalid OHLC rows or conflicting duplicate days fail the provider request;
extra rows outside the requested interval are removed. Empty histories yield null metrics.

- daily_return / return_5d / return_20d: close[t] / close[t-n] - 1, trading observations.
- MA20 / MA50: mean of the last 20 / 50 closes.
- RSI14: Wilder smoothing initialized with 14 changes; flat prices = 50,
  no losses = 100. Requires 15 closes.
- avg_volume_20d: last 20 observations, including the latest.
- relative_volume_20d: latest volume / that average; zero denominator = null.
- volatility_20d: sample standard deviation of 20 simple daily returns × sqrt(252).
- drawdown_from_20d_high: latest close / maximum daily high over the last 20 bars - 1.
- Insufficient warm-up returns null, never fabricated indicator values.

Fundamentals use annual periods, for example 2025. Revenue = net sales (isa3);
net_profit = consolidated profit after tax (isa20); gross margin = gross profit (isa5) /
net sales; net margin = net profit / net sales. Bank revenue and gross margin remain null
when those generic statement items are absent; interest income is not substituted for revenue.
ROE is null because the tested upstream ratios are unreliable.
Year-over-year growth compares exact matching prior-year periods; zero/negative prior amounts
yield null. Margin/ROE changes are same-period year-over-year differences.
Ratios/returns are fractions in JSON; UI formats percentages and percentage-point changes.

NewsItem: id, ticker, published_at, title, summary_or_content, source, url and is_fixture.
Fixture URLs are null; sample content is never represented as a real company announcement.

## API

| Method | Route | Behavior |
| --- | --- | --- |
| GET | /health | Process liveness, not DB/provider readiness |
| GET | /stocks | Active persisted stocks |
| POST | /stocks | Validate and add; repeat input returns the existing stock |
| POST | /stocks/validate | Provider-backed validation |
| GET | /stocks/{symbol} | Persisted stock or 404 |
| GET | /stocks/{symbol}/history | Daily OHLCV; optional start/end |
| GET | /stocks/{symbol}/technical-history | OHLCV plus aligned MA20/MA50/RSI14; optional start/end, same 730-day maximum |
| GET | /stocks/{symbol}/fundamentals/history | Annual history, oldest first; limit=4 (1–20), only available periods |
| GET | /stocks/{symbol}/market | Market snapshot |
| GET | /stocks/{symbol}/fundamentals | Annual fundamental snapshot |
| GET | /stocks/{symbol}/news | Labeled fixture feed; limit 1–20 |
| GET | /stocks/{symbol}/overview | Stock, history, market, fundamentals, news |
| GET / POST | /watchlists | Unchanged 501 scaffolds |
| POST / DELETE | /watchlists/{id}/stocks[/symbol] | Unchanged 501 scaffolds |

Example:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/stocks -Method Post -ContentType application/json -Body '{"ticker":" vnm "}'
Invoke-RestMethod http://127.0.0.1:8000/stocks/VNM/overview
Invoke-RestMethod 'http://127.0.0.1:8000/stocks/FPT/history?start=2026-01-01&end=2026-09-23'
```

Unknown/unregistered stock: 404. Malformed input: 422. Upstream failure: sanitized 502.
History defaults to 180 calendar days, with at most 730 days per request.
Overview currently fails as a whole if a required provider call fails; the UI has retry.
No authentication; bind locally for development.

## Persistence and containers

SQLite is the default real on-disk persistence path. For an existing PostgreSQL server,
set DATABASE_URL to postgresql+psycopg://USER:PASSWORD@localhost:5432/vn30. Plain
postgresql:// URLs are normalized to psycopg. Core entities are persisted;
market/fundamental datasets are fetched on demand and not stored in the database.

SQLite migration/save/reopen was verified. PostgreSQL DDL compiles in tests, but no local
PostgreSQL server was available for live verification. Docker Engine was unavailable;
container verification remains a release gate.

```powershell
docker build -t vn30-intelligence-agent .
docker run --rm -p 127.0.0.1:8000:8000 -v vn30-data:/data -e DATABASE_URL=sqlite:////data/vn30.db vn30-intelligence-agent
```

## Verification

```powershell
uv run pytest -q
uv run python -m scripts.smoke_ssi FPT HPG TCB VNM
uv run python -m scripts.preview_materiality FPT
uv run python -m scripts.smoke_vnstock FPT TCB HPG VNM
# Requires a running backend; validates/adds these symbols in the local DB:
uv run python -m scripts.smoke_visualization FPT HPG TCB MWG
cd frontend
npm run build
npm run typecheck
npm test
```

The default 111-test backend suite is offline; SDK calls are mocked.
This includes 33 Materiality tests and 21 historical evaluation tests. The preview uses existing analytics with explicitly
labeled synthetic fixtures, all excluded from materiality scoring. Smoke is explicitly opt-in,
uses the real provider and exits nonzero on failure.
Nine frontend tests cover names, missing values, safe links, chart adapters, indicator nulls, annual ordering and real date-range mapping.
See [Section 1.6 report](docs/SECTION1_6_REPORT.md) for final QA and the seven new screenshots.
See [UI refresh report](docs/UI_REFRESH_REPORT.md) for screenshots and browser QA.
See [Section 1 report](docs/SECTION1_REPORT.md) for observed results and limitations.

## MVP roadmap and boundaries

Watchlist Intelligence V1 ships a browser-local Personalized Relevance + Monitoring
slice; sector/global relevance and account-owned persistence remain deferred.
Technical Materiality remains paused until new external
data/provenance evidence becomes available. See the canonical checkpoint in CONTEXT.md.

Not implemented: production materiality integration, monitoring weighting, cross-device watchlists,
AI/LLM/Agents SDK, portfolio/P&L, thesis, RAG/PDF, email, prediction, BUY/SELL/HOLD, trading,
multi-agent orchestration, queues, Redis, Kafka, Kubernetes or microservices.
Full VN30 coverage and tick-level streaming remain outside the initial MVP.

## Documents

- [Original product brief](docs/PRODUCT_BRIEF.md)
- [Historical Day 0 report](docs/DAY0_REPORT.md)
- [Section 1 report](docs/SECTION1_REPORT.md)
- [UI refresh report and screenshots](docs/UI_REFRESH_REPORT.md)
- [Financial visualization report](docs/SECTION1_6_REPORT.md)
- [Materiality V0 integration report](docs/SECTION2_PHASE1_REPORT.md)
- [Historical evaluation report and commands](docs/SECTION2_PHASE2_REPORT.md)
- [Official references](docs/reference_repos.md)

.env, local databases, dependencies, build artifacts, logs, editor state and private data/
are excluded from Git. .env.example and dependency lockfiles are tracked.
