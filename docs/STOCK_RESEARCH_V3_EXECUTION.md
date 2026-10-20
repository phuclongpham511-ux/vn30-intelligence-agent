# Stock Research V3 execution

Base: `a7ae546b224fa3fd3c2f61fb145cb5ccf0749371` on
`codex/woofi-latest-app-integration-v1`. Development source only.

## Phase 1 — completed implementation map

- Reuse `Explore`, `StockHeader`, `LivePrice`, `TechnicalChart`, `FollowStock`,
  `CompanyOverview` and the existing ticker-keyed lazy research panels.
- Reuse `FundamentalTrends`, its five destinations, backend display projection,
  Recharts, statement hierarchy, annual/quarterly/TTM and amount-unit controls.
- Reuse the single `StockIntelligence` read and existing browser-local review
  receipts; Community currently sits inside a collapsed disclosure below News.
- Reuse `StockActions` and stored corporate-action evidence. Record verification
  does not establish per-field original-source verification or actual payment.
- SSI current quotes and completed daily history are separate contracts. No new
  quote/financial acquisition is necessary for this source increment.
- Saved VCI FPT/PNJ/VCB receipts have unknown consolidation and unreviewed applicable
  financial display rights. Zero new live financial metrics may be activated.
  Banking uses customer loans/operating income, never generic industrial ratios.

## Focused implementation

1. Expose Community directly through a new additive `#stock-community` destination
   backed by the same retained intelligence component/read. Preserve old anchors.
2. Keep all research destinations legible on mobile; compact the stock header,
   missing-history state, financial toolbar and source/period disclosures.
3. Replace oversized empty financial chart space with actionable compact states;
   retain qualified charts/legends/observations, separate amount/rate axes and gaps.
4. Add statement expand/collapse controls using only the existing source hierarchy.
   Preserve financial/corporate-action qualification, raw evidence and units.

Exact source areas: `Explore.tsx`, `StockIntelligence.tsx`, `stock-detail.ts`,
`FundamentalTrends.tsx`, `FinancialAnalysisPanel.tsx`, `FinancialResearchCharts.tsx`,
`FinancialStatementTable.tsx`, `TechnicalChart.tsx`, stock-scoped CSS and translations;
focused frontend tests. No News or Market Board source change.

## Runtime and boundaries

Initial listeners: 3430 PID 11944; 8430 PID 23312; 3431 PID 30436; 8431 PID 14596.
The second backend wrapper selects its independent `development.db`, with existing
authorized SSI reads and Technical Pilot disabled. No runtime configuration changes.
Do not rebuild over the running frontend's `.next`; use a separate build artifact.
Prior agent frontend startup was rejected by execution policy. Do not retry through
another shell/launcher. Preserve the current instance while completing source work.
Cloud Browser is not exposed; visual acceptance remains PENDING, no local fallback.

## Phase 2 — completed source increment

Community has a direct additive destination; News/Community/Overview keep one
mounted intelligence read, original story IDs and explicit browser-local reviews.
Stock tabs and financial destinations wrap on mobile. Company-data limitations
are inspectable rather than repeated empty sidebar sections. Financial charts
have compact unavailable states, source actions and bounded tooltips. Statement
groups have expand/collapse controls over the existing source-parent tree.
The existing amount/percent legend had a concrete defect: hiding all amount series
left a currency axis. The axes and unit heading now follow selected series.
Bank growth uses the operating-income title, including its accessible caption.

First targeted run: 49 frontend tests PASS after correcting a new test's mistaken
fixture URL (the existing discussion URL is preserved). Typecheck PASS. Final
regression and isolated webpack build follow in Phase 4.

## Phase 3 — completed saved-data qualification

No adapter, numerical engine, schema, permission evidence or qualification rule
changed. No external provider request or financial cache refresh was made.

| UI fields | Existing contract/evidence | Safe result |
| --- | --- | --- |
| Revenue, PAT, assets/liabilities/equity, cash flow | VCI normalized VND amounts; original field/record hashes, annual/quarterly/TTM and source receipts retained | Saved sample basis UNKNOWN and applicable rights unreviewed: source evidence is provisional, live UI status remains UNQUALIFIED and numeric display null |
| ROE/ROA, margins, YoY and leverage | Existing Python formulas and required input-period/basis gates | No new calculation or qualification; unsupported/incompatible inputs remain unavailable |
| EPS, P/E, P/B, BVPS, market cap | Existing valuation input guards | No unsupported TTM/EPS, dated-price joins or inferred valuations |
| Bank growth/assets | Existing bank profile, operating income/customer loans and bank-safe subsets | Generic industrial revenue, margins/liquidity and new banking ratios remain excluded |
| Publication time and report basis | Original source metadata, unknown precision/timezone/consolidation preserved | Read/fetch time never becomes publication time; source receipts are not issuer filings |
| Corporate actions | Existing stored record flags, source URLs, explicit correction/withdrawal and DEMO guards | Qualified recorded terms/dates remain usable within record-level limits; missing/conflicting/fixture facts withheld. No inferred announced/completed/payment lifecycle status |

Reused nine previously qualified display responses (FPT/PNJ/VCB, annual/quarterly/
TTM) and the saved October 20 FPT HTTP response. New-source rendering exercised
all five financial destinations in EN/VI: 100 renders PASS, zero live QUALIFIED or
DEMO metrics promoted. This is source rendering of saved evidence, not browser
acceptance or a new provider qualification audit.

Current bounded SELECT-only development HTTP reads: cached metadata contains all
three representative issuers; existing Watchlist intelligence has two FPT stories,
no loaded PNJ/VCB stories and no loaded discussions for this sample. The missing
identity is explicitly unavailable. All four corporate-action reads return empty
INCOMPLETE coverage; no history was fabricated or imported. Existing curated
cash/share/bonus/rights cases remain covered by the permanent regression tests.

## Progress

- Current phase: 4 (regression, isolated artifact build, HTTP acceptance).
- Completed: Phases 1, 2, 3; 82 relevant backend tests PASS, one existing
  Starlette/httpx deprecation warning.
- Evidence root outside Git:
  `C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/stock-research-v3-20261020/`.
- During read-only HTTP checks the initial 3431 PID was absent and connections
  refused. No server Stop/Start was issued by this task. 3430/8430 and 8431 are
  HTTP 200 with their original PIDs. Cause of the 3431 exit is not established.
- Updated-build serving and visual acceptance remain unverified. Prior frontend
  launch policy rejection is not bypassed. No runtime interruption performed.
- Next executable step: final frontend regression, isolated webpack build and
  saved evidence manifest, then local checkpoint and one consolidated manual
  frontend handoff instruction if the execution boundary remains.
