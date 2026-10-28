# Product Acceptance V1 — offline replay preparation

18 October 2026. Product acceptance remains PARTIAL. This is a prepared acceptance environment, not a release or a successful populated-browser run.

## Dependency diagnosis

The preserved `market-v22-3410/ACCEPTANCE_STATUS.md` records source e01066c47dddbddf9bf3bae980c502c263df0902, NEXT_PUBLIC_WOOFI_VALIDATION=replay and fixture backend 3401. Its app/lib snapshot predates Company Overview, corporate-action validation, Fundamental Analysis and Stock Intelligence increments. This provides a concrete old-package candidate for the served stale Heatmap wording; the currently running process/build identity is NOT independently certified.

`/demo/market` constructs synthetic data locally. It does not prove backend availability. Ordinary equity metadata and ticker search use `/api/stocks/universe`. Stock Detail cannot mount its research panels without that identity. Financials, corporate actions and stock intelligence then require their respective existing API contracts. These API routes proxy to BACKEND_URL; the normal source fallback is 8000, which was not contacted directly or configured in this task. News and Community similarly depend on their existing proxy responses.

Three bounded shell reads of the specified 3410 universe/FPT financials/FPT actions URLs returned connection refusals in this run. No application HTTP response was available to distinguish backend 502, missing fixtures or application 500. Do not assert a current backend exception or a current source-qualification failure from that refusal. The earlier unavailable FPT identity also prevented the browser from reaching financial qualification guards, rather than demonstrating a financial frontend error.

Known separate data gate: the saved FPT annual/quarterly/TTM display packets from the previous qualification increment have unknown reporting basis and no QUALIFIED metrics. Their values must stay withheld. No source qualification or financial display guard was changed.

## Prepared environment

`scripts/prepare_product_acceptance.mjs` creates a new external frontend snapshot, without changing the source frontend's .next directory or an existing preview. Its required inputs are the new destination and the existing saved financial evidence directory. It copies app/lib/public and pinned package files, reuses installed node_modules through a junction, and never copies source .env files. It launches no process.

The acceptance snapshot replaces every existing API handler with the same offline allowlist. Unknown endpoints and acquisition requests return 404; there is no network/backend fallback. A local `/api/acceptance` endpoint identifies the replay environment. Existing browser refresh behavior reads local fixtures only; no provider, database, backend, Collector or acquisition scheduler is introduced.

Snapshot-only storage keys are `woofi.acceptance.watchlist.v1`, `woofi.acceptance.recent-searches.v1`, `woofi.acceptance.language.v1` and `woofi.acceptance.theme.v1`. Production source storage keys and semantics are unchanged. The replay never reads, seeds or clears the user's existing Watchlist. Normal follow/unfollow and review operations still use the canonical application logic.

`/demo/acceptance` links to the real Stock Detail and Watchlist routes:

- AAA/ABC/BBB have explicit DEMO company identities, one stable synthetic company story backed by two source articles, and one DEMO discussion with source/time/engagement provenance. No sentiment or materiality is invented.
- ABC uses the shared existing financial-summary fixture, explicitly converted to is_fixture=true/DEMO, with unavailable valuation metrics. No synthetic QUALIFIED live metric is served. FPT replays unchanged saved unqualified financial display packets. Reported metrics are not recalculated in JavaScript.
- ABC action fixtures demonstrate DEMO, pending, unresolved-conflict and withdrawn states. They contain no invented original documents, event dates or cash/share amounts. All stay untrusted and withheld. Original-source confirmed/incomplete rendering remains covered by existing tests; populated browser acceptance of those real-source states is still a gap.
- The news acquisition window remains 72 hours and community publication window remains 24 hours, evaluated at the fixed replay clock 18 October 2026 12:00 ICT. An outside-window story is excluded. Story IDs, revision member receipts and per-ticker review identity stay unchanged across repeat reads. Dedicated tests cover explicit review, serialization/reload, cross-ticker separation, correction novelty and unfollow preservation.

The banner explicitly identifies OFFLINE ACCEPTANCE REPLAY, the fixed clock, DEMO plus saved unqualified evidence and isolated Watchlist storage. Do not interpret any of it as current-session freshness, issuer disclosure verification or display-rights qualification.

## Prepared artifact and validation

Ready build:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/product-acceptance-v1/ready-build`

48 focused frontend tests PASS (7 replay tests plus existing financial-summary, stock-intelligence, stock-actions, watchlist and watchlist-intelligence cases). No assertions were weakened. Typecheck PASS; optimized Next.js 16.3.8 webpack build PASS, including /demo/acceptance, /demo/market, /api/acceptance, Stock Detail and Watchlist. No backend code changed or provider tests/probes rerun.

ACCEPTANCE_MANIFEST.json records base source SHA, app/lib hashes, copied financial packet hashes, dataset hash and intentional snapshot patches. START_INSTRUCTIONS.txt gives the single normal Next start command after separately authorized graceful release of 3410. The snapshot has not been started. Existing 3410 was not stopped, rebuilt in place or modified.

## Browser boundary and handoff

The prior 33 screenshots remain the only product captures. The browser-control interface used in that run is no longer available. The supported Windows computer-use tool opened a private Chrome window but then stopped because it could not confidently determine the current browser URL for policy enforcement. No further computer input or alternate automation route was attempted. No new screenshot or populated interaction is claimed.

Heatmap correction is in the prepared source/build but remains NOT browser-verified. Company Overview, financial guards, action evidence, News/Community cards, explicit Watchlist unread-to-reviewed transition and navigation/reload persistence require actual browser verification. Unit/contract tests do not substitute for those interactions.

Next action: separately authorize one graceful handoff of the development preview on 3410 to the prepared ready-build, or perform the exact START_INSTRUCTIONS.txt procedure after stopping only that development preview. No backend is required. Then resume remaining browser acceptance when supported browser control can identify and operate the target safely. No production actions are authorized by this handoff.

No production lifecycle/configuration, Supervisor, Collector, SQLite, SSI cooldown, Technical Pilot or FPT automation changes; no push or deployment.
