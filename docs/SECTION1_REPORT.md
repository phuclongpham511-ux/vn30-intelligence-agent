# Section 1 delivery report

Date: 2026-09-23. Scope: Data & Analytics Foundation only.

## 1. Implemented

Dynamic ticker onboarding, live vnstock daily OHLCV and annual financial statements,
normalized internal contracts, deterministic pandas/numpy analytics, market/fundamental/news/
overview endpoints, and a functional Explore UI with a price chart, metrics and provenance.
Watchlist scaffolds and future AI/materiality packages remain unchanged.

## 2. Architecture and data flow

Browser → Next.js same-origin proxy → FastAPI → existing services/provider interfaces →
vnstock adapter → normalized Pydantic objects → pure analytics → API response → Explore UI.
Only the adapter imports vnstock. There remains one root main.py and one FastAPI application.
No ticker-specific branching exists in production services or analytics.

## 3. Files changed

- pyproject.toml / uv.lock: pinned vnstock 4.0.2; pandas, numpy and truststore.
- main.py: sanitized provider error handler.
- routers/stocks.py: onboarding and all data endpoints.
- src/models/__init__.py / src/db/session.py: Stock updated_at, normalized-symbol
  constraint, case-insensitive index, additive Day 0 schema migration.
- src/schemas/stocks.py / data.py: ticker alias, validation, normalized objects and typed overview.
- src/providers/base.py, vnstock/__init__.py, news.py: existing interfaces extended,
  real adapters and labeled news fixtures.
- src/services/stocks.py / data.py: reusable provider dependencies and analytics coordination.
- src/analytics/market.py / fundamentals.py: deterministic calculations.
- frontend/app/: ticker picker, Explore, same-origin API proxy, chart and styles.
- tests/conftest.py: offline dependency override preserving Day 0 scaffold tests.
- tests/test_analytics.py, test_provider.py, test_data_api.py, test_persistence.py.
- scripts/smoke_vnstock.py: explicit opt-in network smoke.
- README.md, docs/SECTION1_PLAN.md, docs/SECTION1_REPORT.md, docs/reference_repos.md.

## 4. vnstock capabilities actually used

- Listing(source="KBS").all_symbols(): ticker validation and company names.
  The observed VCI listing call failed; KBS returned 1,521 symbols.
- Quote(symbol=..., source="VCI").history(start=..., end=..., interval="1D"):
  real daily OHLCV. Adapter filters SDK extra rows outside the requested dates.
- Finance(symbol=..., source="VCI").income_statement(period="year", lang="en",
  dropna=False): up to four annual periods, item rows and year columns.
  dropna=False prevents SDK missing values from being filled with zero.
- VCI ratio() was investigated but returned an empty/unreliable table, and is not
  part of the production data path. ROE stays null.
- No direct upstream HTTP bypass, crawler, alternative paid provider or sponsor-package
  workaround was added.

The installed SDK's OHLC transformation divides VCI prices by 1,000. Our adapter reverses
that once to return VND. Financial statement amounts are already VND. SDK version is pinned
to the tested schema. SDK telemetry and automatic agent setup default off.

## 5. Normalized fields and assumptions

MarketBar: ticker/date/OHLC/volume/source/currency, unique logical date/source per ticker.
All ten required market metrics are implemented. Returns and ratios are fractions;
volatility is annualized sample standard deviation; RSI uses Wilder initialization.
Volume averages include the current observation. Warm-up, zero-volume division and empty
history return null where appropriate. See README for exact formulas.

Fundamentals: annual period, net sales (isa3), consolidated net profit after tax (isa20),
gross margin from isa5/isa3, net margin from isa20/isa3, ROE=null, source/currency.
Growth and margin changes compare the matching previous year. Zero/negative prior-year
growth denominators return null. Missing generic bank revenue is not replaced by interest
income. Sector-specific bank metrics are deferred.

NewsItem has every requested field, plus is_fixture. Current provider emits clearly marked
synthetic examples with source=local-fixture, null URL and an explicit sample notice.
No fabricated news is presented as real reporting.

## 6. Test results

41 offline pytest cases passed, including the existing 17 Day 0 cases.
The old provider-not-ready test now explicitly injects an unconfigured test provider,
preserving that fallback contract without network calls.

