# Fundamental Analysis V1 — qualification and compact overview

Development base: `94583350989e3cb9e459ab47bbe6818aeddd9680`.
This continues the existing Stock Detail Financial Analysis; it is not a new page,
provider, engine, design direction or acquisition project. Browser status: PENDING.

## Reused implementation and evidence

Reused FundamentalTrends, FinancialResearchCharts, FinancialStatementTable, the
existing `/stocks/{symbol}/financials?projection=display` read, financial packet
cache/normalizer, Python financial engine, calculation receipts and source tables.
The four internal research sections, annual/quarterly/TTM controls, period-count
and VND/million/billion display units remain. Company Overview, corporate actions,
Market Workspace V2.2 and the other Stock Detail tabs are preserved.

Read the existing Fundamental Analysis and Fundamental Data Engine reports before
editing. Inspected the provider adapter without calling it. Reused all nine saved
FPT/PNJ/VCB annual/quarterly/TTM responses from
`C:/Users/PC/.codex/tmp/woofi-fundamental-engine-v1-20261013/`.
Their original reads were 2026-10-13, latest annual 2025 and quarter 2026-Q2.
All have unknown consolidation. This is saved-response replay, not a live provider
or freshness check, and it does not extrapolate to all issuers.

## Display contract established from existing source capabilities

All displayed metric arithmetic remains in Python's existing financial engine.
The new display projection does not create ratios, growth, EPS, TTM or valuation.
Currency is VND; monetary outputs remain VND, per-share EPS VND/share, rates
fractions and debt/equity a dimensionless multiple. Millions/billions only scale
presentation; EPS never follows the amount-unit selector.

Common ownership is explicit: response ticker/source/currency, source version,
metadata and statement hashes, row reporting period/frequency, source input codes,
flow basis, consolidation, publication strings and acquisition receipts. Source
`yearReport`/quarter identifiers are used as reported. A fiscal calendar is not
invented; no current-session or historical point-in-time freshness is certified.
Read time is not publication time. Source publication strings retain unknown
timezone/precision. They cannot establish current freshness.

| Metric family | Existing source/definition | Reporting basis and display decision |
| --- | --- | --- |
| Market cap, P/E, P/B, BVPS | No compatible qualified price/share/parent EPS/book-value contract | UNAVAILABLE; no price/financial join or proxy |
| Reported basic EPS | Metadata-qualified income `isa23`; reported basic EPS in VND/share | Annual or supported standalone quarter only; never summed into TTM or relabeled as P/E denominator |
| Revenue / total PAT | Ordinary `isa3` / `isa20`; parent PAT is separately retained in existing performance tables | Exact annual, standalone quarter or existing qualified four-quarter TTM |
| Bank operating income | Qualified bank metadata `isb38`, never ordinary revenue | Same period rules; generic revenue/margins remain excluded |
| Revenue / PAT YoY | Existing exact comparable prior year or same quarter one year earlier | Positive base required for percent; missing/zero/negative bases never become zero growth |
| ROE / ROA | Total PAT / mean current and compatible prior total equity/assets | Annual endpoints, quarter endpoints (not annualized), or existing TTM year-earlier endpoints |
| Gross / net margin | Gross profit / revenue; total PAT / revenue | Positive revenue; ordinary issuer only; no banking substitute |
| Assets / liabilities / equity | Qualified balance fields `bsa53` / `bsa54` / `bsa78` | Period-end balances, including TTM views; not summed flows |
| Debt / equity | Existing nonnegative short + long borrowings / positive equity | Ordinary issuer; compatible period/basis only |
| Operating cash flow / FCF | `cfa18`; existing CFO minus qualified capex outflow | Qualified annual/quarter flow or four-quarter TTM; original outflow signs preserved |

Each overview metric has a status, value or null, unit, definition and missing/
qualification reason. The summary shares the latest period/frequency, publication
and consolidation context with its response; ownership is checked by the client.

- **QUALIFIED**: the existing engine supplied a finite, nonwithheld value with
  qualified input codes, content hashes, VND currency, known flow basis and a
  consistent explicitly supplied consolidated/separate reporting basis. This is
  contract qualification for a reporting period, not new verification of filings,
  display rights, current freshness or investment quality.
