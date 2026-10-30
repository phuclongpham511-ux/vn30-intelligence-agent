# Financial Research experience V2

Base `c2dae7ff100b2ab86db60731a63232a04d96c1cf`, continuing the same development
branch. Source implementation complete; live financial qualification and actual
visual acceptance remain separate. No new provider request or production change.

## Existing reference reviewed

Reused `docs/FUNDAMENTAL_ANALYSIS_V1.md`, `docs/STOCK_DETAIL_UI_V1.md` and the saved
October 13 screenshots under `C:/Users/PC/.codex/tmp/woofi-fundamental-v1-20261013/`:
`sstock-vnd-business-desktop.png`, `sstock-fpt-growth-desktop.png`,
`sstock-vnd-statements-desktop.png` (plus the documented mobile research limits).
No new SStock visit, scraping, database, proprietary assets or wording copied.

Observed strengths applied: five research destinations, paired structural charts,
amount bars with clearly separate rate axes, period/unit controls and source-parent
statement grouping with sticky headers. Woofi retains its typography, tokens,
EN/VI, existing Stock Detail tabs and source/rights guards. We do not reproduce
SStock scores, valuation data, pricing overlays, or infer issuer filings from it.

## Product mapping

| Destination | Implemented | Data boundary |
| --- | --- | --- |
| Business picture | Paired historical asset/funding stacks, funding ratio overlay, supported metric observations and expandable existing ratio/cash-flow research | Asset components are a partial subset, not 100% composition. No inferred residuals. Funding stacks total liabilities and total equity; borrowings/minority interests are not double-counted. Negative/incompatible stacks are withheld. |
| Growth drivers | Revenue/PAT or bank operating-income/PAT bars with existing YoY lines on a separate percent axis, quarterly-result panel, performance/profitability metric groups, existing exact-prior-year change table | Quarterly panel requires Quarterly selection; annual/TTM not relabelled. Operating-margin gap is explicit. No price overlay or causal/speculative narrative. |
| Valuation | Separate P/E and P/B history shells, supported existing valuation slots and methodology/units | Charts remain unavailable: compatible dated prices/per-share data/rights are not established. No flat fake line, sampled proxy or market-cap comparison. |
| Financial statements | Income/Balance/Cash controls; source-parent expand/collapse rows; bold parent hierarchy, sticky period/row headers and local scrolling; existing period/unit selectors | Only actual source parent codes form groups. Unknown/conflicted/cyclic parents stay flat. No total calculated from visible children; original source labels/conflicts and raw evidence stay inspectable. TTM tables retain original quarters. |
| Documents and sources | Existing receipts, source dates, source version/hashes, original metadata, calculation/reconciliation evidence and statement coverage in one destination; safe HTTPS receipt links | Provider API receipt is not an issuer filing. Unknown publication timezone, basis, audit/revision and rights remain unknown. No fabricated document/archive links. |

Existing ratio functionality is retained inside Business picture; source evidence
is moved to Documents and sources rather than duplicated below every chart.
No redesign of Market Board, Heatmap, News, Watchlist or Community. No additional
navigation-triggered request: all sections share the same existing financial
request/cache. Period-count selection filters loaded evidence; frequency changes
use the unchanged annual/quarterly/TTM path. Ticker/frequency ownership, request
deadline/cancellation and explicit retry behavior are unchanged.

## Qualified projection and chart safety

`src/services/financial_presentation.py` now adds six `research_panels` to the
existing **display** response. No separate service, provider, statement schema,
endpoint, scheduler or acquisition path. The projection reuses `metric_status()`
and the existing deterministic engine outputs; it does not calculate new financial
ratios, monetary values, residual assets, TTM or growth in JavaScript or Python.

Each point retains period, value-or-null, qualification status and consolidation.
Only QUALIFIED nonfixture or explicit DEMO values enter charts. Missing basis,
source evidence or applicable rights remains UNQUALIFIED. Missing values stay
UNAVAILABLE, real zero stays zero. Backend gap rows remain gaps rather than
connected missing years or zero fill. Annual/YTD/quarter/TTM definitions are the
existing source contract, not newly certified by this UI.

