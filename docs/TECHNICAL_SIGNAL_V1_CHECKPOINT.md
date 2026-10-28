# Technical Signal Engine V1 — isolated backend checkpoint

Status: PASS for the isolated code checkpoint. Staged manifest and source
preservation checks passed. Live readiness is not implied by code tests.

## Worktrees and base

Source: `C:/Users/PC/.codex/worktrees/technical-development-reconciled/vn30-intelligence-agent`,
branch `codex/technical-development-reconciled`, HEAD
`e64986e0cb011d8af40a122e14d5bb47f540ba22`.

Checkpoint: `C:/Users/PC/.codex/worktrees/technical-signal-v1-checkpoint/vn30-intelligence-agent`,
branch `codex/technical-signal-v1-checkpoint`.

After `git fetch origin`, actual origin/main and checkpoint base were
`e64986e0cb011d8af40a122e14d5bb47f540ba22`. Origin is
`https://github.com/phuclongpham511-ux/vn30-intelligence-agent.git`.
The base contains Quick News `611ffe92fcf32369bd0bf587c2fa302f8d4b2beb`, Adaptive
News `2cc2f71` and its compatibility fix `e64986e`. No old News commit was applied.

## Exact checkpoint manifest

31 files: 8 existing tracked paths with reviewed changes, 21 completed Technical
source/test/report additions, and two new checkpoint audit documents.

- docs/D1_FACTUAL_RUNTIME_V1.md
- docs/D4_RUNTIME_EPISODES_V1.md
- docs/D5_A_RANKING_PACKET_V1.md
- docs/D5_B1_EOD_RUNTIME_CONSUMER_V1.md
- docs/D5_B2_GATED_READ_ONLY_API_V1.md
- docs/EOD_READINESS_CALENDAR_EVIDENCE_V1.md
- docs/TECHNICAL_SIGNAL_V1_CHECKPOINT.md
- docs/TECHNICAL_SIGNAL_V1_CHECKPOINT_MANIFEST.json
- main.py
- routers/technical.py
- src/analytics/episodes.py
- src/analytics/factual.py
- src/corporate_actions/models.py
- src/evaluation/benchmark/episodes.py
- src/evaluation/benchmark/facts.py
- src/evaluation/context.py
- src/materiality/__init__.py
- src/materiality/delivery.py
- src/materiality/detectors.py
- src/materiality/episodes.py
- src/materiality/factual.py
- src/materiality/service.py
- src/services/session_evidence.py
- src/services/technical_api.py
- src/services/technical_eod.py
- tests/test_d1_runtime.py
- tests/test_d4_runtime.py
- tests/test_d5_packet.py
- tests/test_eod_readiness.py
- tests/test_technical_daily_api.py
- tests/test_technical_eod_consumer.py

`TECHNICAL_SIGNAL_V1_CHECKPOINT_MANIFEST.json` records original absolute source
paths, source/checkpoint SHA256 values, transfer modes, reviewed shared-file scope,
patch hash and every excluded source WIP path. The seven Technical tracked diffs
were inspected in full and applied using an explicit path-restricted `git diff
--binary` / `git apply --check` / `git apply` flow. No blanket dirty-tree copy.
The 21 new completed files were copied individually only after confirming each
destination was absent. No source file was written, staged or overwritten.

Shared ownership:

- main.py: only Technical router import and registration; one root FastAPI app.
- materiality/service.py: only additive D1/D4 seams/common factual candidates.
- materiality/__init__.py: exports for runtime and packet contracts.
- materiality/detectors.py: explicit D1 facts/shared Bollinger volume gate;
  calls without factual decisions retain legacy V0 behavior.
- evaluation/context.py: null current-volume guard required by missing-data
  consumer tests; no zero fill or numerical formula change.
- benchmark/facts.py and benchmark/episodes.py: facades over extracted shared
  algorithms, preserving legacy benchmark version spelling/outputs/defaults.
- New materiality/factual.py, episodes.py and delivery.py contain completed
  runtime/backend work, not calibration or experimental dataset builders.

## Discovered minimum dependency

