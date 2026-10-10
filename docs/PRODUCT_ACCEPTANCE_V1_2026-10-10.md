# Woofi end-to-end product acceptance V1 — 2026-10-10

Base: `035ab8d7ea4ec4d8d2d1c1eed48ce5397a9e0ce6` (verified remote main).
Result: local integrated acceptance completed with operational limitations;
production readiness is not asserted. No push or deployment.

## Runtime and evidence boundary

No existing Woofi HTTP server or Python worker was running at preflight.
The latest production Next build ran on localhost:3013 against an isolated
FastAPI service on localhost:8130. SQLite backup reads copied the existing
Downloads database; credentials were loaded privately from its configuration
into process memory, never printed, copied into repository files or committed.
All schema changes, refresh intent and acquired evidence stayed in ignored
`data/product_acceptance/` databases. Downloads main and other worktrees were
never checked out, reset or written by this task.

The pilot database in the Stock Detail supervision worktree was backed up
read-only. It had accepted the October 9 FPT session at 14:05:28 UTC, before
this task read it. The latest reader returned a fresh PROVISIONAL packet with
one moving-average transition. The original product database had no accepted
packet. Only job, retrieval-receipt and accepted-snapshot rows were copied into
the isolated acceptance database to test explicit integration. Supervision and
worker leases were not copied; no FPT supervisor or Technical producer was run
against that evidence. This demonstrates real packet rendering in a local
acceptance runtime, not deployment or existing production database wiring.

## Live verified behavior

“Verified behavior” below means observed API/UI behavior and inspected provenance,
not certification of market finality or the truth of publisher/community claims.

| Surface | Actual observation |
| --- | --- |
| Home / VN-Index | Authenticated SSI read: 1,735.09, -3.88 points, -0.22%, October 9 14:45 Vietnam time. Saturday October 10 correctly showed closed/stale. Current aggregate volume/value stayed unavailable. |
| Index research | Real SSI daily history loaded, 3M/6M controls worked; October 9 OHLC and volume were inspectable. Completed history volume was 819,277,964 shares, distinct from unavailable current-minute aggregates. |
| Explore | 1,522 ordinary-equity metadata records: 406 HOSE, 299 HNX, 817 UPCOM. Server filtering returned VN30=30, VN100=100, HNX30=30; composed HOSE/VN30 and bounded ten-row pages worked. |
| Search/history | Actual FPT exact match ranked first, followed by related company-name matches. Keyboard selection navigated to FPT. Browser-local recent selection and Clear history worked. No full-universe dropdown was fetched. |
| News | All 20 enabled Vietnamese feeds successfully refreshed in bounded canonical News cycles. Company, Industry and Market archives returned 9, 3 and 12 first-page Stories respectively in the final snapshot. Market Show more grew visible rows from 10 to 20; snapshot API pages had no overlapping Story IDs. Broken/missing images can reduce visible rows below the requested page size. |
| Hot Topics | Actual refreshed Stories qualified with 2–3 independent publisher groups and same-Story images. Promotion retained original source titles, links and source counts. Initial empty qualification recovered after worker refresh. |
| Community | Final acquisition succeeded for F319 (29 items), 24HMoney (12) and Chứng Sỹ (2); FireAnt remained disabled. All three enabled sources were healthy. Only one unique discussion qualified in Today/Last 24 hours, yielding two overlapping extractive themes for MSR. Unverified labels, original Vietnamese evidence, explicit windows and partial-sample semantics remained visible. |
| Stock Detail | FPT market close 57,900 VND agreed with the last of 124 completed daily chart observations; -3.02% return, source/date and stale quote were consistent. Annual 2022–2025 vnstock:VCI financials loaded; 2025 revenue 70.1tn and net profit 11.2tn VND, with ROE unavailable. Quick News used actual ingested reporting. |
| Watchlist | Real FPT/MSR membership, News/Community evidence, accepted FPT Technical event, explicit source review and reload persistence worked. The corrected News item reopened as “Updated since review”; the unchanged reviewed Technical item stayed reviewed. MSR Community review persisted without reviewing its News; remove worked. Quote/source/date agreed with Stock Detail. |
| Navigation/localization | Home → index, search → Stock Detail, News section switching, shared navigation → Watchlist, Watchlist → Stock Detail and back worked. EN/VI and light/dark controls preserved source text. Mobile 390×844 Home/index had no horizontal overflow; desktop 1440×1000 Watchlist was inspected. No captured browser error/warning entries were returned. |

## Live provisional behavior

