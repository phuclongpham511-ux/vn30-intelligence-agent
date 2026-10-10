# Woofi — Domain Context

### Technical Stock Detail integration — 2026-10-10

Stock Detail shows delayed PROVISIONAL Technical Insights above the chart.
Its latest lookup selects persisted, actually accepted sessions; a later pending
job does not hide accepted evidence, while retraction withholds the withdrawn
result without silently falling back. Unknown coverage has no invented date.
The evaluated session and source-check timestamp remain visible. Up to three
unchanged D5 insights, a genuine no-meaningful-change result, or explicit
incomplete/unavailable states are shown. Minute/focus revalidation reads cached
backend evidence only, clears old results and rejects obsolete requests.
PROVISIONAL stays separate from VERIFIED; D1/D4/D5 algorithms are unchanged.
See docs/TECHNICAL_STOCK_DETAIL_V1.md.

## Product purpose

Woofi helps active retail investors identify which changes deserve attention across Vietnamese equities.

North Star:

> Do not give users more data. Help them know what deserves attention.

The product is a research and monitoring system, not an automated trading or recommendation engine.

## Core domain language

### Market discovery and research feeds

Stock discovery uses SSI FastConnect ordinary-equity metadata across HOSE, HNX and UPCOM. Persisted/watchlisted stocks are personalization, not the supported universe. A separate metadata snapshot refreshes daily in the canonical ingestion worker (failed attempts retry after 15 minutes); HTTP discovery reads the cache. Unknown instrument types are excluded. Stock records and market history remain lazy.

News uses Company / Industry / Market Brief. A deterministic headline/read-layer mapping preserves older Article/Story records and provenance. Company, Industry and Market Brief are semantic research archives and retain single-source reporting with explicit source counts. Hot Topics requires at least two independent publisher groups in one recent Story (re-ingestion never adds a mention) and a usable same-Story source thumbnail; Hot Topics ranks publisher breadth first, capped article activity second, then latest activity. This is publisher attention, not Materiality or corroborated truth. Company requires a primary-subject identity in the current SSI ordinary-equity cache, never legacy fixtures or arbitrary organization names. Broad macro/market and primary sector framing take precedence over incidental tickers. Vietnamese publishers are the only active News sources; removed foreign publisher history remains stored but excluded from current feeds and cluster evidence. Recognized foreign subjects require explicit Vietnam relevance or a primary listed issuer. Headline classification and company-name coverage remain partial.

Community shows a short evidence-grounded title, a bounded representative sentence and discussion/source/time metadata. Terms, complete bounded evidence, original URLs and source status remain inspectable in disclosures. Original source text may retain its source language; interface labels remain English. Same-day Vietnam filtering, native identities, review state and source isolation are unchanged; Community Momentum remains unimplemented.

Explore is the market landing page: latest SSI VN-Index summary, multi-publisher Hot Topics, then ten-row equity discovery. VN30/VN100/HNX30 filters use SSI indexList + securitiesByBoard(index) memberships persisted separately and refreshed daily by the canonical worker; cached failures retain their source/as-of/status. Current market presentation is separate from completed daily analytics: live prices never enter MA/RSI, replay or Technical Materiality. Demand-leased SSI trade streaming serves only visible Explore results, followed Watchlist symbols and the open Stock Detail ticker; search remains metadata-only. A bounded process cache shares quotes, with dated reference metadata loaded once per Vietnam day and a limited one-minute bootstrap for quiet symbols. VN-Index uses a separate ten-second current one-minute read cache and may legitimately show today; completed daily OHLC still admits only previous completed sessions. SSI indexSummary currently lags at the previous session, so current index aggregate volume/value stay unavailable rather than borrowing old totals. The hero links to completed historical index research. Fresh dated source evidence plus Vietnam session windows select 07_watching while active; break/closed/unconfirmed use bullish/bearish/neutral from observed direction. Runtime LLM token usage for market refresh is zero.

News navigation is Industry → Company → Market Brief → Community Pulse. Hot Topics is a promotion layer on Explore; it does not hide matching stories in News categories. Compact search shows typed matches or up to eight browser-local recent ticker selections with individual remove and Clear history controls, never the full universe dropdown. Watchlist membership and review semantics are unchanged.

Community Pulse explicitly selects Today or Last 24 hours; no automatic fallback relabels yesterday as today. Open web sessions trigger coalesced background ingestion through `/ingestion/refresh`, respecting persisted source cadence. For source freshness without an open browser, run `uv run python -m scripts.ingest_data --watch`. Read endpoints continue to read persisted evidence. Overnight empty Today and stale sources after stopping the worker are honest states, not deleted content.
When the web shell opens, it records durable due-source News refresh intent and requests a coalesced convenience cycle for other domains. News acquisition requires the canonical worker; persisted data remains readable while it runs.

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

