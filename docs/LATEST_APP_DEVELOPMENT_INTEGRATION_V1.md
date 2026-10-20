# Latest application integration and isolated runtime — 20 October 2026

## Source decision

Integration branch: `codex/woofi-latest-app-integration-v1`.
Application base: `548e10d855b3d470b4eb2019ae027118a0505b14`.

All requested reference commits are already ancestors of this base:

- `a98793a159b203d87937ec3c66b8e3e4b45cad41`: approved full-row Market Board/Overview movement shading, following the existing UI V2, Hot Topics and navigation work.
- `c2dae7ff100b2ab86db60731a63232a04d96c1cf`: per-input financial qualification and original source provenance.
- `ad29339f684035b5e0697a97972a79865d0f98bf`: five Financial Research destinations, guarded projections and source-parent statement hierarchy.

The actual diffs and ancestry were inspected. No cherry-pick, merge, component
rebuild or Supervisor PID-reuse integration is necessary. Both application instances
therefore contain these existing features; this is not a new UI difference from
the already-running 548e10d instance. This commit records the verified integration
and runtime handoff only. Application implementation is unchanged.

## Isolation

The existing frontend/backend at `127.0.0.1:3430` / `127.0.0.1:8430` were both HTTP
200 at the initial inspection and were not stopped, restarted, edited or replaced.
The new worktree has its own frontend `.next` build. Its `node_modules` junction
reuses the existing installed dependencies; no dependency installation or update
was performed against the old instance.

Second frontend: `http://127.0.0.1:3431/` (prepared, not running).
Second backend: `http://127.0.0.1:8431/` (started, HTTP verified).

External runtime folder:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/woofi-latest-app-integration-20261020`.

Its `development.db` is an independent copy of the existing immutable supported
19 October backup, verified against its SHA-256, SQLite integrity and foreign keys.
Neither the first development DB nor the production DB is used by the second app.
Only copied development schema is initialized by normal FastAPI development startup.

The external `serve_backend.py` imports the real `main.app` from this worktree,
sets the explicit isolated database URL, clears SSI credentials, disables Technical
Pilot and overrides only the SSI demand-service dependency to raise the existing
provider-unavailable error. It never creates a Collector, SSI demand thread,
scheduler or replacement API. Existing VCI financial requests and qualification
logic remain unchanged. Missing values are not replaced with synthetic facts.
The frontend build/start configuration uses `BACKEND_URL=http://127.0.0.1:8431`,
provisional SSI flag `0`, and no replay/demo activation.

## Validation completed

- Backend relevant application regression: **157 passed**, no failures/skips.
  One existing Starlette TestClient deprecation warning.
- All frontend unit/contract tests: **305 passed, 1 skipped**, no failures/errors.
- `npm.cmd run typecheck`: PASS.
- `npm.cmd run build -- --webpack`: PASS, including TypeScript/static generation.
- New backend FPT Financial Analysis display endpoint: HTTP **200**, actual
  `vnstock:VCI` response, with existing provenance/basis/rights guards retained.
- No new SSI request, Collector or production lifecycle action.

Saved evidence outside the repository:

- `latest-app-integration-backend.xml` and `latest-app-integration-frontend.xml`
  in the parent external visualization directory.
- `FINANCIAL_HTTP.json` and `ISOLATION.json` in the runtime folder.

## Exact remaining blocker

Host execution policy rejected the normal frontend launch:
`npm.cmd run start -- --port 3431`.
No alternative executable, shell, launcher or policy override was attempted.
A subsequent bounded HTTP/process diagnostic command was also rejected by policy;
its checks must not be represented as completed.

The second backend remains in its supported development exec session (94836).
Second-frontend HTTP, proxy routing, client interactions and route acceptance are
not yet verified. Cloud Browser visual acceptance is PENDING; no local browser
was launched or controlled. A successful build is not product acceptance.

If permitted by the operator's host policy, the user can start the prepared build
with this one PowerShell block (the agent did not execute it successfully):

```powershell
Set-Location 'C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-latest-app-integration-v1\frontend'
$env:BACKEND_URL='http://127.0.0.1:8431'
$env:NEXT_TELEMETRY_DISABLED='1'
$env:NEXT_PUBLIC_WOOFI_SSI_PROVISIONAL='0'
$env:NEXT_PUBLIC_WOOFI_VALIDATION=''
npm.cmd run start -- --port 3431
```

Then verify backend health, frontend homepage, `/#market-board`, `/#market-heatmap`,
`/#explore-stocks`, `/news`, `/watchlist`, `/stocks/FPT`, the frontend stock/financial
API proxy and default-disabled internal SSI route. Hash fragments are client-side
destinations: fetching the homepage alone does not validate their interactions.
Do not restart the first instance or production to complete these checks.

No push, merge, application deployment, production Supervisor/pin/data/journal or
Collector change is included. Financial charts/valuation whose reporting basis,
compatible inputs or applicable rights remain unqualified stay withheld.