The first isolated related run had **424 passed / 1 failed**. The unchanged D4
corporate-action neutrality test constructs UNKNOWN context with
`reason='pending_verification'`. The committed CorporateActionContext Literal
rejected that value; the dirty source accepted it through a Dividend model change.
An isolated reproduction confirmed the exact Pydantic literal validation failure.

Only the single Literal member was selectively added in checkpoint
`src/corporate_actions/models.py`. This is a required CA-context descriptor for
the existing Technical test/contract, not Dividend acquisition, notice fields,
pending-correction lookup or scoring behavior. The test/assertions are unchanged.
Immediate reproduction after the narrow transfer: **1 passed**.

The source file's remaining additions (source_updated_at/source_title/evidence_text,
validator and has_pending_correction) were excluded, as were all changes to
CorporateActionRepository/storage/db/session. The existing committed CA importer,
revision handling and enrichment remain the implementation used by this checkpoint.

## Exclusions and independence

53 source WIP files are wholly excluded; one CA model file is partly included only
as described above. All 54 exclusion entries are in the JSON manifest.

Excluded work includes Dividend UI/translations/Stock Detail/API, ingest_dividends
and VSDC ingestion/read/source files, Dividend worker registration, new tables and
schema migration, Dividend-adjusted reliability tests, dirty CONTEXT.md Dividend
section, experimental calibration/evaluation modules, scripts, tests/reports and
decision-invariance research artifacts. No data archive, credentials, .env,
local database, protected historical payload or runtime snapshot was copied.

Both worktrees initially lacked own .env and default vn30.db. The new worktree
started with an empty index/worktree and installed its own .venv using
`uv --system-certs sync --frozen`; pyproject.toml and uv.lock are unchanged.
No source .venv, PYTHONPATH path or symlink was used by checkpoint tests.
Introspection confirms all four runtime functions resolve inside the checkpoint;
OpenAPI contains GET /technical/{ticker}/daily. The source worktree is not on
the checkpoint process sys.path. The exact functions are:

- evaluate_d1_market_events
- evaluate_d4_market_events
- build_technical_daily_packet
- evaluate_technical_eod_packet

The source-only Dividend/calibration files are absent. Frontend, Stock Detail,
News/Quick News/Adaptive News, existing routes, CA repository/storage, database
setup and dependency files remain identical to the committed base.

## Components and release boundary

| Component | Included behavior |
|---|---|
| D1 | Nearest-rank q95, inclusive equality, prior 60–252 valid observations, independent price/volume facts, UNRESOLVED and shared Bollinger confirmation |
| D4 | Family-specific deterministic episode identities/replay, confirmed closure/re-entry and explicit unresolved gaps/left boundary |
| D5-A | Deterministic Base/S/N/C/type/ID ranking, maximum Top 3, retained overflow and three distinct packet states |
| D5-B1 | One bounded EOD consumer, cutoff/identity/source/basis/units/calendar/bar-bound completion contracts and diagnostics |
| D5-B2 | Local-only read-only GET, typed packet/diagnostic, required-evidence gate and per-process resource guard; no HTTP acquisition |

No new algorithm, materiality cutoff, feature, LLM ranking or BUY/SELL/HOLD logic
was implemented while reconciling. Operational evidence remains required:
the API returns a diagnostic when Security/local history/calendar/completion
evidence is absent. Tests use persisted synthetic temporary input files and mock
SDK transport, not live SSI proof. No fixture was written to the production path
`runtime/technical_eod_evidence` and no producer exists in this checkpoint.

| Readiness | Result |
|---|---|
| CODE_READY | YES — isolated focused/full backend validation passed |
| LIVE_SSI_VERIFIED | NO — no live authorized acquisition performed |
| CALENDAR_READY | PARTIAL — contracts/tests exist; complete verified live calendar unavailable |
| EOD_COMPLETENESS_READY | PARTIAL — bar-bound contracts/tests exist; operational SSI proof unavailable |
| SNAPSHOT_PRODUCER_READY | NO |

Historical vendor vintage/PIT certification and official calibration remain
outside this code checkpoint. Older copied implementation reports record their
original source-worktree test counts; they are historical milestone records.
This report's isolated counts are the checkpoint evidence.

