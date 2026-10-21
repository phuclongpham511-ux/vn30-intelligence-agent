# Free data first — financial intelligence delivery

21 October 2026. Worktree `woofi-financial-data`, branch
`feature/financial-data-intelligence`, starting commit `86000d3`.

SStock remains the product and information-architecture benchmark. WiData is
optional background research, with no integration, subscription or prerequisite.
This increment delivers usable private saved-data views through the existing
financial engine and Woofi components. It adds no paid service, dependency
upgrade, silent provider fallback, production configuration or background fetch.

## Available real data

| Evidence | Useful result | Qualification |
|---|---|---|
| Existing VCI/vnstock | All original FPT, HPG, MWG, PNJ, REE, TCB, VCB and SSI histories remain selectable; annual, quarterly and TTM period-end amounts | 2,816 original display-eligible presentations across 24 views; original metadata gaps remain explicit |
| HPG original Q4/2025 consolidated filing | Annual 2024–25 revenue/profit/cash flow; 2025 assets/funding; gross/net margins, FCF, conversion, growth, current/quick ratios and debt/equity | 31 canonical reported cells plus two separately retained FX reconciliation cells; original VND, scope and fiscal boundaries evidenced. This is a pre-audit Q4 filing, not the later audited revision |
| TCB original 2025 annual report | Annual 2024–25 bank income, loans, deposits, balances, all three cash flows and reported EPS; 2025 ROE/ROA/growth; accounting loans/deposits | 32 canonical reported cells. Statement amounts are million VND; EPS is VND/share. Consolidation and calendar year are explicit |
| CafeF saved summary | VHM 2022–25 gross profit, PAT, parent PAT, assets, liabilities and equity: eight fields × four periods | 32 partial observations; thousand-VND transport scaling is inferred and labelled. Original currency/unit, scope and publication are unknown; unsupported net revenue and ratios stay unavailable |
| VSDC official saved notices | Three FPT cash-dividend notices, with cash per share, record/payment dates, original notice date and links | Incomplete history; no inferred ex-date, payment confirmation or dividend yield |
| Existing SSI SecuritiesInfo | 406 observed HOSE memberships across 61 exact provider categories, with issuer links and per-metric coverage | Current observed snapshot, not a dated historical taxonomy. No code-prefix hierarchy or effective dates invented |

The two original-report views contain **100 SOURCE_VERIFIED and 100
ACCOUNTING_VERIFIED metric-period observations**: 63 reported and 37 derived.
These are not 100 distinct metric definitions. Publication-time and public-rights
qualification remain independent: both are zero, as is FULLY_VERIFIED.

The preferred nine-issuer/three-frequency selection displays 2,660 observations.
Switching to the original provider preserves all 2,816 original presentations;
the union of selectable original, report and new CafeF presentations is 2,948.
These counts overlap economic periods and sources; none is market completeness.
See [the field-level recovery](EVIDENCE_RECOVERY_REPORT.md) and
[per-metric coverage CSV](validation/free-data-v2/VERIFIED_METRIC_COVERAGE.csv).

## Activated product coverage

The existing Financial Analysis navigation, shared period/unit controls, four
chart panels, financial tables, source disclosures and dividend timeline are
reused. The evidence selector chooses an entire reviewed annual packet or the
original provider history; it never splices source values across periods.
Quarterly/TTM switches continue to select the original provider history.

- Overview, revenue/profit and growth: HPG annual amounts/margins/growth; TCB
  bank-specific income and lending/funding growth. Original eight-issuer amount
  histories remain useful; VHM adds partial annual coverage.
- Balance sheet, cash flow, profitability and financial health: original-report
  inputs unlock HPG FCF and liquidity/leverage, TCB financing cash flow and
  average-balance returns. Unknown-scope provider ratios are still withheld
  individually; an unrelated gap does not blank a reported amount panel.
- Industry and peers: 61 directories and eight categories with saved financial
  evidence, including banks, securities, real estate and manufacturing. Tables
  show usable individual observations, source, scope, verification and missing
  companies. The actual sample has no category with two accounting-qualified
  issuers, so numerical ranks/percentiles remain empty. Historical totals stay
  disabled. This is useful partial industry research, not sector aggregation.
- Dividends: the existing FPT action view reads three official saved notices in
  explicitly enabled private mode; other sampled issuers show incomplete empty
  coverage rather than a claim of no dividends.
- Valuation: existing UI and missing-data behavior retained. P/E/P/B history,
  dividend yield and specialist unsupported indicators receive no invented
  prices, weighted shares, classifications or source vintages.

## Free providers actually investigated

Six CafeF financial requests, two original issuer PDF downloads and three VSDC
notice requests returned HTTP 200 and supplied the new saved adapters. All 32
FPT cross-source comparison cells agreed with VCI within 1,000 VND after the
documented transport scaling (largest difference 499 VND); this validates the
scaling check, not CafeF original metadata or identical accounting vintages.

The installed vnstock 4.0.2 VCI and KBS source code, current official docs, vnfin
and VietFin schemas were compared before choosing fields. One direct KBS finance
request returned HTTP 400/154 bytes; its robots endpoint also returned 400. One
VNDirect request returned HTTP 403/13 bytes. No retries, impersonation, proxy,
alternate host or restriction bypass followed. Neither failed response supplied
financial data. Candidate FPT PDF URLs returned 404 and were not used as proof.
See [provider metadata and source receipts](PROVIDER_METADATA_AUDIT.md).

## Verification and runtime

Actual `main.app` in-process ASGI checks pass for **54 stock views** (preferred
and original provider), **61 industry responses** and **nine dividend responses**.
Independent calculations from the reviewed source values pass. All 54 stock
responses pass the frontend financial contracts and are rejected by its public
consumer. All 61 industry responses and nine dividend pages pass English and
Vietnamese server rendering and their private/public boundaries. These checks
start no listener, use no application database and make zero provider requests.

Frontend regression: 328 passed, one existing skip; typecheck and webpack build
pass. Backend results and the initial subprocess timeouts are recorded in
[test receipts](validation/free-data-v2/TEST_RESULTS.json).

**Runtime/browser/mobile acceptance: PENDING.** The prior preview launch was
rejected before process creation as “blocked by policy.” This mission did not
attempt another launch or a workaround. Read-only inspection at
2026-10-21T03:31:43Z found zero listeners among the eight inspected development/
production/preview ports; this does not establish application health.
[The manual checklist](DASHBOARD_VERIFICATION.md) specifies the supported
launchers and real-data acceptance steps for an approved operator window.

## Remaining work

Prioritize a second original-report issuer in an existing category to unlock
compatible private peer ranks, then reviewed bank notes and securities/property
fields. The TCB report contains loan-quality/deposit notes, but these specialist
rows were not mapped in this increment; their presence is not a validated NPL or
CASA series. Map each indicator only after confirming its exact denominator,
scope, fiscal coverage and field meaning. Add original audited HPG opening
balances before average-balance returns/turnover, and qualified quarterly filings
before derived quarterly/TTM activation. Preserve each document revision.

Resolve applicable source-family public reuse evidence and publication vintages
only for views that need them. Private current amounts and supported calculations
remain useful meanwhile. Run the approved browser/mobile checklist. No WiData
dependency, subscription, push or merge is required for these next steps.
