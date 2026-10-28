# Stock Detail UI V1 — local checkpoint

STATUS: Implemented on `codex/woofi-stock-detail-v1`; local commit only.
BASE: Verified `origin/main` at `bc1f149518d16976b499d61723302b7faff87aca`.

## Actual SStock research

SSTOCK_PAGES_INSPECTED:

- [Stock board](https://sstock.vn/bang-dien): index strip, industry view,
  Top stocks, ticker tables and actual PNJ navigation.
- [PNJ technical page](https://sstock.vn/phan-tich-ki-thuat/PNJ): workspace shell
  and embedded chart frame. The embedded content stayed blank during the bounded inspection.
- [VND research](https://sstock.vn/phan-tich-nhanh-co-phieu/VND): quote header,
  price/volume chart and range/indicator controls, news, company profile/history,
  leadership/subsidiary grouping, dividend dates/ratios and original document links.
  Fundamental tabs inspected: business picture, growth, valuation, income statement,
  balance sheet, cash flow and documents. Technical TradingView and Stockmap shells
  were opened, but their embedded analysis did not finish rendering.
- VND at an actual narrow viewport: stacked header, horizontally scrollable tabs,
  chart and denser statistics. No inaccessible analysis is claimed as inspected.

AUTHENTICATION_LIMITATIONS: No login challenge appeared in the available browser
session. No authentication, paywall or access control was bypassed. Embedded
technical rendering, rather than a verified login requirement, limited that inspection.

REFERENCE_SCREENSHOTS: Local images in
`C:/Users/PC/.codex/tmp/woofi-stock-detail-v1-20261012/`:
`sstock-board-desktop.png`, `sstock-pnj-technical-desktop.png`,
`sstock-vnd-overview-desktop.png`, `sstock-vnd-profile-desktop.png`,
`sstock-vnd-fundamentals-desktop.png`, `sstock-vnd-statements-desktop.png`,
`sstock-vnd-overview-mobile.png`. `sstock-vnd-chart-range-desktop.png` is an
additional chart view, not a dividend screenshot. Dividend structure was inspected
through the page's accessible content and source-document links.

DESIGN_PATTERNS_ADOPTED: Prominent ticker/quote identity, chart-led overview,
compact contextual sidebar, horizontal research tabs, progressive disclosure,
source-linked corporate events and dense financial tables. Woofi branding, mascot,
fonts, themes and chart components are retained. SStock scores, proprietary artwork,
assets, code and numerical data were not copied into the product.

## Implemented slice and data boundaries

WOOFI_STOCK_DETAIL_CHANGES:

- Header with issuer name, exchange, SSI price/change/source timestamp and source
  session; explicit browser-local follow/unfollow using existing Watchlist state.
- Overview / Fundamental analysis / Technical analysis / Dividends & corporate
  actions / Company news tabs, keyboard navigation and hash/back/forward support.
- One reusable price/technical chart, volume and selectable history ranges;
  range/indicator selections survive tab changes. Daily observations stay separate
  from current quotes. Independent reads prevent a financial-provider failure from
  blocking the header and other research sections. Stock reads have 20-second
  timeouts, cancellation and explicit retries; obsolete ticker responses are rejected.
- Financial charts and reported evidence reuse existing backend metrics. Loaded
  annual observations survive tab changes; hidden Recharts views are not rendered.
- Accepted Technical evidence keeps its existing PROVISIONAL/incomplete/retraction
  states. Chart indicators are descriptive, not accepted EOD assurance or advice.
- Company news reuses the qualified persisted Company feed, representative publisher
  articles and direct original links. Community remains separately labeled unverified.
- Corporate actions reuse the append-only repository through a small SELECT-only
  endpoint, without stock onboarding, acquisition, schema changes or source rewrites.
  The latest observation is selected before ticker filtering. Response size is bounded
  to 50 by default / 100 maximum; repository selection scans existing observations.
  The source-observation timeline is ordered by receipt time, not an invented event date.

DATA_AVAILABLE: SSI cached equity identity, current quotes and completed daily OHLCV;
backend market statistics and MA20/MA50/BB/RSI; source-reported annual VCI financials;
qualified News, persisted Community, existing Watchlist receipts and VSDC observations.

DATA_MISSING: Full company narratives, ownership, valuation metrics, full statements,
order book/foreign-flow views and some financial indicators (including observed missing
ROE). Technical acceptance and corporate-action coverage remain incomplete. Explicit
unavailable states replace absent data; no estimated metrics or recommendations.

DIVIDEND_INTEGRATION: Event type, ex-rights/record/payment dates, cash VND/share,
new shares per old share, subscription price, verification state, original source text,
documents, receipt time and source revisions are preserved. Missing ex-rights dates
are never inferred from record dates. Pending, withdrawn and fixture observations
withhold trusted dates/terms while retaining inspectable evidence and fixture labels.

## Acceptance and evidence

DESKTOP_MOBILE_ACCEPTANCE: Actual dev-browser Explore selections opened FPT, PNJ and
MCH with the correct issuer/exchange; all five tabs, keyboard tab movement and hash
reload were exercised. Desktop width 1425 CSS pixels and mobile widths 375/385 CSS
pixels were observed; mobile page width equaled scroll width. EN/VI and dark/light
were exercised. Follow FPT survived reload; explicit unfollow removed only the test
membership on the isolated port-3015 browser origin.

Evidence types:

- LIVE SOURCE READ: Existing approved SSI reader supplied FPT 56,300 VND,
  PNJ 19,200 VND and MCH 141,200 VND, source timestamp October 13 at 14:45 ICT,
  source session closed. These are observed source values, not fabricated opening data.
  Charts/analytics used completed daily observations through October 12, separately labeled.
  Annual financials were real VCI source reads; no independent financial audit is claimed.
- PERSISTED: News/Community/VSDC used an isolated copy of a consistent October 12
  product backup, without a collector. News coverage honestly showed stale source
  checks. PNJ and MCH qualified news linked directly to their original publishers;
  FPT had an honest missing-news state. No publisher fetch or evidence backfill.
- PERSISTED VSDC: MQB showed 400 VND/share, record date October 16, payment October 27,
  unknown ex-rights date, original Vietnamese evidence and
  [VSDC notice](https://vsdc.vn/vi/ad/200942). FPT/PNJ/MCH had no recorded actions in
  this incomplete copied dataset. No absence-of-events claim was made.
- FIXTURE: Endpoint/render tests cover revisions, future receipts, pending corrections,
  withdrawn and fixture observations, source links, missing/zero financial values,
  independent failures, wrong-ticker rejection, lazy deep links and review preservation.
  Existing frontend tests cover qualified News and Technical assurance states.

Before/after local images are in the same artifact directory:
`woofi-fpt-before-desktop.png` (October 12 baseline),
`woofi-fpt-after-desktop.png` (October 13 intermediate overview capture),
`woofi-pnj-news-desktop.png`, `woofi-mch-mobile-vi-light.png`,
`woofi-mch-fundamentals-mobile-dark.png`, `woofi-mqb-vsdc-mobile.png`.
The intermediate FPT capture predates the final metadata timestamp correction;
the subsequently observed UI correctly uses the aware universe timestamp (22:07 ICT).
The new hierarchy replaces the baseline's long vertical stack and adds visible source
session, section navigation, follow control and a dedicated corporate-action view.

TEST_RESULTS:

- Focused new frontend: 14 tests (stock-detail, stock-actions, stock-fundamentals,
  stock-tabs); full frontend suite: 128 passed.
- Focused backend/regression: 32 passed across stock corporate-action API,
  corporate-action context/edges and existing stock APIs. SELECT-only evidence captured.
- Typecheck passed; optimized production build passed with Next.js 16.3.8.
- Browser acceptance used the isolated dev server, not the live runtime.
- Production-serving browser smoke: NOT_VERIFIED. Automatic approval review rejected
  the isolated `npm run start -- --port 3015` command with `blocked by policy` and no
  further explanation. No alternative startup was attempted to bypass that decision.

REVIEW: One focused self-review against this spec and repository standards completed.
Resolved issues: naive metadata timestamp display, inaccessible inactive tab targets,
hidden financial-chart sizing, fixture labels on pending observations, bounded stock
request failure and unnecessary market/history reads on direct non-chart deep links.
No remaining blocking code findings identified. No new dependency or framework.

COMMIT: Local implementation checkpoint on the branch above; exact SHA in handoff.
PUSH_READINESS: Ready for integration review; no push/deployment performed.
NEXT_SAFE_ACTION: Review the local diff/screenshots, then perform an authorized
isolated production smoke before any separately authorized integration or cutover.

Safety: live runtime/configuration/product DB, Downloads WIP, ingestion ownership,
SSI adapter, supervisor, Technical EOD policy and paused FPT automation were not changed.
No feature worktree, collector, migration, public deployment or Git push was created.