FPT October 9 Operational EOD is **PROVISIONAL**, not VERIFIED. Both Stock
Detail and Watchlist displayed the same moving-average transition, evaluated
session, revision-check time and version. The real reader reported
`safe_to_display_as_verified=false`. Other tickers with no accepted snapshot
returned diagnostics. Scoring, six-hour matching-read gate, 24-hour publication
gate, retraction policy and accepted-packet selection were not changed.

Community is live acquired **unverified discussion evidence**. Source health and
successful transport do not substantiate assertions in an investor post.

## Defect and local fix

Actual CafeF article `188261008155658978` changed its title and URL slug between
the original persisted snapshot and the current RSS feed. The old implementation
created a new Article/Story and Watchlist counted two identities for one article.
An unchanged exact URL also failed to apply a changed headline.

Ingestion now recognizes the observed CafeF numeric article suffix only on
`cafef.vn`/`www.cafef.vn`, within the same registered source. A known native
identity or exact URL updates current title/link/tags and the worker projection
without replacing Article/Story identity, original publication/first-seen date,
publisher provenance or Story activity date. Different IDs and host lookalikes
remain separate. Another publisher cannot overwrite the original publisher's
headline. This is a current correction seam, not an immutable correction ledger
or a generalized publisher-ID parser.

A fresh backup of the original real database was refreshed against the actual
CafeF feed with the fix: one native article remained, the Story identity stayed
the same and its revision changed. Watchlist showed one updated item at its
original October 8 time. Existing duplicate records created before this fix
are not automatically merged or deleted; operator-reviewed reconciliation would
be required for such databases. The original source database was not migrated.

## Validation

- Nine API acceptance assertions passed against real available data: bounded
  discovery, composed VN30/HOSE filtering, FPT search order, chart/market
  consistency, real PROVISIONAL envelope, Watchlist response, News page bound,
  stable disjoint News pages and unknown-Technical diagnostics.
- Focused News/adaptive/correction/Watchlist regressions cover identity changes,
  age preservation, unrelated native IDs, host lookalikes and publisher ownership.
- Frontend regression: 87 passed; typecheck passed. Production Next 16.3.8 build
  from the exact supplied frontend base was served; the local fix changes only
  backend News ingestion, its tests and this report.
- Full backend regression and final focused results are recorded in the local
  checkpoint validation below. The existing Starlette/httpx warning is retained.
- Git whitespace checks and protected Technical/EOD code identity checks passed.

Fixture-only coverage remains the controlled regression suites and previous
synthetic browser scenarios for errors/retries, revisions/retractions, obsolete
responses, pagination extremes, storage corruption and unsupported tickers.
Those scenarios do not establish live source coverage or production readiness.
The legacy `/stocks/FPT/news` API still returns an explicitly flagged local
sample; the inspected Quick News UI reads the real News archive instead.

## Operational limitations and next milestone

The first isolated canonical cycle reported News `OperationalError` and F319
`TimeoutError`. A News retry and four subsequent bounded News cycles succeeded;
a later Community cycle succeeded for all enabled sources. The initial database
error's driver detail was not captured, so its root cause is unresolved and it
must not be described as fixed. Source failures and stale/empty UI states were
observable rather than hidden.

All market observations occurred outside the trading session. Authenticated
bootstrap/history was exercised, but active-session trade streaming, reconnection
and intraday freshness remain unverified live. Metadata/index membership remained
cached with disclosed sync times; no market-wide EOD coverage is claimed.

There is no always-on worker/OS supervisor in the original runtime and Technical
evidence still requires explicit database wiring. Browser-only Watchlist storage,
partial issuer classification, bounded public discussion coverage, absent native
News/Community retraction ledgers, delayed single-ticker Technical coverage and
uncertified vendor historical vintage remain product limits.

Recommended next milestone: an operator-reviewed runtime reliability acceptance
slice with one explicit data configuration, supervised canonical News/Community
worker, supervised FPT packet wiring, sanitized database-failure diagnostics and
a market-open quote/streaming acceptance run. Keep Technical scoring/EOD policy
unchanged. Wider Technical coverage and production rollout require separate review.

## Local checkpoint validation

Final source validation: **917 backend tests passed** (190.44 seconds),
**66 focused backend tests passed**, **87 frontend tests passed**, and frontend
typecheck passed. The production frontend build at the unchanged base was served
for actual runtime UI acceptance. One existing Starlette/httpx deprecation
warning remained; no failing tests were suppressed. Credential-pattern scan,
Git diff whitespace checks and unchanged protected-code checks passed.

The checkpoint includes only News normalization/ingestion, regression tests,
CONTEXT.md and this report on local branch `codex/woofi-product-acceptance-v1`.
Runtime databases and detailed acquired API evidence remain ignored under
`data/product_acceptance/`. Remote main remains the supplied base. Temporary
acceptance services were stopped after validation.
