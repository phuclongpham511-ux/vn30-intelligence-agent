# Technical Benchmark V1 acquisition decision — 2026-10-04

Decision: **REACQUIRE_CERTIFIED_DATA**. Readiness: **BLOCKED_BY_DATA_OR_PROVENANCE**.

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
