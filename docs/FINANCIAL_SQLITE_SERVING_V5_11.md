# Financial SQLite serving V5.11

Baseline `b72d64d`, branch `feature/financial-data-intelligence`; 23 October 2026.
The existing private Financial API can now read the V5.5 journal through the
existing Financial Engine and dashboard response contract. Default serving
remains saved captures; SQLite is an explicit private development switch.

## Activation and rollback

From the repository root, with the existing prepared private capture directory:

```powershell
$env:WOOFI_PERSONAL_FINANCIAL_READS = 'sqlite'
$env:WOOFI_PERSONAL_SQLITE = (Resolve-Path '.local/financial-research-v55/financial.sqlite').Path
.\.venv\Scripts\python.exe -B -m scripts.serve_personal_financials .local/free-data-v4-ready
```

The supported launcher uses the one `main.app`, binds only `127.0.0.1:8432`,
disables forwarded-header authorization, sets development/private flags and
rejects public/source acquisition routes. The adapter also requires development,
personal-research opt-in and the numeric-loopback bind. Existing socket-peer and
Host checks stay active. SQLite errors do not silently fall back to source files.
Missing/invalid database configuration returns 503; absent ticker/revision or
frequency returns 404. No database is created, migrated, repaired or written.

Rollback: stop the private launcher, set
`$env:WOOFI_PERSONAL_FINANCIAL_READS = 'captures'` (or remove that variable), then
restart the same command. `WOOFI_PERSONAL_SQLITE` is ignored in capture mode.
This switch does not change product database configuration, journal selections,
source files, formulas, public APIs or production processes. Unknown flag values
fail closed. Both synthetic regression and a real FPT quarterly API check verify
SQLite → captures → SQLite rollback parity (34 rows, all nonvolatile response
fields equal). An unavailable SQLite path returns 503 despite a valid capture
fallback directory, and creates no file. The database hash remains unchanged.

The existing frontend launcher can be used after its production build:

```powershell
$env:WOOFI_PERSONAL_RESEARCH = '1'
$env:APP_ENV = 'development'
$env:BACKEND_URL = 'http://127.0.0.1:8431'
$env:WOOFI_PERSONAL_BACKEND = 'http://127.0.0.1:8432'
node frontend/scripts/serve-personal-research.mjs
```

It binds `127.0.0.1:3431`; the financial view works independently of missing
market identity at `/stocks/FPT#stock-fundamentals`. Market/core requests still
use the separately configured backend 8431. No market acquisition is initiated
by this integration; that backend was not started in the acceptance pilot.

## Read and revision contract

`sqlite_research_packet(journal_path, ticker, frequency=..., evidence=...,
source=..., capture_id=..., capture_directory=...)` reuses `MetricJournal` in
read-only/query-only mode. It returns the exact stored `FinancialPacket` and
source capture digest, with annual/quarterly observations, all statement families,
source codes, parents, units, nulls, metadata and provenance intact. The existing
engine computes metrics; stored metric rows are not used as a second calculator.
TTM processing reuses existing engine rules over saved quarterly observations.

Each response uses one immutable whole capture. There is no reconstruction from
individually selected rows, no cross-source filling and no latest-hash heuristic.
An explicit capture must belong to the requested ticker/source/frequency. It is
filtered before loading other revisions. A fixture cannot enter the private view.

Where the legacy capture index exists, its digest pins the matching database
revision without rereading source files. A missing pinned revision fails closed.
An annual-only legacy packet does not hide a distinct quarterly database packet.
Without a usable index pin, provider mode/quarterly mode selects an unambiguous
provider capture; preferred annual mode favors an unambiguous original. Multiple
remaining revisions require explicit selection. A shorter revision never replaces
a longer history merely because it was fetched later.

The existing private route accepts optional `source` and `capture_id` query
parameters in SQLite mode. For example an explicitly selected original VJC
quarterly capture uses `/personal-research/financials/VJC?frequency=quarterly&capture_id=...`.
These selectors are available through the direct private API; the unchanged
dashboard retains its preferred/provider control and does not add a revision UI.
Unavailable optional provider hints do not invalidate a validated original.
Private responses retain `Cache-Control: private, no-store` and noindex headers.

## Real acceptance and parity

The pilot used the unchanged existing journal and capture bundle; private
artifacts are under `.local/financial-serving-v511/`.

- FPT, TCB and SSI: preferred/provider annual and quarterly paths match stored
  capture packets and response contents, including 34-quarter histories.
- VHM: both annual paths match CafeF captures; quarterly SQLite reads use the
  existing VCI packet, adding the quarterly serving coverage absent in CafeF.
  Annual and quarterly sources remain explicitly different; no splicing occurs.
- VJC: the explicit V5.10 original revision reads through the private route and
  supports the same five qualified quarterly YoY insights. The existing insight
  service remains a private Python seam; no new insight UI or endpoint is added.
- **14 packet/response parity cases** compare all fields except volatile
  `read_at`. Source metadata, nulls, statement hierarchy and metric values match.
  The API's existing available-period-type hint can additionally mention a
  separate provider frequency; this hint does not add provider amounts.
- **30/30 dated VN30 issuers**, **60 annual/quarterly private API requests**,
  all return valid financial rows/statements and private cache policy.
- Integrated-browser checks on the isolated stack verify FPT annual original
  reports, switching to quarterly VCI, 2018-Q1–2026-Q2 history, charts, source and
  qualification warnings, and the income statement table. Screenshot:
  `.local/financial-serving-v511/browser-quarterly.png`. This is exercised-flow
  acceptance, not exhaustive visual acceptance for every issuer/chart or viewport.
  Other representative issuers were verified through API/contracts.

The temporary private acceptance listeners at 3431/8432 were stopped after the
browser checks. Existing production/runtime listeners were not restarted.

Database integrity is `ok`, foreign-key errors zero. All **1,635** pre-existing
private/unrelated files, including the SQLite database itself, match their
pre-pilot SHA-256. No schema, statement, selection or metric revision changed.
No new financial acquisition or private-document migration occurred. Tooltip
modifications and other unrelated worktree changes remain outside this commit.

## Validation and limits

Focused adapter tests cover exact revision selection, 34-quarter/null/hierarchy
parity, missing coverage, invalid database, rollback, production denial, private
API equality, optional-source ambiguity and unrelated corrupt revisions.
Frontend regression: **338 passed, one existing skip**; typecheck and production
build exit 0. Existing frontend components and response contracts need no edits.
Final backend regression: **1,722 passed and 32 subtests passed**, exit 0, in
279.57 seconds; one existing Starlette/httpx deprecation warning. Focused
adapter/storage/private API/insight regression: **91 passed**; the final adapter
suite itself contains **10 passing tests**. No frontend code or chart redesign
was required. Full logs and exit statuses remain private under the pilot root.

An initial backend run exposed an outdated test mock target after the read switch
was introduced. The test now patches the underlying saved-capture service seam
and continues to verify the default capture route. Independent standards review
also identified an optional-provider edge case; it and explicit capture isolation
were fixed with regression tests. Final standards review: **0 outstanding
findings / 0 smells**. Spec review: **0 actionable findings**.

Remaining limits: the fixed August 2026 universe is not a continuously updated
membership feed; source comparability/rights limits remain; ambiguous revisions
require explicit capture selection; industry/peer services still use their saved
capture paths; private rendering does not authorize public display. Full browser
acceptance beyond the exercised FPT flow remains pending. No production changes,
push or merge are part of this delivery.
