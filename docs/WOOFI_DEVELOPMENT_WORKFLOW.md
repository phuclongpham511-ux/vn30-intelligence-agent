# Woofi development and stable workflow

## Everyday command

From the worktree being edited (currently
`C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-financial-data`):

```powershell
node scripts/dev.mjs
```

Use `http://127.0.0.1:3102/news`; backend docs are at
`http://127.0.0.1:8102/docs`. Installed `frontend/node_modules` and the worktree's
`.venv` are reused. No dependency installation is performed. For an explicitly
selected installed Python, set `WOOFI_DEV_PYTHON` before the command.

The terminal stays open. Ctrl+C (or typing `stop` then Enter) stops only this launcher and its owned backend;
EOF from the launcher also gracefully stops the backend after an unexpected
parent exit. Occupied 3102/8102 ports cause refusal, never process replacement.
There is no daemon, autostart, PID-file adoption or force-kill recovery.

## Root cause and reused tooling

The stable configuration at `C:\Users\PC\WoofiRuntime\config\runtime.json`
pins `a98793a159b203d87937ec3c66b8e3e4b45cad41`. Its frontend/API run on 3000/8000.
This is deliberate release immutability, not a broken hot-reload mechanism.
The earlier 3101 preview runs `next start` from a separately built AppData snapshot;
it is not a development server. Its API proxy still uses the old 8000 backend.
`frontend/app/api/news/[[...path]]/route.ts` forwards to `BACKEND_URL`, defaulting
to 8000, without requiring a shared source identity. README's older individual
commands also default both development services to stable ports. Together these
allow a newer UI and older API to be combined accidentally.

News V3 already implements `q` and `research_category=ALL` in this feature
worktree. No new API migration or backend feature is needed for development.
The pinned stable API rejects ALL and ignores q. That difference belongs in
release acceptance, not every UI-edit cycle.

Existing pieces reused: Next's documented custom server / Webpack Fast Refresh,
the single root `main.app`, existing FastAPI routes and dependency overrides,
the SQLite schema, and News's injected-fetch offline fixture seam. Prior
`LATEST_APP_DEVELOPMENT_INTEGRATION_V1.md` established isolated databases but used
manually prepared snapshots. `serve-personal-research.mjs` is a specialized
saved-private-financial launcher with fixed ports, not the general dev workflow.

## Environment boundaries

| | Development | Stable |
|---|---|---|
| Source | Current worktree, including WIP | Approved immutable release |
| Web / API | 3102 / 8102, loopback only | Existing 3000 / 8000 |
| Frontend | Source mirrored automatically; Next dev / Fast Refresh | Built release |
| Backend | Same worktree's main.app; restart command for Python changes | Supervisor-owned process |
| Data | Fresh synthetic SQLite for each run | Protected canonical product database |
| Acquisition | Disabled; no worker or provider connections | Existing canonical collector |
| Release operations | None | Existing approved promotion and rollback |

The launcher creates `%LOCALAPPDATA%\Woofi\Development\run-*`. Packaged Windows
apps may resolve this to the app's LocalCache directory. Each run contains only
DEMO SQLite, identity metadata and a generated frontend workspace. Runtime folders
are retained; there is no automatic recursive cleanup or data import. No existing
database can be supplied to this command.

Frontend app/lib/public/tests are automatically mirrored every 500 ms. This is
necessary because Next's Windows route watcher did not discover a junction-linked
app directory. Changes and removals propagate only to files created by this mirror.
node_modules is a dependency junction. Generated next-env.d.ts, tsconfig changes
and .next output stay outside the worktree, preserving existing WIP. Symlinks,
.env files, SQLite/database files and PDFs are excluded from the source mirror.
Config and dependency changes require a restart. The mirror fails closed if it
cannot synchronize; it does not keep silently serving an old frontend.

The development-only banner labels DEMO data and the startup branch/commit.
`/__woofi_dev__/identity` on both ports exposes the same run ID, worktree, startup
SHA and data scope. The frontend starts only after the matching backend identity
is verified. The SHA describes the startup base; uncommitted frontend edits are
live. Restart after branch switches, commits, or backend changes to refresh the
identity and Python imports.

The child environment excludes credentials, provider settings and private paths.
Backend Settings explicitly disables .env loading. Private financial and ingestion
routes are denied in this process. Provider dependencies return unavailable.
A process-local Python audit hook denies outbound connections, external DNS,
subprocess launches and SQLite connections outside this run's own database.
No collector is started and no stable Supervisor policy is changed. Local Host,
Origin and browser fetch-site checks reject foreign-site access.

Fixtures are clearly marked DEMO in the banner, publisher and headlines. The
synthetic security rows simulate the existing SSI identity contract just as the
offline tests do; production qualification rules remain unchanged. These rows are
not evidence of actual securities, financial results or provider observations.
Real financial research, live prices, and acquisition remain unavailable here.
Watchlist/local preferences are isolated by the separate browser origin, but can
persist across development runs; the synthetic backend database resets each run.

## Three daily tasks

1. **Modify and preview UI:** run the command, edit frontend source, and inspect
   3102. Fast Refresh applies edits without commit/push/build/cutover. The first
   page compilation can take several seconds. Use the DEMO banner to distinguish
   this from the stable app.
2. **Modify frontend and backend together:** edit both in this same worktree,
   add/use focused offline tests, then Ctrl+C and rerun the command after Python
   changes. Both services start from that worktree with a new matching run ID and
   fresh DEMO DB. Never point the new frontend at 8000 to work around an API issue.
3. **Approve and promote stable:** review and commit the coherent feature changes,
   run regression/build and saved-data acceptance, then prepare an immutable release
   and obtain approval for the existing Supervisor cutover. Verify a fresh backup,
   ownership, compatible data/schema, one collector and rollback before promotion.
   Use the documented release workflow; this command does not promote, merge or
   change the stable source pin. Promote at milestones, not after every UI edit.

Necessary safeguards remain: stable source pin, DB isolation/backups, collector
ownership checks, port ownership, graceful shutdown and rollback. Redundant for
routine preview: Git commit/push, immutable release preparation, stable-backend
compatibility audits and Supervisor cutovers. No Supervisor change is proposed.

## Validation

```powershell
.venv\Scripts\python.exe -m pytest tests/test_development_workflow.py tests/test_news_intelligence_v3.py tests/test_news_pagination.py -q
node --test frontend/tests/development-workflow.test.mjs
cd frontend
npm test
npm run typecheck
```

Use the integrated browser on 3102 to search ABC (three stories across categories),
narrow Industry (one), and test an unmatched term (zero). Verify the same run ID
on both identity URLs and the development run header on proxied News responses.
The synthetic fixture uses the real search/qualification/pagination code.
For hot reload, temporarily change the development-only banner and confirm it
updates without a manual reload while the search input remains; restore the edit.

Observed on 27 October 2026: matching frontend/backend identity, real News proxy
search 3/1/0 results, health/stocks HTTP 200, private/ingestion/foreign-Origin
requests HTTP 403, and browser Fast Refresh with input preserved. Stable frontend
PID 7584, backend PID 35720 and old preview PID 24324 remained unchanged. No
production configuration, financial DB, release policy or collector was changed.

Regression results: 135 backend development/News/research tests passed; full
frontend suite 369 passed and one existing skip; TypeScript passed. A second
launcher refused the occupied port without replacing its owner. Typing `stop`
produced Uvicorn's normal application shutdown and launcher exit 0; both dev
listeners were released. All 16 pre-existing WIP files retained their SHA-256.
No commit or push was performed for this workflow change.
