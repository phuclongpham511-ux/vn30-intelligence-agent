# VN30 Intelligence Agent — Domain Context

## Product purpose

VN30 Intelligence Agent helps active retail investors identify which changes deserve attention across Vietnamese equities.

North Star:

> Do not give users more data. Help them know what deserves attention.

The product is a research and monitoring system, not an automated trading or recommendation engine.

## Core domain language

### Material Event

A factual change detected from normalized market, technical, fundamental, news, or corporate-event evidence.

A Material Event is not inherently positive or negative for investment returns. Direction only describes the observed change.

### Materiality

How worthy an event is of the user's attention.

Materiality is **not**:
- predicted future return;
- bullishness or bearishness;
- BUY / SELL / HOLD;
- investment advice.

### Base Materiality

The non-personalized materiality score produced from:

```text
Significance
+ Novelty
+ Evidence Confidence
→ Base Materiality
```

V0 currently uses a provisional deterministic combination. Historical evaluation exists to calibrate later versions rather than justify intuition-based weights.

### Significance

How large, unusual, or economically important the event is.

Potential evidence channels:
- own-history abnormality;
- market-relative abnormality;
- sector-relative abnormality;
- economic magnitude.

Missing channels remain null and are excluded from the available-channel calculation. They are not silently converted to zero.

### Novelty

Whether the event represents genuinely new information or a new state relative to what has recently been observed or alerted.

Novelty is not historical abnormality.

Examples:
- entering an RSI regime can be novel;
- remaining in the same RSI regime is not a new transition;
- repeating the same event shortly after an earlier occurrence should generally have lower novelty.

### Evidence Confidence

How trustworthy and complete the evidence supporting an event is.

Relevant concepts include:
- source quality;
- data completeness;
- provenance;
- corroboration when it provides independent evidence.

Multiple technical indicators derived from the same OHLCV series are not automatically independent sources.

### Historical Replay

A chronological reconstruction that asks:

> If the system had been running at this historical time, using only information available then, what would it have detected and scored?

Replay must be point-in-time safe and must not use future observations.

### Replay Case

The immutable record of one historical Materiality V0 output, including original evidence, context features, scores, reason codes, provenance, score version, and split.

Human review never overwrites the original Replay Case.

### Review Queue

A deterministic sample of replay cases selected for human judgment.

The queue should emphasize:
- high scores;
- borderline scores;
- channel disagreement;
- repeated events;
- rare event types;
- incomplete or excluded cases;
- data-quality flags;
- control samples.

Holdout cases never enter the review queue.

### Human Review

A separate label attached to a Replay Case.

Verdicts:
- approve;
- reject;
- modify;
- uncertain.

Attention levels:
- 0: ignore;
- 1: low;
- 2: material;
- 3: critical.

Human review is the bridge between historical replay and formal calibration.

### Benchmark Dataset

Replay cases joined with human labels while preserving original engine outputs.

This benchmark is used to evaluate and later calibrate Materiality Engine behavior.

### Calibration

Evidence-based adjustment of thresholds, mappings, weights, cooldowns, deduplication rules, and context effects.

Calibration must use reviewed historical evidence. It must not use holdout cases.

### Validation

A chronological period used to compare calibration variants after tuning on the calibration period.

### Holdout

A protected chronological period that remains untouched during tuning and review.

It is used only for a later formal assessment of the selected engine version.

### Stress Period

Older or unusual historical regimes evaluated separately from the recent calibration era.

Stress history is useful for rare events but should not be mixed equally into current-regime distributions.

### Monitoring Baseline

The dimensions a user cares about for a stock, such as:
- Fundamentals;
- News;
- Price;
- Technical;
- Valuation.

These preferences are weights, not hard filters.

### Personalized Materiality

A later-stage ranking layer that adjusts Base Materiality using user context such as monitoring preferences, portfolio exposure, and thesis relevance.

Personalization may change priority. It must not rewrite facts.

### Attention Budget

The product constraint that surfaces only a small number of the most material insights, typically the top 1–3, instead of recreating information overload.

### Thesis

An optional investment narrative tracked over time.

A thesis may be suggested, modified, tracked, or ignored. It is not required for the MVP and is separate from Base Materiality.

## Evidence hierarchy

The user-facing mental model is:

