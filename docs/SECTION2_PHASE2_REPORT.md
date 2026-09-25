# Section 2 — Phase 2: Historical evaluation framework

## Status

Implementation, real-data pilot and the first human review batch are verified.
**Phase 2 framework/pilot acceptance gates are satisfied**, subject to the source
limitations below. Three explicit user labels are saved; no labels were invented.
This is not formal accuracy validation, proof of vendor point-in-time vintages,
or production readiness. Phase 3 has not been started.

Baseline: `cf12b35c4256014c0d9e6a1b1bff272b1ab0e311` on the actual repository.
Materiality V0, Section 1.6 analytics/schemas/providers/services, root main.py,
dependency lockfiles and all frontend files remain unchanged. Exactly one FastAPI
application remains; MaterialitySlot is still a placeholder.

## Observed source audit (2026-09-25)

The first request used 2000-01-01 as a configurable discovery lower bound.
The installed community SDK reported an approximately eight-year daily-history
limit. That first audit failed for FPT and VN30 and is retained locally; it is not
claimed as successful coverage. The pilot was then explicitly requested from
2018-09-26 through 2026-09-24, excluding the current incomplete session.

| Stream | Earliest | Latest | Valid sessions |
| --- | --- | --- | ---: |
| FPT | 2018-09-26 | 2026-09-24 | 1,995 |
| HPG | 2018-09-26 | 2026-09-24 | 1,995 |
| TCB | 2018-09-26 | 2026-09-24 | 1,995 |
| VIC | 2018-09-26 | 2026-09-24 | 1,995 |
| VN30 | 2018-09-26 | 2026-09-24 | 1,987 |

Source: vnstock 4.0.2 / VCI. Eight VN30 rows failed the existing OHLC validity
checks and were quarantined with raw values and reason codes in the audit.
No price repair or interpolation was performed. Benchmark index levels are
stored in points, undoing the stock adapter's VND scaling; returns use the shared
market_snapshot implementation. Stock prices remain VND and volume remains shares.

Each stock has 92 weekday gaps over this interval, but there is no verified exchange
calendar, so these are **not** claimed to be missing trading sessions. Normalized
stock dates are unique. The existing stock normalizer collapses identical raw
source duplicates; their raw count is unknown. Conflicting duplicates fail the
provider request. The evaluation store rejects duplicate normalized keys.

Each pilot stock supplies annual financial periods 2022–2025, without actual
publication timestamps. These 16 records are cached for audit and excluded from
replay. The four news records are explicitly synthetic and excluded. No reliable
historical sector classification/comparison stream is available.

Dataset: `20260925T063757835331Z-1ae5044146b8`.
SHA256: `1ae5044146b8e5bfa339b3ac72022ffbbc4314d3555e4f9628eeddea985f7ef8`.
9,987 normalized observations: 7,980 stock bars, 1,987 benchmark bars, 16 annual
financial records, and four fixture news items.

## Point-in-time contract and limits

HistoricalObservation separates observation_time from available_at and reuses
MarketBar/TechnicalBar/FundamentalPeriod/NewsItem payloads. Timestamps must be
aware; identity mismatches are rejected. Unknown availability remains null.

The daily source does not expose actual publication instants. The pilot models
completed bars as available conservatively at **23:59:59 UTC+07** on the trading
date, explicitly marked `end_of_day_assumption`. This supports end-of-day replay;
it does not establish intraday/session-close publication latency.

Downloaded prices are a current vendor vintage, not an archived vintage from each
historical date. Adjustment semantics remain **unknown**. Later revisions or
retrospective adjustments cannot be ruled out. No-lookahead tests establish the
algorithm's chronological integrity; they do not prove the vendor's data vintage
was point-in-time. Every case carries these limitations and adjustment status.

Financial reporting periods are never converted to guessed publication dates.
Fundamentals/news replay is not enabled, even if a manually imported timestamp
exists; expansion requires a separately verified stream. Excluded inputs are
persisted separately in excluded_observations.jsonl with explicit reasons.

Replay processes available market records chronologically, computes existing
analytics on the prefix only and never calls a provider. Late/revised out-of-order
market observations are rejected rather than rewriting earlier states. A fixture
anywhere in an indicator prefix marks its derived candidates as fixtures.

