# Woofi Financial Data Intelligence — delivery, 21 October 2026

## Financial Intelligence V4 — current, 2026-10-21

V4 supersedes the historical checkpoints below: **341 source/accounting and
reporting-metadata-qualified observations (216 reported, 125 derived), 70 supported
definitions out of 77 canonical definitions, ten saved issuers**. Qualified original
histories cover FPT 2022–24, TCB 2023–25, VCB 2024–25, HPG 2024–25 flows/2025 balance
and MWG pre-audit 2024. VNM/SSI remain useful partial provider coverage.
Original captures and revisions remain preserved; metric-level gaps stay visible.
FPT dated ordinary BVPS is supported for 2023/24; P/E/P/B/earnings yield remain
unavailable without matched prices, shares and corporate-action evidence.
The bank comparison is **TCB/VCB, 2/22 observed banks, 15 FY2025 metrics**;
observed-industry ranks/percentiles are suppressed. Historical sector totals stay
disabled. No WiData or paid subscription is required.

Supported private launchers and live HTTP checks PASS. Actual integrated-browser
desktop checks PASS for exercised flows; mobile, tooltips, exhaustive retries and
full live-market context remain PENDING. Backend **1,600 + 32 subtests**, frontend
**334 passed + one existing skip**, typecheck/build and real contracts/static
rendering PASS. PIT/public-rights/fully-verified counts remain separately zero.
See [V4 delivery](FINANCIAL_INTELLIGENCE_V4_DELIVERY.md),
[feature comparison](SSTOCK_FEATURE_COMPARISON_V4.md),
[acceptance and manual checklist](DASHBOARD_VERIFICATION_V4.md),
[coverage](validation/free-data-v4/VERIFIED_METRIC_COVERAGE.csv), and
[valuation decisions](VALUATION_EVIDENCE_AUDIT.md).

## Historical record (superseded by V4 above)

## V3 free-data expansion — historical V3 checkpoint

From bdc70ad, the existing financial-data branch now delivers 64 supported
definitions and 175 source/accounting-verified observations (113 reported,
62 derived), with original VCB statements and deeper TCB notes. A separately
exposed reporting-metadata dimension also qualifies 175 observations. Fifteen
TCB/VCB FY2025 peer metrics now have ranks, percentiles and covered distributions.
The financial experience adds source-backed highlights and dedicated task views,
company-specific industry navigation and a dividend shortcut. Nine issuers, all
original captures and the 406/61 classification snapshot remain preserved.
Runtime/browser/mobile PENDING; no paid provider, WiData requirement, push/merge.
See [V3 delivery](FINANCIAL_INTELLIGENCE_V3_DELIVERY.md),
[feature matrix](SSTOCK_FEATURE_COMPARISON_V3.md),
[coverage](validation/free-data-v3/VERIFIED_METRIC_COVERAGE.csv), and
[manual acceptance](DASHBOARD_VERIFICATION_V3.md).

## Prior bdc70ad free-data continuation

SStock is the product/UI benchmark. No WiData integration or paid subscription
is required. Three explicit free saved-source adapters now add CafeF VHM annual
amounts, selected original HPG/TCB filing evidence and official VSDC dividends.
The existing four chart panels, statement tables, source selector, industry page
and dividend timeline expose supported real data through private research mode.

The two original-report views have **100 source-verified and 100
accounting-verified metric-period observations** (63 reported, 37 derived).
Publication-time/public-rights verification remains separate and zero. The
original 2,816 provider presentations remain selectable; preferred views have
2,660 and the union is 2,948. All 54 stock, 61 industry and nine dividend saved
API responses pass; frontend data contracts/rendering, typecheck and build pass.
Industry observations are usable in eight captured categories; qualified
multi-company rankings/historical sector totals remain unavailable.

Runtime/browser/mobile validation remains PENDING; the previous policy rejection
was not bypassed. New reports and exact commands:
[free-data delivery](FREE_DATA_DELIVERY_REPORT.md),
[evidence recovery](EVIDENCE_RECOVERY_REPORT.md),
[provider audit](PROVIDER_METADATA_AUDIT.md),
[industry status](INDUSTRY_TAXONOMY_STATUS.md),
[activation decision](ACTIVATION_DECISION.md),
[coverage](validation/free-data-v2/VERIFIED_METRIC_COVERAGE.csv),
[tests](validation/free-data-v2/TEST_RESULTS.json).

The following sections preserve the earlier checkpoints; their zero derived-data
and inactive industry statements do not describe the new private views.

## Prior 86000d3 real-data activation from 591f665

**DATA_ACTIVATION_STATUS:** PARTIAL. Eight real saved issuers now pass the existing
private API and frontend contracts across 24 annual/quarterly/TTM projections.
The prepared bundle extends the raw-capture reader to pinned TCB/SSI canonical
captures without acquiring or promoting provider data.

**ACTIVATED_REAL_METRICS:** 25 distinct supported reported fields across the sample;
2,816 eligible private observations. Zero fully VERIFIED or publicly activated
real metrics. All missing scope/original metadata and comparison gates remain.

