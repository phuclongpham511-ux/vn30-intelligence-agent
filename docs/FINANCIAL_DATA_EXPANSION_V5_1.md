# Financial Data Expansion V5.1

**Branch:** `feature/financial-data-intelligence`
**Base:** `76afaea`
**Scope:** saved financial data, quarterly history and statement detail; no provider acquisition or chart redesign.

## Coverage recovered from saved data

The V4 saved VCI captures already contained 34 contiguous quarterly periods from 2018-Q1 through 2026-Q2 for six of the seven prioritized issuers. The private API requested eight periods, the engine rejected requests over 20, and the dashboard had no history selection beyond eight. V5.1 raises the existing bounded private path to 34 periods and adds 16- and 34-period choices to the existing selector.

| Ticker | Source | Annual periods | Quarterly periods | Source-reported metric-period observations | Newly visible vs. V4 |
|---|---|---:|---:|---:|---:|
| FPT | VCI | 8 | 34 | 714 | 546 |
| HPG | VCI | 8 | 34 | 714 | 546 |
| MWG | VCI | 8 | 34 | 714 | 546 |
| TCB | VCI | 8 | 34 | 510 | 390 |
| VCB | VCI | 8 | 34 | 510 | 390 |
| SSI | VCI | 8 | 34 | 408 | 312 |
| VNM | CafeF saved annual summary | 4 | 0 | 0 | 0 |

Across the six VCI histories, the existing API exposed 840 metric-period observations from the latest eight quarters. The full histories now expose 3,570, a gain of 2,730. This uses the same pinned captures and mapped fields; no new provider request was made. The saved quarterly income and cash-flow records carry `standalone` basis, while balance-sheet records carry `point_in_time` basis. Gaps remain missing. The existing TTM calculation and its labels are unchanged.

## Detailed statement lines

The authorized personal-research projection now exposes direct VCI statement lines when the source code, hierarchy, finite reported value, VCI unit contract and non-prohibited access state are intact. The existing statement table displays original codes and source parent relationships. It does not add parent and child values together, fill residuals, or use these rows to build new composition charts. A YTD source line remains labelled YTD and does not become a standalone quarter. Explicit EPS and share-volume labels retain per-share and share-count units; ambiguous ratio/percentage labels do not inherit a currency unit.

The 34-quarter histories contain the following source line definitions by statement:

| Ticker set | Income statement | Balance sheet | Cash flow |
|---|---:|---:|---:|
| FPT, HPG, MWG (each) | 25 | 121 | 41 |
| TCB, VCB (each) | 26 | 84 | 51 |
| SSI | 78 | 206 | 147 |

The V4 eight-quarter payloads contained 912 visible source-line values across these six companies. The expanded histories expose 44,662, a gain of 43,750 line-period values. These are source rows, not 43,750 newly defined financial metrics. The increase adds 1,200 ticker/statement/field-code combinations to the existing statement tables.

## Provider and evidence limits

The installed environment has `vnstock 4.0.2`; V5.1 does not upgrade it or reacquire data. The project uses KBS for symbol listing, but has no KBS financial-statement adapter. A bounded public KBSV check found issuer reports, including a VNM company report, but did not establish a machine-readable quarterly feed or data-use permission for ingestion. No KBS financial data was imported. VNM therefore remains annual-only in the saved Woofi inventory. The KBSV report is available from [KB Securities Vietnam](https://www.kbsec.com.vn/pic/Service/KBSV_Baocaocapnhat_VNM_20222103.pdf).

Private research authorization remains separate from publication rights. These observations are still source-reported, not independently reconciled or approved for public display. Existing source-selection, identity, period, unit, conflict, and rights guards remain in place.

## Implementation and verification

V5.1 raises the financial engine and private endpoint bound to 40, requests 34 saved periods through the existing private proxy, and extends the existing period selector. The broader provider line projection is restricted to the existing VCI source packet and does not change the public endpoint or the verified annual-report adapter.

Validation uses synthetic contract tests plus an offline replay of the pinned real captures. The backend suite passed **1,605 tests and 32 subtests**; the frontend suite passed **336 tests with one existing skip**. Focused history/projection tests passed **68 tests**. Typecheck and optimized production build passed. The suite emitted one existing Starlette/httpx deprecation warning. No runtime restart or visual acceptance was performed for this data-only update.
