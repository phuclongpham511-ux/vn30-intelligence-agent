# Financial data collector V5.7 controlled pilot

Assessment: 22 October 2026. Baseline: `94baed8` on
`feature/financial-data-intelligence`. The pilot consumes the preserved V5.6
backlog and the dated August 2026 VN30 membership snapshot.

The subsequent [cached VJC quarterly review](FINANCIAL_COLLECTOR_V5_7_VJC_FOLLOWUP.md)
records the completed selected-row extraction and its separate before/after audit.
The measurements below describe the original pilot checkpoint.

## Pilot and measured result

HDB, MSN and VJC were selected from the actual P0 backlog: each had zero saved
income, balance and cash-flow observations at both annual and quarterly
frequencies. Six statement-family tasks per issuer were attempted, 18 total.
The private plan records their exact task IDs and a SHA-256 of the canonical
V5.6 backlog JSON. It validates a 3-5 issuer selection and at most ten sources.

| Measure | Before | After |
|---|---:|---:|
| VN30 issuers with saved financial values | 20/30 | 23/30 |
| VN100 issuers with saved financial values | 23/100 | 26/100 |
| VN100 issuers without saved financial values | 77 | 74 |
| Annual income / balance / cash issuers | 23 / 23 / 21 | 26 / 26 / 24 |
| Quarterly income / balance / cash issuers | 21 / 21 / 21 | 24 / 24 / 24 |
| Immutable capture revisions | 28 | 32 |
| Statement-period observations | 1,368 | 1,446 |
| Metric revision records, including unavailable records | 82,484 | 84,487 |

The three VCI packets each add 2022-2025 annual and 2025-Q3-2026-Q2 quarterly
data across the three statement families. These are 24 new issuer-period pairs
and 72 statement-period records. The reviewed HDB original adds six independent
annual source records for 2023/2024, without splicing them into VCI history.
All 18 initial zero-statement P0 tasks are resolved at the family-presence level;
this does not certify complete history or that every source field is present.

Actual source-line values: HDB VCI 1,288; MSN VCI 1,496; VJC VCI 1,496; HDB
original 24. Total **4,304** reported source amounts, plus one separately
reviewed, unqualified NIM observation. Source facts remain inspectable for
private research. The normalized journal appends 2,003 metric records, including
481 unqualified reported records; the remaining records include blocked derived
and unavailable metrics. **Zero** newly materialized metric records are promoted
to public-display-qualified values. These counts are deliberately separate.

## Sources and restrictions

Six source candidates were investigated and recorded with URL, issuer, title,
reporting period, document type, nullable publication date, restrictions and status:

