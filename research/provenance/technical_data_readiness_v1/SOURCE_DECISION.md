# Technical Benchmark V1 acquisition decision — 2026-10-04

Decision: **REACQUIRE_CERTIFIED_DATA**. Readiness: **BLOCKED_BY_DATA_OR_PROVENANCE**.

Current qualification update: **2026-10-07**. **PRODUCT QUALIFICATION: PASS /
APPROVED**; **OFFICIAL TECHNICAL BENCHMARK QUALIFICATION: BLOCKED / NOT ADMISSIBLE
YET**. The dated 2026-10-04 investigation below remains historical evidence; the
provider-confirmed update at the end supersedes its unresolved SSI capability
questions, not its benchmark admission/governance requirements.

## Evidence and scope

Inspected existing acquisition/normalization code and active D2 V3 sections 8–13;
no legacy market payload or protected review source was reopened. The cohort and
B6 identity projections are the only existing data artifacts needed for this check.

`src/evaluation/acquisition.py` explicitly declares unknown adjustment semantics,
current vendor vintage rather than archived PIT vintage, no verified exchange
calendar, and unavailable raw duplicate counts. It returns normalized observations
and a normalized checksum; this path does not preserve original HTTP response
bytes or capture the installed provider/package version as acquisition evidence.
The installed versions today (vnstock 4.0.2, vnai 2.6.1, pandas 3.0.6) cannot be
assigned retroactively to prior downloads. Repeating the same acquisition would
improve receipt metadata but would not repair B3 or B5.

No claim is made that an uninspected dataset is intrinsically corrupt. It is not
certifiable through the inspected pipeline's evidence, and opening mixed legacy
payloads to search for missing proof would violate the pre-load exclusion rule.

## One coherent replacement path, still conditional

Prefer one provider's dated, original EOD stock records plus matching index/session
records and effective-dated corporate-action coverage. Capture raw responses,
explicit request bounds/instruments, UTC acquisition timestamp, endpoint/API and
package versions, units, source vintage/revision policy, normalization version,
raw/normalized hashes, availability assumption, and source evidence references.
Never use default current-date endpoints. Do not fetch a ticker/date request that
intersects B6 exclusions; do not download a mixed file and filter it afterward.

Source research on 2026-10-04:

- Vnstock's [Quote documentation](https://www.vnstocks.com/docs/vnstock-data/du-lieu-giao-dich)
  describes adjusted historical chart prices. This describes vnstock_data, not
  proof of semantics for a previously acquired vnstock community snapshot. It
  provides no verified historical-vintage guarantee for our windows.
- SSI's [FastConnect API specification](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api)
  documents date-bounded DailyStockPrice (separate close/adjusted-close, reference
  price and volume fields), DailyIndex, and security identity metadata. Its
  authentication requires customer-issued credentials. These API fields make it
  a candidate acquisition path, not a certified dataset or corporate-action ledger.
- SSI's [current access overview](https://developers.ssi.com.vn/docs/getting-started/overview)
  also requires market-data API credentials. None were present in the narrowly
  checked SSI environment-variable pairs; no global credential search was performed.

No paid access, account registration or authentication was attempted. Provider
documentation was read, not frozen as a data certificate. URLs alone do not prove
historical completeness, volume adjustment semantics or original publication times.

The prior B5B bounded HOSE API probes yielded no daily backbone; annual-scale
chart points are not session evidence. This task did not repeat an archive crawl.
For a replacement source, verify actual session coverage only for admitted
windows, preserve partial sessions, and quarantine unexplained gaps. A missing
stock row never establishes suspension, no-trade or provider failure.

## Comparability decision

Use original, documented units with complete action coverage over each required
reference/indicator window, or a verified cutoff-safe adjustment vintage. Exclude
affected windows until sufficient comparable history is established. Equality of
reference and previous closing price alone does not prove absence of all share
unit changes; it cannot certify volume comparability. No heuristic discontinuity
threshold or inferred corporate-action policy was introduced.

## Completed B6 integration

The pinned case ledger and its stock-day projection cover 64 V1, 64 V2 and 160 V3
cases. The loader verifies both artifact hashes before using identity metadata;
it never follows provenance references into review files. The scope adapter binds
this ledger to the existing admission contract, and the guarded request entry
point enforces it before the still-disabled payload-loader boundary.

Episode bounds remain UNRESOLVED. Certification covers protected stock-days only.
Future candidate episodes/windows overlapping uncertain protected context must
be quarantined under D4; this work does not implement or claim episode isolation
for a real candidate set.