Components within a point must share basis; historical chart periods retain the
latest usable accounting basis, withholding other bases as explicit gaps. An
individual direct metric may still be shown independently with its own basis;
that does not permit charting incomparable consolidated and separate figures
together. Selecting fewer loaded periods recomputes the chart's coverage status.

Frontend validates the projection owner/source/frequency, allowed keys and units,
fixture status, ordered periods, value equality with displayed engine observations,
nonnegative/compatible stacks, basis consistency and unavailable valuation guards.
The renderer also withholds malformed unqualified values in the observation table.
Raw unqualified amounts are never chart fallbacks. Old payloads without chart
projections receive explicit shells. Empty period responses retain section shells.
Series selection affects presentation only; accessible observation tables expose
actual point statuses. Qualification reasons remain inspectable for partial charts.

Bank assets use qualified customer-loan fields, never industrial cash/inventory
categories. Growth substitutes operating income for revenue. NIM/NPL/CASA remain
unsupported; no inferred sector, new financial-health score or recommendations.
Other financial/unknown issuer types retain the safe generic supported subset.

## Source qualification result

Replayed preserved FPT/PNJ/VCB captures through normalizer → engine → display →
frontend contract. All 9 responses and 54 panels pass their contracts; **no new
live QUALIFIED metric or numeric panel point** is activated. Actual samples still
lack reporting consolidation and applicable VCI rights evidence. Asset breakdown
also lacks qualified canonical receivables/fixed-assets/investments mappings.
P/E/P/B lack complete compatible valuation inputs. Synthetic tests exercise valid
and invalid arithmetic/plot paths and are not evidence of live source qualification.

Existing VCI unit/provenance conventions and all source/rights guards from
`FINANCIAL_ANALYSIS_V2_FOUNDATION.md` are preserved. SSI rights do not grant VCI
content rights. There are no new provider probes or browser-side diagnostic
overrides. The implementation is generic across supported tickers, not an FPT/PNJ/
VCB-only product route. No synthetic records were added to public routes.

## Validation and limitations

71 focused backend tests PASS (9 new panel cases) and 47 focused frontend tests
PASS (8 new cases, including new empty-response coverage). Tests cover the retained
financial API/cache/calculation seams, Stock Detail integration, rights/basis
rejection, gaps/zeros, bank exclusions, stacked composition, YoY/quarter/TTM,
source hierarchy collapse/cycles/conflicts, EN/VI, safe links and unavailable
valuation. Existing expectations were updated only for the requested navigation
move; original metric/source assertions are tested in their new destinations.
No assertion was removed to hide a financial data error.

Optimized webpack production build and TypeScript validation are performed in
a separate artifact copy. No running preview, production build or server process
is replaced. Evidence root:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/financial-research-experience-v2-20261019/`.
Saved replay evidence, build source hashes and validation manifest remain outside Git.

Cloud Browser is unavailable in this session. **Browser acceptance PENDING**:
desktop/mobile geometry, scroll/sticky behavior, interactive tooltips, legend
toggles and theme rendering have not been visually accepted. Automated SSR/contract
tests and a successful build do not establish visual PASS. No local browser or
replacement browser was opened; saved reference PNG inspection is not new product
acceptance. No new screenshots of this implementation are claimed.

Next product step: inspect the exact development build in the permitted Cloud
Browser when available, using existing isolated saved evidence and labelled test
fixtures. Keep source qualification separate: attach reporting-basis and applicable
VCI display-permission evidence for the first FPT period before any new real-field
activation. Additional asset categories and valuations require their own input
qualification; they do not block the existing usable generic research interface.

Production `a98793a`, installed P1, Collector singleton, product SQLite, ownership,
cooldowns, Technical Pilot OFF and FPT PAUSED are untouched. No push, merge or deploy.