Benchmark context requires both the stock's current and previous trading dates
to have valid matching benchmark records available by replay_time. Missing,
late, fixture or invalid benchmark data yields null; no nearest-date matching or
forward-fill is used. Sector and economic magnitude remain null.

## Context mapping and event memory

Version: `empirical-v0.1`. A configurable trailing window defaults to 252 sessions
with 60 required historical values. The current row is never in its reference
sample. Ties use empirical midranks `(less + equal / 2) / count`.

- Price strength: percentile of absolute daily return.
- Volume strength: upper-tail percentile of volume.
- MA-cross strength: percentile of absolute MA20/MA50 spread.
- RSI-entry strength: percentile of distance of RSI14 from 50.
- Market-relative strength: percentile of absolute stock-minus-VN30 return.
  Return residuals are not passed to volume events.

Raw return, return/volume z-scores, relative volume, trailing annualized volatility,
MA spread, RSI distance, excess return and sample counts are retained separately.
Z-scores use only preceding observations and never serve as Novelty. Constant
samples yield null z-scores, while empirical ranks remain defined. No V0 weights,
novelty boundaries, or event thresholds were changed.

Event memory stores previous emitted events by ticker/type and calculates calendar
days elapsed. Lookup occurs before recording the current event; a future/current
memory timestamp is rejected. State-transition behavior is inherited from V0.

The primary era starts a new history/context/memory sequence. Older history is
replayed separately as stress data rather than mixed equally into recent ranks.
Warm-up observations may be unassigned to an evaluation split and are not queued.

## Coverage-based pilot splits

The date configuration was selected after the audit, not by a blind ratio split.
Change primary_start and explicit periods to choose a different recent window.
This pilot has seven recent years and approximately one earlier stress year.

```json
{
  "primary_start": "2019-09-25",
  "calibration_period": {"start": "2020-01-01", "end": "2023-12-31"},
  "validation_period": {"start": "2024-01-01", "end": "2024-12-31"},
  "holdout_period": {"start": "2025-01-01", "end": "2026-09-24"},
  "stress_period": {"start": "2018-09-26", "end": "2019-09-24"},
  "lookback_sessions": 252,
  "min_history": 60
}
```

Overlapping/reversed splits are invalid. Holdout cases are stored in a separate
holdout_cases.jsonl, never enter queues or human label imports, and have no score
distribution in development summaries. They have not been used to tune anything.
This is a workflow boundary, not filesystem access control. A later formal holdout
assessment requires its own explicit workflow; the current importer rejects it.

## Real replay and review queue

Run: `c3e0725bf6fa3bfa` under the dataset's runs directory.

| Measure | Result |
| --- | ---: |
| Candidates | 15,418 |
| Scored / excluded | 15,403 / 15 |
| Abnormal price / unusual volume | 7,492 / 7,500 |
| RSI entries / MA crosses | 275 / 151 |
| Calibration / validation | 8,218 / 2,057 |
| Holdout / stress / unassigned | 3,511 / 1,550 / 82 |
| Similar event within five days | 14,908 |
| Human review queue | 30 |
| Saved human labels | 3 — approve 3, reject 0, modify 1 |

The 15 exclusions have no available significance channel during warm-up. Every
case is flagged for unknown adjustment semantics and modeled daily availability.
No pilot case triggered the diagnostic `abs(daily_return) >= .15` flag for suspected
corporate-action/extreme moves. That flag is only a review diagnostic, not a price
adjustment, permanent detector threshold, or changed materiality score. Corporate
actions can occur below this heuristic; unknown adjustment flags remain on all cases.

The queue covers nine RSI cases, ten volume cases, six MA crosses and five price
cases, drawn round-robin from high scores, low/borderline scores, channel
disagreement, exclusions, repetitions, rare event types and hash-based controls.
The suspected-corporate-action stratum is empty in this pilot. Stable hash ordering
provides reproducible pseudorandom controls without runtime randomness.

The large candidate count is an observed V0 behavior: supplied normalized inputs
produce price/volume candidates each eligible day, even at low percentiles. This
phase reports that behavior instead of secretly tuning thresholds. A small MA
cross can also disagree sharply with the market-relative channel; these cases are
intentionally exposed for human review.

