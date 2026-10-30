# VN30 core financial coverage V5.9

Assessment: 23 October 2026. Branch: `feature/financial-data-intelligence`.
Baseline: `cd194595` (V5.8), verified present at origin before collection.

## Scope and evidence

The existing V5.6 inventory was recomputed from the V5.5 SQLite journal before
choosing tasks. The latest saved complete HOSE membership snapshot is effective
3 August 2026; the 2 February snapshot remains preserved. This is coverage of
that dated universe, not a claim that membership was reverified on 23 October.

The measured zero-data VN30 issuers were LPB, SHB, SSB, STB, TCX, VIB and VPL.
VHM and VNM also had P0 gaps: annual cash flow and all three quarterly statement
families. Plans were generated from the actual fingerprinted P0 backlog, not
from an assumed ticker list. Two serial groups contain four and five issuers.
No VN100-only acquisition was selected.

The existing V5.7 collector, installed vnstock VCI adapter and immutable SQLite
import path are reused. Each SDK statement request is paced by six seconds.
The bounded SDK provides at most four annual and four quarterly periods.
Captured files are canonical SDK responses, not original HTTP wire bodies.
Reporting scope, fiscal boundaries and publication dates remain unknown where
the SDK does not establish them. No provider reconciliation is required.

The refreshed [VN30 matrix](FINANCIAL_COVERAGE_V5_9_MATRIX.csv) reports observed
period counts and family statuses. `AVAILABLE` means that the saved statement
periods contain source values; it does not certify every line, complete history,
comparability, original-document verification or public redistribution rights.
Unqualified metric observations remain separate from statement-family presence.

## Measured result

| Measure within dated VN30 | Before | After |
|---|---:|---:|
| Issuers with any saved financial values | 23/30 | 30/30 |
| Issuers with all six annual/quarterly statement families | 21/30 | 30/30 |
| Annual income / balance / cash issuers | 23 / 23 / 21 | 30 / 30 / 30 |
| Quarterly income / balance / cash issuers | 21 / 21 / 21 | 30 / 30 / 30 |
| Initial zero-statement P0 tasks remaining | 50 | 0 |

Seven newly represented issuers: LPB, SHB, SSB, STB, TCX, VIB and VPL.
VHM/VNM gained their four missing families without replacing CafeF history.
There are no remaining zero-data VN30 tickers or missing core statement families
at this checkpoint. All 50 initial P0 tasks resolve by actual database presence.
Historical-depth, metric-definition and source-qualification gaps remain.

| Acquired ticker | Annual periods | Quarterly periods | Non-null source line values |
|---|---|---|---:|
| LPB | 2022–2025 | 2025-Q4–2026-Q3 | 1,288 |
| SHB | 2022–2025 | 2025-Q3–2026-Q2 | 1,288 |
| SSB | 2022–2025 | 2025-Q3–2026-Q2 | 1,288 |
| STB | 2022–2025 | 2025-Q3–2026-Q2 | 1,288 |
| TCX | 2022–2025 | 2025-Q4–2026-Q3 | 3,448 |
| VHM | 2022–2025 | 2025-Q3–2026-Q2 | 1,496 |
| VIB | 2022–2025 | 2025-Q3–2026-Q2 | 1,288 |
| VNM | 2022–2025 | 2025-Q3–2026-Q2 | 1,496 |
| VPL | 2022–2025 | 2025-Q3–2026-Q2 | 1,496 |

Nine source captures add 216 statement-period observations and **14,376**
non-null source-line amounts. There are **28 new issuer-year pairs** and
**36 new issuer-quarter pairs** relative to all saved sources. There are 36
captured source-specific annual periods: eight VHM/VNM issuer-years already
existed under CafeF, so these do not inflate the 28 newly available years.

No acquired statement family is classified `PARTIAL` or `SOURCE_UNAVAILABLE` by
V5.6; all have values in each returned period. This status does not count each
missing source line as complete. No unit/semantic-unqualified source-line amounts
were counted as usable. The normalized metric journal separately adds **5,544**
records: 1,200 reported and 942 derived numerical observations remain
`UNQUALIFIED`, plus 3,402 unavailable/blocked records. Newly qualified metric
records and newly public-display-qualified observations are both **zero**.

All nine VCI candidates succeeded; source failures and access failures are **0**.
The successful structured source filled the targeted family gaps, so additional
IR/PDF acquisition was unnecessary in this bounded pass. No original-PDF review
or source-rights certification is claimed. SDK-returned periods are retained as
reported; a missing later quarter is not inferred to be a filing failure.

## Validation and preservation

- Acquisition, collector, SQLite, coverage, Financial Engine, Insight Engine,
  reviewed-report and private-projection regression: **187 passed**, one existing
  Starlette/httpx deprecation warning. See private `tests.log` and exit code 0.
- Both complete batch repeats use nine cached captures, make no new acquisition
  calls, and insert **0 captures, 0 statements and 0 metric revisions**.
- SQLite `integrity_check=ok`; foreign-key check has zero errors. Schema remains
  version 1. Storage changes: captures **33→42**, statements/selected observations
  **1,449→1,665**, metric revisions **84,564→90,108**.
- Full row-set comparison with the pre-run backup shows **zero prior rows
  missing or changed** in all four journal tables, including period selection.
  All **1,570** pre-existing private/unrelated file hashes match. This includes
  longer histories, PDFs, tooltip changes, the feasibility note and other work.
- All nine new immutable packets pass Financial Engine annual, quarterly and TTM
  processing. V5.8 saved-insight calls also pass annual YoY, quarterly YoY and
  quarterly QoQ for assets, profit and operating cash: **27 calls, 81 results**.
  All 81 correctly remain `INSUFFICIENT_COMPARABLE_DATA` because source reporting
  metadata is incomplete; statement availability is not comparison eligibility.

The delivery diff was reviewed against the mission and repository standards:
only this summary and its derived VN30 count/status matrix are included. No
application implementation, public API, UI, production configuration or database
schema changes are required. Existing public/private gates and private financial
files are preserved. Commit locally only; no push or merge is part of V5.9.

## Private reproducibility

All source captures and operational artifacts stay under
`.local/financial-collector-v59/`: dated before/after inventories, fingerprinted
batch plans/backlogs, original SDK captures, resumable state, immutable run
results, cached-repeat results, tests and preservation audits. The existing
financial database remains `.local/financial-research-v55/financial.sqlite`.
`before.sqlite` is the consistent pre-acquisition backup, not a new serving store.

To resume an existing plan using the original collector CLI (substitute batch
number 1 or 2), from the repository root:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.collect_financial_pilot --plan .local/financial-collector-v59/batch-1/plan.json --backlog .local/financial-collector-v59/batch-1/backlog.json --root .local/financial-collector-v59/batch-1 --journal .local/financial-research-v55/financial.sqlite --industry-snapshot .local/free-data-v4-ready/observed-memberships.json
```

No source refresh flags are needed for a cached repeat. Coverage is recomputed
with `scripts.report_financial_coverage --as-of 2026-10-23` and the same journal
and industry snapshot. Operational plans, source amounts, PDFs and SQLite files
are excluded from Git. This delivery changes only the coverage summary and matrix;
the existing collection and analytics implementation required no modification.