**VERIFIED_TICKERS:** No fully qualified issuer history. Saved-source/contract
validation passed for FPT, HPG, MWG, PNJ, REE, TCB, VCB and SSI.

**INDUSTRY_MAPPING_STATUS:** 406 original HOSE provider pairs/61 codes reviewed as
a private snapshot, not a dated taxonomy. Real industry aggregates remain inactive.

**RUNTIME_STATUS:** PENDING. The prior “blocked by policy” startup rejection was
not bypassed. No running service was changed; current-branch visual/mobile
acceptance is not claimed.

Current evidence and operator steps:
[activation report](REAL_DATA_ACTIVATION_REPORT.md),
[blockers](REMAINING_BLOCKERS.md),
[dashboard verification](DASHBOARD_VERIFICATION.md),
[API checks](validation/REAL_DATA_API_VALIDATION.json),
[frontend contracts](validation/REAL_DATA_FRONTEND_VALIDATION.json).
Current test results are recorded in validation/REAL_DATA_TEST_RESULTS.json.

## Original 591f665 delivery record

The feasible source implementation and bounded direct benchmark are delivered in
an isolated branch. Real public data activation remains unqualified. Missing
vendor definitions, source rights and financial evidence are explicit gaps; the
delivery does not claim full SStock parity or all-listed-equity coverage.

**WORKTREE:** C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-financial-data

**BRANCH:** feature/financial-data-intelligence

**BASELINE:** b88f6f00250ea1a3ddc2a87ce7aabb95653d6573, the clean latest integration
checkout. Original checkout/main and unrelated worktrees were preserved.

**SSTOCK_PAGES_RESEARCHED:** Board; PNJ company overview/profile/dividends,
business picture/growth/valuation/income/balance/cash/documents; FPT statement and
overview; bank TCB overview/growth/risk; SSI overview/growth/portfolio; VHM growth;
retail industry overview/peer position/ranking/impact/valuation; narrow FPT
technical app gate. Visible overview checks covered all seventeen requested
tickers plus PNJ: eighteen issuers. The initial sign-in boundary later resolved
in the ordinary current integrated-browser session; no credentials or bypass
were used. See [inventory](sstock/PRODUCT_INVENTORY.md),
[page map](sstock/PAGE_AND_TAB_MAP.md), observation receipts and fourteen screenshots.

**SSTOCK_METRICS_CATALOGED:** 198 distinct observed financial labels, including
statement rows, chart components, loan segments, portfolio and ranking/valuation
columns. This is a label inventory, not 198 verified formulas. Exact undisclosed
definitions/aggregations/adjustments remain marked unknown. English translations
explain the labels and do not assert vendor-provided terminology.
See [catalogue](sstock/METRIC_CATALOG.csv) and
[specialist observations](sstock/INDUSTRY_METRIC_CATALOG.md).

**WIDATA_INDUSTRY_METRICS:** 29 catalogue entries: seventeen directly inspected bank
methodology definitions, one documented CASA article entry and eleven observed
industry table columns. HPG/TCB/SSI/VHM company templates, statement interactions,
TCB indicators and industry controls were inspected. Sector aggregation formulas,
membership vintages and complete numerical coverage remain unverified.
See [benchmark](widata/PRODUCT_AND_INDUSTRY_BENCHMARK.md) and
[catalogue](widata/METRIC_CATALOG.csv).

**EXISTING_WOOFI_METRICS:** 49 canonical engine outputs before this increment,
including the balance diagnostic; 25 mapped raw statement fields. Existing
annual/quarterly/TTM, growth, ratios, evidence gates, statement explorer and
dividend/action timeline were reused. Current total is 60 outputs.
See [inventory](data/CURRENT_DATA_INVENTORY.md),
[field mapping](data/EXISTING_FIELD_MAPPING.csv), and
[engine catalogue](data/WOOFI_METRIC_CATALOG.csv).

**NEW_VERIFIED_METRICS:** Eleven newly implemented deterministic outputs validated
with synthetic numerical fixtures: working capital; average equity/assets/inventory;
asset/inventory turnover; accounting loan/deposit ratio; four loans/deposits
YoY/QoQ changes. Zero newly qualified public real-source metrics. Existing ten
saved official PNJ facts match VCI exactly; this replay does not newly qualify
source metadata, document binary/page images or commercial permissions.

**MISSING_METRICS:** Qualified banking NIM/COF/YEA/CASA/NPL/LLR/CAR; securities
margin/FVTPL/AFS/HTM/brokerage/IB/funding costs; property customer advances and
project/revenue-recognition evidence; insurer specialist fields; action-adjusted
weighted shares/parent equity/compatible price vintages for EPS/BVPS/P/E/P/B
history; industry growth/history and real membership. See
[field gaps](data/MISSING_METRICS.md) and [remaining gaps](REMAINING_DATA_GAPS.md).