Each queue item includes scores, timestamped evidence, raw/normalized context,
provenance, limitations and the original complete ReplayCase. HumanReview is a
separate append-only versioned label; original cases never change. All verdicts,
including uncertain, remain available in reviewed_benchmark.jsonl. Phase 3 must
select appropriate labels and keep uncertainty/exclusions visible; this file is
not an automatic accuracy certification.

The user explicitly supplied the first batch, saved as `human-v1` with a UTC
recording timestamp. Notes are preserved verbatim in human_reviews.jsonl and
joined with unchanged original cases in reviewed_benchmark.jsonl:

| Case | Case ID | Verdict | Attention | Original Base |
| --- | --- | --- | ---: | ---: |
| A: FPT, RSI entry, 2020-05-13 | 4595990fa38acf5d85d052ca | approve | 3 | 1.000000 |
| B: VIC, volume, 2019-06-19 | 0450ef21c7b28fec90921a48 | reject | 0 | 0.416667 |
| C: VIC, MA cross, 2020-06-19 | 78f6f7d2bd6ccdad7c0f4c7d | modify | 1 | 0.830914 |

User notes:

- A: strong multi-signal event; retain adjustment-basis-unverified flag.
- B: zero significance but Base inflated by novelty/confidence; candidate should not be material.
- C: valid MA cross, but Base is inflated by market-relative price movement that is not directly aligned with the tiny crossover.

C's event type remains ma_cross; the user modified attention, not the event type.
No engine scores, thresholds or candidate exclusion decisions were rewritten.
`adjustment_semantics_unknown` and `adjustment_basis=unknown` remain on all three
cases. SHA256 checks before/after import prove replay_cases.jsonl,
holdout_cases.jsonl, review_queue.jsonl and run_manifest.json are unchanged;
verification is recorded in human_batch_001_integrity.json.

The summary now reports one approve, one reject and one modify, with original
score distributions by attention level. The two disagreements are recorded as
inputs for future calibration, not instructions to tune V0 during Phase 2.
Only 3 of 30 queued cases are reviewed. This satisfies the initial reviewed-batch
gate but is far too small for formal accuracy claims. All labels and benchmark
data remain local under Git-ignored data/evaluation. No synthetic test label is
stored in the real pilot; test labels exist only in pytest temporary directories.

## Commands and artifacts

All historical data, caches, cases, queues and labels live under the existing
Git-ignored data/evaluation directory. No large dataset is committed.

```powershell
uv run python -m scripts.audit_historical_data FPT HPG TCB VIC --start 2018-09-26 --end 2026-09-24
# build_historical_dataset offers the same audited ingestion entry point.
uv run python -m scripts.replay_materiality <dataset-directory> --config <config.json>
uv run python -m scripts.build_review_queue <run-directory> --size 30
uv run python -m scripts.import_human_reviews <run-directory> <human-authored-labels.jsonl>
uv run python -m scripts.report_evaluation <run-directory>
```

Dataset manifests include checksum, observed coverage, sources, requested range,
limitations, adjustment basis and quarantine records. Loading verifies integrity.
Existing datasets/runs/queues are protected against accidental replacement.
Review revisions append with a new review_version; metrics use the latest label
per case and retain all previous labels. Provider failures are reported, never
replaced with fake historical observations.

## Verification and exit gate

- Backend: **111 passed** (90 existing + 21 historical evaluation tests).
- Frontend: **9 passed**; typecheck and production build passed, without changes.
- Real audit, replay, queue generation and reporting commands completed.
- Offline CLI integration test exercises dataset creation, replay, queue, human
  label import, joined benchmark export and refreshed metrics.
- Tests cover causality, exact benchmark dates/availability, missing channels,
  event memory, determinism, fixture contamination, split/holdout isolation,
  immutable label separation, duplicate rejection, unknown publication times,
  dataset hashes, quarantine, and provenance persistence.
- Existing Starlette/httpx test-client deprecation warning remains; no dependency
  changes were introduced.

2.2A, 2.2B and the initial 2.2C human-review batch are complete. 2.2D remains
deferred because publication/sector data has not been proven trustworthy.
The exit artifact is V0 plus real historical replay, three user-reviewed cases
and a separate untouched holdout. No Phase 3 tuning or production integration
has been started. Source-vintage and adjustment limitations remain unresolved
and must stay visible in future calibration work.
