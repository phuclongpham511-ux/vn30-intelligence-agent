# Fundamental Analysis V1 — source-limited research workspace

STATUS: Local implementation checkpoint. Automated checks pass. New frontend
production browser acceptance is NOT_VERIFIED because the preview launch was
rejected by automatic approval review. No push, deployment or canonical cutover.
BASE: Verified origin/main 68ada977b513903a6327eff3edde6d3e10f84ceb.
BRANCH: codex/woofi-fundamental-analysis-v1, using the existing development checkout.

## Observed SStock reference

- Previous valid Stock Detail research inspected the stock board → PNJ flow at
  https://sstock.vn/bang-dien; evidence remains in docs/STOCK_DETAIL_UI_V1.md.
- This task interactively inspected VND and FPT at
  https://sstock.vn/phan-tich-nhanh-co-phieu/VND and the actual FPT ticker-search
  navigation. Fundamental analysis has business picture / growth / valuation /
  financial statements / documents grouping. The business-picture charts adapt
  to the securities issuer's asset/funding/profit categories. FPT growth shows
  adjacent business-performance charts, visible legends and annual comparison.
- The VND income table loaded real source rows, expandable grouped items,
  right-aligned numbers, period columns, an amount-unit selector, and sticky
  period/header chrome while scrolling. The quarter selector offered Q1–Q4 and
  Cả năm; selecting Cả năm changed the loaded table to annual columns. Source and
  reporting context remain visible above the workspace.
- Balance-sheet and cash-flow navigation controls were clicked but did not
  produce a stable independently verified selected table during the bounded
  observation. Their numerical content is NOT claimed as inspected this task.
- FPT was observed at 390×844: stacked controls/identity/metrics and horizontally
  navigable research tabs. Lower chart/table mobile interactions and hover
  tooltip behavior were not independently verified. Chart legend and fullscreen /
  image controls were visible, not reproduced as extra Woofi features.
- https://sstock.vn/huong-dan-su-dung: landing page and quick-stock-analysis
  navigation were accessible; no completed deep financial tutorial is claimed.
- No login challenge appeared in this available browser session; no access
  controls were bypassed. Source branding, artwork, code, financial database and
  scores were not copied into Woofi.

REFERENCE_SCREENSHOTS: C:/Users/PC/.codex/tmp/woofi-fundamental-v1-20261013/
sstock-vnd-business-desktop.png, sstock-vnd-statements-desktop.png,
sstock-fpt-growth-desktop.png, sstock-fpt-growth-mobile.png.

DESIGN_PATTERNS_REPRODUCED: Nested financial navigation within the unchanged five
Stock Detail tabs; compact reported-metric strip; adjacent trend/growth charts;
shared frequency, period-count and amount-unit controls; metric rows against
period columns; aligned numeric values with sticky row labels; secondary source
disclosure. Woofi typography, cool-blue emphasis, chart library and theme tokens
remain. Source-dependent gaps prevent pixel-level fidelity claims.

## Financial provider inventory and availability

Existing VnstockFundamentalDataProvider calls VCI income_statement(period="year",
lang="en", dropna=False), with a one-hour process cache. It normalizes four annual
columns in the observed current SDK response. This path does not persist financial
statements into SQLite. SSI supplies market metadata/quotes/history, not this
financial-statement dataset. No new provider or SStock data acquisition was added.

The existing provider was read for FPT, PNJ and VCB, outside ORM/database startup.
The captured provider audit contains actual normalized annual records. A separate
bounded FPT field-metadata read confirmed isa3 = Net sales, isa5 = Gross Profit,
isa20 = Net profit/(loss) after tax. The PAT field is not relabelled as parent-owner
profit. All amounts remain VND; millions/billions are display units only.

| Field / semantics | FPT / PNJ observed | VCB observed | Treatment |
| --- | --- | --- | --- |
| Reporting periods | Annual 2022–2025 | Annual 2022–2025 | Exact year columns; no quarter/YTD mixing |
| Net revenue (isa3) | Available | Missing | No bank operating-income substitute |
| Profit after tax (isa20) | Available | Available | Source field, not parent-attributable profit |
| Gross/net margin | Existing backend ratios available | Missing | Withheld for financial identities |
| Revenue/PAT YoY | Exact prior-year backend comparison | PAT only | Percent unavailable for zero/negative/missing base |
| Absolute changes | Existing fields, calculated in Python | PAT only | Current and exact prior-year values inspectable |
| ROE | Missing | Missing | Dash / omitted chart series |
| Parent-owner PAT, equity, ROA, EPS, P/E, P/B | Not exposed | Not exposed | Honest coverage disclosure |
| Balance sheet / cash flow | Not exposed | Not exposed | Explicit unavailable statement states |
| Quarterly / TTM | Not supported | Not supported | Quarterly disabled with explanation; no TTM calculation |
| Consolidated / standalone, publication date | Not supplied | Not supplied | Unknown, never inferred from year or retrieval time |
| Financial persistence | None in existing product schema | None | Audit capture and replay are labelled separately |
| Sector master | Product Stock sector/industry often null | Null in observed identity | No invented authoritative taxonomy |