**NEW_DATA_SOURCES:** No new runtime provider or silent failover. Existing
vnstock 4.0.2/VCI retained; TCB and SSI were conservatively captured once through
the existing adapter, joining six saved issuers. SSI pricing/auth remained
untouched. KBS Java source was inspected and pinned; robots retrieval returned
400, so automated collection stopped. vnfin/vietfin remained documented
candidates. Official PNJ saved-text evidence was replayed. The annual-report
index remains a metadata lead; CC BY-NC OCR data was excluded from commercial
runtime. See [comparison](sources/PROVIDER_COMPARISON.md),
[access evidence](sources/API_VALIDATION.md) and
[rights](sources/LICENSING_AND_ACCESS.md).

**DATA_QUALITY_FINDINGS:** Eight VCI issuers, 24 statement receipts and 1,008
statement observations: eight annual 2018–2025 and 34 quarterly 2018Q1–2026Q2
periods per statement. All sampled observations lack qualified consolidation,
original-unit and publication metadata. The dedicated journal stores 23,040
normalized versions, with 17,757 UNQUALIFIED and 5,283 UNAVAILABLE; none is
QUALIFIED. Repeating ingestion inserted zero revisions and made zero provider
requests. These are measured sample counts, not market-wide percentages.
See [coverage](DATA_COVERAGE_REPORT.md), [matrix](data/DATA_COVERAGE_MATRIX.csv)
and [ingestion report](data/INGESTION_REPORT.json).

**DASHBOARDS_IMPLEMENTED:** Four additional projections in existing Financial
Analysis: cash flow/reinvestment, profitability history, liquidity/leverage and
bank lending/deposits. Existing financial and corporate-action modules remain.
New /industries provides industry/period/frequency/effective-membership controls,
per-metric coverage, selectable peers, rank/percentile/contributions and
method/source/exclusion details. VI/EN, unit formatting and responsive table
scrolling reuse Woofi components. /demo/financial-intelligence is explicit
synthetic replay only; normal build output contains the not-found result and no
demo heading or synthetic taxonomy content.

**INDUSTRY_ANALYTICS_STATUS:** Working foundation: versioned taxonomy and dated
membership contracts, separate model guards, qualified-fact sums and matched
ratio cohorts, accounting compatibility gates, revision conflict exclusion,
coverage, numerical competition ranks/midrank percentiles and finite contributions.
Read-only APIs use an explicitly configured private journal, never acquire on
industry requests. No real taxonomy is enabled; real industry coverage is zero.
Industry P/E/P/B stay unavailable, never an arithmetic mean of issuer multiples.
Classification publication vintages are not certified; point-in-time qualification
remains false even with conservative as_of filtering.

**BACKEND_TESTS:** Baseline 1,517 passed plus 32 subtests. Final full suite 1,532
passed plus 32 subtests. One pre-existing Starlette/httpx deprecation warning.
New tests cover normalized contracts, units/models, turnover, balance identity,
revision idempotence/conflicts/as-of, dedicated-journal safety, offline ingestion,
matched sector arithmetic/coverage, missing/conflicting evidence and nonfinite
aggregate/contribution handling. No unrestricted live-endpoint tests.

**FRONTEND_TESTS:** Baseline 321 passed, one skipped. Final 323 passed, one existing
skip (324 total). New industry ownership, coverage, quality and fixture contracts
are included.

**TYPECHECK:** npm run typecheck passed.

**BUILD:** npm run build -- --webpack passed. Normal generated
.next/server/app/demo/financial-intelligence.html contains the not-found result
and excludes the synthetic demo heading/taxonomy. Actual integrated-browser
acceptance before stopping the isolated preview covered chart rendering,
model/frequency switching, VI/EN, both themes, desktop and an observed narrow pane.
No controlled device-width matrix or real-data activation acceptance is claimed.
See [browser evidence](validation/BROWSER_ACCEPTANCE.md).

**UNRESOLVED_BLOCKERS:** Applicable financial-data reuse rights; original scope,
units and publication vintages; licensed/reconciled secondary data; real reviewed
taxonomy; specialist input notes and share/price histories; original PNJ binary
and page-image verification. Requested FPT/HPG/TCB/SSI two-provider numerical
comparison remains incomplete. Final preview restart was rejected by automatic
approval review as “blocked by policy”; it was not retried through another launcher.
The existing successful browser pass and compiled-output check are retained;
post-build runtime recheck remains pending.

**COMMIT_STATUS:** Local delivery commit in the dedicated feature branch; repository
HEAD identifies the commit. Private captures, journal, dependencies and logs are
ignored and excluded.

**PUSH_STATUS:** Not pushed, merged, deployed or applied to production. No secrets
or production database/configuration were changed.

**RECOMMENDED_NEXT_STEPS:** Qualify one small real cohort with source rights and
original filing metadata; review and import a dated taxonomy; then activate
per-metric coverage and compare against original reports. Extend bank/securities/
property/insurance mappings only with reconciled notes. Add matched-cohort industry
growth/history and share-vintage valuation once inputs support them. See
[runbook](../docs/FINANCIAL_DATA_INTELLIGENCE_V1.md),
[decisions](IMPLEMENTATION_DECISIONS.md) and [roadmap](NEXT_PHASE_ROADMAP.md).