## Independent validation

Commands executed from the clean checkpoint worktree:

```powershell
uv --system-certs sync --frozen
.venv/Scripts/python.exe -m pytest tests/test_d1_runtime.py tests/test_d4_runtime.py tests/test_d5_packet.py tests/test_technical_eod_consumer.py tests/test_eod_readiness.py tests/test_technical_daily_api.py tests/test_technical_benchmark.py tests/test_materiality.py tests/test_bollinger.py tests/test_historical_evaluation.py tests/test_corporate_action_context.py tests/test_corporate_action_edges.py tests/test_corporate_action_curated.py tests/test_corporate_action_history.py tests/test_corporate_action_replay.py tests/test_corporate_action_study.py -q --tb=short --junitxml=$env:TEMP/woofi-technical-checkpoint-focused-final.xml
.venv/Scripts/python.exe -m pytest -q --tb=short --junitxml=$env:TEMP/woofi-technical-checkpoint-full.xml
.venv/Scripts/python.exe -m scripts.check_technical_identity
git diff --check
git diff --cached --check
```

Final focused/related regression: **425 passed** in 128.57 seconds. Final full
backend: **811 passed** in 151.14 seconds. One existing Starlette/httpx deprecation
warning, no unexpected regression. Identity guard PASS across 9 files;
unstaged/milestone/staged whitespace checks PASS.

| Suite | Isolated passed count |
|---|---:|
| D1 runtime | 46 |
| D4 runtime | 27 |
| D5-A packet | 48 |
| D5-B1 consumer | 36 |
| EOD readiness | 34 |
| D5-B2 API | 51 |
| Technical benchmark | 43 |
| Materiality | 33 |
| Bollinger | 54 |
| Historical evaluation | 21 |
| Corporate Action context/edges/curated/history/replay/study | 32 |
| Focused related total | 425 |
| Full backend total | 811 |

The six completed Technical suites contribute 242 tests. The full checkpoint
also runs 569 base-repository tests. The dirty source's prior 936-test result is
not substituted for these isolated results: its additional Dividend/calibration/
research suites are outside this checkpoint. No tests were weakened or altered;
all six new suites were copied byte-for-byte from the source.
No frontend changed, so frontend build/typecheck/test are not required by this
backend-only checkpoint. Existing shared API/News regressions are in full pytest.

## Git and review

Source inspection verified 17 modified tracked, 65 untracked files, no staged
changes. All 82 dirty-file SHA256 values, status entries, original branch/HEAD,
tracked diff digest and index-entry digest were recorded before transfer.
Pre-commit verification confirmed all 82 source status entries and dirty-file
hashes unchanged, no newly dirty/untracked files, no staged changes, original
branch/HEAD unchanged. Original tracked diff SHA256:
`9c677b285d213c095d94962b31c078572d3245bacaf4b33e52d03296121202d1`.
Original index-entry SHA256:
`916d67304637ccbf6c7d9d329957c25e89ae333a1dfe39a42113b0bbdf0208ff`.
The source branch pointer is not changed by this task. Existing source WIP remains
recoverable in place; no reset/stash/clean/rebase/commit operation there.

Complete source/shared diffs and the new Technical files were reviewed against
the task and AGENTS.md. Manifest hashes match every transferred file, and the
one selective dependency is the exact single model-enum hunk documented above.
No unapproved algorithm/scoring change, unrelated feature, dependency version,
secret configuration or generated database is included. Staging uses only the
31-file manifest; staged path equality and whitespace checks passed before commit.
Commit message: `feat: establish technical signal engine v1 backend checkpoint`.
The new commit's parent must be the exact origin/main base above. No push is
authorized or performed. Retrieve the checkpoint SHA with git log; it is not
self-embedded in this document.

Next minimal task: qualify one recent completed operational SSI stock-day with
an actual receipt, independent venue occurrence/closure evidence and content-bound
completion evidence; establish authorized snapshot storage and verify the API on
that local snapshot. Do not infer completion from market close or invent a verified
snapshot producer from these tests.
