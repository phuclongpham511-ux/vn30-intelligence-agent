# VN30 Intelligence Agent

Help active retail investors know which changes deserve attention across Vietnamese equities.
The eventual product will rank material changes and show only the top 1–3 insights with inspectable evidence.

## Status: Section 1.5 — UI Refresh

Working vertical slice: dynamic ticker → vnstock → normalized schemas → deterministic
analytics → FastAPI → Explore UI. Live market and annual financial data were verified for
FPT, TCB, HPG and a newly onboarded VNM. News is explicitly labeled synthetic sample data.
No Materiality Engine or AI has been implemented.

TCB, FPT and HPG remain initial seeds, not a hardcoded supported universe.

## Run locally

Requirements: Python 3.12+, uv, Node.js 24+ and npm (Node 24.16 tested; frontend tests use native TypeScript support). From repository root:

```powershell
uv --system-certs sync --frozen
Copy-Item .env.example .env
uv run python -m scripts.seed_stocks
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Do not overwrite an existing .env when upgrading. The seed command creates the schema,
applies the additive Day 0 Stock migration and seeds idempotently. No OpenAI key is required.

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
dark/light themes. Global search can validate and add new tickers. Stock detail includes
daily prices, technical metrics, grouped fundamentals, raw data and labeled sample news.

The interface is permanently English-only. Only trusted display_name_en metadata is
shown as a company name; otherwise the ticker is displayed. Raw company_name is retained
in the backend but is never a UI fallback. New tickers do not require frontend branches.
The seed command applies the additive display-name migration idempotently.

## Architecture

Exactly one root main.py and one FastAPI app.

```text
Explore UI → Next.js API proxy → FastAPI routers → services
                                                ↓
                       existing provider interfaces → vnstock adapters
                                                ↓
                      normalized schemas → pure analytics → API
```

Stack: Python, FastAPI, SQLModel/SQLAlchemy, Pydantic, psycopg, pandas, numpy, uv;
Next.js, React, TypeScript; pytest and pytest-asyncio; backend Dockerfile.

- MarketDataProvider: KBS listing validates the universe and supplies company names;
  VCI Quote supplies daily OHLCV.
- FundamentalDataProvider: VCI annual income statements, up to four periods in the
  verified community package. vnstock is pinned to 4.0.2 because mappings are version-specific.
- NewsProvider: clearly labeled local fixtures, no crawler or invented live news.
- Stock keeps the existing symbol/company_name fields (equivalent to ticker/name).
  updated_at and a case-insensitive unique index were added. The HTTP input accepts ticker or symbol.
- Bounded process-local caches: 5-minute market history, 1-hour fundamentals and listings.
  Cache expiration retries upstream; there is no stale/fake fallback.
- External SDK import is lazy. SDK telemetry and automatic agent-guide installation default off.
  System TLS certificates are used without disabling certificate verification.

## Data contracts and formulas

All price and financial amounts use **VND**, volume uses shares. VCI SDK OHLC prices are
in thousands of VND and are multiplied by 1,000 exactly once in the adapter.
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
set DATABASE_URL to postgresql+psycopg://USER:PASSWORD@localhost:5432/vn30, then run the seed
command. Plain postgresql:// URLs are normalized to psycopg. Core entities are persisted;
market/fundamental datasets are fetched on demand and not stored in the database.

SQLite migration/save/reopen was verified. PostgreSQL DDL compiles in tests, but no local
PostgreSQL server was available for live verification. Docker Engine was unavailable;
container verification remains a release gate.

```powershell
docker build -t vn30-intelligence-agent .
docker run --rm -v vn30-data:/data -e DATABASE_URL=sqlite:////data/vn30.db vn30-intelligence-agent uv run --no-sync python -m scripts.seed_stocks
docker run --rm -p 127.0.0.1:8000:8000 -v vn30-data:/data -e DATABASE_URL=sqlite:////data/vn30.db vn30-intelligence-agent
```

## Verification

```powershell
uv run pytest -q
uv run python -m scripts.smoke_vnstock FPT TCB HPG VNM
cd frontend
npm run build
npm run typecheck
npm test
```

The default 43-test backend suite is offline; SDK calls are mocked. Smoke is explicitly opt-in,
uses the real provider and exits nonzero on failure.
Four frontend presentation tests cover English names, missing values, signed percentages and safe links.
See [UI refresh report](docs/UI_REFRESH_REPORT.md) for screenshots and browser QA.
See [Section 1 report](docs/SECTION1_REPORT.md) for observed results and limitations.

## MVP roadmap and boundaries

Next: Section 2 — deterministic Materiality Engine, followed by monitoring priorities,
watchlist attention budget, evidence-based explanations and minimal stock-context chat.

Not implemented: materiality, event scoring, monitoring weighting, watchlist intelligence,
AI/LLM/Agents SDK, portfolio/P&L, thesis, RAG/PDF, email, prediction, BUY/SELL/HOLD, trading,
multi-agent orchestration, queues, Redis, Kafka, Kubernetes or microservices.
Full VN30 coverage and tick-level streaming remain outside the initial MVP.

## Documents

- [Original product brief](docs/PRODUCT_BRIEF.md)
- [Day 0 plan](docs/DAY0_PLAN.md) and [historical Day 0 report](docs/DAY0_REPORT.md)
- [Section 1 plan](docs/SECTION1_PLAN.md) and [Section 1 report](docs/SECTION1_REPORT.md)
- [UI refresh report and screenshots](docs/UI_REFRESH_REPORT.md)
- [Official references](docs/reference_repos.md)

.env, local databases, dependencies, build artifacts, logs, editor state and private data/
are excluded from Git. .env.example and dependency lockfiles are tracked.