## Exact outstanding dependency

Supply an accessible, explicitly bounded provider export or provider access with
documented original/adjusted price and volume semantics, historical revision/PIT
policy, action coverage and session provenance. Then acquire only pre-authorized,
unprotected windows, certify their evidence and run real-prefix/rebuild checks.
Credentials alone would not satisfy B3/B5. No owner decision changing benchmark
meaning or governance is requested. Access to a qualifying source is needed;
otherwise proceeding would require weakening D2, which is not authorized.

No official Development cases, Fresh Validation selection, holdout access or
score tuning occurred. Synthetic tests establish guard behavior, not data readiness.

Validation: 223 tests passed across certified exclusions, metadata projection,
population, Safeguard 6, admission, benchmark framework, analytics and materiality.
The current preflight was rebuilt twice with identical bytes/hash. Actual-data
PIT/prefix and dataset rebuild checks remain NOT_RUN because no real source is
admitted. The preflight does not promote passing synthetic tests to data PASS.

## SSI provider-confirmed qualification update — recorded 2026-10-07

Evidence authority: the owner's provider-confirmed SSI response supplied in the
task “Record SSI Historical Data Qualification Result and Formalize the Technical
Materiality Data Path.” This records that supplied response, not an independently
inspected correspondence archive. Its original response date/message ID were not
supplied; the date above is the repository recording date. No new SSI query,
historical acquisition or archival operation was performed for this update.

### Product and research are separate qualifications

| Use case | Decision | Meaning |
|---|---|---|
| Product market data | **PASS / APPROVED** | SSI FastConnect supports current/live presentation, Explore, Watchlist, Stock Detail, adjusted historical charts and current technical indicators computed from the currently available adjusted series. Existing normalization remains price **VND ×1**, volume **shares ×1**; daily analytics admit completed sessions only. |
| Official PIT-sensitive Technical Materiality benchmark | **BLOCKED / NOT ADMISSIBLE YET** | Current SSI Historical API alone cannot establish the historical vintage, cutoff-safe comparability and provenance required by D2. **REACQUIRE_CERTIFIED_DATA / BLOCKED_BY_DATA_OR_PROVENANCE** remains the research decision. |

The product qualification remains valid. Product suitability does not certify
historical replay inputs, and obtaining API credentials does not establish PIT
integrity or long-term archival permission. No product provider change is needed.

### Resolved questions and remaining requirements

| Question | Provider-confirmed answer / closed question | Remaining limitation or admission requirement |
|---|---|---|
| Historical Daily OHLC price basis | **RESOLVED: adjusted** in FastConnect V3. | An adjusted label alone does not establish the vintage visible at a replay cutoff. |
| Corporate-action adjustment coverage | **RESOLVED:** cash dividends, stock dividends/bonus shares, additional issuance and rights offerings trigger historical price adjustment. | Complete effective-dated action evidence and cutoff-safe price/volume comparability for admitted windows still require certification; price adjustment does not prove volume adjustment semantics. |
| Adjustment methodology availability | **RESOLVED: not provided**; no detailed formulas, factor tables or adjustment-rate tables. | Complete algorithm/factors are **NOT AVAILABLE / KNOWN LIMITATION**, not an open reverse-engineering task. Revisit only if SSI publishes new evidence. |
| Historical query version | **RESOLVED:** returns the data currently stored by SSI at query time. | No guarantee that this equals the dataset received at an earlier historical cutoff. |
| Historical corrections/revision metadata | **RESOLVED: not provided**; no record-level updated_at, revision ID, historical-data version ID or correction/adjustment notification mechanism. | Exact historical revision history is **NOT AVAILABLE**; no record-level revision lineage can be inferred. |
| Historical vintages / PIT retrieval | The supplied response provides **no mechanism** to retrieve an older version. | Historical vintages and PIT retrieval are **NOT AVAILABLE through the qualified product**; current history is not a PIT archive. |
| Raw/unadjusted history | **RESOLVED: not currently available** through this product. | Future development intent only; no production capability or official implementation date. |
| Benchmark-grade historical provenance | Current API capabilities are insufficient for the official benchmark. | **BLOCKED:** vintage, action/comparability, listing/history and session continuity evidence must satisfy existing admission rules. |
| Long-term storage/retention rights | Not answered in the supplied SSI response. | **SSI_STORAGE_RETENTION_RIGHTS: UNRESOLVED** for raw historical responses, successive versions and long-term internal snapshots; explicit confirmation required. |