SSI product Market Data qualification has PASSED. SSI Market Data Provider Integration
V1 uses the official SDK 3.2.1 raw authenticated transport, dynamic security metadata,
bounded pagination and existing deterministic analytics. SSI is the default market
provider with no silent fallback; Fundamentals remain temporarily on vnstock/VCI.
SSI officially confirms Historical Daily OHLC is adjusted for cash dividends,
stock dividends/bonus shares, additional issuance and rights offerings. Product
normalization remains prices VND ×1 and volume shares ×1; only bars dated before
today in Asia/Ho_Chi_Minh are eligible for daily analytics, even after market close.
Historical charts/current indicators use the currently available adjusted series.

Provider confirmation recorded 2026-10-07: Historical API returns the currently
stored version at query time. SSI provides no detailed adjustment formulas/factors,
record-level revision timestamps/version IDs/correction notifications, or historical
vintage retrieval. Raw/unadjusted history is unavailable; future development intent
has no implementation date. The private adjustment method is a known limitation,
not an open reverse-engineering task. SSI remains APPROVED for product market data,
but current SSI history alone is NOT ADMISSIBLE for the official PIT-sensitive
Technical benchmark. The blocker is dataset provenance, not the implemented
Technical Engine V0. Technical Materiality V1 calibration remains PAUSED/BLOCKED.

Preferred research path: a certified historical source, or deterministic versioned
raw-price + effective-dated, cutoff-visible corporate-action reconstruction, with
session continuity and provenance verified. Future SSI raw data must be re-qualified.
Long-term SSI snapshot retention requires explicit storage-right confirmation
(currently UNRESOLVED); a future archive cannot recover 2020–2024 vintages. The frozen
benchmark frame/cohort, protected cases and sealed 2025–2026 holdout remain unchanged.
See [source decision](research/provenance/technical_data_readiness_v1/SOURCE_DECISION.md).

### Bollinger Technical Events V1 — 2026-10-07

BB(50,2) uses 50 completed daily closes: SMA50 +/- two sample standard deviations
(ddof=1); first 49 values remain null. Stock research's existing chart has an
optional BB control, sharing SMA50 as its middle line and exposing backend values
in the crosshair legend and raw table. Live quotes never enter this calculation.
`bollinger_lower_reversal_volume` / `bollinger_upper_reversal_volume` require an
inclusive low/lower or high/upper touch within 0–2 completed observed sessions,
then a strict close back inside the current band and above/below the previous close.
The confirmation session is the event date; its positive volume must have the
existing trailing unusual-volume midrank >= .95 (default replay: 60 prior sessions).
Zero-width bands cannot emit events. At most one event per direction/session is
emitted; a touch can reconfirm within its short window, with existing recurrence
Novelty rather than automatic transition novelty. Significance reuses price
abnormality context; volume is evidence/eligibility, not an extra scoring channel.
These are provisional technical observations, not return predictions or trade
recommendations. PIT/admission/calibration status remains unchanged; no Watchlist
delivery or chart event markers are introduced.

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

Top Stories exposes one earliest-published representative (unknown dates sort last), with
additional publisher evidence behind a disclosure; ranking/diversity is unchanged.
RSS media/enclosure metadata or an image in the feed description/content may provide a thumbnail; article bodies are not retained. Sector is demoted to Advanced
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

### Corporate-action-aware Technical context V1 — 2026-10-08

SSI adjusted history remains authoritative for return, MA, RSI, Bollinger Bands
and volatility. Verified corporate actions add inspectable context after scoring;
they never suppress events, assert causation, change Significance/Novelty/Base,
thresholds or volume rules. V1 matches only the exact effective/ex-date session,
distinct from announcement, record and payment dates. Unresolved ex-dates do not
match. Actual receipt (`observed_at`) gates both current enrichment and replay;
source publication alone cannot backfill knowledge. Corrections append source
versions; late notices append timestamped context updates without rewriting the
original scored event. Incomplete source coverage means UNKNOWN when no match
is observed, never a certified absence. Initial source is a curated verified
dataset plus an explicit import/service seam, not an automatic corporate-action
feed or a live Technical UI. Practical knowledge-time handling is an operational
constraint; exact vendor PIT is not a general Product blocker. Official Materiality
calibration and historical vendor-vintage certification remain outside this V1.

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

## Product branding and localization

The user-facing product is **Woofi**. Repository and internal technical names remain unchanged; VN30 remains a legitimate market index. The supplied Woofi wordmark is separate from the existing white-wolf state mascots.

Product chrome supports English and Vietnamese through a typed frontend dictionary/context. A saved browser preference takes precedence; otherwise Vietnamese browser locales select Vietnamese and other locales select English. Headlines, excerpts, Community themes/evidence, company and publisher names, ticker symbols and quotes retain their source language. Localization changes presentation, never numerical ground truth or research semantics.

### Technical EOD operational persistence — 2026-10-10

The owner reports direct SSI permission for free authorized API use, historical
storage/retention, derived analytics, third-party redistribution and commercial
use within Woofi. This is owner-reported authorization, not independently
reviewed legal documentation; the former assumed storage-right blocker is removed.

