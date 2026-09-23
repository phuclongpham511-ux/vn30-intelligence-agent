# VN30 Intelligence Agent — Day 0 Implementation Plan

> This document is the implementation contract for Day 0.
>
> The purpose of Day 0 is **not** to build the full MVP. It is to establish a clean, future-compatible foundation that Codex can extend over the next development days.

## 1. Day 0 Objective

By the end of Day 0, the project should have:

- A working repository structure
- A bootable FastAPI backend
- A bootable Next.js frontend
- PostgreSQL-compatible configuration
- Initial core database models
- Dynamic ticker architecture
- Provider abstractions
- `vnstock` provider scaffolding
- Seed stocks: TCB, FPT, HPG
- Basic test coverage
- Evaluation scaffold
- Clear project documentation

Day 0 should **not** implement the full analytics, AI, Materiality Engine, thesis tracking, portfolio, or email features.

## 2. Product Context

The project is a personalized equity intelligence system.

The user can:

- Explore supported stocks
- Add stocks to a watchlist
- Define monitoring priorities
- Receive only the most material insights
- Ask the AI to explain why an event matters

The MVP must prove:

1. Material events can be detected.
2. The same event can have different importance for different user contexts.
3. An Attention Budget can reduce information overload.

## 3. Seed Stocks

Use the following three stocks for development and evaluation:

- `TCB`
- `FPT`
- `HPG`

These are **seed stocks only**.

### Critical Requirement

Do not design the application around a fixed list of three tickers.

Avoid business logic such as:

```python
SUPPORTED_TICKERS = ["TCB", "FPT", "HPG"]
```

inside analytics, monitoring, or materiality services.

The system should be future-compatible with dynamic ticker onboarding.

## 4. Dynamic Ticker Design

Introduce a `Stock` entity.

Suggested fields:

```text
id
symbol
exchange
company_name
sector
industry
is_active
created_at
```

Future flow:

```text
User enters ticker
↓
Provider validates ticker
↓
Create Stock record
↓
Fetch initial market/fundamental data
↓
Run analytics
↓
Ticker becomes available in Explore / Watchlist
```

For Day 0, TCB/FPT/HPG are seeded into the database.

## 5. Data Provider Strategy

Primary data source:

- `vnstock`

Do not couple business logic directly to the library.

Create provider abstractions.

### Required abstractions

```text
MarketDataProvider
FundamentalDataProvider
```

Optional future abstraction:

```text
NewsDataProvider
```

Desired dependency direction:

```text
Router
↓
Service
↓
Provider Interface
↓
Vnstock Provider
↓
vnstock
```

### Rule

Do not call `vnstock` directly from:

- FastAPI routers
- Materiality Engine
- AI Agent layer
- Frontend-facing services

The data provider should be replaceable later.

## 6. Backend Technology

Use:

- Python
- FastAPI
- Pydantic
- PostgreSQL
- SQLModel or SQLAlchemy
- uv

Testing:

- pytest
- pytest-asyncio

### FastAPI Constraint

There must be:

```text
exactly one root main.py
exactly one app = FastAPI()
```

Do not create:

```text
app/main.py
```

## 7. Frontend Technology

Use:

- Next.js
- React
- TypeScript

Day 0 only requires a minimal frontend scaffold.

No polished UI is needed.

## 8. Proposed Repository Structure

```text
vn30-intelligence-agent/

├── main.py
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── README.md
├── Dockerfile
│
├── routers/
│   ├── health.py
│   ├── stocks.py
│   ├── watchlists.py
│   └── monitoring.py
│
├── src/
│   ├── config/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── providers/
│   │   ├── base.py
│   │   └── vnstock/
│   ├── analytics/
│   ├── materiality/
│   ├── monitoring/
│   ├── agent/
│   └── services/
│
├── tests/
│
├── evaluation/
│   └── materiality_cases.json
│
├── scripts/
│   └── seed_stocks.py
│
├── frontend/
│
└── docs/
    ├── DAY0_PLAN.md
    └── reference_repos.md
```

Do not create unnecessary files or abstractions beyond this contract.

## 9. Initial Database Models

Implement only the models needed for Day 0.

### User

```text
id
email
created_at
```

Authentication is not required on Day 0.

### Stock

```text
id
symbol
exchange
company_name
sector
industry
is_active
created_at
```

### Watchlist

```text
id
user_id
name
created_at
```

### WatchlistItem

```text
id
watchlist_id
stock_id
created_at
```

### MonitoringPreference

```text
id
user_id
stock_id
dimension
priority
```

Supported `dimension` values:

```text
fundamentals
technical
news
```

Supported `priority` values:

```text
primary
secondary
low
```

## 10. API Contract — Day 0

Only implement what is necessary.

### Health

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Stocks

Scaffold:

```text
GET /stocks
GET /stocks/{symbol}
POST /stocks/validate
```

`POST /stocks/validate` may return a placeholder response on Day 0 if provider validation is not yet implemented, but the API contract should exist.

