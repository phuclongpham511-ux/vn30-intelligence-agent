# Financial Intelligence V4 — product acceptance, depth and valuation

2026-10-21. Continues `d452f8e` on `feature/financial-data-intelligence` in
the existing financial-data worktree. SStock is the product benchmark; no WiData,
paid API, dependency upgrade, main change, push or merge is required.

## Delivered result

The same saved-data engine now supports **341 SOURCE_VERIFIED and
ACCOUNTING_VERIFIED metric-period observations**, also complete for reporting
metadata: **216 reported + 125 derived**, up from 175. **70 distinct definitions
are supported (36 reported, 34 derived), from 77 canonical definitions**.
Historical point-in-time verification, public redistribution approval and fully
verified coverage remain independently zero. These are authorized private views.

| Issuer | Preferred original-report periods | Verified observations | Supported definitions |
|---|---|---:|---:|
| FPT | 2022–2024 | 117 | 48 |
| HPG | 2024–2025 flows; 2025 closing balance | 53 | 37 |
| MWG | Selected 2024 statements, pre-audit vintage | 30 | 30 |
| TCB | 2023–2025 common statements; 2024–2025 selected credit notes | 94 | 42 |
| VCB | 2024–2025 | 47 | 28 |

Definition counts overlap across issuers. FPT/TCB histories use explicit
whole-period document selection. No individual field is filled from another
document. Every original manifest, PDF, reviewed page, raw token, overlapping
revision and source date remains pinned privately. An issuer history identifies
the collection; each input retains its original document source, URL, binary
hash, record hash, receipt hash and observation time. Ratios and growth spanning
different document binaries are withheld; publication timing is never inferred.
FPT's original and later comparative EPS bases are preserved rather than silently
treated as one corporate-action-adjusted series.

Ten issuers now have saved financial views: FPT, HPG, MWG, PNJ, REE, SSI, TCB,
VCB, VHM and VNM. Existing eight original VCI captures are byte-identical.
The source selector retains their longer provider histories (up to eight annual
and 34 quarterly periods), with their original metadata limitations. VHM and new
VNM each have four partial annual CafeF summaries (2022–2025). Gross sales is
still excluded from net revenue; unknown scope/units/fiscal boundaries are not
transferred from unrelated filings. Missing cash flow stays missing.

The preferred projection has 2,477 display-eligible presentations. All selectable
provider/summary and reviewed views have 3,221 presentations (2,816 original +
64 CafeF + 341 reviewed), with overlapping source vintages; these are not 3,221
unique economic facts. A shorter qualified default does not delete the longer
selectable provider history. The original 2,816-row evidence matrix is unchanged
byte for byte; `validation/free-data-v4/BASELINE_REFERENCE.json` pins the V3 copy.

## Observable product improvements

- Fixed Stock Detail's all-page identity gate: authorized saved financial and
  dividend endpoints validate ticker ownership independently and remain usable
  when the core market backend is unavailable. Company/quote facts remain unknown.
- Show separate source/accounting counts and display availability in the collapsed
  verification disclosure, rather than making missing publication evidence look
  like an absence of source verification.
- Reuse period/unit/source controls, existing chart groups and statement tables.
  Add a dated EPS/book-value/input table; distinguish money, per-share units and
  actual share counts. Link each history period to its original document.
- Preserve filing-vintage warnings and gaps. Hide the company-peer link until
  actual ticker/period data is loaded, avoiding an empty-context destination.
- Replace observed-industry ranks and percentiles with explicit comparison scope.
  TCB/VCB FY2025 support 15 two-company comparison metrics, **2 of 22 observed
  banks**, with median/min/max of that pair and 20 missing companies. TCB-only
  credit indicators show one observation and no distribution. No qualified
  industry ranking or historical sector aggregate is enabled.

## Valuation

FPT's **2023 and 2024 period-end book value per ordinary share** is supported by
same-date ordinary shares and the owners' capital/reserve note. The numerator
excludes non-controlling interests and budget funds; it is not total group equity.
Reported EPS retains its source vintage and VND/share unit. P/E, P/B, market cap
and earnings yield remain unavailable: the private bundle has no matched SSI
price/share/corporate-action vintage. No historical market valuation or backtest
is presented. See [the valuation audit](VALUATION_EVIDENCE_AUDIT.md).

## Acceptance and tests

The supported launchers successfully bind **127.0.0.1:8432** (saved API) and
**127.0.0.1:3431** (private Next server). The earlier exact rejection,
`CreateProcess rejected: blocked by policy`, is historical; it did not recur on
this mission's normal launch. No policy override or alternate port was used.
Core market backend 8431 is absent and was not replaced with invented market data.

Actual integrated-browser desktop checks cover financial navigation, highlights,
balance/cash/profitability/bank health, period selection, annual/quarterly source
switching, FPT book-value/statements/share units/dividends and company-to-peer
navigation. Mobile visual acceptance, chart hover tooltips, exhaustive error
interactions and the surrounding live market experience remain PENDING. Static
and contract checks are reported separately, not substituted for these checks.
See [the acceptance record and manual checklist](DASHBOARD_VERIFICATION_V4.md).

Final machine-readable test outcomes are in
`validation/free-data-v4/TEST_RESULTS.json`: backend regression/calculation tests,
frontend tests, typecheck, production build, 60 stock API contracts, 61 category
responses, ten dividend responses, ten company-peer responses and 144 real-data
EN/VI static financial render cases (including honest unavailable-view fallbacks).

## Remaining work

1. Capture/review additional original annual and quarterly filings for the seven
   priority issuers, particularly VNM/SSI; expand banking peers with comparable
   originals. Current two-bank statistics do not represent all banks.
2. Review historical document comparability and EPS corporate-action adjustments
   before enabling cross-document growth or point-in-time valuation.
3. Recover matched SSI prices and complete share/action evidence; the existing
   quote adapter alone cannot establish a valuation vintage.
4. Complete mobile, tooltip/error-state and wider browser acceptance. Restore an
   approved core development backend separately if company/market context is needed.
5. Obtain applicable public-use permission before exposing these private values
   publicly. This does not block authorized local financial functionality.

No raw financial response, PDF, transcribed source table or private screenshot
is committed. New source acquisition outcomes and exact hashes are recorded in
`validation/free-data-v4/SOURCE_RESPONSE_AUDIT.json`; originals stay in `.local`.
