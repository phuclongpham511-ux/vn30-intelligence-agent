# Woofi UI/UX Redesign & News Freshness V1 — progress

## Verified development state

- Worktree: `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/vn30-intelligence-agent`.
- Branch: `codex/woofi-visual-news-v1`.
- Verified base: `135a31fa88f4e275015701024dd40bb585cfcb4f`.
- Local checkpoint: the feature commit containing this final progress file; exact SHA is recorded in the external verification receipt and final handoff. No push or cutover.
- Existing canonical ports 3000/8000 and collector remain unchanged.
- Isolated acceptance harness: frontend 3050, backend 8150, copied product database. No collector or credentials in the harness.
- Evidence: `C:/Users/PC/Woofi-visual-news-validation-20261011` (outside Git; public DTOs, isolated database, audit results, test logs and screenshots).

## Completed milestones

A. News / Hot cards: one existing representative, real same-story thumbnail, compact metadata, separate source evidence page. Primary reporting expansion rows removed. Deduplication unchanged.
B. Related tickers: existing headline associations, three default chips, batched existing market endpoint; original SSI percentage and reference date retained. Unknown is neutral. No news-causation claim.
C. Home Investor Attention: actual unique discussion counts, ticker activity and themes. No inferred sentiment; original evidence stays reachable.
D. VN-Index: approved mascot immediately left, numeric focal point, compact closed/stale/session information, optional available aggregates.
E. Shared movement: green/red/yellow/neutral for positive/negative/zero/missing; readable direction and symbols. Search remains metadata-only where no quote exists.
F. Watchlist: existing activity/review semantics retained, stocks with unreviewed observed items first, quiet sections collapsed, source and storage details secondary.
G. News diagnosis: consistent read-only backup; recomputed and persisted feed identities/order match for every category. Industry legitimately newest Oct 9, Company Oct 10, Market Oct 11. Hot ranks publisher coverage rather than pure publication recency. News reader now refreshes visible tabs every minute and on focus/visibility return without acquiring sources.

## Verified tests and acceptance so far

- Backend: `python -B -m pytest -q`: 934 passed, 1 existing dependency deprecation warning (230.44 seconds).
- Frontend: `npm test`: 96 passed (including real component rendering, archive refresh/pagination, fixture disclosure and discussion-window navigation tests).
- Final typecheck and production build passed.
- 13 isolated API checks passed; 2,416 publisher Article rows and 30 Dividend records retained.
- SStock existing session inspected News and AAA detail. No login automation, code or asset copying.
- Browser: desktop dark EN / light VI Home; mobile light VI Home/News/Watchlist/ACB; source Evidence page; actual SSI PNJ/SHB percentage and Oct 9 reference dates.
- Watchlist explicit review: 3 unreviewed became 2 only after an explicit click; membership and count 2 survived reload in the isolated origin.
- News auto-refresh: remove/restore only an existing derivative-cache row in the isolated database, preserve all publisher dates and raw evidence; already-open Market page gained the restored real headline without navigation/reload/frontend restart.
- Browser stock fundamentals unavailable state intentionally exercised: harness blocks uncaptured provider calls. It is not a demonstrated production failure.
- Zero/missing/stale movement covered with explicitly labelled offline fixtures; no fabricated production price.

## Completed final gates

1. Mobile dark EN Company/Community, Market Show more, MSR filtering and Last 24 hours navigation verified; screenshots retained.
2. Independent Standards and Spec reviews PASS after focused freshness, fixture and window corrections; manual ticker/window persistence browser-tested.
3. Final frontend tests, typecheck and production build PASS.
4. Full report: `docs/WOOFI_UI_UX_REDESIGN_V1.md`, including replay/fixture limits and unchanged backend policies.
5. One local feature checkpoint; original worktrees and canonical runtime preserved. No push or deploy. Next action is owner review and explicitly authorized integration.

Next.js dev generated frontend AGENTS.md, CLAUDE.md and next-env.d.ts changes. Bytes are preserved externally in `next-generated/`; AGENTS/CLAUDE remain untracked and excluded. Production build restored tracked next-env to baseline.
