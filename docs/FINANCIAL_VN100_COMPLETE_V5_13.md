# Complete VN100 financial acquisition V5.13

Baseline `4c4b0c4fdb11b2e654fee7f86b52565414d7cc56`, branch
`feature/financial-data-intelligence`. The preserved constituent universe is
effective 2026-08-03. Coverage is measured from selected real observations in
the existing V5.5 journal; statement presence does not certify history depth,
comparability or redistribution rights.

## One command and recovery

```powershell
.\.venv\Scripts\python.exe -B -m scripts.collect_financial_vn100 --journal .local/financial-research-v55/financial.sqlite --root .local/financial-complete-v513 --industry-snapshot .local/free-data-v4-ready/observed-memberships.json
```

This same command resumes the same pinned queue. It is an explicit operator
operation, not a scheduler. Before acquisition it verifies journal integrity,
uses SQLite's supported backup API and restores to a separate private path.
Exact bidirectional comparisons verify all four restored tables. Prior private
source files and protected unrelated worktree files are hash-pinned.

The runner recomputes the full initial universe, selecting only absent core
families, including partially covered issuers where applicable. The saved
baseline, journal path and as-of date bind resumption. No assumed 57-ticker list
is embedded in production code. Private `queue.json` records the full initial
tasks, completed chunks and actual per-family terminal states. Per-source
collector state persists immediately after each issuer attempt. A final
two-issuer chunk is supported without weakening the legacy V5.7/V5.12 contracts;
the maximum remains five issuers and ten candidates per collector call.

Every chunk reuses `run_collector`, `acquire_batch`, the installed VCI adapter,
the existing journal and canonical Financial Engine. SDK reads are serial,
paced at least six seconds apart. The approved free path exposes at most four
annual and four quarterly periods per family. No direct endpoint, upgraded
subscription or historical-limit workaround is used. Existing 34-quarter
captures and all immutable revisions remain preserved.

Completed source receipts, access restrictions and validation failures are not
automatically fetched again. Identified top-level transport errors receive at
most one additional attempt after twelve seconds; the retry budget is persisted
before that request. A process interruption during that retry cannot reset the
budget. SDK errors retained only within partially returned packets do not
trigger a whole-packet refresh: missing families remain explicit PARTIAL/source
limitations. Unknown error causes are not relabeled as access restrictions.

After each chunk the queue recomputes coverage and assigns initial tasks to
COMPLETED, PARTIAL, SOURCE_UNAVAILABLE, ACCESS_RESTRICTED, VALIDATION_FAILED or
RETRY_EXHAUSTED from actual observations and receipts. Imported packets alone
do not establish completeness. Downloaded documents do not count as observations.
The original reports, source codes, hierarchy, nulls, units, scope/basis and
source references remain inspectable. Normalized metric qualification is
separate from source-line availability.

## Validation scope

Private acceptance uses the V5.11 SQLite switch and canonical in-process
FastAPI application. Annual and quarterly responses, original source/revision
selection, no-store headers, engine processing and immutable repeat imports
are checked without changing production reads or starting blocked previews.
The default saved-capture fallback and frontend implementation are unchanged.

All private queue receipts, backup/restore artifacts, hashes, source captures,
before/after inventories and detailed audits remain under
`.local/financial-complete-v513`. Only code, synthetic tests, this report and
coverage metadata are eligible for the delivery commit. No push or merge is
part of V5.13.

## Final measured outcome

| Measure | Before | After / added |
|---|---:|---:|
| Issuers with all six core families | 43/100 | 100/100 |
| Partially covered / zero-data issuers | 0 / 57 | 0 / 0 |
| Initial issuers processed successfully | - | 57/57 |
| Initial tasks COMPLETED | - | 342/342 |
| New statement families | - | 342 |
| New issuer/annual periods | - | 228 |
| New issuer/quarterly periods, union across families | - | 229 |
| New statement-period observations | - | 1,368 |
| New source-line values | - | 100,576 |
| New normalized metric revision records | - | 35,189 |
| New UNQUALIFIED records | - | 24,261 |
| New UNAVAILABLE records | - | 10,928 |
| Source failures / partial issuers | - | 0 / 0 |

