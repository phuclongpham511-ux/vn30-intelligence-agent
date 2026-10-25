# VN30 Intelligence Agent

A personalized equity intelligence system for Vietnamese equities, starting with VN30.

The project is designed around one core question:

> **Among everything happening around the stocks I follow, what actually deserves my attention?**

Instead of showing users more raw data, the system monitors market, fundamental, technical, and news signals, ranks them by personalized materiality, and surfaces only the most important insights.

## Product Goal

Most stock platforms already provide price, charts, financial statements, technical indicators, news, broker research, and watchlists.

The problem is not lack of data. The problem is **information overload**.

The goal of this project is to:

1. Detect meaningful changes.
2. Evaluate how important each event is.
3. Personalize that importance based on user monitoring preferences.
4. Limit output to the top 1–3 insights that deserve attention.
5. Explain why each selected event matters while keeping raw evidence inspectable.

## Primary User

The MVP targets an **active retail investor** who tracks several Vietnamese stocks, reads market news and company fundamentals, uses charts and technical indicators, and does not want to manually process every signal every day.

Secondary users such as brokers and portfolio managers may be supported later.

## MVP Scope

The first MVP focuses on three seed stocks:

- `TCB`
- `FPT`
- `HPG`

These are development and evaluation seeds only.

The system must **not hardcode business logic around these three symbols**. The architecture should support adding new tickers later.

### Included in MVP

- Stock Explore page
- Watchlist
- Monitoring preferences
- Fundamentals
- Price / technical signals
- News
- Rule-based Materiality Engine
- Attention Budget: top 1–3 insights only
- AI explanation layer
- Minimal stock-context chat
- Evaluation set for materiality ranking

### Not Included in Initial MVP

- Portfolio tracking
- Cost basis / P&L
- Thesis tracking
- RAG over research PDFs
- Email notifications
- Trading execution
- BUY / SELL recommendation bot
- Full VN30 coverage
- Realtime tick-level streaming
- Multi-agent orchestration

## Core Product Hypotheses

### H1 — Material Change Detection

The system can distinguish meaningful changes from routine noise.

### H2 — Personalized Materiality

The same event can receive different importance levels for different user preferences.

Example:

```text
Event:
TCB breaks an important technical level

User A:
Technical = PRIMARY
→ HIGH

User B:
Technical = LOW
→ MEDIUM
```

### H3 — Attention Budget

Even if a user monitors every available dimension, the product still surfaces only the top 1–3 events that matter most.

## Monitoring Baseline

Each watchlist stock has a monitoring baseline.

MVP monitoring dimensions:

- Fundamentals
- Price / Technical
- News

Each dimension has a priority:

```text
PRIMARY
SECONDARY
LOW
```

These are **weights**, not hard filters.

A LOW-priority signal can still be surfaced if it is unusually important.

## Materiality Engine

The Materiality Engine is the core differentiator.

Conceptually:

```text
Event
+
Stock context
+
User monitoring baseline
↓
Materiality Engine
↓
LOW / MEDIUM / HIGH
+
reasons
+
evidence
```

The first version should be deterministic and rule-based.

The LLM should **not** decide materiality from scratch.

## AI Role

The AI layer is responsible for interpretation, not numeric truth.

### Deterministic layer

Used for:

- Returns
- Moving averages
- RSI
- Volume anomalies
- Fundamental changes
- Materiality scoring

### AI layer

Used for:

- Explaining what changed
- Explaining why it matters
- Explaining why an event was ranked HIGH / MEDIUM / LOW
- Answering contextual questions about the stock currently being viewed

Core principle:

```text
Numbers
→ deterministic analytics

Interpretation
→ AI
```

## Data Source

Primary provider:

- `vnstock`

The system should use provider abstractions so the data source can be replaced later without rewriting business logic.

```text
Router / Service
↓
Provider Interface
↓
Vnstock Provider
↓
vnstock
```

## Dynamic Ticker Support

The initial database seeds:

```text
TCB
FPT
HPG
```

Future target flow:

```text
User enters a new ticker
↓
Validate through provider
↓
Create Stock entity
↓
Fetch historical data
↓
Run analytics
↓
Ticker becomes available in Explore / Watchlist
```

## Technology Stack

### Backend
- Python
- FastAPI
- Pydantic
- PostgreSQL
- SQLModel or SQLAlchemy
- pandas
- numpy

### AI
- OpenAI Agents SDK

### Frontend
- Next.js
- React
- TypeScript

### Charts
- TradingView Lightweight Charts
- Recharts

### Testing
- pytest
- pytest-asyncio

### Packaging / Deployment
- uv
- Docker

## Repository Constraint

The project must contain:

```text
one root main.py
one app = FastAPI()
```

Do not create another `main.py` under an `app/` directory.

## MVP Definition of Done

The MVP is successful when:

- The app can explore TCB, FPT, and HPG.
- A user can add stocks to a watchlist.
- A user can assign monitoring priorities.
- The system detects multiple raw events.
- The Materiality Engine ranks those events.
- The same event can receive different importance for different user contexts.
- The Watchlist shows only the top 1–3 insights.
- The AI can explain why an event matters using existing evidence.
- An evaluation set measures materiality behavior.
- The architecture can accept another supported ticker without rewriting core logic.

## North Star

> **Do not give users more data. Help them know what deserves attention.**
