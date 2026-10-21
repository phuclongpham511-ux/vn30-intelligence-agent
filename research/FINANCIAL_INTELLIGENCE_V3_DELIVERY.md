# Financial Intelligence V3 — implementation delivery

21 October 2026. Existing `woofi-financial-data` worktree,
`feature/financial-data-intelligence`, base `bdc70ad`. No paid API, subscription,
WiData requirement, dependency upgrade, production change, push or merge.

## What a user can now do

Financial Analysis opens with a compact period-labelled financial snapshot and
revenue/profit history before balance and cash-flow detail. Dedicated destinations
cover revenue/earnings/growth, balance sheet, cash flow, profitability and health,
alongside statements and sources. Navigation retains groups with usable data;
missing profitability or valuation does not hide a valid amount view. The existing
dividend timeline has a direct shortcut. The industry link carries company,
period and frequency into its observed classification rather than opening an
unrelated default category. Woofi components, colours and source controls remain.

TCB's health view now has original-note deposit and credit-quality ratios, with
inspectable definitions and the precise population exclusions. Its industry
comparison can rank TCB and VCB on 15 compatible FY2025 metrics and show the
covered sample's median/minimum/maximum. Missing members remain in the denominator.
All figures come from the saved source/engine; no browser-side financial arithmetic
or vendor ratio import supplies them.

## Measured improvement from bdc70ad

| Measure | Base | V3 |
|---|---:|---:|
| Distinct supported metric definitions | 50 | **64**: 34 reported, 30 derived |
| Source-verified metric-period observations | 100 | **175** (+75%) |
| Accounting-verified observations | 100 | **175** |
| Reporting metadata complete | Previously embedded in other checks | **175**, now a separately exposed dimension |
| Reported / derived verified observations | 63 / 37 | **113 / 62** |
| Original-report issuers | HPG, TCB | **HPG, TCB, VCB** |
| Real qualified multi-company peer metrics | 0 | **15**, TCB/VCB FY2025 in observed bank category 8355 |
| Observed classifications | 406 HOSE members / 61 categories | Unchanged, preserved |
| Total saved issuer coverage | 9 | 9; depth improved before adding tickers |
| PIT / public rights / fully verified | 0 / 0 / 0 | 0 / 0 / 0, separate from current private availability |

The canonical calculation catalogue now contains 74 definitions. Sixty-four
actually appear in the measured eligible views; the remaining ten are unavailable
in this sample. Valuation summary placeholders are not counted as working
calculations. A metric definition is counted once across issuers/periods.

The original **2,816** eligible provider presentations and exact capture bytes
remain available. V3 preferred views have **2,615** presentations: **2,553 reported
and 62 derived**. Shorter qualified report packets take annual priority for three
issuers; the original eight-year provider histories remain selectable. The union
of selectable source presentations is **3,023 = 2,816 + 175 + 32 CafeF**. These are
source/metric/period presentations, not unique economic facts or market coverage.

HPG contributes 53 verified presentations / 37 definitions; TCB 75 / 42; VCB
47 / 28. Overlapping definitions must not be added to claim 107 unique metrics.
The selected reports contain 113 canonical reported cells plus two HPG FX
reconciliation cells, which are not extra headline metrics.

## Sources and historical coverage