Counts come from the existing selected observations and immutable revisions;
no downloaded document is counted. All 57 initial issuers completed, in 12
internal chunks. No alternative acquisition was necessary because the VCI path
returned all six families. CafeF's existing adapter handles saved annual
summaries rather than a general live six-family fallback; arbitrary original
PDFs still require reviewed mappings. Neither was needed for this queue.

Each new family contains four source periods. The annual labels are 2022-2025.
Quarterly spans differ by issuer and statement. In particular NT2 income and
balance contain 2025-Q4 through 2026-Q3, while cash contains 2025-Q3 through
2026-Q2. Its union is five issuer/quarters, explaining **229**, rather than
228, newly observed issuer/quarter pairs. This does not claim five matched
quarters across all three statements. Missing NT2 cash for 2026-Q3 remains a
newer-period/history gap. No cross-family filling or fabricated comparison
was performed.

The [full matrix](FINANCIAL_COVERAGE_V5_13_MATRIX.csv) lists each family's own
period span, status, count, internal gaps and source-line count for all 100
issuers. Historical completeness is separate from six-family presence. The
new histories remain four periods per family, and history before the first
observed source period remains unknown. Existing eight 34-quarter histories
remain unchanged. Longer history needs later authorized source access or
backfill; this delivery does not defeat the approved SDK's free-period limit.

All source-line amounts retain original codes/hierarchy/units and provenance.
Eight source lines retain unqualified/nonstandard-unit semantics; they are not
silently promoted to canonical monetary inputs. The 24,261 UNQUALIFIED records
comprise **8,680 reported**, **7,845 derived**, **7,736 unavailable-kind**
records. The other **10,928** are UNAVAILABLE. No newly stored metric record
has a qualified numeric `value`; source amounts remain inspectable in private
statements/input references. No public rights or independent source verification
are granted by family completeness.

Remaining acquisition backlog counts: P1 **90**, P2 **374**, P3 **210**,
P4 **1,539**. These represent history/newer-period checks and specialist or
metric-definition gaps, not zero-data issuers. All 342 initial missing-family
tasks are resolved; new history tasks are not subtracted from that result.

## Preservation and delivery checks

Integrity is **ok**, foreign-key errors **0**. Exact comparisons find **0**
prior rows removed or changed across all four journal tables, and **0**
differences between the backup and isolated restore. All **1,716** prior
private/protected file hashes match. No previous capture was replaced.
Storage remains schema 1: **110** captures, **3,278** statement observations,
**3,275** selections and **131,611** metric revision records.

During development, the initial process was deliberately stopped during an
unfinished BAF request to add bounded recovery and task-level classifications
identified in review. No completed BAF capture was discarded. The same queue
and baseline were resumed, then every remaining chunk proceeded automatically;
no user command per batch was needed. No environment runtime limit stopped the
completed queue. Terminal checkpoints remain resumable with the command above.

Regression: **1,727 backend tests and 32 subtests passed** on the final runner;
focused queue/collector/coverage/storage/acquisition/engine/insight/private API
tests: **152 passed**. One existing Starlette/httpx deprecation warning remains.
No V5.13 regression failure was hidden or waived. The prior V5.12 Supervisor
timing failure is documented in that checkpoint's report; it did not recur in
the final V5.13 run. Frontend implementation and production configuration were
not changed, and blocked services were not restarted.

All **57** new packets pass annual/quarterly/TTM engine processing (**171**
calls). All **200** default private annual/quarterly VN100 API requests return
200 with rows and the existing three-statement/no-store contract. **114**
additional explicit source/revision API responses exactly match projection of
the corresponding immutable stored packet, excluding only volatile `read_at`.
No mixed-revision packet or new numerical engine is introduced.

Reimporting every new packet and its normalized metric facts inserts **0**
captures, **0** observations and **0** facts. Repeating the entire terminal
queue invokes no acquisition and leaves storage counts unchanged. The checkpoint
is **TERMINAL**, with all **12** chunks and **342** tasks completed. The resume
command is also a safe no-acquisition repeat while this queue remains terminal.

Implementation standards review found no actionable violations. Spec review
identified bounded-retry and per-task checkpoint gaps; both were corrected and
re-reviewed with no remaining P1/P2 findings. The independent final report
review could not run because the review agents reached their usage limit.
The primary agent checked the delivery counts against the saved audit,
checkpoint, serving/parity receipts and 100-row matrix before committing.