| Candidate | Acquisition / extraction outcome |
|---|---|
| HDB, MSN, VJC financial statements through installed `vnstock==4.0.2` VCI Finance methods | Three bounded canonical SDK captures imported. SDK reads were serial and paced at least six seconds apart. These captures are SDK-normalized responses, not original HTTP wire bodies. |
| [HDBank annual report 2024, official issuer CDN](https://cdn.hdbank.com.vn/hdbank-file/uploads/f384d1892df010445b09b5b08cfbe0ad/20250421-HDBANK-AR-2024-EN-FINAL-view-web_1745231068352.pdf) | Original PDF downloaded and hashed; 24 amounts from PDF pages 112-114 / printed pages 222-227 reviewed and imported using the existing `reviewed-report-v2` adapter. |
| [Masan IR financial statement directory](https://www.masangroup.com/vi/investor-relations/) | HTTP 403 from the downloader. Recorded `ACCESS_RESTRICTED`; no bypass or automatic retry. |
| [VietJet separate Q1 2025 statements](https://ir.vietjetair.com/File_Upload/financial-information/financial-reports/2025/Separate%20Q1.2025.pdf) | Original PDF downloaded and hashed. `DOWNLOADED_AWAITING_REVIEW`; no financial values imported from this document and no coverage credit assigned to its download. |

Two PDF binaries and three canonical SDK captures were acquired. A final repeat
reused all five, made no new source requests and inserted zero captures,
statement observations or metric revisions. Original PDF SHA-256 values:

- HDB: `8dedf78770f24c6046969e32131cc3e2291143a301f82e9ac22cdce9bd0b3346`
- VJC: `26f340d97c97dc29eef66335772a4cd2bcce49d497b6c2e3f30a9f4aa3492f7b`

Publication dates are left unknown when the original evidence does not establish
them; URL dates and receipt timestamps are not substituted. Publicly reachable
does not establish redistribution permission. All collected evidence remains
private, and existing public/private access controls remain in force.

## Original extraction and directly reported banking KPI

The existing reviewed-report adapter verifies each monetary token against its
source row, year columns, original unit, fiscal boundaries, issuer, consolidation
scope, page-text hash, rendered-page hash and PDF hash. Selected HDB statement
amounts use an explicitly reported **VND million** scale. Both annual balance
identities and cash-flow identities pass. Original labels, raw grouped numeric
tokens, normalized VND amounts, page/table references and source scope are retained.

The PDF text was extracted deterministically with the bundled pypdf runtime;
whitespace was normalized per line, and the relevant complete spreads were
rendered with Poppler and visually inspected. The private reviewed manifest pins
those exact text/image hashes. Repeating the same manifest is deterministic.
Arbitrary new PDFs still require a reviewed mapping; downloading a report never
guesses a table layout, scale or canonical definition. No LLM calculated values.

PDF page 37 / printed page 72 reports FY2024 NIM of **5.58%**. Its raw percentage,
normalized fraction, original label, document hash, page and exact quoted
passage are retained in a reported `MetricObservation`. The passage does not
establish the full average-asset definition or reporting scope, so `value=null`,
`quality_status=UNQUALIFIED`, and its numeric source evidence stays in `input_refs`.
Coverage marks that period `PARTIAL`, not `AVAILABLE`. The current reference
quarter remains missing. No regulatory or provider ratio is substituted.

## Reusable workflow

`scripts.collect_financial_pilot` calls the internal `run_collector` service:

1. Validate explicit P0 task IDs against the fingerprinted V5.6 backlog and dated
   VN30 membership; require 3-5 issuers and at most ten source candidates.
2. Use the existing `acquire_batch` and VCI adapter for bounded provider packets,
   or acquire a declared public PDF/HTML URL. Save original document bytes under
   their hash; preserve every refreshed revision.
3. Stop on access restrictions, including 429; retry transport/5xx failures once.
   Enforce timeout and 40 MB document bounds. Redirects are recorded for review
   rather than followed to a new unreviewed source.
4. Resume validated cached files by default. A downloaded document remains
   awaiting review until its `review_manifest` is supplied. HTML can be archived;
   automatic arbitrary HTML financial extraction is not implemented in this pilot.
5. Reuse `report_packet` for reviewed annual originals and `normalized_metrics`
   for the unchanged Financial Engine. Optional `ratio_review` records only
   explicitly unqualified source-reported banking ratios with page references.
6. Append through `MetricJournal.import_packet` and `append`; recompute coverage
   using `build_coverage`. Each run saves immutable plan/before/after/result JSON;
   a private state manifest records completion and failure per source candidate.

An acquisition plan uses contract `financial-collector-plan-v57`, `as_of`,
`backlog_sha256`, `task_ids` and `candidates`. The fingerprint is SHA-256 over the
UTF-8 JSON serialized with sorted keys, two-space indentation, unescaped Unicode,
no NaN and a trailing newline. Each candidate supplies `id`, `ticker`, `issuer`,
`kind` (`vci` or `document`), `url`, `discovery_url`, `title`, `reporting_period`,
`document_type`, `published_date`, `access` and `access_notes`. Documents also
provide `format` (`pdf` or `html`), optional `expected_periods`, `review_manifest`
and `ratio_review`. Review files are relative to the private collector root.
Review schemas are the existing `ReviewedReport` and the narrow `RatioReview`.

```powershell
Set-Location 'C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-financial-data'
.\.venv\Scripts\python.exe -B -m scripts.collect_financial_pilot --plan .local/financial-collector-v57/plan.json --backlog .local/financial-collector-v57/backlog.json --root .local/financial-collector-v57 --journal .local/financial-research-v55/financial.sqlite --industry-snapshot .local/free-data-v4-ready/observed-memberships.json
```

The default rerun reuses saved evidence. Explicit `--refresh-documents` fetches
document revisions; `--refresh-sdk` invokes the existing bounded SDK acquisition.
When the legacy file index defers a shorter candidate, the collector archives it
separately and lets SQLite append its new periods; the longer file-index history
and all earlier selected period values remain. A new document hash requires matching fresh reviewed evidence. Earlier
files and selected observations remain. V5.5's deliberate rejection of remapping
the same raw hash to a different normalized packet still applies.

No schema migration or additional financial database was needed. Acquisition
state is a private JSON manifest, not a duplicate financial fact store. Serving
still uses existing captures; no HTTP route or frontend contract changed.

## Private evidence and coverage outputs

Under `.local/financial-collector-v57/`:

- `backlog.json`, `plan.json`, `state.json`, `documents/`, `sdk/`
- `hdb-review.json`, `hdb-ratio-review.json`, `hdb-pages/`
- `runs/<run_id>/{plan,before,after,result}.json`
- `coverage-after.json`, `coverage-after-matrix.csv`, `before-after.json`
- `before-v57.sqlite`, `preservation-and-engine-audit.json`

The original V5.6 matrix/report remain the dated baseline. The refreshed private
matrix includes all 100 target issuers. Its backlog now has P0 **50**, P1 **63**,
P2 **112**, P3 **411**, P4 **386** (1,022 tasks). Resolving initial P0 gaps exposes
additional history and metric gaps, so the total backlog can increase. No tasks
beyond this pilot were acquired. Unknown history before a first observed period
is not fabricated as missing.

## Validation and remaining gaps

Seventeen collector tests exercise idempotent reruns, actual backlog binding,
incorrect ticker rejection, period/unit rejection, interrupted runs, isolation of
failures, access/rate-limit handling, bounded retries, document revisions,
new-period insertion, preservation of 34-quarter history and unqualified ratios.
Focused collector/coverage/storage/batch regression: **50 passed**. Full backend
regression: **1,662 passed and 32 subtests passed**, with one existing
Starlette/httpx deprecation warning. Frontend code is unaffected, so its typecheck
and production build were not required for this change.

Live preservation audit: zero prior rows missing or changed across all four
SQLite tables; all 99 prior source-file hashes match; SQLite integrity and
foreign-key checks pass. All four new captures pass annual/quarterly/TTM engine
processing and the existing personal-research projection. The final repeat
inserts zero rows. The tooltip modifications and feasibility note remain outside
the V5.7 commit. All binaries, normalized private captures, journal files and
reviewed financial values stay outside Git.

Remaining gaps include 74 VN100 issuers without data, seven zero-data VN30
issuers, missing statement families for VHM/VNM, longer quarterly history for
the new issuers, HDB ratio definition/scope verification, review of the acquired
VJC original, restricted MSN original-source access and public-use rights.
No push, merge, production change, scheduler, preview restart or full-universe
collection is part of this delivery.

## Standards

Final independent review: **0 outstanding documented-standard findings and 0
smell findings**. Review fixes preserve short-refresh provenance and pass every
new candidate through the existing canonical source-line validation boundary.

## Spec

Final independent review: **0 outstanding spec findings**. A shorter candidate
can append a new quarter while leaving the longer capture index and old selected
observations intact. Invalid mapped amounts cannot enter the journal or become
the selected resumable candidate.

Review totals: Standards **0**, Spec **0**; no outstanding worst issue on either
axis. The two pre-existing tooltip edits and feasibility note were excluded from
the review and commit.