```text
INSIGHT
"What does this mean?"
    ↓
METRIC
"What are the numbers?"
    ↓
SOURCE
"Where did this come from?"
```

AI explanation must remain grounded in inspectable evidence.

## Current architecture stage

### Project checkpoint — 2026-10-05

This is the canonical current project status. It supersedes earlier phase-status
summaries; historical research documents and implementation commits remain intact.

Completed capabilities:

- **Foundation / Data & Analytics:** FastAPI, data/database foundation, dynamic
  ticker support, stock data, deterministic fundamental analytics and stock APIs.
- **UI/UX + Financial Visualization:** Explore, Stock Detail, financial charts,
  responsive layout and light/dark themes.
- **News V1 — COMPLETE:** 10 Vietnamese and 5 global sources; ingestion and
  configurable polling; deterministic normalization/deduplication and idempotent
  repeated ingestion; Article → Story model; deterministic topic/ticker/sector
  tagging; Top Stories, Trending Topics, Latest News and Global Markets; source
  failure isolation and telemetry. No full article persistence or LLM dependency.
- **Connected News Discovery — COMPLETE:** stock pages connected to ingested news;
  ticker/sector/country/source/topic filtering; shareable filtered URLs and source
  update status, reusing the existing News architecture.
- **Market Briefing Usability & Readiness — COMPLETE:** separate Briefing, Latest
  News and Global Markets views; improved navigation, mobile usability and
  empty/error states; relevant ingestion and UI validation completed.
- **Mascot UI V1 — COMPLETE:** centralized state system, restrained state semantics
  and placement; mascot is secondary to financial information and is not the
  primary brand/logo.

Pre-existing local UI/mascot follow-up changes remain outside this documentation
checkpoint commit. Pushing this checkpoint publishes existing implementation
commits, not uncommitted working-tree changes.

### Technical Materiality — PAUSED

Technical Materiality is paused, not abandoned. Materiality Engine V0 and
research/evaluation infrastructure already exist, including historical replay and
reviewed evidence. Further calibration/deployment is blocked by external
historical-data/provenance requirements. Do not continue without new source evidence.

Unresolved requirements:

- historical price provenance;
- corporate-action / adjustment evidence;
- trading-session continuity;
- point-in-time integrity;
- avoiding future-information leakage.

SSI product Market Data qualification has PASSED. SSI Market Data Provider Integration
V1 uses the official SDK 3.2.1 raw authenticated transport, dynamic security metadata,
bounded pagination and existing deterministic analytics. SSI is the default market
provider with no silent fallback; Fundamentals remain temporarily on vnstock/VCI.
SSI historical OHLC is adjusted, prices VND ×1 and volume shares ×1. Only bars dated
before today in Asia/Ho_Chi_Minh are eligible, including after market close.
Technical Materiality remains BLOCKED by PIT vintage, historical revision policy,
full adjustment methodology and benchmark continuity/provenance. Do not restart
calibration. Existing protected-case, validation and holdout safeguards remain in force.

### Watchlist Intelligence V1 — browser-local monitoring slice implemented

The existing Watchlist page now supports following/removing available stocks,
recent ticker-matched Story developments, source evidence, distinct Story counts,
explicit review state, and links to Stock Detail / filtered Latest News. Membership
and reviewed Story IDs persist in this browser only; there is no cross-device sync
or account identity. Account-owned Watchlist/WatchlistItem models and their CRUD
scaffolds remain unchanged; no parallel database membership system was introduced.

The read-only `/watchlists/monitoring` POST endpoint reuses News ingestion/tags and
groups matching articles by Story ID over the last 72 hours of ingestion. An exact
ticker tag is required; sector/global relevance is deferred. New means a Story ID
not explicitly marked reviewed for that ticker, not a re-ingested article or a
Materiality judgment. Failed requests and unavailable stocks do not become zero.
This ships Personalized Relevance + Monitoring only; the broader direction below
remains a roadmap, not an authorization to start another phase.

News and stock-linked discovery reasonably answer **“What is happening?”** The
remaining product gap is **“What changed for the stocks I follow?”**

The Watchlist Intelligence direction turns the existing Watchlist into a personalized
monitoring workspace. Reuse it rather than rebuilding it from scratch:

```text
Existing Watchlist + News Stories + Ticker / Sector / Topic metadata
                  + existing market/fundamental context
→ personalized relevance / monitoring
→ “What changed for what I follow?”
```