Qualified PROVISIONAL EOD jobs now use the configured database and canonical
ingestion worker. Only metadata receipts persist before acceptance. Independent
HOSE calendar/publication evidence, matching fresh authenticated SSI reads at
least six hours apart, and a second request at least 24 hours after the qualified
publication remain mandatory. Atomic versioned snapshots preserve normalized
evidence and existing D1/D4/D5 outputs. Later source revisions retract affected
provisional outputs; corrected versions require requalification. Expiring fenced
leases and durable due times support restart recovery and cache-first operation.

The read-only `/technical/{ticker}/daily/operational?session=YYYY-MM-DD` endpoint
serves accepted PROVISIONAL packets with explicit session, assurance, receipts,
version and revision-check freshness, or unavailable/incomplete diagnostics.
HTTP does not acquire SSI data or score packets. The separate VERIFIED gate is
unchanged. Operational tables are excluded from verified benchmarks and
certification; this slice does not reopen calibration or protected historical cases.
Real FPT data produced a durable accepted provisional packet for 2026-10-08.
The 24-hour publication gate prevents same-day provisional admission. Future
qualified-session acquisition, wider ticker scheduling, process supervision and
Stock Detail integration remain rollout work; see docs/TECHNICAL_EOD_PERSISTENCE_V1.md.

News tabs display Industry → Company → Market → Community Pulse (Ngành → Doanh nghiệp → Thị trường → Cộng đồng). The visible Market label replaces Market Brief; internal `briefing` / `MARKET_BRIEF` identities remain unchanged. Category tabs identify the view without repeated category headings below them.


### News refresh and thumbnails V2 — 2026-10-08

Twenty public Vietnamese publisher RSS feeds are enabled. Ten additions were checked
against non-empty recent live feeds; related publishers share a publisher group.
News lists show one earliest-published representative per existing lexical Story,
with additional original reporting behind a disclosure. Matching remains approximate,
with conflicting-number protection; publisher attention is not factual corroboration.
Archive rows require a source image and sort by latest publication in a Story. Their read window is 72 hours
from publication (first-seen only when publication is absent), without deleting stored
evidence or renewing age on duplicate ingestion. `/news/feed/page` exposes bounded
pages and an `as_of` timestamp so later arrivals do not shift a Show more sequence.
The UI initially requests 12 Stories. Only explicit Show more reveals the next 12;
minute refreshes update only already-revealed pages. New category/filter selection
starts a fresh first page. Source images stay inside their own Story; missing/broken
images hide the news item, per user preference. No illustration substitutes a source photo.
Web sessions request refresh at opening and every five minutes. News refresh intent is
durable and worker-owned, with adaptive per-source scheduling described below. News,
Hot Topics and stock News re-read each minute; no OS supervisor is introduced.


### Technical supervised EOD pilot V1 — 2026-10-10

Technical supervised acquisition is a separate, explicitly configured single-ticker
pilot. It extends independently qualified HOSE evidence, stores metadata receipts
between reads and reuses the existing provisional snapshot producer. Each cycle
may obtain at most one bounded SSI history scope; HTTP remains a persisted read.
The six-hour matching-read and 24-hour publication gates, VERIFIED separation
and D1/D4/D5 behavior remain unchanged. Missed runs recover from durable due times,
leases and receipts; revisions retract affected provisional snapshots. See
docs/TECHNICAL_SUPERVISED_EOD_V1.md for scope, supervision and remaining limits.

### Adaptive News ingestion V1 — 2026-10-08

Twenty RSS sources retain their evidence and publisher groups. Six configurable
financial/stock publishers use 30-minute weekday-session cadence, standard sources
120 minutes; lunch/off-hours use 240 and weekends 360 minutes. Asia/Ho_Chi_Minh
09:00–11:30 / 13:00–15:00 on weekdays is a scheduling heuristic, not a holiday
calendar or a guarantee that an exchange is open. Config lives in src/news/schedule.json
and each registry entry's scheduling_priority. Legacy alternate registries retain
explicit fixed cadence when that field is absent.

The canonical worker wakes each minute, fetches at most six sources per cycle and
uses two shared database-leased fetch slots. Source leases, fenced writes, failure
backoff and refresh intent survive process restart. No immediate transport retry:
failed attempts back off 30, 60, 120… minutes, capped at 24 hours. Socket timeout is
20 seconds, feed bytes/items remain bounded. Lease expiry is ten minutes.

News/Hot Topics/illustrated Quick News read worker-built persisted research rows.
Due/stale visits only record deduplicated refresh intent; they never fetch upstream
or rebuild projections. No worker means pending intent plus cached/empty data, not
a completed refresh. Source status reports pending requests and worker requirement.
Dirty Story markers survive interruption between evidence and projection commits.
Only changed Stories are projected; universe refresh can reclassify existing rows.
Empty/duplicate-only cycles reuse the projection. Recency and 72-hour eligibility
are filtered cheaply at read time; a 96-hour derivative retention buffer supports
ordinary pagination snapshots. Cache caps at 10,000 Stories; full original evidence
stays stored. Raw /news/latest, unillustrated /news/top and detail remain evidence
reads, not low-cost visual cache routes. See docs/ADAPTIVE_NEWS_INGESTION_V1.md.
