# VN100 financial expansion V5.12

23 October 2026; branch `feature/financial-data-intelligence`, baseline
`829cfbe9627ce2a254fee26fca9ff65b478da676` (V5.11, verified on origin).
This delivery reuses the existing collector, V5.5 financial journal, V5.6
coverage inventory, Financial Engine and V5.11 private serving contract.

## Universe and selection

The preserved complete HOSE snapshot effective **3 August 2026** remains the
100-company measurement universe. The February snapshot and original membership
evidence remain unchanged. A bounded web search did not verify a newer official
complete constituent notice; current quotes and ETF basket notices do not
establish a replacement membership list. This is dated-universe coverage, not
a claim of continuous membership through today.

Coverage is recomputed from actual selected SQLite observations before planning.
The initial batch selects ten zero-data P3 issuers: EIB, BSI, BCM, ANV, BMP,
BWE, CII, CMG, DCM and DGW. All have six missing statement families in the saved
inventory. They represent banking, securities, property, agriculture, building
materials, water, construction, computer services, chemicals and distribution
under the existing provisional SSI labels. Those labels remain partially
verified; they do not establish an official historical taxonomy. Availability
is untested until acquisition, not inferred from membership or sector.

## Reusable bounded execution

`financial-collector-plan-v512` is an additional accepted plan contract in the
existing collector. It binds a matching as-of date, preserved membership and
fingerprinted V5.6 backlog to non-VN30 VN100 P3 statement tasks. The original
V5.7 VN30 P0 plan contract retains its original gates. Both execute 3-5 issuers
and at most ten source candidates per invocation; this pilot uses two groups
of five. No second collector, database, migration or calculator is introduced.

