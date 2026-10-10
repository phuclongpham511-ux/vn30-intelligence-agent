# Technical V1 Stock Detail integration

Status: **COMPLETE** for the approved isolated checkpoint and Stock Detail slice.

## Backend checkpoint

Local branch: `codex/woofi-technical-stock-detail`.
Local checkpoint: `e7acc5998504f4e7e2561fee363ecd500063fd6b`.
Base: `84cb2ef5141010b6e6230f3146f5e1e34216adc8`.

The checkpoint contains the 22 approved backend/test/evidence documentation files
plus the transfer manifest in TECHNICAL_BACKEND_CHECKPOINT_MANIFEST.md.
Normalized staged Git blobs matched all source files. It excludes credentials,
.env files, databases, raw market history and generated market-data snapshots.
849 backend tests and the nine-file identity guard passed before commit.
The original worktree remains at its original HEAD with its original WIP.
All 22 source SHA-256 values and the original database checksum were unchanged
after validation. No push or deployment occurred.

## Public contract and UI

- Additive `GET /technical/{ticker}/daily/operational/latest` accepts no query.
  Bounded SELECT-only lookup prefers the most recent previously accepted job.
  A later pending job does not imply newer coverage or hide an accepted session.
  A retracted most recent accepted job returns its diagnostic; older output
  is not silently resurrected. With no known job, requested_session is null.
- Successful shape remains the existing provisional_packet wrapper. Assurance
  is PROVISIONAL and safe_to_display_as_verified is false. Existing explicit
  session and VERIFIED endpoints are unchanged.
- A same-origin Next GET proxy uses BACKEND_URL and no-store. Neither HTTP
  read layer acquires SSI data or scores events. Infrastructure errors are
  sanitized; no secrets or private references are supplied to the browser.
- The panel sits above the existing price/chart workspace. It shows the actual
  evaluated session, source-check time in Vietnam time, delayed-review wording
  and PROVISIONAL badge. FRESH describes revision-check cadence, not same-day
  or latest-exchange-session coverage. STALE shows Source check overdue.
- Up to three supplied top_insights retain server order. Factual family labels
  and observed direction are shown, with original evidence inspectable.
  No score, signal, price, explanation or return forecast is calculated here.
  NO_MEANINGFUL_TECHNICAL_CHANGE is distinct from incomplete evidence.
- Accepted provenance, snapshot/version identity, checks and limitations remain
  inspectable. Product chrome supports EN/VI; original evidence remains intact.
- Initial load, minute checks while visible, tab activation, focus and manual
  Retry read only persisted output. Revalidation clears displayed old output.
  Abort/unmount/ticker identity guards prevent obsolete results from appearing.
  Failures and retractions remove accepted labels and insights.

## Actual FPT result

The original database was accessed using SQLite mode=ro and immutable=1.
Its checksum before and after was
`20ec8eafdf268f9310e254ce41cdd3fdaa9a792db9e5baebd194a2c5a53a3ec5`.
No database or raw SSI history was copied, and no SSI request was made.

The real API and Next proxy returned snapshot
`3c596852c76a4850ac229606c3aa75ee`, version 1, PROVISIONAL, for
**2026-10-08**, with **NO_MEANINGFUL_TECHNICAL_CHANGE** and zero insights.
Source checked: 2026-10-10 06:30:27.705427 UTC. Source-check status was FRESH
at validation. This does not claim October 9 or October 10 session coverage.

Desktop (1440 × 1000) and mobile (390 × 844) rendered that real packet through
the production Next app and actual latest API/proxy. Non-Technical overview
identity was scaffolded with no prices or financial values; unrelated sources
were deliberately unavailable, avoiding provider acquisition or database writes.
This validates the real Technical integration, not the availability of all
other Stock Detail data sources in a clean worktree.

## Validation

- Final full backend: **854 passed**, including existing V0/V1 regression.
- Focused persistence/latest API: **28 passed**.
- Frontend: **73 passed**, including actual component rendering, safe parsing,
  delayed session, empty/multiple/incomplete states, EN/VI and transport errors.
- Typecheck and optimized production build: **PASS**.
- Real FPT browser test: **PASS** on desktop and mobile; no page errors and
  no Technical panel horizontal overflow.
- Synthetic browser cases: loading, obsolete delayed response, four supplied
  events capped at three, source retraction, corrected version 2, stale check,
  missing calendar, API error and Retry. These are UI fixtures, not live events
  or new production packets.
- Technical identity guard: **PASS (9 files)**; git diff --check: **PASS**.
- Existing Starlette/httpx deprecation warning remains. npm audit reported
  three high-severity findings in existing Next/sharp/source-map-js dependencies.
  Dependency versions and lockfile were unchanged; separate dependency
  remediation is needed before wider rollout.

Browser runner (requires installed Playwright and Chrome, a local Next server
on 3011 and a safely configured persisted backend):

```powershell
cd frontend
node tests/technical-insights.browser.mjs <absolute-playwright-package-path>
```

The local immutable database harness and screenshots were Git-ignored validation
artifacts only. Temporary Next BACKEND_URL configuration was removed afterward.

## Changed integration files

- CONTEXT.md
- routers/technical.py
- src/services/technical_eod_store.py
- tests/test_technical_operational_latest.py
- frontend/app/components/Explore.tsx
- frontend/app/components/stock/TechnicalInsights.tsx
- frontend/app/api/technical/[ticker]/daily/operational/latest/route.ts
- frontend/lib/technical-insights.ts
- frontend/lib/translations.ts
- frontend/tests/technical-insights.test.mjs
- frontend/tests/technical-insights.browser.mjs
- docs/TECHNICAL_STOCK_DETAIL_V1.md

These integration changes were validated again and authorized for a local
checkpoint on 2026-10-10: 854 backend tests, 73 frontend tests, typecheck,
production build, identity guard and diff checks passed. No push or deployment.

## Remaining limits and next milestone

The clean checkout intentionally has no credentials or production database.
Normal local operation must connect BACKEND_URL to a configured backend reading
the existing accepted evidence store; missing infrastructure yields unavailable
state. This slice does not create historical sessions for other tickers.

The unchanged six-hour matching-read and 24-hour post-bulletin publication rules
make Technical review delayed. Future accepted sessions require independently
qualified calendar/publication evidence, bounded job ingress and a running
worker. Worker supervision, future-session acquisition and wider coverage remain
operational rollout work. No same-day policy tier has been introduced.

Next milestone: remediate existing
frontend dependency findings, and qualify supervised bounded acquisition for
future sessions/tickers. Push/deployment still require separate authorization.

## Hardening follow-up — 2026-10-10

Integration was locally checkpointed as `162d1de`; compatible dependency
remediation was checkpointed as `beb3b9a`. Current audit is zero vulnerabilities.
The preserved validation above describes the earlier integration milestone.
Final hardening validation passed 897 backend tests, 73 frontend tests, typecheck,
production build and the real FPT desktop/mobile browser runner with Next 16.3.8.
Supervised FPT-only discovery/acquisition and durable recovery are documented in
TECHNICAL_SUPERVISED_EOD_V1.md. No same-day tier, push or deployment was introduced.