Initial intended scope: relevant latest stories per watched ticker,
new-development counts, new-since-last-seen state, relevant sector/global stories,
and useful no-change / empty / unavailable states. Use deterministic relevance
first. This is **Personalized Relevance + Monitoring**, not full Materiality or
Materiality scoring. The browser-local slice above implements only ticker-tagged
monitoring and explicit review; broader relevance and durable user identity remain
outside this V1 slice.

### News refinement and Community Pulse V1 — 2026-10-05

Top Stories now exposes one deterministic registry-selected representative with
additional publisher evidence behind a disclosure; ranking/diversity is unchanged.
Explicit feed media metadata may provide a thumbnail. Sector is demoted to Advanced
headline-tag filtering because current company sector mapping is missing and actual
coverage is sparse. No sector values were invented.

Community Daily Pulse groups same-day public investor discussion into top 1–3
extractive themes. It remains separate from publisher News, sentiment, Materiality
and investment advice. Active sources: F319 public latest-page comments, 24HMoney
public community posts, and Chứng Sỹ public post pages/sitemap. Each polls every
15 minutes with robots checks, bounded requests and isolated persisted status.
FireAnt remains deferred: no stable unauthenticated item feed was verified.
Today means the Vietnam calendar day using actual publication time, never observed
time or an old thread's age; explicit `window=last24h` is labelled Last 24 hours.
There is no automatic stale-data fallback. Stable native item identities and bounded
immutable text/attribution revisions preserve evidence; legacy F319 thread tables
and observations remain compatible. Conservative text dedup retains original links;
themes rank by unique items, source breadth and recency, not truth or prediction.
Stock Detail, Watchlist and Community Pulse expose themes and expandable evidence.
Watchlist review is explicit and separate from News; item identity determines novelty.
No Community Momentum or SSI historical retention is implemented.

### Data Update Reliability V1 — active milestone, implemented 2026-10-06

One canonical `python -m scripts.ingest_data [--watch]` worker operates existing
News and Community services outside FastAPI. Persisted per-source cadence survives
restart; separate sessions isolate failures. Source status exposes actual last
attempt/success and cadence-relative freshness. Successful Community acquisitions
now append raw timestamped nullable replies/views observations without backfill or
momentum claims. Automatic OS/process restart requires a future external supervisor.

Community is now integrated into Stock Detail and browser-local Watchlist monitoring.
Both read bounded ticker-matched persisted discussions with explicit source freshness.
Watchlist Community review uses separate thread identities from News Story IDs;
only explicit review updates browser-local state, and count changes do not create
new discussions. Community remains separate from News and Materiality, and is
neither sentiment nor Momentum. Momentum remains deferred until daily coverage and repeated observations are sufficient.

Technical Materiality remains paused pending SSI / certified historical-data
provenance evidence; this milestone does not reopen calibration or protected cases.

### Later direction and current non-priorities

An **AI Product Layer** may later summarize watchlist changes, explain why a story
relates to a stock and synthesize existing evidence. LLMs interpret and synthesize
inspectable evidence; they do not invent calculations or facts.

Longer term: News + Technical + Fundamentals + user context → Unified Materiality
→ Personalized Attention Budget. Neither this integration nor the AI layer is the
next implementation task. Personalized materiality, live materiality UI, portfolio
context, thesis tracking and the AI/LLM agent layer remain future capabilities.

Do not introduce now: vector DB, embeddings, bulk LLM news summarization, sentiment
engine, broader social crawling/profiling, full portfolio intelligence, Watchlist rewrite,
further Technical calibration without new source evidence, or microservices /
Kafka / Redis / Celery / Kubernetes.

Product progression: News **“What is happening?”** → next **“What changed for what
I follow?”** → future Materiality **“What matters to me?”** The North Star remains:
**“Do not give users more data. Help them know what deserves attention.”**

## Engineering principles

- Deterministic Python computes financial metrics and Materiality inputs.
- AI interprets or orchestrates; it does not invent calculations.
- Structured facts belong in structured data stores.
- RAG is for unstructured evidence such as filings, research reports, and management commentary.
- Technical analysis uses OHLCV and deterministic indicators rather than screenshot interpretation.
- New technology is added only when a real problem requires it.