### Watchlists

Scaffold routes:

```text
GET /watchlists
POST /watchlists
POST /watchlists/{id}/stocks
DELETE /watchlists/{id}/stocks/{symbol}
```

Full business behavior is not required on Day 0 unless easy to implement cleanly.

## 11. Environment Configuration

Create `.env.example`.

Include:

```text
DATABASE_URL=
OPENAI_API_KEY=
```

Optional:

```text
APP_ENV=development
```

The backend must boot without requiring a valid OpenAI API key.

AI is not part of Day 0 execution.

## 12. Day 0 Provider Abstractions

Create clean provider interfaces.

### MarketDataProvider

Future methods may include:

```text
validate_symbol(symbol)
get_history(symbol, start, end)
get_latest(symbol)
```

### FundamentalDataProvider

Future methods may include:

```text
get_financials(symbol)
get_key_metrics(symbol)
```

Implementation folder:

```text
src/providers/vnstock/
```

Day 0 may contain real or stub implementations, but the abstraction boundary must be clear.

## 13. Seed Script

Create:

```text
scripts/seed_stocks.py
```

It should seed:

```text
TCB
FPT
HPG
```

The script should be idempotent.

Running it twice must not create duplicate stock records.

## 14. Evaluation Scaffold

Create:

```text
evaluation/materiality_cases.json
```

Include at least two sample cases.

Example:

```json
[
  {
    "case_id": "case_001",
    "symbol": "FPT",
    "event": {
      "dimension": "technical",
      "type": "price_breakdown"
    },
    "user_context": {
      "technical_priority": "primary"
    },
    "expected_level": "high"
  },
  {
    "case_id": "case_002",
    "symbol": "FPT",
    "event": {
      "dimension": "technical",
      "type": "price_breakdown"
    },
    "user_context": {
      "technical_priority": "low"
    },
    "expected_level": "medium"
  }
]
```

Do not implement the full Materiality Engine on Day 0.

## 15. Frontend Scaffold

Inside:

```text
frontend/
```

Create a minimal Next.js + TypeScript application.

Required route:

```text
/
```

Placeholder routes:

```text
/stocks/[symbol]
/watchlist
```

The UI may show simple placeholder content.

No chart implementation is required on Day 0.

## 16. Tests

At minimum create:

```text
tests/test_health.py
tests/test_stock_model.py
```

The test suite must pass.

If database integration tests are expensive to configure on Day 0, use the simplest reliable setup that preserves future PostgreSQL compatibility.

## 17. Documentation

Create / update:

```text
README.md
docs/DAY0_PLAN.md
```

README should include:

- Product problem
- MVP scope
- Seed stocks
- Architecture principle
- Tech stack
- Current project status
- Explicit out-of-scope list
- Future roadmap

## 18. Out of Scope for Day 0

Do not implement:

- Materiality Engine
- Technical indicators
- Fundamental analytics
- News ingestion
- AI Agent
- AI explanation
- Contextual chat
- Portfolio
- P/L
- Thesis tracking
- Suggested thesis
- RAG
- PDF ingestion
- Email notifications
- Broker mode
- Trading
- BUY / SELL recommendations
- Multi-agent architecture
- LangGraph
- Redis
- Kafka
- Kubernetes
- Microservices

## 19. Day 0 Tasks for Codex

### Task 1 — Initialize repository

Create:

```text
main.py
pyproject.toml
uv.lock
.env.example
.gitignore
README.md
Dockerfile
```

Use `uv`.

### Task 2 — FastAPI skeleton

Create the only FastAPI application in root `main.py`.

Add:

```text
GET /health
```

Expected response:

```json
{"status": "ok"}
```

### Task 3 — Configuration

Create environment-driven application settings.

The app must start without an OpenAI API key.

### Task 4 — Database layer

Create PostgreSQL-compatible database configuration.

Implement the initial models:

```text
User
Stock
Watchlist
WatchlistItem
MonitoringPreference
```

### Task 5 — Provider abstraction

Implement interfaces for:

```text
MarketDataProvider
FundamentalDataProvider
```

Create the `vnstock` provider package.

Do not expose `vnstock` directly outside the provider layer.

### Task 6 — Seed stocks

Implement idempotent seeding for:

```text
TCB
FPT
HPG
```

### Task 7 — API skeleton

Add health, stock, and watchlist route scaffolding.

Do not overbuild business logic.

### Task 8 — Evaluation scaffold

Create `evaluation/materiality_cases.json` with two sample cases.

### Task 9 — Frontend scaffold

Create Next.js + TypeScript frontend with:

```text
/
/stocks/[symbol]
/watchlist
```

Placeholder pages are acceptable.

### Task 10 — Tests

Create and run:

```text
test_health.py
test_stock_model.py
```

All tests must pass.

## 20. Day 0 Definition of Done

Day 0 is complete only if all of the following are true:

