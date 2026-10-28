# Adaptive News V1 / Quick News integration — 2026-10-08

Remote base: `611ffe92fcf32369bd0bf587c2fa302f8d4b2beb` (Quick News).
Adaptive News input: `79a477fc9703d99abf9c0c352b6cb3df18506e07`.
Cherry-picked integration: `2cc2f71`.

Integration occurs in a separate clean worktree. The original dirty main, its
Technical/Dividend work and local `.env` are outside the integration.

## Compatibility changes

- Resolve StockNews and presentation-test conflicts while retaining the Company
  Story feed, one leading Story, bounded related headlines, source evidence,
  archive link and EN/VI keys. Refresh cached Company data every minute.
- Add `ranking=attention` to the existing cached Company feed for Quick News.
  Independent publisher breadth, capped activity and latest activity retain the
  original digest order. Archives continue to default to publication recency;
  single-publisher Company Stories remain eligible.
- Correct UTF-8 translation keys damaged during initial conflict resolution.
- PostgreSQL projection shares the evidence writer's transaction advisory lock
  after cache bootstrap, through evidence reads and dirty-marker acknowledgement.
  This prevents a concurrent evidence commit's dirty marker being cleared before
  its evidence is projected. SQLite retains its serialized write transactions.

## Verification executed in the integration worktree

Dependencies only: original `.venv` Python interpreter; separate `npm ci
--no-audit --no-fund` installation in the integration frontend. No original source,
untracked tests, `.env`, production database or live crawler is used.

- `python -m pytest -q --tb=short`: 569 passed.
- `python -m pytest -q --tb=short tests/test_news_adaptive.py
  tests/test_research_feed.py tests/test_news.py tests/test_news_correction.py
  tests/test_news_refinement.py tests/test_news_pagination.py tests/test_ingestion.py`:
  63 passed.
- `npm test`: 66 passed.
- `npm run typecheck`: passed.
- `npm run build`: passed with the regular Turbopack build.
- `git diff --check`: passed.
- Registry inspection: 20 enabled Vietnamese sources, six priority sources;
  configured 30/120/240/360-minute cadence, two fetch slots, six sources per cycle.

Tests cover cache-only Company ranking, source evidence/images, scheduler leases,
failure isolation, restart recovery, clustering, Hot eligibility, pagination and
72-hour expiry, leading/related Quick News presentation, refresh cancellation and
EN/VI. The PostgreSQL seam checks shared lock identity and transaction sequencing;
an actual PostgreSQL concurrency test was not run. The backend suite reports one
existing Starlette/httpx deprecation warning.

Earlier checkpoint results (692/567 backend, 67/63 frontend) came from dirty
working-tree versus staged-independent suites. They are historical reports, not
the verification results above. This integration adds two backend and three
frontend regression tests to the clean committed suites.

The original local main remains at `79a477f`; it requires a separate safe
reconciliation before further development/pushing. Do not pull/reset/stash its
dirty worktree to synchronize it automatically.
