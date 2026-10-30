# SSI SecuritiesSummary No Content diagnosis V1 — 2026-10-20

Decision: **cause UNPROVEN; no application correction or activation justified**.
The dated requests conform to the inspected endpoint/SDK request contract. The
observed difference is historical-row availability versus same-day unavailability,
not a demonstrated malformed query, EOD-only contract, or entitlement rejection.
New SSI/auth requests in this diagnosis: **zero**. No production changes.

## Production read-only status

One inspection at **11:00:19–11:00:25 ICT** used the installed P1 Status primitives,
bounded native listener/runtime census and Restart Manager owner reads. It did not
run lifecycle control, obtain the ingestion mutex or instantiate a provider.

- Installed five Supervisor files match commit `67aab035` **byte for byte**.
- Application configuration and checkout HEAD remain
  `a98793a159b203d87937ec3c66b8e3e4b45cad41`.
- Durable intent remains RUNNING. Recorded generation is
  `b00d6a8001a2482d853b2dec8d219329`; the stored `control_phase=starting` and
  `policy_state=HEALTHY` are stale observations, not current qualification.
- Recorded Supervisor and all three role roots are absent. P1 descendant evidence:
  unresolved=false, verified_live=0, retained_unverified=0, unknown=0,
  identity_conflicts=0. Complete native runtime census returned `[]`.
- Listeners 3000/8000, ingestion-lock file owners and database file holders returned
  `[]`. Both HTTP reads failed with Windows connection refused (10061).
- Current service health and Collector singleton qualification are UNVERIFIED.
  No running Collector identity/generation or valid active ingestion ownership
  can be certified. Empty file-holder inventory does not establish mutex ownership
  or authorize Start.
- Last published heartbeat: **2026-10-19 16:18:52 ICT**. Collector log last write:
  **2026-10-19 16:18:29 ICT**, a filesystem time, not an event timestamp. Its tail
  shows completed/skipped ingestion cycles, including community successes, but no
  current SSI progress. Saved SSI universe/membership success times are
  `2026-10-19 01:44:34.396987` / `01:44:38.101563` as stored in SQLite.
- SQLite integrity `ok`; foreign-key violations `[]`. Diagnostic SQL initially used
  nonexistent `last_attempt`/`last_success` columns; its error remains saved. A
  targeted read-only completion at **11:02:18 ICT** used the actual `_at` columns
  and retained integrity results. No second native census or policy retry occurred.
- Config, intent, status and launch record hashes remained unchanged. No Stop,
  Start, recovery, acquisition, lock deletion or protected record publication.

**Production is unavailable with stale RUNNING evidence, not HEALTHY.** Recovery
requires a separate task; this diagnosis does not clear or reconcile lifecycle state.

## Previous successful request versus current responses

| Attribute | Saved ACB success | October 20 observations |
|---|---|---|
| API path/method | GET `/api/v3/data/securitiesSummary` | Same |
| Selection | `symbol=ACB`, no index | `ACB` or `FPT`, no index |
| Dates | `from=to=2026/10/16` | `from=to=2026/10/20` |
| Pagination | `pageIndex=1,pageSize=2` | Same |
| Request time ICT | Oct 17 20:26:47.910511 | Oct 20 09:32:01/02 and 09:37:22/23 |
| Response | business code 200, one row, pagesCount=1 | HTTP 200, business code 204, no data key |
| Row time | tradingDate Oct 16, no source event timestamp | No row/date/event timestamp |

Successful ACB values: `totalMatch="5160300"`,
`totalMatchValue="106488260000"`, `close="20600"`. Received Oct 17
20:26:48.812223 ICT. These remain historical, not current-session values.
Previous original HTTP status/headers/wire bytes were not saved: the archive
contains the decoded JSON envelope. Do not invent byte-level parity.

All four October 20 raw response files contain exactly
`{"code":204,"msg":"No Content"}` with SHA-256
`e938ae23cc2fc8fffb1ef0a1c61d7eda57d7ea63ef5947fd56a9711e001c2bfc`.
All four hashes were rechecked. There are no rows to normalize, compare, sum or
use to infer zero activity. Round separation was approximately 321 seconds.

The same raw Woofi adapter, SDK 3.2.1, canonical credential reference and
no-retry diagnostic configuration were used. Original host/header/account/scope
receipts are incomplete, so identical credential values, product rights and
historical on-wire host cannot be certified. No credentials/tokens were read in
this task. October 20 saved authentication HTTP 200 proves transport-level auth
success, not Summary entitlement. FPT has no successful Summary baseline here.

## SDK and official contract findings

