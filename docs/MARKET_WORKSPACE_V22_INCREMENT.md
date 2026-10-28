# Market Workspace V2.2 — bounded local implementation

Base: `cb5979fa5e1717d4b634a98490cc391f6da50aa5` on the existing
`codex/woofi-market-board-correction` checkout. The pre-existing uncommitted KL/GT
presentation, provider evidence handling, tests and qualification documents are
retained in this checkpoint. No component or research restart.

## Application changes

- `frontend/lib/priceState.ts` is the shared exact-value resolver for CEILING,
  ADVANCING, REFERENCE, DECLINING, FLOOR, STALE, UNAVAILABLE, UNKNOWN and ERROR.
  `app/price-state.css` owns the purple/green/yellow/red/cyan and neutral tokens.
  QuoteMap Board prices, LivePrice and TickerMovement use the shared system.
  The percentage Heatmap retains its five-bin legend and equal-area semantics.
- Limits require matching instrument/date, explicit compatible VND quote and
  limit units, qualified provenance and ordered reference/limits. Observation
  limits require the same valid source timestamp. Separately qualified trading-day
  limits require the same original reference without borrowing a tick timestamp.
  Missing qualification falls back to qualified ordinary direction, never an
  inferred limit. Stale/error states stay neutral. Foreign-instrument values are
  withheld by the actual LivePrice/TickerMovement renderers.
- `src/services/market_summary.py` normalizes one original SecuritiesSummary pair
  without I/O. Original `totalMatch`/`totalMatchValue`, raw date, source, retrieval
  time, exact decimal strings, matched scope and individual metric validity remain
  inspectable. Completeness is separate from freshness, finality, units and rights.
  The function does not grant qualification or fabricate source time; its evidence
  is not directly publishable as verified live activity. Amount parsing is bounded.
  No price×volume calculation, summary acquisition/cache, worker or API is added.
  Existing UI can already render externally qualified activity; normalization alone
  must not manufacture the qualification receipt needed to activate it. Date-only
  summaries still need the separately reviewed temporal publishing contract.
- Optional industry organization reuses existing compact Board tables, source
  controls and numeric sorting. It accepts only explicitly labeled synthetic
  categories for DEMO-numbered tickers in a replay build. Names/counts and an
  Unclassified group are shown; no industry returns are computed. Ordinary Board
  remains default. Switching to Heatmap preserves Heatmap rendering. Real ICB
  records are not assigned to demo categories or activated for product use.
- `/demo/market` is gated by `NEXT_PUBLIC_WOOFI_VALIDATION=replay`. It uses a fixed
  clock, invented DEMO tickers, independent synthetic matched totals, nine state
  examples and an unqualified-unit toggle. Production-bound builds return not-found
  at this route and cannot enable the synthetic industry option.

## Validation

Focused frontend regression: **79 passed, zero failed** across price-state,
industry-preview, trading-activity, QuoteMap, localization, research presentation,
market-board, market-workspace and live-market tests. Typecheck PASS. Pure Python
summary tests: **20 passed**, using the preserved actual ACB October 16 response,
not a new provider read. Existing broad backend campaigns were not repeated.

The stale-zero localization assertion now requires neutral stale rendering; a
separate fresh exact-reference rendering test requires yellow. Existing synthetic
limit fixtures now supply explicit VND units, a deterministic clock and coherent
reference/change values. Assertions were not weakened to accept unsafe limit data.

Evidence directory:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/market-v22/`.

Build/browser outcomes and final development SHA are recorded in that directory's
`FINAL_REPORT.md`. Do not interpret automated rendering or a successful build as
interactive browser acceptance. New screenshots must show the new checkpoint;
an older preview screenshot is not V2.2 evidence.

## Unchanged qualification and production gates

Reuse the five saved SSI reads indexed in
[SSI_MARKET_DATA_QUALIFICATION.md](SSI_MARKET_DATA_QUALIFICATION.md). No request
was repeated. Actual KL/GT units/scope/timing and rights, limit units/day-effectiveness,
and ICB rights/taxonomy/effective dates remain unqualified. No new live data family
was activated. The ordinary unsupported KL/GT state remains unavailable; the
synthetic qualified-contract values are DEMO only. Live session acceptance remains
PARTIAL and is not certified by the saved completed-day response.

No production/Supervisor Stop, Start, installation, source-pin change, Collector,
SQLite mutation, forced SSI fetch, cooldown reset, push or deployment. Technical
Pilot OFF and FPT PAUSED remain required and were not modified.
