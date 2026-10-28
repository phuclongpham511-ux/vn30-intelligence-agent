# Technical V1 provisional operational EOD — approved policy and implementation

Updated: 2026-10-10. Status: **live PROVISIONAL acceptance, durable persistence
and read-only operational API passed**. See the current
[persistence report](TECHNICAL_EOD_PERSISTENCE_V1.md). The October 9 checkpoints
below remain historical evidence.
The prior [evidence investigation](TECHNICAL_V1_OPERATIONAL_EVIDENCE_2026-10-09.md)
is preserved unchanged. The project owner approved a separate PROVISIONAL tier
with conditions. The VERIFIED consumer, its completion attestation, and the
read-only Technical API remain the verified boundary.

## Approved terms

- Independently qualified HOSE venue records must cover every date in the
  bounded read range. Unknown dates, merely scheduled opening, unverified
  closures, and ticker suspension/no-trade prevent an accepted packet.
- The target needs an independently sourced official post-session publication
  with its actual published, observed and verification times. The timestamp
  cannot be the reader's 23:59:59 EOD availability assumption.
- Both SSI reads use authenticated SDK transport and bypass the five-minute
  history cache. Each receipt binds ticker, requested range, request start,
  reader observation, response receipt, normalization and full content digest.
  The second request must **start** at least six hours after the first response
  and at least 24 hours after the qualified publication time. The full bounded
  normalized histories must match, not just the target close.
- Accepted output is wrapped as PROVISIONAL with
  `safe_to_display_as_verified=false`. A revised fresh SSI read of the same
  range invalidates the active in-memory output. Provisional output cannot be
  inserted into the verified API envelope and is excluded from benchmark and
  certification paths.
- Historical persistence required confirmation of SSI storage/retention rights.
  On October 10 the owner reported direct SSI permission for storage, retention,
  processing, derived analytics, redistribution and commercial use. This removes
  the former assumed blocker, as owner-reported authorization rather than
  independently reviewed legal documentation. The subsequent persistence slice
  stores historical data only after the unchanged acceptance gates pass.

These rules do not assert vendor finality or historical PIT vintages. The
current SSI adjusted series remains a product input, not an official benchmark
source. D1, D4 and D5 numerical semantics and the existing VERIFIED gate are
unchanged.

## Implemented seams

`SsiMarketDataProvider.get_history_fresh` reuses the existing bounded raw SDK
transport and normalization while bypassing the process cache. The ordinary
`get_history` path keeps its prior cache behavior.
`capture_fresh_ssi_read` uses that method and returns an in-memory
`AuthenticatedSsiHistoryRead` without credential or token fields.

`assess_provisional_eod` checks the typed `CalendarEvidence`,
`HosePublicationEvidence`, both SSI receipts, source/content identity, fixture
flags, and the timing rules. Missing or contradictory inputs return named
`INCOMPLETE_EVIDENCE` reasons. A URL on an official host and a supplied hash do
**not** authenticate a real exchange document by themselves: an acquisition
process or operator must independently retrieve, inspect and qualify the source
content before supplying the typed records. No source-acquisition process is
represented as complete here.

`evaluate_provisional_technical_eod_packet` calls the existing consumer's D1,
D4 and D5 path only after the separate provisional gate passes. It wraps the
result as `ProvisionalTechnicalDailyPacket`; it does not call or alter the
verified HTTP route. Critical unresolved price/volume facts and incomplete
packet states remain diagnostics. The in-memory registry removes an active
packet when a later fresh read of the same scope has a different full-history
fingerprint; `ProvisionalInvalidation` records the affected packet and versions.
Registry state is intentionally ephemeral, so a restart requires requalification
and no previous provisional output is silently restored. The registry is not yet
connected to a user-facing delivery channel.

`summarize_provisional_result` reports bounded status, reason codes, receipt
times, version and counts without raw bars or authentication material.
`TechnicalAPIPacket` now rejects any packet whose completion assurance is not
`VERIFIED`, preventing a provisional inner D5 packet from being presented as a
verified HTTP response.

## Live evidence and limits