- **UNAVAILABLE**: no supported value/calculation, absent qualified source value,
  missing exact prior period, invalid denominator/base or unsupported valuation.
- **UNQUALIFIED**: source semantic evidence or reporting basis is unknown/conflicting.
  Values remain null in displayed metrics, chart rows and affected comparisons.
- **DEMO**: an explicitly fixture-marked packet demonstrates the existing arithmetic
  and known units. It cannot produce QUALIFIED live metrics. Missing or conflicted
  inputs still remain unavailable/unqualified. No demo route/data was activated.

Known standalone **financial statements** mean separate reporting, not a standalone
**quarterly flow**. The UI now labels those concepts separately in EN/VI.

## Product increment and conservative gate

The existing overview now has four compact groups: valuation, business performance,
profitability and financial health. It includes 19 metric slots for ordinary issuers;
bank performance substitutes operating income. Missing values remain useful labeled
slots with inspectable reasons, rather than invented metrics or a health score.
Definitions are expandable per metric. Report basis and read time are visible;
original receipts/inputs remain inspectable. Existing charts, comparisons and
statement controls continue below and in their existing sections.

The display projection now withholds unknown-consolidation values throughout its
metric/chart/comparison view. Original statement amounts remain behind an explicitly
unqualified evidence disclosure rather than becoming qualified table values.
Per-period statement headers show both flow and consolidation basis. The full
financial engine API is retained for source/calculation inspection, with no change
to its numerical definitions or original values. The current UI requires the new
display contract; an old/missing summary cannot silently certify values.

Ticker/frequency transitions hide prior data before a new effect runs, preventing
the previous company's/reporting period's numbers from flashing under new controls.
Existing request deadline, process cache, manual retry and cancellation remain;
no polling, worker, provider probe or acquisition change was added.

Layout uses the current theme tokens and compact definition lists, two columns
on large screens and stacked groups on mobile. Numeric columns wrap within bounded
width. EN/VI chrome is translated; source names, formulas and original labels remain
inspectable. Desktop/mobile and light/dark rendering are NOT browser-accepted yet.

## Saved source qualification result

None of the nine saved responses passes the new live display gate because all
have unknown consolidation. FPT/PNJ annual/quarterly each produce 15 UNQUALIFIED
and 4 UNAVAILABLE slots; TTM has 14 and 5. VCB annual/quarterly each have 11 and 8;
TTM has 10 and 9. No packet is fixture-marked or promoted to current live evidence.
All nine projected responses pass the current frontend display contract.

This deliberate conservative change makes existing unknown-basis evidence visible
as a gap rather than certifying cross-basis analysis. No missing basis was filled
from issuer names, old taxonomy, market prices or synthetic records. Completion of
live data acceptance requires existing-provider basis/publication/rights evidence
and separate browser acceptance, not another unbounded source-acquisition project.

## Validation and boundaries

Frontend: 219 PASS, 1 SKIP, 0 FAIL in the final complete Node unit/render suite
(220 cases). The skip is the existing optional real persisted-API replay requiring
external evidence configuration; no assertion was disabled for this increment.
Backend: 46 PASS across the financial engine, display projection, research,
provider cache and new summary tests, in a separate focused run. The existing
Starlette/httpx deprecation warning remains. Typecheck and isolated optimized
webpack build PASS. Build-source hashes match the development app/lib files.

Coverage includes source/display units and EPS scaling, calendar/frequency/owner
mismatches, missing values, zero/negative comparison bases, zero denominators,
consolidation conflicts and unknown basis, unknown quarterly flows, TTM EPS,
DEMO/live separation, source immutability, SELECT-only HTTP access, no additional
provider call in the projection, and ticker/frequency transition rendering.
Existing Market Workspace, company/actions, translations and other frontend tests
remain passing. No product test was weakened to hide a data failure.

Logs, saved-response audit with input hashes, nine projected saved replays and the
isolated build are retained under
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/fundamental-analysis-v1-increment/`.
Tests use synthetic packets, mocked provider methods or saved response replay,
with in-memory test SQLite.
No financial fact in the saved captures was changed. No product database,
Supervisor, Collector, application source pin, acquisition state, cooldown,
Technical Pilot or FPT automation was changed. No push, deployment, server launch,
preview retry, port investigation or host policy operation was performed.
