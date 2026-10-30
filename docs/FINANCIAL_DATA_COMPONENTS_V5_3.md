# Financial Intelligence V5.3 — Detailed Components

## Outcome

V5.3 exposes the existing saved VCI statement hierarchies through the current
personal-research `research_panels` contract. It uses the existing chart and
statement components; no provider was added, no data was acquired, and no
financial engine or visual chart system was duplicated.

The projection retains each original source line code, English/Vietnamese
labels, unit, value, reporting period, consolidation label, source and statement
basis. It does not sum children, calculate a residual, create a total, or
interpolate a missing period. Source-reported values remain restricted to the
existing personal-research scope; this work does not approve public-display or
redistribution rights.

## Reusable source mapping

The existing `FinancialLine` records are the mapping source. For each selected
statement period, V5.3 groups eligible VND lines by their explicit VCI `parent`
identifier and source-code family:

| Profile | Source-code families | Focused fields visible in saved hierarchy |
| --- | --- | --- |
| Non-financial | `isa`, `bsa`/`bsb`/`bss`/`bsi`, `cfa`/`cfb`/`cfs` | Cost of sales, expenses, profit lines; cash, investments, receivables, inventory, fixed assets, liabilities and equity children where the source supplies parent links |
| Bank | `isb`, `bsa`/`bsb`/`bss`/`bsi`, `cfa`/`cfb`/`cfs` | Interest income/expense, fee income/expense, interbank placements, trading and investment securities, gross customer loans and loan allowance, customer deposits, reserves and cash-flow detail |
| Securities | `isa`/`iss`, `bsa`/`bsb`/`bss`/`bsi`, `cfa`/`cfb`/`cfs` | Brokerage and other securities revenue, FVTPL/financial-asset income and expenses, financial assets, borrowings, customer cash-flow lines and equity components where explicit source lines exist |

The four representative packets confirm that these fields already contain
real, non-null VND amounts. “Codes with values” counts unique source line codes
with at least one amount in the saved annual or quarterly history; it does not
mean each code is present in every period.

| Issuer | Profile | Income codes / with values | Balance codes / with values | Cash-flow codes / with values | Component chart code-series slots |
| --- | --- | ---: | ---: | ---: | ---: |
| FPT | Non-financial | 25 / 23 | 122 / 121 | 41 / 41 | 183 |
| TCB | Bank | 26 / 24 | 86 / 84 | 52 / 51 | 104 |
| VCI | Securities | 79 / 76 | 208 / 204 | 148 / 147 | 345 |
| VIC | Non-financial | 25 / 23 | 122 / 121 | 41 / 41 | 183 |

Most amount-bearing source lines are now represented in a parent-sibling or
unparented-lines view. Parent panels require at least two observed child codes.
Single-child groups and codes with no values in the selected frequency remain
available in the detailed statement table rather than being promoted into a
misleading composition chart.

A sibling panel contains only direct children of its source parent. The parent
amount is omitted from that chart. A second view groups VND source lines whose
metadata has no parent; it is always an unstacked time series because available
metadata does not establish whether unparented totals overlap. Direct line
values are never treated as a calculated metric.

All custom panels are partial. Their qualification details report the number
of observed child/root line codes with values per period. This is a count of
visible source lines, not a percentage of the reported parent amount. Codes
absent from every selected source period cannot be enumerated from the stored
canonical packets, so the application does not claim complete monetary
coverage or manufacture a missing residual.

## Measured saved-packet coverage

The private bundle contains 23 issuer packets. Twenty-one use the existing VCI
hierarchy and now have three statement-family component views. The remaining
two, VHM and VNM, contain CafeF annual income and balance summaries but no VCI
line hierarchy or cash-flow observations, so they do not receive fabricated
component charts.

| VCI profile | Issuers with component views | Panels per issuer (income / balance / cash) | Code-series slots per issuer (annual / quarterly) |
| --- | ---: | ---: | ---: |
| Non-financial | 12 | 29 total | 183 / 183 |
| Bank | 7 | 21 total | 104 / 104 |
| Securities (`financial_other`) | 2 | 40 total | 345 / 345 |
| **All VCI hierarchy packets** | **21** | **575 total panels per frequency** | **3,614 code-series slots per frequency** |

The panel total includes 63 unparented-line views per frequency. The other 512
panels are explicit-parent views. Code-series slots count panel placements and
may repeat an identifier across issuers or view groupings. They are not newly
acquired fields; they are saved VCI lines now available through charts as well
as the statement tables.

Balance groups stack only if every visible amount in the group is non-negative
and the group is one source-parent's direct siblings. This yields 240 stacked
balance panels / 1,192 series slots in quarterly mode and 238 / 1,184 in annual
mode. Negative or otherwise incompatible balance groups use grouped bars.
Income and cash-flow panels are grouped bars. Neither chart type implies a
computed reconciliation.

| Period selection | Saved VCI coverage | Additional sources |
| --- | --- | --- |
| Quarterly | Eight issuers have 34 periods: FPT, HPG, MWG, PNJ, REE, SSI, TCB and VCB. Thirteen other VCI issuers have four periods each. | VHM and VNM have no saved quarterly observations. |
| Annual | Eight issuers have eight periods; thirteen VCI issuers have four periods each. | VHM and VNM have four CafeF annual periods each, but no compatible VCI hierarchy or cash-flow packet. |

The dashboard period selector continues to choose the available annual or
quarterly history. Every component row uses the selected packet's original
period label and source basis; missing component values remain unavailable.

## Product integration and limits

The existing Stock Detail financial dashboard exposes the new views under the
Performance, Balance sheet and Cash flow sections, in a collapsed “Detailed
source-line components” group. Each chart retains the existing keyboard-
operable series controls, amount formatting, source attribution, partial-data
disclosure and chart-observations table. There are no new calculations for
valuation, ratios, sector ranks or financial statement totals.

These observations remain `SOURCE_REPORTED`, not independently
`ACCOUNTING_VERIFIED`. Source parent metadata is used to prevent an explicit
parent and its children appearing together in a composition series; it does
not prove the statement's overall accounting identity. Reporting basis is
retained per chart row, and existing safeguards suppress a chart if the
consolidation labels conflict across its periods. Public use and redistribution
remain outside this private-research activation.

Visual/browser acceptance was not performed for V5.3. The existing preview was
not restarted. Production build and frontend contract tests validate the UI
integration, but visual acceptance remains **PENDING** until the approved
preview launcher and browser are used to inspect long-period FPT/TCB charts and
the securities-specific component views.

## Validation

- Focused backend personal-financial regression: 32 passed.
- Full backend suite: 1,619 passed, 32 subtests passed; one existing
  Starlette/httpx deprecation warning.
- Frontend suite: 337 passed, one existing optional replay skipped.
- TypeScript typecheck and optimized production build: passed.
- Saved-packet API contract replay: all 23 quarterly and 23 annual projections
  validated against the frontend contract.
- No new provider calls or acquisition were made; validations read the
  existing saved private packets.
