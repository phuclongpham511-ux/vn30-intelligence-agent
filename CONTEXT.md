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

Completed:
- data and analytics foundation;
- dynamic ticker onboarding;
- financial visualization foundation;
- Materiality Engine V0;
- historical evaluation framework;
- first human-reviewed historical batch.

Current work:
- expand the reviewed benchmark before formal calibration.

Not yet production-integrated:
- personalized materiality;
- Attention Budget;
- live materiality UI;
- real news intelligence;
- portfolio context;
- thesis tracking;
- RAG;
- AI/LLM agent layer.

## Engineering principles

- Deterministic Python computes financial metrics and Materiality inputs.
- AI interprets or orchestrates; it does not invent calculations.
- Structured facts belong in structured data stores.
- RAG is for unstructured evidence such as filings, research reports, and management commentary.
- Technical analysis uses OHLCV and deterministic indicators rather than screenshot interpretation.
- New technology is added only when a real problem requires it.