**One new original issuer source:** Vietcombank's official 2025 audited
consolidated report, HTTP 200, 11,552,186 bytes, 84 scanned pages, SHA-256
`295f397de287f84c26dafbfa06f668604aa696a013e236253149d8547d032d1f`.
Visually reviewed PDF pages 8, 9, 11–14 and 18 supply 32 selected 2024–25 cells,
explicit consolidation/calendar boundaries, million-VND units and separate
VND/share EPS. Both balance identities and both cash-flow/endpoint equations pass.
Original PDF/PNG hashes and selected source rows/columns are pinned privately.
The report date/approval does not become a historical publication timestamp.
[Original issuer PDF](https://www.vietcombank.com.vn/-/media/Project/VCB-Sites/VCB/Nha-Dau-tu/Files/BC-dinh-ky/BCTC/2025/20260327---VCB---BCTC-hop-nhat-kiem-toan-nam-2025.pdf?ts=00010101000000).

**Existing TCB source expanded:** reviewed original annual-report PDF pages
167, 168 and 174 add nine reported note fields over two years. Its PDF binary
is unchanged; the new extraction has its own manifest digest/review reference.
The 2024–25 classified-loan subtotal excludes securities margin/advance lending.
Five loan grades reconcile exactly to that subtotal. General and specific
allowances exclude the separately reported securities-margin allowance.

New definitions are `customer_demand_deposits`, `classified_loans`,
`loan_grade_1`…`loan_grade_5`, `loan_allowance_general`,
`loan_allowance_specific`, `classified_nonperforming_loans`,
`classified_loan_allowance`, `demand_deposit_share`, `npl_classified_ratio`,
and `classified_loan_coverage`.

- Demand-deposit share = demand deposits / customer deposits. This is an explicit
  accounting CASA-style definition, not a claim of the vendor's CASA measure.
- Classified NPL = grades 3–5 / the matching classified-loan subtotal, excluding
  securities margin lending from the denominator.
- Provision coverage = matching general + specific allowances / grades 3–5.
  No subsidiary margin allowance is silently added.

HPG retains its distinct Q4 pre-audit 2024–25 annual source and 2025 closing
balance. VHM retains eight partial CafeF fields over 2022–25. Original provider
annual histories span 2018–25; quarterly captures span 2018-Q1 through 2026-Q2,
with eight most recent periods displayed by default. Qualified new ratios use
only the two reviewed annual years. No publication, missing year, earlier balance
or quarterly/TTM flow basis is manufactured. There are 25 populated preferred
views out of 27; VHM quarterly/TTM correctly return empty coverage.

**New SDK/API families: zero.** The existing generic original-report adapter
handles VCB and the deeper TCB note evidence. Existing SSI/VCI/CafeF/VSDC paths
remain. Normal HPG audited-2025 and FPT annual-2025 PDF requests returned HTTP
403 / 17 bytes (`error code: 1010`); no retry/header impersonation/alternate host
followed. Prior KBS 400 and VNDirect 403 findings were carried forward, not
misrepresented as successful reads. Installed vnstock remains 4.0.2; vnfin and
VietFin schema findings remain background evidence, with no package/code copy or
upstream data-rights inference. See [source receipts](validation/free-data-v3/SOURCE_RESPONSE_AUDIT.json).

## Industry and quality behavior

The actual current comparison is an **observed 17 October 2026 membership
snapshot** with FY2025 financials, not 2025 historical composition or a live
21 October universe refresh. The bank cohort covers two of 22 observed members.
Its 15 ranked metrics include common income, balance, cash flow, ROE/ROA and
accounting loans/deposits. TCB's note ratios currently have one covered issuer:
they appear as individual observations, without a rank or sample median.
The other seven captured categories retain useful partial observations.

Source evidence, accounting consistency, reporting metadata, historical PIT,
public usage rights and the all-dimensions result are separately disclosed.
REPORTING_METADATA_COMPLETE covers original unit/currency, fiscal boundaries,
scope/basis and source/record identity needed by current statements. It does not
certify an audit opinion, correction-release history or publication timestamp;
those unknown fields remain explicit in the source contexts.
Current private dashboards do not require historical publication-time proof.
A contradictory loan-grade subtotal blocks affected ratios while leaving the
reported fact and unrelated cash flow/deposit calculations inspectable.
Public consumers and default-off socket/Host checks still reject private data.
Historical sector totals remain disabled and unknown dates remain unknown.

## Validation and acceptance

- Backend: **1,591 passed and 32 subtests passed**, one existing Starlette/httpx
  deprecation warning; no failures.
- Frontend: **331 passed, one existing skip**; typecheck and production webpack
  build pass.
- Actual saved-data ASGI: 54 stock projections, 61 industry responses and nine
  dividend responses pass. These include expected empty coverage, not 54 populated
  financial histories. Nine company-context peer APIs additionally pass.
- Independent actual-source checks validate the three note ratios, bank
  average-balance ROE/ROA, ranks, percentiles and covered medians/ranges.
- All 54 stock responses pass frontend contracts; 61 industry/nine dividend
  responses render in both languages. Eighty financial view cases across five
  issuers/eight selected destinations/two languages pass static rendering,
  including unavailable-section fallbacks. This is not 80 working dashboards.
- No validation listener, application DB write, provider refresh or source
  mutation was required. Originals/private responses/documents remain ignored.

**Woofi runtime/browser/mobile: PENDING.** The prior automatic approval rejection
was `CreateProcess rejected: blocked by policy`, before preview startup. No new
restart or workaround was attempted. Current read-only listener/config inspection
and [the exact manual checklist](DASHBOARD_VERIFICATION_V3.md) are separate from
ASGI/static checks. SStock itself was revisited in the integrated browser on TCB
business-picture/growth pages; that is benchmark research, not Woofi acceptance.

See the [feature comparison matrix](SSTOCK_FEATURE_COMPARISON_V3.md),
[coverage CSV](validation/free-data-v3/VERIFIED_METRIC_COVERAGE.csv),
[field-level evidence](validation/free-data-v3/ACTIVATED_VIEW_EVIDENCE_MATRIX.csv),
[real acceptance](validation/free-data-v3/V3_REAL_ACCEPTANCE.json) and
[test receipts](validation/free-data-v3/TEST_RESULTS.json).

## Next useful increments

Review more original annual/quarterly documents once ordinarily accessible;
prioritize FPT and earlier compatible HPG balances for turnover/longer returns.
Map VCB loan/deposit notes to extend specialist peer coverage; independently
qualify NIM's earning-asset average before adding it. Securities margin/FVTPL/
brokerage inputs, property advances/project notes, CAR, price/share vintages for
valuation and dividend yield remain unsupported. Six QoQ growth definitions,
asset/inventory turnover, average inventory and ROE change have no qualified
display coverage in the measured catalogue. Individual missing indicators do
not disable the working source-backed views. Run approved browser/mobile
acceptance before claiming visible end-to-end completion or deploying publicly.
