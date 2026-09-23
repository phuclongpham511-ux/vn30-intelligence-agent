# VN30 Intelligence Agent

Help active retail investors know which changes deserve attention across Vietnamese equities.
The problem is information overload: the eventual product will rank material changes and
show only the top 1–3 insights, with inspectable evidence.

## Current status: Day 0

A bootable FastAPI backend and Next.js frontend, relational models, provider boundaries,
idempotent seed script, tests and evaluation examples. This is a foundation, not a working
investment intelligence product. No live market data or AI is connected.

The seeds **TCB, FPT and HPG** are development examples only. Stock routes query the database;
provider interfaces and dynamic frontend routes accept other tickers.

## Quick start

Requirements: Python 3.12+, uv, Node.js 20.9+ and npm. Run backend commands from the repository root.

```powershell
uv sync --frozen
Copy-Item .env.example .env
uv run python -m scripts.seed_stocks
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000/docs or http://127.0.0.1:8000/health.
No OpenAI API key is needed. If a corporate TLS proxy causes UnknownIssuer,
use `uv --system-certs sync --frozen`; certificate verification stays enabled.

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:3000. Routes: `/`, `/stocks/TCB` (dynamic symbol), `/watchlist`.
The frontend contains placeholders and does not call the backend yet.
On this Windows machine, set `$env:NODE_OPTIONS='--use-system-ca'` before npm
installation to trust the system certificate store.

## Database

SQLite is the zero-setup local default. Set `DATABASE_URL` in .env to
`postgresql+psycopg://USER:PASSWORD@localhost:5432/vn30` for an existing PostgreSQL database.
The driver is included; `postgresql://` is normalized to psycopg too.
Run the seed command after changing databases. It explicitly creates initial tables;
starting the web server does not mutate the database. Health reports process liveness,
not database readiness.

Models: User, Stock, Watchlist, WatchlistItem, MonitoringPreference.
Unique constraints prevent duplicate symbols, watchlist membership and per-dimension preferences.
Priorities primary / secondary / low will be weights, not filters.
No users or watchlists are seeded. Schema migrations and authentication are future work.

## API

| Method | Route | Day 0 behavior |
| --- | --- | --- |
| GET | /health | 200, {"status":"ok"} |
| GET | /stocks | Active stocks from the database |
| GET | /stocks/{symbol} | Stock details or 404 |
| POST | /stocks/validate | Normalizes input; valid=null, status=not_implemented |
| GET / POST | /watchlists | 501 scaffold |
| POST | /watchlists/{id}/stocks | 501 scaffold |
| DELETE | /watchlists/{id}/stocks/{symbol} | 501 scaffold |

Validation body: `{"symbol":"VNM"}`. This endpoint does not onboard stocks yet.
Watchlist POST body: `{"user_id":1,"name":"Research"}`; add-stock body uses symbol.
Monitoring has a model only. This local development service has no authentication.

## Architecture and stack

One root main.py creates the only FastAPI app. Dependency direction:

```text
Router → Service → Provider Interface → vnstock adapter → external library
```

Python, FastAPI, Pydantic Settings, SQLModel / SQLAlchemy, psycopg, uv;
Next.js App Router, React and TypeScript; pytest and pytest-asyncio; Docker.
MarketDataProvider and FundamentalDataProvider are structural interfaces.
Vnstock adapters explicitly raise ProviderNotReadyError. The external vnstock package
will be selected and integrated in Day 1; it is intentionally not installed for unused stubs.

Future numerical analytics and materiality scoring will be deterministic.
AI will explain existing evidence, not invent numerical facts or independently rank materiality.

## Verification

```powershell
uv run pytest -q
cd frontend
npm run build
npm run typecheck
```

Tests use isolated in-memory SQLite with foreign keys enabled and compile PostgreSQL DDL.
Evaluation cases describe expected personalization; no scoring engine runs yet.

Backend container (requires a running Docker daemon):

```powershell
docker build -t vn30-intelligence-agent .
docker run --rm -v vn30-data:/data -e DATABASE_URL=sqlite:////data/vn30.db vn30-intelligence-agent uv run --no-sync python -m scripts.seed_stocks
docker run --rm -p 127.0.0.1:8000:8000 -v vn30-data:/data -e DATABASE_URL=sqlite:////data/vn30.db vn30-intelligence-agent
```

Use an external PostgreSQL URL instead for a shared environment.
Dockerfile packages the backend only.

## MVP scope and roadmap

The future MVP includes stock Explore, watchlists, monitoring preferences, fundamentals,
technical signals, news, rule-based materiality, top 1–3 insights, evidence-based AI explanations,
minimal stock-context chat and evaluation.

- Day 1: dynamic market data and validation via vnstock.
- Days 2–4: fundamentals, news, Explore.
- Days 5–7: materiality, personalized monitoring, watchlist attention budget.
- Days 8–10: explanations and contextual chat, evaluation, polish and release.

Out of Day 0: analytics, Materiality Engine, live ingestion, AI, chat, charts and functional watchlists.
Out of initial MVP: portfolio / P&L, thesis tracking, RAG / PDF ingestion, email,
broker mode, trading and BUY / SELL recommendations, full VN30 coverage, tick streaming,
multi-agent orchestration, LangGraph, Redis, Kafka, Kubernetes and microservices.

## Project documents

- [Day 0 implementation plan](docs/DAY0_PLAN.md)
- [Original product brief](docs/PRODUCT_BRIEF.md)
- [Verification and delivery report](docs/DAY0_REPORT.md)
- [Official references](docs/reference_repos.md)

Environment files, local databases, virtual environments, node_modules, generated builds,
caches, editor state and private datasets are excluded from Git. .env.example and both
dependency lockfiles are tracked.
