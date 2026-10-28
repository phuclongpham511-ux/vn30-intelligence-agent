# Section 2 — Phase 1: Materiality Engine V0 integration

## Repository and preservation

Integrated into the actual repository starting at main commit
`4228b7367ce08ada02d3a68e441c167ea5545e8b` (Section 1.6).
The original standalone source remains untouched in the sibling
`vn30_intelligence_agent` workspace. This checkout is `vn30-intelligence-agent`.
No standalone README, root package initializers, dependency manifest, or
application entry point was copied over the existing architecture.

Exactly one root `main.py` and one FastAPI application remain. Existing routers,
providers, services, schemas, analytics, dependencies, and frontend files are
unchanged. MaterialitySlot remains the existing placeholder. No production API,
persistence, ranking, preferences, AI, or frontend integration has been added.

## Compatibility changes from the empty-workspace version

- Removed its parallel `Observation` schema. Market detectors/services take the
  existing `TechnicalBar`; fundamental detectors/services take `FundamentalPeriod`.
  Ticker, source, currency, dates and annual periods come from these schemas.
- Reused `technical_history`, `market_snapshot`, and `fundamental_history`.
  MA/RSI and YoY growth are not reimplemented. Price-event return evidence comes
  from the existing snapshot calculation, with both closing prices preserved.
- Replaced `revenue_growth` / `net_profit_growth` inputs with repository fields
  `revenue_growth_yoy` / `net_profit_growth_yoy`. Retained fraction units, VND
  prices and share volumes. Bank revenue, margins and ROE remain null.
- Replaced the arbitrary `comparison_basis` string with native annual periods;
  comparison requires adjacent years. Reject mixed tickers, sources, currencies
  and reversed/equal observation dates. Callers must supply adjacent trading
  observations; the engine does not infer a trading calendar or accounting restatements.
- Moved synthetic provenance to explicit keyword-only `is_fixture` on detection
  and service calls, applying to all supplied observations/context. Existing market
  and financial schemas have no fixture flag; the preview always passes True.
  News remains unsupported in V0, including the existing fixture news provider.
- Preview now generates native MarketBar/FundamentalRecord inputs and runs the
  existing analytics instead of hand-authoring indicator observations. Symbol
  normalization/validation uses the existing SymbolRequest contract.
- Expanded tests for native schemas, identity/period validation, analytics reuse,
  financial null handling and preview output. Retained independent immutable
  dataclasses for materiality-only domain concepts; no duplicate data schemas.

## Scoring and service contract

Significance averages only available own-history, market-relative,
sector-relative and economic-magnitude channels. Missing channels do not become
zero. Finite normalized inputs are clamped to [0,1] before component scoring;
clamping is flagged. Non-finite inputs and invalid elapsed-day values are rejected.

Novelty is 1 for transitions or unavailable similar-event history; otherwise it
is .25 through day 1, .50 through day 5, .75 through day 20, and 1 thereafter.
Unavailable event history is flagged. Confidence is source quality times
event-required completeness, with zero confidence and exclusion for fixtures.
Base is the arithmetic mean of S/N/C for eligible candidates.

No significance evidence, no raw evidence, fixtures and all news produce explicit
exclusion reasons and a null Base. Unavailable significance is null, not zero.
This is the intentional representation of the specification's non-score case.
Every result retains its candidate, raw evidence, components and reason codes.

Detectors require all fields needed by that event, so emitted completeness is 1.
Direct candidate evaluation supports partial completeness and flags it. Missing
unrelated financial fields do not reduce confidence. Normalized strengths must
be supplied externally; there is no hard-coded price or volume material threshold.
Technical transitions without strength remain inspectable but excluded.
Gross and net margins can use separate context keys (`gross_margin`, `net_margin`).

MA equality followed by separation counts as entry across the boundary; touching
alone emits nothing. RSI entry is strictly above 70 or below 30. Direction refers
to observed movement, not a return forecast or trading recommendation.

The engine has no network calls, database writes or user preference lookup.
Fundamental `observed_at` is a reporting-period label, not a known publication
instant. Phase 2 must supply point-in-time availability and historical calibration.

## Verification

On Python 3.12.10, Node 24.16.0 and npm 11.13.0:

| Check | Result |
| --- | --- |
| `uv --system-certs sync --frozen` | Passed, existing lockfile unchanged |
| `uv run pytest -q` | 90 passed: 57 existing + 33 Materiality |
| `python -m scripts.preview_materiality FPT` (repository virtualenv) | Exit 0; 8 candidates, all 7 event types |
| `npm ci` in frontend | Passed, lockfile unchanged |
| `npm test` | 9 passed |
| `npm run typecheck` | Passed |
| `npm run build` | Passed; production routes generated |

Pytest reports one dependency deprecation warning about Starlette's httpx-based
test client. It does not fail tests; no dependency changes were needed.

Preview results: four market/technical candidates have S=.8; four fundamental
candidates have S=.6. All have N=1, C=0 and Base=null because all preview evidence
is explicitly synthetic. The eight candidates include both gross and net margin
changes. Non-fixture scoring and the Base arithmetic are verified separately by tests.

No live data smoke, historical replay, or calibration is claimed by this phase.

## Files changed

- `README.md` — current status, preview command, test count and report link.
- `src/materiality/__init__.py` — exports in the existing reserved package.
- `src/materiality/models.py` — materiality domain models and input bounds.
- `src/materiality/scoring.py` — deterministic components and Base.
- `src/materiality/detectors.py` — native market/fundamental candidate detectors.
- `src/materiality/service.py` — pure evaluation entry points.
- `scripts/preview_materiality.py` — offline, native-analytics preview.
- `tests/test_materiality.py` — scoring and integration regression coverage.
- `docs/SECTION2_PHASE1_REPORT.md` — this report.