One bounded fresh authenticated FPT read through the new acquisition path
returned 131 nonfixture daily observations for 2026-04-01 through 2026-10-08.
Its request/observation/receipt chronology was valid and the cache was bypassed.
With no independently qualified HOSE calendar supplied, the new assessment
returned `INCOMPLETE_EVIDENCE: verified_session_calendar_unavailable`.
The rendered official HOSE [October 8 trading bulletin](https://www.hsx.vn/vi/tin-tuc/hose-diem-tin-giao-dich-ngay-08-10-2026/2503043)
shows publication at **08/10/2026 16:34:41** and a trading summary for that
session. The attached [official PDF](https://staticfile.hsx.vn/Uploads/UploadDocuments/2503043/20261008%20Tong%20hop%20thong%20tin%20giao%20dich.pdf)
returned HTTP 200, `application/pdf`, 146,288 bytes and SHA-256
`5ebe406bd2cce959f92ca7ee49dc4d9b59b123f8f917498f96c371ca726865f8`
when retrieved in memory on 2026-10-09. The page does not state a timezone;
the official [HOSE RSS catalog](https://api.hsx.vn/n/api/v1/News/NewsFeed)
uses `+0700` for its build time. The independent timezone corroboration and
qualified publication instant are recorded below.
The bulletin proves the target HOSE session occurred. It does not establish
SSI bar publication or finality.
The official [2026 HOSE trading holiday calendar](https://www.hsx.vn/vi/lich-giao-dich)
identifies closures on April 27, April 30–May 1, and August 31–September 2
within this read range, and states that the August 22 Saturday make-up workday
has no exchange trading. The official [HOSE trading-hours rule](https://staticfile.hsx.vn/Uploads/UploadDocuments/2372196/2.Thoi%20gian%20giao%20dich.pdf)
states Monday–Friday sessions, excluding holidays. The schedule supports
closure records; actual sessions require their own source records.

## Qualified comparison window and first receipt

The comparison range was narrowed to **2026-07-01 through 2026-10-08**. The
public [HOSE session index](TECHNICAL_V1_HOSE_SESSION_INDEX_2026-07-01_2026-10-08.tsv)
records 69 official dated trading bulletin references. Combined with 31
weekend/holiday closures from the official rule and holiday notice, it covers
all 100 dates with no gap, duplicate, or unexpected bulletin. The index SHA-256
is `88b288afa760f13e09522624f17b9fa6dce481047bf2bbfee839d13ebec9bd49`.
Constructing `CalendarEvidence` from these public records yielded 69 occurred
sessions and zero unresolved dates. This calendar evidence concerns venue
sessions, not SSI history finality or FPT corporate-action comparability.
The official [HOSE October 8 end-of-day table](https://www1.hsx.vn/vi/du-lieu-giao-dich/thong-ke/du-lieu-cuoi-ngay)
also showed an FPT row with positive matched volume when its date control was
set to 08/10/2026. That supports target-date trading, not equality with SSI's
adjusted OHLCV: HOSE's displayed units and adjustment basis differ.

The earlier 131-observation read lacked a durable, complete receipt. A new
bounded authenticated fresh FPT read for the narrowed range returned 69
nonfixture adjusted observations. Its metadata-only [first receipt](TECHNICAL_V1_FPT_FIRST_RECEIPT_2026-10-09.json)
records scope, actual request/observation/response times, source/units,
transport/cache provenance and the canonical full-history SHA-256. The
receipt file SHA-256 is
`4c7672c46a1ab929a271e27587d2fe8305b08b178ae1a1dc52cea87485390499`.
It contains no raw OHLCV, credentials or tokens. The response was received at
**2026-10-09 06:48:04.755945 UTC**. The compact-receipt code rechecks scope,
chronology, provenance and its digest against a later full read; a self-reported
receipt is not cryptographic proof of SSI authentication by itself.
One bounded authenticated SSI security-universe read independently confirmed
FPT as a HOSE ordinary stock. The metadata-only
[security receipt](TECHNICAL_V1_FPT_SECURITY_RECEIPT_2026-10-09.json) has
SHA-256 `6446ad20e1ab1ff692ae8b3a7799f213d5a46c85fb33bfc3ddf1cd87ccc4f20d`.
It can populate only a transient in-memory security row for the live consumer;
the configured local database query currently fails with `OperationalError`.

The official PDF's HTTP `Last-Modified` is **2026-10-08 09:34:42 UTC**, one
second after the bulletin's displayed **16:34:41** when interpreted as UTC+7.
The official HOSE RSS catalog also uses `+0700`. This independently supports
the bulletin display's UTC+7 timezone, making the publication time
**2026-10-08 09:34:41 UTC**. The [publication evidence](TECHNICAL_V1_HOSE_PUBLICATION_2026-10-08.json)
records these source facts and the PDF hash. Its file SHA-256 is
`416f1fbc0e4cb0f95c2db1174858997b0bfe485480b706fca45d235f4413ad8e`.
The PDF modification time is corroboration of the displayed timestamp, not a
substitute for an SSI bar publication receipt.

The 24-hour bulletin gate is **2026-10-09 09:34:41 UTC**. Six hours after the
new first SSI receipt is **2026-10-09 12:48:04.755945 UTC**. The latter is the
earliest eligible second-request start; a short scheduling margin is prudent.
SSI's own bar publication time remains undocumented and is not inferred from
the HOSE bulletin.

One in-chat Codex automation, `woofi-fpt-second-ssi-evidence-read`, is scheduled
for **2026-10-09 19:50 Asia/Ho_Chi_Minh** with a single occurrence. It targets
this thread. Its prompt checks the exact worktree, credential availability,
HEAD and hashes of all four evidence files before any SSI request; it must
recompute both gates and stop without a request if the environment or time is
wrong. The scheduled environment has not yet run, so access to its future
filesystem and credentials is a required runtime preflight, not assumed.

At this checkpoint, no second read, provisional packet, production snapshot, or API result was
claimed. The operational smoke does not
enter calibration, reviewed cases,
protected benchmark inputs or development summaries of event outcomes.

## Progress before the time-gated follow-up

- Completed: separate provisional evidence models, uncached authenticated read,
  timing/content/calendar checks, D1/D4/D5 wrapper, in-memory invalidation,
  safe diagnostics and verified API exclusion.
- Evidence: synthetic boundary tests and the bounded live acquisition above.
  The focused SSI/provisional/EOD readiness suite passed (129 tests), and the
  provisional/API suite passed (63 tests) before the compact-receipt addition.
  Its focused tests then passed (14 tests), and the full repository suite passed
  (826 tests). `scripts.check_technical_identity` passed (9 files) after the
  final compact-receipt edit.
  The test run emitted one existing Starlette/httpx deprecation warning.
- Changed files: `src/providers/ssi/__init__.py`,
  `src/services/technical_eod.py`, `src/services/technical_api.py`, new
  `src/services/provisional_eod.py`, `tests/test_ssi_provider.py`, new
  `tests/test_provisional_eod.py`, and this document. The prior evidence report
  stays unchanged.
- Blocking inputs at that checkpoint: an actual second authenticated SSI read after both gates,
  and SSI historical storage rights before any persistent producer. The local
  database metadata query currently raises `OperationalError`; the scheduled
  live D1/D4/D5 consumer run will use the validated metadata in a transient
  in-memory session if the provisional gate passes.
- Planned safe action at that checkpoint: run one time-gated, same-scope fresh SSI read, compare its
  canonical digest with the first receipt, then re-evaluate the provisional
  gate and focused regressions. Keep any incomplete result out of the verified
  API and benchmark.

No commit, push or deployment is authorized or performed.

## Time-gated live follow-up (2026-10-09)

The scheduled single run rechecked the exact resolved worktree and HEAD
`84cb2ef5141010b6e6230f3146f5e1e34216adc8`. The existing settings loader
resolved both SSI credential fields; no credential value was printed or changed.
`.env` remains ignored by Git. The metadata-only first receipt, HOSE session
index, HOSE publication evidence and SSI security receipt were all present and
matched the SHA-256 digests recorded above. The older operational evidence
report was not changed.

The official HOSE index, weekday trading rule and 2026 holiday notice yielded
69 occurred sessions, 31 qualified closures and 100 contiguous calendar records
for 2026-07-01 through 2026-10-08, with no unresolved dates. The qualified
HOSE bulletin publication time was **2026-10-08 16:34:41 UTC+7**
(**09:34:41 UTC**). It is a HOSE bulletin timestamp, not an SSI bar publication
or SSI finality attestation. The 24-hour publication gate was
**2026-10-09 09:34:41 UTC**, while the six-hour first-read gate was
**2026-10-09 12:48:04.755945 UTC**. The second request started after both gates,
at **2026-10-09 12:52:24.395867 UTC**.

Exactly one bounded fresh authenticated SSI history request for FPT over the
same 2026-07-01 through 2026-10-08 range completed at
**2026-10-09 12:52:26.603611 UTC**. It returned 69 nonfixture adjusted daily
observations with VND prices and share volumes through the existing uncached
SSI SDK path. Its full canonical history SHA-256 was
`4bdfe85b7b7c7bdb8dc9c13c520887922fcf54660bd1a3b47099617676536a22`,
identical to the first receipt. `assess_provisional_eod` returned `PROVISIONAL`
with no reason codes. This matching read is operational stability evidence
under the approved policy, not proof of SSI finality.

Using the separately validated SSI FPT security identity, the existing
D1/D4/D5 consumer ran with a transient SQLite database held only in memory.
It returned an in-memory `PROVISIONAL` packet for FPT on 2026-10-08, with
`NO_MEANINGFUL_TECHNICAL_CHANGE` and zero current-session events. The packet
was marked unsafe to display as VERIFIED. It was not placed in any production
snapshot, persistent database, verified API, benchmark or certification
dataset; the process has exited, so there is no retained live packet to serve.
No raw SSI OHLCV was persisted. SSI historical storage rights remain unconfirmed.
SSI's public [FastConnect Data API guide](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
documents access, and its [service information](https://guide.ssi.com.vn/ssi-products/general-information)
documents registration and credential handling, but neither establishes a right
to retain historical OHLCV in this use case. The newer
[SSI Developer Portal conditions](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
likewise describe access and data availability without establishing storage
rights for this account. An applicable SSI agreement or written permission is
still needed before any persistent historical-data producer is enabled.

The focused SSI/provisional/Technical EOD/readiness regression suite passed
**133 tests** with one existing Starlette/httpx deprecation warning. No source
or test files were changed during this time-gated follow-up. No further SSI
request, retry or automation was scheduled. No commit, push or deployment was
performed.
