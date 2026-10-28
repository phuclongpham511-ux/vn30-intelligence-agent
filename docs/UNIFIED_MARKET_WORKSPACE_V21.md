# Approved Unified V2.1 — development implementation

Design approval is explicit in the user's implementation request. Scope is local development and isolated acceptance only; no push, integration into origin/main, runtime-pin change or deployment is authorized.

## Milestone 1: source and implementation decisions

Use the existing `woofi-visual-news-v1/vn30-intelligence-agent` worktree on `codex/woofi-market-board-correction`, HEAD `b5af18c30f722406f884a0d2ef07c4bc1d87e9e9`. Local `origin/main` resolves to `1d7706a90f9270fa91e245c671ccb7ed9ce98777`; the current production config's canonical SHA matches it. This is a local-ref/config observation, not a remote fetch or a production stability claim.

Preserve the three existing modified files (QuoteMap, translations, quote-map tests) containing the unknown-coverage error fix and the two generated untracked frontend instruction files. No reset/stash/new worktree is needed.

Source of truth inspected: approved `unified-v2-1` HTML/JS/CSS, screenshots and CHANGE_REPORT.md under the chat's visualization package; repository AGENTS.md, CONTEXT.md, frontend instructions/DESIGN.md and existing quote/index/universe/research contracts. The prototype provides visual layout only. None of its prices, ticker lists, classifications or illustrative publications may enter product code.

Implementation slices:

1. Extend the existing quote presentation helpers with movement organization and five source-percentage bins; verify numerical sorting, stale/missing/unknown semantics and filtered-sample counts.
2. Reuse `useEquityPage` once and `LivePrices` once for the selected bounded page across Overview/Board/Map. Reuse the current index hook, original provenance, metadata and research routes. One global ticker search drives metadata discovery; no second quote architecture or acquisition loop.
3. Apply compact market-route shell/nav/context, ordinary three-panel tables, optional movement groups, equal-area stock map and compact future-data disclosure. Keep News/Watchlist functionality and all existing Stock Detail research tabs/data paths.
4. Run focused tests, required typecheck/build and relevant frontend regression once; review the diff; use an officially authorized loopback-only application preview pointed exclusively at a deterministic no-DB/no-provider fixture backend. Stop if execution is denied. Browser evidence must be labelled simulated, with live acceptance separate.

Runtime boundary: production config/source, Supervisor processes, Collector singleton/mutex, SQLite, provider acquisition/cooldowns and Technical/FPT settings are read-only throughout. Any remaining source integration, verified backup, ownership and live-session gates precede a separately authorized release.

Implementation and validation results will be appended after the work is complete.

## Milestone 2: implemented scope

`MarketWorkspace` replaces the mixed Explore homepage. The existing global
`StockSearch` drives its metadata query through a small React search context;
there is no duplicate search field. `useEquityPage` and a single selected-page
`LivePrices` provider remain the quote/discovery contracts. Workspace hash modes
retain that mounted lease; ordinary numeric sorting and optional movement
organization survive metadata filter/loading transitions. News and Watchlist
retain their previous service and navigation contracts.

Market routes use the approved compact shell, context, density, language/theme
tokens, source controls, and inactive future-data disclosure. VN-Index comes from
the existing qualified index endpoint; a second VN30 index value is not invented.
Original observation/session times and the previous unknown-coverage fix remain.
The map uses exactly five source-percentage bins and neutral old/missing cells.
Stock Research keeps all five existing sections, follow behavior, chart/history,
financial engine, company news and evidence. Its empty history canvas is compact
and hidden behind the explicit missing/error/loading state; populated charts keep
the existing library/data paths unchanged.

## Milestone 3: engineering and browser evidence

- Focused numerical/presentation tests cover partitions, filtered counts, exact
  percentage boundaries, numerical sorting, original values, stale/missing and
  failed-transport coverage. Existing source/error tests are preserved.
- Final frontend regression: **175 passed, 1 skipped, 0 failed** (176 tests).
  Explicit TypeScript no-emit check passed. The supported webpack production
  build passed. Default Turbopack crashed while starting its CSS worker even
  after official escalation; the existing checkpoint also used webpack. No
  permission denial was bypassed and no alternate preview port/launcher was used.
- The official escalation mechanism approved fixture-only backend 3401 and the
  built application on loopback 3400, with BACKEND_URL fixed to 3401 and an
  explicit `SIMULATED UI VALIDATION — NOT LIVE SSI` banner. The fixture backend
  does not open SQLite, acquire data or forward requests to production.
- Actual browser screenshots cover all four screens, 1440×900 and 390×844 CSS,
  EN/VI and light/dark (32 cases). No horizontal page overflow was observed.
  The ordinary board's first row is approximately 337px desktop / 390px mobile,
  compared with the approved prototype's 286px / 358px: qualified membership,
  coverage and session context explain the additional chrome. Research retains
  richer real functionality rather than copying the prototype placeholders.
- Actual interactions exercised ordinary sort, groups, filters/search, map entry,
  stock routes, source dialogs/Escape/focus return, research tabs and source
  limitations. The mixed fixture produces 14 advancing / 9 declining / 5
  unchanged / 2 stale-or-missing; filtering to one current stock produces 1/0/0/0.
- Real browser cases distinguish pending requests, HTTP failure, timeout, metadata
  loading/failure, confirmed missing prices and old-session neutral data. They
  are simulated UX evidence, not live SSI or production acceptance.

Artifacts: the chat visualization package's `woofi-design-review/application-v21/`
contains the actual screenshot gallery, design comparisons, geometry records,
state evidence, detailed report and PNG manifest. Local fixture source/scenario
and test log remain in the neighbouring `market-board-acceptance` directory.

## Milestone 4: checkpoint and release boundary

This work is a resumable local development checkpoint. No push or deployment is
authorized. The commit includes the prior tracked error-state correction with the
approved UI; the pre-existing generated frontend instruction files remain in place.

Live data acceptance is **PARTIAL**: October 17 is outside a normal Vietnamese
trading session, and no provider acquisition/cooldown was forced. The frontend
contracts and saved metadata are not proof of current VN30 coverage or freshness.
Financial/history/news availability still depends on their qualified source paths;
fixtures exercise honest missing/unavailable cases without synthetic financials.

Production remained on canonical `1d7706a90f9270fa91e245c671ccb7ed9ce98777`.
Read-only inspection found the pre-existing Supervisor record in `blocked` phase,
reason `WINDOWS_PROBE_TIMEOUT probe=native_collectors timeout_seconds=5`, while
production listeners and the existing Collector chain were present. This task
does not repair that condition or certify runtime stability. Technical Pilot and
FPT automation were not modified.

The final read-only PID check did not find the recorded Supervisor PID 25280.
Backend 15760, Frontend 12208 and Collector root/native child 8628/30700 retained
their original creation times. The runtime pin and epoch were unchanged. Treat
Supervisor availability/ownership as an unresolved release blocker, not as a
healthy runtime certified by this UI task; no restart or lifecycle repair was
attempted.

Remaining release gates: user review of actual development screenshots; live
normal-session coverage/source/freshness and provider failure qualification;
normal source integration/review; resolution and verification of Supervisor
ownership/readiness and singleton state; verified product SQLite backup; explicit
release authorization. Do not deploy to complete any missing acceptance gate.