BANKING_HANDLING: Cached company identity and existing sector/industry labels
provide a conservative whole-token exclusion for bank / banking / ngân hàng,
securities and insurance terminology. This is a safety restriction, not a new
verified sector classification. Revenue, generic gross/net margin and revenue
growth are withheld for those identities; PAT remains available. No inventory,
cash conversion, NPL, CASA, NIM or other unsupported banking metrics are derived.
Unknown sector stays unknown; future authoritative sector coverage remains a gap.

## Implementation and assurance

- New GET /stocks/{symbol}/fundamentals/research reads cached Security/Stock
  identity without require_stock/onboarding. It calls only the existing financial
  provider, reuses fundamental_history for ratios/YoY, and adds Python absolute
  changes. It performs no INSERT/UPDATE/DELETE, acquisition-worker launch, database
  migration or persistence. Limit is 1–20, default 8; source/ticker/currency and
  duplicate annual ownership checks fail closed. Existing financial endpoints,
  normalized records and raw inputs remain unchanged.
- The Financial overview leads with latest reported metrics and deterministic
  What changed? values, with no causal narrative, recommendation or Materiality.
  Business performance has interactive series controls, amount/growth charts and
  a matching numeric table. Tooltip, legend and axis units use the same display
  scale. Missing-year placeholders break lines without fabricating observations.
- Financial statements exposes a clearly labelled source-limited income summary;
  balance sheet and cash flow have distinct unavailable states. Financial ratios
  separates profitability/growth from unsupported leverage/liquidity/valuation.
- Annual / quarterly controls disclose actual capability. Loaded-period count and
  VND / million / billion selection update charts and tables together. Read time
  describes provider/cache access, not publication time. Source evidence and
  reporting-basis gaps remain inspectable.
- Five primary tabs, identity, prices, chart/Technical behavior, corporate actions,
  News and Watchlist are untouched except replacement of the Fundamental tab's
  content. Financial data remains lazy, independently failed/retryable, aborted
  on ticker change/unmount and bounded by the existing 20-second timeout.
  Internal controls survive primary-tab changes; hidden Recharts surfaces do not
  mount responsive charts against a zero-size container.
- Responsive tables scroll inside their own region, retain sticky metric labels
  and keyboard focus. Product chrome supports VI/EN; source names/text stay original.
  Existing Woofi dark/light tokens and semantic numerical-change colors are reused.

## Validation evidence and limitations

TEST_RESULTS: 35 focused backend tests passed across financial research, existing
history/stock APIs/provider behavior. SQL inspection proves the new endpoint is
SELECT-only even for a universe identity without a persisted Stock row. Frontend
suite: 135 passed, including owner/currency/period validation, true zero vs missing,
missing-year gaps, source/unknown-basis states, bank-safe fields, statement empty
states and existing five-tab/other-Stock-Detail regression coverage. Typecheck and
optimized Next.js production build passed. Final validation is recorded in the
checkpoint handoff, after the last small contract/label correction.

LIVE_EXISTING_PROVIDER_READ: FPT/PNJ/VCB annual records were obtained through the
existing VCI adapter and stored only in the task's audit directory. No SSI or full
market acquisition was run. API REPLAY: An isolated SQLite online copy of current
product metadata/evidence and those captured records served a bounded VCB research
read; source was explicitly Replay:vnstock:VCI. VCB correctly returned only PAT
and exact prior-year change, with generic financial fields null. The original
product database was opened read-only for copying; it was never initialized or
modified. The isolated API helper was stopped after preview launch rejection.

PRODUCTION_BROWSER_STATUS: NOT_VERIFIED. Automatic approval review rejected
BACKEND_URL=http://127.0.0.1:8016; npm run start -- --port 3016 with "blocked by
policy" and no further reason. No alternative port, dev launcher or proxy was
used to bypass the decision. New Explore→FPT/PNJ/VCB browser flows, chart hover,
physical desktop/mobile, theme switching and screenshot comparison remain
unverified. Build/test PASS is not browser PASS. SStock reference screenshots are
available; new Woofi screenshots could not be captured. No pixel-level fidelity
claim is made.

REVIEW: One focused correctness review checked source mappings, VND units,
comparability and invalid growth bases, bank exclusions, unknown publication/basis,
malformed ownership, old API compatibility, bounded reads, missing/empty states,
chart/table shared data, control retention, localization and scope. No blocking
code/data-safety finding remains. Browser visual acceptance is an explicit gate
still needing a permitted preview.

CHECKPOINT_COMMIT: See task handoff exact SHA; this document is included in that
single local checkpoint. Do not push or deploy automatically.
NEXT_SAFE_ACTION: Run the prepared build in a permitted isolated preview, complete
Explore → FPT/PNJ/VCB financial browser acceptance, then review for integration.
No canonical runtime update is authorized by this checkpoint.

Safety: Canonical runtime source/config/services, product DB, credentials, News /
Community ingestion, collector scheduling, FPT automation, Technical EOD policy
and Downloads WIP were not modified. No collector or new development worktree was
started; no new UI framework/dependency was installed.