- [ ] Repository boots locally.
- [ ] `GET /health` returns HTTP 200.
- [ ] There is exactly one root `main.py`.
- [ ] There is exactly one `app = FastAPI()`.
- [ ] PostgreSQL-compatible configuration exists.
- [ ] Core Day 0 database models exist.
- [ ] Provider interfaces exist.
- [ ] `vnstock` provider package exists.
- [ ] TCB, FPT, HPG can be seeded idempotently.
- [ ] Core business logic does not depend on a fixed three-ticker list.
- [ ] Frontend boots locally.
- [ ] Required frontend routes exist.
- [ ] Tests pass.
- [ ] Evaluation scaffold exists.
- [ ] README is present and accurate.
- [ ] No future-scope AI / Thesis / Portfolio / RAG / Email features are implemented yet.

## 21. Architecture Principle

Keep this dependency direction:

```text
vnstock / external data
        ↓
Provider Layer
        ↓
Data / Analytics
        ↓
Material Event Detection
        ↓
Materiality Engine
        ↓
Monitoring Baseline
        ↓
Attention Budget
        ↓
AI Explanation
        ↓
Explore / Watchlist UI
```

Day 0 only builds the foundation required for the upper layers to be added later.

## 22. Implementation Rules for Codex

### Do

- Keep code simple.
- Keep modules small.
- Write tests.
- Use English for code, comments, schemas, commits, and documentation.
- Keep ticker handling dynamic.
- Keep `vnstock` isolated behind providers.
- Keep future analytics deterministic.
- Document trade-offs.

### Do Not

- Hardcode TCB/FPT/HPG into core business logic.
- Build portfolio features.
- Build thesis features.
- Build RAG.
- Build AI Agent logic yet.
- Add LangGraph.
- Add multi-agent architecture.
- Add email.
- Add trading features.
- Create another `main.py`.
- Create unnecessary infrastructure.
- Over-engineer abstractions that are not required by the MVP.

## 24. Git and GitHub Setup

The project must be version-controlled with Git and pushed to GitHub as part of Day 0.

### Repository name

```text
vn30-intelligence-agent
```

### Required Git setup

1. Initialize Git in the project root.
2. Use `main` as the default branch.
3. Create a `.gitignore` suitable for:
   - Python
   - FastAPI
   - uv
   - virtual environments
   - Next.js
   - Node.js
   - IDE/editor files
   - local databases
   - cache/build artifacts
   - environment files
4. Keep `.env.example` in the repository.
5. Never commit:
   - `.env`
   - API keys
   - secrets
   - database credentials
   - local virtual environments
   - `node_modules`
   - generated caches
   - proprietary/private datasets
6. Create the initial commit only after the Day 0 scaffold, tests, and documentation are in a valid state.

Suggested initial commit message:

```text
chore: initialize VN30 Intelligence Agent project
```

### GitHub repository

Create or connect to a GitHub repository named:

```text
vn30-intelligence-agent
```

Preferred visibility for this portfolio project:

```text
Public
```

Use public visibility only if the repository contains no private credentials, proprietary data, confidential reports, or restricted datasets.

### Push requirements

After the local Day 0 implementation is complete:

1. Add the GitHub repository as `origin`.
2. Push the `main` branch.
3. Verify that the repository is accessible on GitHub.
4. Verify that no secrets or local-only files were committed.
5. Confirm that `README.md` renders correctly on GitHub.

### If GitHub authentication is unavailable

Do not invent credentials, tokens, or authentication state.

Stop before the push step and report:

- the exact blocker,
- the exact command the user should run after authenticating,
- whether the local repository and commit are already ready.

### Required GitHub report from Codex

After pushing, Codex should report:

```text
Repository URL
Default branch
Latest commit hash
Latest commit message
Push status
```

Codex should also list any files intentionally excluded from version control.

---

## 25. Expected Output From Codex

After implementation, Codex should report:

1. Files created or modified.
2. Commands used to install dependencies.
3. Commands used to run the backend.
4. Commands used to run the frontend.
5. Commands used to run tests.
6. Test results.
7. Git repository status.
8. GitHub repository URL if push succeeded.
9. Latest commit hash.
10. Any assumptions made.
11. Any issues or blockers.
12. Any deviations from this specification and why.

Do not silently change scope.

---

## 26. Next Step After Day 0

After Day 0 is verified:

```text
Day 1
→ Dynamic market data via vnstock

Day 2
→ Fundamentals

Day 3
→ News

Day 4
→ Explore Page

Day 5
→ Materiality Engine v0

Day 6
→ Monitoring Baseline + personalization

Day 7
→ Watchlist + Attention Budget

Day 8
→ AI explanation + minimal contextual chat

Day 9
→ Evaluation

Day 10
→ Polish + demo + GitHub release v0.1.0
```

---

## 27. Final Day 0 Principle

> **Day 0 is successful when the foundation is clean enough that the Materiality MVP can be built without an architectural rewrite.**

It is not successful because many features exist.
