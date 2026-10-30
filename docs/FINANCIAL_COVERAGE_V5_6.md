# VN30/VN100 financial coverage and acquisition gaps V5.6

Assessment: 22 October 2026. Branch: `feature/financial-data-intelligence`.
V5.5 baseline: `3ba50fa`. This is an offline planning inventory over the existing
dedicated SQLite journal. It does not acquire reports, change the Financial Engine,
switch HTTP serving, change the product database, or grant display rights.

## Dated index universe

The [HOSE July 2026 constituent notice](https://staticfile.hsx.vn/Uploads/UploadDocuments/2479382/15072026%20CBTT%20-%20Danh%20muc%20thanh%20phan%20HOSE-Index%20thang%207.2026.pdf)
contains separate active VN30 (30), VNMidcap (70) and VN100 (100) tables. The
active VN30 and VNMidcap sets are disjoint and exactly reproduce the VN100 set.
Reserve lists were excluded. The notice's PDF SHA-256 is
`441799b3afbc4f29f8b53ce6ef3b500b9121a4d032ca4cfeb1d4aa6e14407879`.
The 3 August 2026 effective date is corroborated by the
[contemporaneous notice report](https://tapchikinhtetaichinh.vn/hose-cong-bo-danh-muc-vn30-ky-thang-7-2026-bo-sung-mch-va-tcx-161885.html).
The latest *complete, dated* constituent list found in this review is the July
notice. No continuous update through 22 October is certified.

The earlier [HOSE January 2026 list, distributed by PHS](https://www.phs.vn/tin-tuc/hose-danh-muc-co-phieu-thanh-phan-cua-bo-chi-so-hose-index-ky-thang-012026/6361399)
is retained as a separate 2 February 2026 effective snapshot; its broker-hosted
PDF SHA-256 is `a89a30791f450cc66a2bb81496eda3f250a75697b4102ea75401d29da0ff2814`.
These are two preserved snapshots, not a complete event history between reviews.
For dates preceding the first snapshot, membership is `UNKNOWN`.

Industry labels are optional evidence from the saved SSI observed classification
review. The review has no certified taxonomy version or classification effective
date; its labels are `PARTIALLY_VERIFIED` and never treated as official HOSE GICS
or historical industry membership. A saved financial packet's `NH` or `CK` type
can identify bank or securities model when the SSI label is absent. Others remain
`unknown`. The current inventory identifies 18 bank, 12 securities, 17 real
estate and 53 unclassified VN100 tickers under these limited rules. Sector KPI
requirements apply only to an identified sector; unknown sectors remain `UNKNOWN`.

## Measured SQLite coverage

The source is the V5.5 `financial_selection` view of immutable revisions, plus
existing `financial_metric` facts. Selected revisions are counted once per
source/statement/period/scope/basis. Original source packets and older revisions
remain inspectable by capture ID. No amount is substituted for a null or missing
field. A value stored for personal research does not imply public display rights.

| Scope | Issuers | Any saved data | Annual income | Annual balance | Annual cash | Quarterly income | Quarterly balance | Quarterly cash |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| VN30 | 30 | 20 | 20 | 20 | 18 | 18 | 18 | 18 |
| VN100 (includes VN30) | 100 | 23 | 23 | 23 | 21 | 21 | 21 | 21 |

The full [100-ticker matrix](FINANCIAL_COVERAGE_V5_6_MATRIX.csv) records annual
and quarterly income/balance/cash period counts per issuer, earliest/latest
income period, internal quarterly gaps, industry evidence status, and public
eligibility. Its 77 zero-data tickers have **unknown** historical period extent;
zero here means absent from this dedicated journal, not absent at a provider.

Eight longer captures (FPT, HPG, MWG, PNJ, REE, SSI, TCB, VCB) each retain eight
annual and 34 quarterly periods from 2018-Q1 through 2026-Q2. The other 13 VCI
issuers have four annual/four quarterly periods. VHM and VNM have four annual
summary periods, and no saved quarterly observations. No internal quarterly
holes were found between the observed first and last income periods in this
sample. The latest **observed anywhere** is 2026-Q3 (VPB/VCI); the latest annual
reference is 2025. Those are release-check hints, not filing deadlines or proof
that every issuer must already have reported those periods. No period before an
issuer's first saved observation is fabricated as missing.

All six statement families have their own `AVAILABLE`, `MISSING`, `PARTIAL` or
`SOURCE_UNAVAILABLE` status. Core and specialist metric cells also support
`NOT_APPLICABLE` and `UNKNOWN`. Per-period metric records preserve source, unit
when known, formula/definition when stored, reported-versus-derived origin and
display eligibility. All 23 saved issuers currently have **zero** statement
families eligible for public display under the stored source rights fields.
Fixture-marked captures remain listed by capture ID but do not count as real
financial coverage or feed metric facts. None of the current 100 issuers is
fixture-only. The canonical engine's ordinary-company ratio applicability is
retained for banks and other financial issuers.

## Specialist and industry gaps

The latest-reference specialist assessment is deliberately strict. Seven of the
18 identified banks have saved financial packets; the other 11 need core
statements first. In those seven saved banks, NIM, verified CASA, CAR, CIR, cost
of funds and regulatory LDR have no validated latest-period mapping (7/7 each).
NPL and loan-loss coverage are `MISSING` for six and `PARTIAL` for one at the
latest reference, with historical original-note evidence retained separately.
Credit and deposit growth are likewise missing for six and partial for one.
The existing accounting loan/deposit ratio is **not** called regulatory LDR;
the demand-deposit share is **not** called verified CASA.

Two of the 12 identified securities issuers have packets (SSI and VCI). Latest
reference margin lending, brokerage revenue, FVTPL, proprietary trading,
financial assets, borrowings and operating-performance definitions all lack
verified mappings (2/2 each). Three of the 17 observed real-estate issuers have
packets (VHM, VIC, VRE). At the latest reference, inventory, buyer advances,
borrowings, receivables, project information and presales/backlog have no complete
mapped value (3/3 each). Earlier source fields and partial components remain
inspectable in the JSON output. Specialist KPIs have separate annual and
quarterly cells for each saved period, including source, unit, definition and
capture ID where available. The global latest-reference quarter is a planning
hint; a missing quarter there does not erase earlier coverage or prove a filing
is due.

## Ranked backlog and execution seam

The generated backlog has 68 P0, 54 P1, 102 P2, 411 P3 and 340 P4 tasks.
P4 captures missing secondary/core metric inputs at each issuer's latest saved
annual and quarterly periods. Unsupported valuation definitions remain explicitly
unresolved and do not imply a verified market-data source. P0 targets missing statement families for current-snapshot
VN30 tickers HDB, LPB, MSN, SHB, SSB, STB, TCX, VHM, VIB, VJC, VNM and VPL.
P1 covers limited/incomplete quarterly history or newer-period release checks
among other VN30 issuers. P2 is reserved for specialist KPI gaps in issuers with
saved statements. P3 covers remaining VN100 statement gaps. Each task has a
stable `task_id`, ticker, family, priority, confirmed internal `missing_periods`,
optional candidate reference period, industry, reason and suggested source
category. Every suggested source has `source_availability=UNTESTED`; the future
crawler must verify actual content, publication and use rights before ingestion.

Run the read-only service with the existing Windows virtual environment:

```powershell
Set-Location 'C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-financial-data'
.\.venv\Scripts\python.exe -B -m scripts.report_financial_coverage --journal .local/financial-research-v55/financial.sqlite --as-of 2026-10-22 --industry-snapshot .local/free-data-v4-ready/observed-memberships.json --output .local/financial-research-v55/coverage-v56.json
```

The ignored private `.local/financial-research-v55/coverage-v56.json` contains
the complete machine-readable company cells and acquisition backlog. The command
opens SQLite read-only, rejects missing database paths and public output paths,
performs no network call, and never writes to the journal. The committed
membership JSON can accept future dated snapshots after source review. The
coverage itself stays derived, so no V5.5 schema migration or duplicate financial
observation table is needed. No HTTP route was added; this is an internal service
and CLI and leaves existing dashboard contracts unchanged.

## Validation and limits

Focused tests cover dated membership selection, reserve exclusion, period-gap
semantics, selected-revision deduplication, null-only and fixture sources,
sector applicability, specialist history, backlog generation, rights separation
and read-only database bytes. The full backend regression passed **1,645 tests
and 32 subtests** with one existing Starlette/httpx deprecation warning.
The focused coverage module passed eight tests. Frontend code was not changed,
so typecheck/production build were not affected. Existing tooltip edits and
prior feasibility notes remain uncommitted. No live acquisition, production
writes, database recreation, preview restart, push or merge is part of this
delivery.