The existing CLI runs either contract:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.collect_financial_pilot --plan .local/financial-expansion-v512/batch-1/plan.json --backlog .local/financial-expansion-v512/batch-1/backlog.json --root .local/financial-expansion-v512/batch-1 --journal .local/financial-research-v55/financial.sqlite --industry-snapshot .local/free-data-v4-ready/observed-memberships.json
```

Repeat with `batch-2` for the second group. Plans, fingerprints, per-source
state, SDK captures and immutable run receipts are retained under the private
pilot root. The CLI defaults to cached reads; refresh flags require an explicit
operator invocation. Do not automatically repeat inaccessible candidates.
`resolved_initial_tasks` records exact resolved families for either contract;
the legacy `resolved_initial_p0_tasks` field remains exclusive to P0 tasks.

Acquisition uses installed vnstock VCI Finance methods, serial six-second
pacing and the free SDK's actual four-period response bound per frequency.
No direct endpoint or subscription workaround extends history. Captures are
SDK-normalized evidence, not original HTTP wire bodies or independently reviewed
issuer documents. Original source codes, nulls, parent relationships, period,
units and provenance stay in immutable packets. Unsupported metadata stays
unknown; there is no cross-provider reconciliation or public-rights promotion.

## Safety and acceptance

Before acquisition, `MetricJournal.backup` uses SQLite's online backup API to
create private `before.sqlite`; the same supported procedure restores it into
an isolated `restore-test.sqlite`. Integrity and exact table-row comparisons
verify the restored snapshot. These are backup/restore artifacts, not new
financial stores. Production configuration and blocked previews are untouched.

The preservation manifest hashes all prior private source files and protected
unrelated worktree files. After collection, an audit compares all four existing
journal tables against the backup and verifies every prior hash. New data is
appended to the existing journal. No old history or source file is replaced.

Each successful issuer is checked through the V5.11 SQLite read switch and the
canonical in-process private FastAPI application at annual and quarterly
frequencies, asserting existing rows/statement contract and private no-store
headers. The same stored packets pass annual, quarterly and TTM engine calls.
No runtime service is started or restarted. Capture-mode fallback remains the
default. Frontend contract tests exercise the existing dashboard; no frontend
implementation changes or new browser acceptance are part of this batch.

## Measured outcome

| Measure | Before | After / added |
|---|---:|---:|
| VN100 issuers with real statement values | 33/100 | 43/100 |
| Zero-data VN100 issuers | 67 | 57 |
| Newly covered companies | - | 10 |
| New issuer/statement/frequency families | - | 60 |
| New issuer/annual periods (not multiplied by statement) | - | 40 |
| New issuer/quarterly periods (not multiplied by statement) | - | 40 |
| New statement-period observations | - | 240 |
| New reported detailed source-line amounts | - | 16,704 |
| New normalized metric records, including unavailable | - | 6,160 |
| New unqualified reported metric records | - | 1,560 |
| All new UNQUALIFIED records (reported / derived / unavailable) | - | 4,316 (1,560 / 1,436 / 1,320) |
| Source acquisition failures | - | 0/10 |
| Initial P3 statement-family tasks resolved | - | 60 |

All ten issuers have four annual periods, 2022-2025, in all three statement
families. BSI, ANV and BMP provide four quarters from 2025-Q4 through 2026-Q3;
the other seven provide 2025-Q3 through 2026-Q2. These are source period labels;
unknown fiscal boundaries or scope are not inferred. No confirmed internal
holes occur within these four-quarter spans. History before the first saved
period remains unknown, and four quarters are explicitly limited history.

The 1,560 unqualified reported metric records remain distinct from 16,704
inspectable source-line amounts and from unavailable/blocked derived records.
Zero new records are granted public-display eligibility. Presence of a statement
does not certify every line, comparability, complete history, or source rights.

Backlog counts change from P1/P2/P3/P4 **90/169/411/496** to
**90/192/381/652**. Resolving 60 initial missing-family tasks exposes 30
limited-quarterly-history tasks plus specialist/metric work. A net backlog
reduction is not the coverage measure. Full before/after observations and exact
resolved task IDs remain in the private receipts. The committed
[100-company matrix](FINANCIAL_COVERAGE_V5_12_MATRIX.csv) records family presence,
period spans, internal gaps and source-value counts from actual selected rows.

Remaining zero-data companies (57): BAF, BVH, CTD, CTR, CTS, DBC, DIG, DPM,
DSE, DXG, EVF, FRT, FTS, GEE, GEX, GMD, HAG, HCM, HDG, HHV, HSG, HT1,
KBC, KDC, KDH, KOS, MSB, NAB, NKG, NLG, NT2, NVL, OCB, PAN, PC1, PDR,
PHR, PLX, POW, PVD, PVT, SBT, SIP, SJS, TAL, TCH, TPB, VCG, VCK, VGC,
VHC, VIX, VND, VPI, VPX, VSC, VTP. Existing covered companies also retain
history, specialist-definition and qualification gaps; no further acquisition
is authorized by this completed batch.

## Regression and delivery

SQLite integrity is **ok**, foreign-key errors **0**. Exact comparisons show
**0** prior rows removed or changed in each of the four tables, and **0**
differences between the backup and isolated restore. All **1,653** pre-existing
private/protected file hashes match. Storage remains schema 1: **53** captures,
**1,910** statement observations, **1,907** selections and **96,422** metric
revision records. Existing 34-quarter histories remain intact.

Both cached batch repeats insert **0** captures, **0** observations and **0**
metric facts and invoke no provider. All **10** new packets pass annual,
quarterly and TTM Financial Engine calls (**30** calls); all **20** private
annual/quarterly API requests pass. Each of the six statement families is
present for **43/100** issuers after acquisition, up from **33/100**. This
family-level presence does not imply historical completeness.

Metric qualification details remain explicit: the 6,160 new records comprise
4,316 UNQUALIFIED records and 1,844 UNAVAILABLE records. None has a qualified
numeric `value`; source-reported amounts remain inspectable in the statements
and input references. No unsupported YoY comparison is filled from missing
quarters. No new independent source verification was performed.

Focused collector/coverage/storage/acquisition/serving/private API/insight tests:
**130 passed**. Frontend: **338 passed, one existing skip**. Full backend run:
**1,723 passed, 32 subtests passed, one failure** in the unrelated Windows
Supervisor finite-role fixture, which did not observe its second launch inside
25 seconds. An isolated repeat of that exact test passed in **8.53 seconds**;
no Supervisor code was changed. The initial full run is retained as a failed run,
not relabeled as an all-green suite. One existing Starlette/httpx deprecation
warning remains. Logs and exit statuses are private under the pilot root.

Standards review: **0 actionable documented-standard or smell findings**.
Spec implementation review: **0 actionable findings**. Source changes only
extend explicit collector plan eligibility and its task reporting; public APIs,
engine formulas and frontend implementation are unchanged.

Delivery is a local commit of source, tests, this report and the coverage-count
matrix. Private SQLite, backup/restore files, captures, prior PDFs and detailed
financial values are excluded. Unrelated worktree files stay uncommitted.
No push or merge is part of this delivery.