The official [Summary endpoint](https://developers.ssi.com.vn/docs/api-reference/data-securitiesSummary)
requires Bearer authentication, JSON Content-Type, `from`/`to` in YYYY/MM/DD with
ordered dates, and exactly one symbol/index selector. Pagination is supported.
The saved queries meet those requirements; uppercase ACB/FPT have no demonstrated
format defect. The page describes daily records and documents invalid requests
with 400; it does not explain the observed business-code 204 or publication timing.

The official [Python service methods](https://developers.ssi.com.vn/docs/sdk/python/service-classes)
expose current and historical Summary methods. Installed 3.2.1 implements both
through `_get_securities_summary` and `SecuritiesSummaryRequest.to_dict()` on the
**same endpoint**. Current merely supplies today's date to both boundaries.
An offline spy confirmed identical query construction for an identical day;
SDK page-size defaults differ from the deliberately bounded two-row diagnostic.
Changing to the SDK's current method is not an evidenced fix. The SDK's current
date uses host-local time; the actual diagnostic explicitly used the ICT date.

Offline malformed-input characterization: SDK rejects empty required strings,
but forwards whitespace symbols, impossible dates and reversed ranges to a Mock.
This is shallow SDK validation, not a provider observation. The real saved requests
contain none of those invalid inputs. It does not prove malformed input causes 204.

The [official error appendix](https://developers.ssi.com.vn/docs/api-reference/appendix/error-codes)
documents authentication/scope/product restrictions, including insufficient scope
and product not enabled under 403. No business `code=204,msg=No Content` mapping
was located in the inspected Summary page or appendix. That absence is a documentation
gap; it neither rules out a provider-side access filter nor proves one occurred.

### Timing, alternate intraday path and qualification

- DOCUMENTED: date-range daily Summary and a current-day SDK convenience method.
- OBSERVED: one completed-day ACB row; four same-day empty responses during the
  previously recorded continuous-session window.
- INFERRED hypothesis only: requested same-day rows were unavailable from the
  selected service/account at those observation times.
- UNKNOWN: intraday refresh/publication SLA, EOD-only restriction, 204 cause,
  current account/product coverage and applicable new-field display rights.

The [official stream contract](https://developers.ssi.com.vn/docs/api-reference/subscribeUnsubscribeMarketData)
documents per-stock trade `v` as daily matched volume, `q` as individual quantity,
and source time `t`. It does not supply a direct cumulative matched-value field
in that trade payload. Index-summary totals are index-scoped, and put-through
totals have a different scope. None is a safe replacement for stock Summary GT.
Do not derive GT from last price times volume or rounded average price times volume.
No new subscription or alternative feed was opened.

## Adapter trace and correction decision

`SsiMarketDataProvider._request()` authenticates through the existing SDK raw REST
transport and returns decoded JSON unchanged. SDK default headers contain JSON
Content-Type and Accept; actual historical headers were not preserved. No Summary
method is activated in this adapter or its production acquisition path.

The SDK transport validates **HTTP** status, then returns JSON. Its Summary model
parser uses `data.get('data', [])`, losing business-envelope distinctions in the
returned model list; row-model defaults can also turn missing numeric fields into
zero. Woofi deliberately retains the raw envelope instead. The October 20 runner
saved code/msg and raw wire bytes before projecting missing data to an explicitly
unavailable state. It did not fabricate rows, zeros or source timestamps.

The existing live adapter retains `trade.v` as unverified-unit activity and GT as
unavailable. Its process-local cache is not independent qualified evidence, and
those production processes are now absent. No inspected evidence establishes an
independently qualified current intraday KL/GT cache. Instantiating live consumers
or calling demand-triggering stock APIs to inspect it is outside this task.

**Application correction: NONE.** No demonstrated client defect explains the
provider's empty body. Do not guess an endpoint/date/units change, raise retries,
upgrade the SDK, replace the working feed or weaken public guards.

Twelve permanent offline boundary tests were added in
`tests/test_ssi_summary_diagnosis.py`: raw envelopes (success, 204, business error,
null data), SDK method parity, missing inputs, envelope-as-row rejection and absent
snapshot rejection. These protect provenance/guards; they do not certify live data.
Invalid-date characterization is saved separately and does not bless invalid inputs.

## Validation and evidence

- Focused Python: **83 passed, 32 subtests passed**, including 12 new cases.
  Files: `test_ssi_summary_diagnosis`, `test_market_summary`, `test_ssi_provisional`,
  `test_ssi_qualification_v2`. One existing Starlette/httpx deprecation warning.
- Frontend provisional/public access regression: **10 passed**. Default OFF,
  production rejection, public non-exposure and no-acquisition shell checks pass.
- No application/frontend implementation changed; typecheck/build and unrelated
  UI acceptance were not repeated. No browser, push, deployment or public activation.

Full local evidence directory:
`C:\Users\PC\.codex\visualizations\2026\10\17\01a14811-87da-7ee2-8499-7835dd010da3\ssi-summary-no-content-20261020`.
It contains the original read-only status and errors, targeted SQL completion,
installed P1 hash comparison, receipt/archive hash comparison, and offline invalid
input characterization. Prior raw receipts remain in sibling `ssi-live-v3-20261020`;
the earlier archive remains in `ssi-qualification`. Nothing was overwritten.

## One bounded follow-up experiment — NOT executed or authorized here

Test one hypothesis: **availability differs by requested trading date within the
same account/session**, rather than a demonstrated request-shape defect.

After separate authorization and fresh production ownership/session safety checks,
use at most **three wire attempts total**: one authentication if needed, then two
read-only ACB Summary GETs with identical transport, pageIndex=1 and pageSize=2:
one for the known Oct 16 date, one for the verified current trading day. Use one
token, no refresh/retries or extra endpoint/ticker. Count failures. Save safe host,
method, exact query, nonsecret headers, status, body bytes/hash, provider trace ID
if present, HTTP Date and request/receipt times before parsing. Never save tokens.

Historical row plus current 204 supports date-conditioned unavailability for that
observation only; it does not prove EOD-only semantics. If both fail, stop with
access/service/baseline uncertainty. If both return rows, report recovered availability
and separately qualify day/source time; do not retrofit missing morning evidence.
Any 401/403/429/transport ambiguity stops the experiment without another route.
Public activation stays OFF in every outcome until applicable field/rights gates pass.