Earlier empirical adjustment checks remain evidence of adjusted prices, coherent
corporate-action behavior and plausible product normalization. They do not certify
SSI's complete private method or historical vintages. Further reverse-engineering
solely to certify this benchmark is closed out; unknown formula details remain an
explicit limitation rather than assumed facts.

### Why current SSI history is not provably PIT-safe

For a replay cutoff **T = 2024-09-20**, a query made today for observations before T
returns the series currently stored today. It may contain corporate-action
adjustments, corrections or other revisions applied after T. SSI supplies neither
an old-version retrieval mechanism nor historical version/revision evidence to
reconstruct exactly what a customer would have received at T.

**Current historical data != provably point-in-time historical data.** Filtering
rows by trading date or applying an assumed EOD available_at cannot remove later
knowledge embedded in revised prices. This is a data-provenance limitation, not
evidence of a defect in event detection, MA/RSI, Significance, Novelty, Evidence
Confidence, Base Materiality or replay code. Do not rewrite those algorithms or
calibrate anyway while merely documenting the limitation.

### Technical status and preserved governance

**TECHNICAL ENGINE V0: IMPLEMENTED.** Existing deterministic infrastructure covers
abnormal-price candidates, unusual volume, MA-cross and RSI-regime events,
Significance, Novelty, Evidence Confidence, Base Materiality V0, recurrence/event
memory, historical replay, evaluation/human review and protected benchmark/holdout
governance. This is an implementation status, not a claim of calibrated V1 quality
or certification of existing historical inputs.

**TECHNICAL MATERIALITY V1 CALIBRATION: PAUSED / BLOCKED** pending an admissible
historical dataset. The blocker is primarily the dataset, not the V0 engine.
Passing product qualification does not authorize calibration or official generation.

Preserve [D2 V3](../../../docs/TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md): official
stock-days remain **2020-01-01 <= session_date < 2025-01-01**, with only explicitly
authorized PIT-valid warm-up; the existing frozen cohort stays frozen, not replaced
by today's VN30 membership. The **2025–2026 holdout remains SEALED**. Closed
Validation V1/V2 and completed V3 reviewed cases remain excluded under B6; uncertain
episode overlap stays quarantined. No benchmark output, cohort, exclusions,
thresholds, scores or governance contract is changed.

`preflight.json` remains the preserved 2026-10-04 preflight artifact, not a new SSI
certificate. B3/B4/B5 and real-data PIT-prefix/rebuild checks are not promoted to
PASS by this documentation update; no preflight or official benchmark is regenerated.

### Preferred path to unblock, in priority order

1. **PATH A — certified historical source.** Seek a source with sufficiently
   documented raw/unadjusted EOD prices and volume semantics, effective-dated
   corporate actions, exchange sessions, listing/history identity, revision policy,
   vintage/PIT evidence and reproducible export/version information. A different
   research provider is acceptable while the product continues using SSI. A raw
   source alone is not automatically certified; all applicable D2/B2–B6 gates and
   authorized-scope checks still apply.
2. **PATH B — raw prices + corporate-action reconstruction.** If sufficiently
   complete raw history becomes available, define an inspectable, deterministic,
   versioned and reproducible research normalization using verified exchange
   sessions and effective-dated corporate actions. At cutoff T, use only action
   information effective by T **and available by T**, preserving original raw
   records, knowledge/availability dates and revision provenance. Backdated later
   knowledge cannot pass the cutoff. This path must not depend on reverse-engineering
   SSI's adjusted series and does not waive raw-source revision/PIT requirements.
3. **PATH C — future SSI raw-data requalification.** Re-qualify only when production
   access actually exists. Verify price/volume semantics, corporate actions,
   revision policy, historical vintages, session provenance, continuity and
   storage/use rights; future raw data does not automatically solve PIT.
4. **PATH D — forward snapshot archive, conditional on rights.** Only after explicit
   storage/retention permission, prospectively retain provider, request parameters,
   acquired_at_utc, trading/session dates, licensed raw/normalized snapshots,
   content hash, API/SDK version and normalization version. This task starts no
   archive. Retention can establish locally observed versions and detect changes
   between captured snapshots **from the archive start onward**; without vendor
   revision metadata it does not identify exact unobserved correction times or
   guarantee all intervening versions were captured. An archive begun in 2026
   cannot reconstruct 2020–2024 vintages or by itself unblock that benchmark.

This update authorizes no source purchase/acquisition, calibration, benchmark
generation or relaxation of missing-data/protected-data standards. Next: qualify
the provenance commitments of a candidate certified historical source before
requesting any benchmark data.