Coverage includes reference Wilder RSI values, return/MA/volume/volatility/drawdown
calculations, warm-up, flat prices, zero volume, invalid OHLC, duplicate bars, yearly
comparisons, missing data, mocked SDK normalization/units, bank null behavior, API
404/422/502 behavior, typed overview, dynamic onboarding and idempotency, disk persistence
and Day 0 migration. One existing upstream Starlette/httpx deprecation warning remains.

Real vnstock smoke (separate command, not part of pytest):

| Ticker | Daily bars | Market as_of | Latest annual period | Result |
| --- | ---: | --- | --- | --- |
| FPT | 123 | 2026-09-23 | 2025 | PASS |
| TCB | 123 | 2026-09-23 | 2025 | PASS |
| HPG | 123 | 2026-09-23 | 2025 | PASS |
| VNM | 123 | 2026-09-23 | 2025 | PASS |

Each smoke verified provider validation, normalized market history, MA50, and a non-null
reported net profit. Failures produce nonzero exit status.

## 7. Frontend build and demo

Next.js production build: PASS. TypeScript no-emit check: PASS.
Browser demo verified VNM onboarding from input " vnm ", then changing to FPT and TCB.
All three Explore pages displayed real dated prices, chart, market metrics and annual
fundamentals. TCB correctly omitted unavailable generic revenue/margin/ROE fields.
News was visibly labeled as sample data. VNM company name came from the live listing.

## 8. Persistence / PostgreSQL

Real SQLite file migration, seed, API insert and independent-session retrieval passed.
The actual local database contains TCB/FPT/HPG/VNM with updated_at populated.
A test also reopens a disk database after migrating a Day 0 schema.

PostgreSQL-compatible configuration/driver remain intact and table DDL compilation passes.
No PostgreSQL service, installation or listener on port 5432 was available locally.
Live PostgreSQL verification is therefore NOT completed; this conditional environment
gate is recorded explicitly rather than claimed as passed.

## 9. Docker

Docker CLI exists, but Docker Desktop's Linux engine pipe is unavailable.
Container build/run remains unverified and is deferred to the release gate per the spec.
Dockerfile continues packaging the backend with the locked dependencies.

## 10. Known limitations

- Four annual reporting periods, no quarterly feed in this slice.
- ROE unavailable; bank-specific revenue interpretation and metrics deferred.
- News fixtures only; no live news classification.
- In-process cache only; data refresh depends on upstream availability/rate limits.
- Provider-empty market requests may be raised as upstream errors by vnstock itself.
- Overview fails as a whole on required-provider failure; UI supports retry.
- Prices follow provider adjustment conventions; this is not an unadjusted trading feed.
- No authentication, production deployment, portfolio, AI or Section 2 implementation.
- SDK may print upstream upgrade/community notices during live requests.

## 11. Local commands

```powershell
uv --system-certs sync --frozen
uv run python -m scripts.seed_stocks
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
uv run pytest -q
uv run python -m scripts.smoke_vnstock FPT TCB HPG VNM
cd frontend
$env:NODE_OPTIONS='--use-system-ca'
npm ci
npm run dev
npm run build
npm run typecheck
```

Backend defaults to SQLite. Use DATABASE_URL for an existing PostgreSQL database.
Frontend server BACKEND_URL defaults to http://127.0.0.1:8000.

## 12. Example API requests

```powershell
Invoke-RestMethod http://127.0.0.1:8000/stocks -Method Post -ContentType application/json -Body '{"ticker":"VNM"}'
Invoke-RestMethod http://127.0.0.1:8000/stocks/VNM/market
Invoke-RestMethod http://127.0.0.1:8000/stocks/VNM/fundamentals
Invoke-RestMethod http://127.0.0.1:8000/stocks/VNM/news
Invoke-RestMethod http://127.0.0.1:8000/stocks/VNM/overview
```

## 13. Next section readiness

Core Section 1 data path: PASS, with the explicit fixture-news and unavailable-local-
PostgreSQL allowances in the specification. Ready for Section 2 development.
Live PostgreSQL and Docker deployment verification remain open release tasks.
Nothing from Section 2 has been implemented.

Changes are committed with "feat: add vnstock data and analytics foundation" and pushed
only after tests/build pass. The final delivery message records the verified commit and
remote state. Environment files, local databases, caches and dependencies remain untracked.
