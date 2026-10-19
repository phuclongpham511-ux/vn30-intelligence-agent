# Product Acceptance V1 — 18 October 2026

PRODUCT_ACCEPTANCE: PARTIAL

Browser loaded the running preview at http://127.0.0.1:3410/demo/market against the reported checkpoint 26c0bc48877170c781e886945533ea9c563796fe. Source checkout matched that clean checkpoint at the start. The served bundle's exact source path was not independently identified.

## Browser evidence

Fixture Board and Heatmap rendered across desktop 1440x1000 and mobile 390x844, EN/VI, light/dark. No horizontal page overflow was measured in those combinations. Compact/Detailed tiles, movement grouping, optional synthetic industry groups, numeric volume/value sorting, nine labelled price states, mobile source dialog and suppression of unqualified KL/GT units were exercised. Ceiling/floor states used synthetic qualified-contract fixtures only; heatmap retains its five-bin legend and neutral unknown/stale/missing semantics. No live SSI acceptance is claimed.

Root Overview could not load equity metadata or VN-Index. Both synthetic DEMO01 navigation and the FPT Stock Detail route displayed unavailable states, preventing Company Overview, Financial Analysis, Corporate Actions and Company News/Community acceptance. Watchlist's empty state and review/storage disclosure rendered; FPT search reported unavailable, so follow/review/unread persistence transitions were not tested. News displayed an error; Community controls and loading state were observed without accepting populated items.

## Confirmed defect and narrow correction

Sorted Heatmap incorrectly reused the Board's down-column panel reading instruction. Change only its ordinary-grid footnote to read across each row, then down, in EN/VI. Board and movement-group instructions remain unchanged. Add a focused rendered-component regression for those modes and languages.

Validation: 35 focused tests passed across quote-map, market-board, market-workspace, price-state, trading-activity and industry-preview; typecheck with incremental output disabled passed; git diff --check passed. No optimized build or backend test rerun for this text-only frontend correction.

Browser reload still served the old footnote after the source edit. Consequently the correction is source/SSR-tested but NOT browser-verified. No server restart or alternate port was attempted. Do not mistake the earlier screenshots for proof that the correction was applied to the served preview.

## Artifacts and boundaries

33 browser JPEGs plus matrix measurements and detailed acceptance report:
C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/product-acceptance-v1/

Key screenshots: desktop-board-en-dark.jpg, desktop-heatmap-compact-en-dark.jpg, desktop-heatmap-detailed-vi-light.jpg, mobile-board-source-vi-light.jpg, mobile-unqualified-totals-vi-light.jpg, mobile-stock-fpt-unavailable-vi-light.jpg. Screenshots show the pre-correction preview.

No server process launch/termination, host-policy change, production change, database/journal modification, provider qualification probes, new acquisition, push or deployment. No watchlist state was seeded or cleared. Existing frontend navigation was exercised; backend target configuration was not inspected or changed. Technical Pilot and FPT automation were not changed or re-certified.

## Remaining acceptance

The isolated preview must serve the current source correction and existing qualified replay/fixture contracts for stock metadata/detail, financial display, actions and stock intelligence before the remaining populated flows can be accepted. This does not authorize a backend/Collector launch or connection to production acquisition. Preserve source qualification and missing-data gates. Live-data acceptance remains separate.
