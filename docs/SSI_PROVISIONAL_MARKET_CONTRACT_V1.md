# Provisional SSI Market Data Contract V1

Owner decision recorded 2026-10-18; source base
`f3f70b413a1cfa2e53abdec028e643a2b674e285`.

The owner authorizes internal engineering conventions without another SSI
clarification round. This supersedes the need for those answers **for isolated
internal normalization only**. It is not SSI certification, public display
permission, production activation or a relaxation of financial/industry guards.
The [public field-qualification questions](SSI_MARKET_BOARD_FIELD_QUALIFICATION_V1.md)
remain public-release gates. No provider probe, browser or server operation ran.

## Contract and numerical boundary

`src/services/market_summary.py::normalize_provisional_market` extends the existing
pure normalization module. `normalize_summary_pair` retains its old unqualified
behavior. There is no new provider adapter, cache, endpoint, worker or polling.
Existing cache observations or saved raw evidence can be passed explicitly; this
increment uses saved evidence only and does not wire acquisition into normalization.

| Field | Internal convention | Validation |
| --- | --- | --- |
| MasterData floor/refPrice/ceiling | VND/share, multiplier 1 | Positive finite exact-decimal inputs; floor <= reference <= ceiling, including equality. No assumed percentage band or historical-price replacement. |
| SecuritiesSummary totalMatch | Shares, multiplier 1 | Nonnegative integer, missing is rejected rather than zero-filled. Security lotSize never rescales it. |
| SecuritiesSummary totalMatchValue | VND, multiplier 1 | Original nonnegative matched value; never inferred from last price × quantity. |
| Pair semantics | Instrument/day cumulative matched snapshot | Every response replaces its predecessor; there is no accumulator or successive-snapshot sum. Exact trade inclusion remains provisional, never all-market volume. |
| Key | symbol + exchange + tradingDate | Exact ordinary Stock identity on HOSE/HNX/UPCOM; matching symbol and any explicit venue fields; MasterData venue required. Conflicting venues/dates are rejected. |

Python is the numerical authority. Decimal parsing preserves original representations
and exact normalized strings; booleans, malformed numbers, nonfinite/negative values,
fractional shares, oversized inputs, values above the JS safe-number bound and lossy
float transport are rejected. Explicit conflicting source currency/unit metadata is
not overridden by a convention. There is no clamping, rescaling or anomaly repair.

Plausibility requires zero quantity/value together, or an observed value within
`floor × quantity .. ceiling × quantity`. Exact rational comparisons are independent
of the caller's Decimal precision. This is a conservative consistency screen, not
a GT calculation, an assertion about actual trade inclusion, or evidence of vendor
finality. Legitimate exceptions can remain rejected until explicitly reviewed.

## Time, provenance and qualification

The output contract is `ssi-provisional-market-v1`, convention version
`woofi-owner-market-conventions-v1`. Every metric is `PROVISIONAL_INTERNAL` with
`unit_authority=owner_engineering_convention`. Top-level fields explicitly state
`NOT_SSI_CERTIFIED`, `public_display_eligible=false` and
`display_rights=NOT_QUALIFIED_FOR_PUBLIC`.

Trading date, optional offset-aware source timestamp, and fetched/receipt time are
separate. Future/inconsistent dates or receipt chronology are rejected. No source
time is fabricated for the saved date-only MasterData/Summary. A previous-day packet
is stale; a same-day packet without source time is unverified even if just fetched.
The internal source-age threshold is 120 seconds, not an SSI latency/finality SLA.

Each source record is deep-copied with its original values and fields, source kind,
original receipt/source times, source-document SHA-256 reference and a canonical
record SHA-256. These hashes identify evidence; they do not authenticate SSI or
grant rights. The accepted receipt interface supplies times and a document hash,
not credentials or authorization headers. Original source archives remain unchanged.

Saved ACB data is real historical evidence under provisional owner conventions,
not synthetic DEMO and not a current-session quote. The MasterData fixture and
security identity were checked against the preserved October 17 raw response with
SHA-256 `7daa4ee90df0e8241749e3004326ccd4d6035d1df2725789d67ee6a40d62202b`;
the existing Summary fixture matches that same source document. The saved day is
2026-10-16: floor 19200, reference 20600, ceiling 22000, quantity 5160300 and value
106488260000. No financial fact or source timestamp was invented.

`scripts.prepare_ssi_provisional` can reproduce the packet from the two saved
fixture wrappers and an explicit evaluation clock. It imports no API/database,
never reads credentials, and refuses to overwrite an existing output file.

## Default-disabled internal Board integration

Internal route: `/internal/ssi-market`. All of the following are required:

- `NODE_ENV=development`;
- `NEXT_PUBLIC_WOOFI_SSI_PROVISIONAL=1` (unset by default);
- `NEXT_PUBLIC_WOOFI_VALIDATION=replay`;
- direct localhost/127.0.0.1/[::1] Host. Next.js-generated forwarding headers may
  repeat that exact Host and identify one loopback peer. Foreign hosts/peers,
  host mismatches and forwarding chains are rejected.

Use the existing development command's loopback binding and an isolated test profile.
The Host check is defense in depth, not a substitute for loopback binding or an
authentication service. Production builds reject the route even with opt-in set.
No running preview was reconfigured, enabled or restarted in this task.

Subsequent internal browser acceptance found that Next.js automatically supplies
the forwarding headers above for direct requests. The initial blanket rejection
made the route inaccessible; the bounded correction and actual acceptance evidence
are recorded in `SSI_INTERNAL_BOARD_ACCEPTANCE_V1.md`. The development-only,
explicit opt-in and replay gates remain mandatory.

The route feeds the existing QuoteMapView via an explicitly internal prop. Its
normal Board, Heatmap and Watchlist consumers receive no provisional records.
The Board independently requires the same development/replay/opt-in gate, page
scope and Board mode. Malformed packets, duplicate instruments, mixed days and
incompatible quote references fail closed. The legacy qualified price/activity
DTOs and their consumers remain unchanged; provisional records cannot promote
themselves into qualified ceiling/floor colors or session activity.

The existing sortable table presents separately labelled provisional KL/GT. A
compact EN/VI evidence section supplies bands, exact units, day, freshness,
source time, fetched time and expandable raw receipts. Missing last price remains
missing. No daily close is fabricated into a live quote. Provisional sorting never
sums snapshots. On mobile, exact values/units remain in the evidence section even
where the existing compact table hides its activity columns.

The internal shell does not mount the ordinary shell's ingestion-refresh POST,
ticker search, universe or quote acquisition consumers. Internal ticker buttons
inspect evidence instead of navigating to backend-backed Stock Detail. No Watchlist
membership or review storage is mounted. Theme storage has a separate internal key;
the existing language provider and design system are reused. A single local expiry
at source-age limit/day rollover, plus focus re-evaluation, updates status without
fetching or starting a polling loop. No new browser acceptance is claimed.

## Validation results

- Provisional Python contract: **37 passed**, including saved ACB, generation
  parity, raw immutability, missing/invalid numbers, venue/date/receipt conflicts,
  exact plausibility under low Decimal precision, zero-pair and replacement semantics.
- Existing unqualified Summary regression suite: **20 passed**, separate run.
- Complete frontend suite: **258 passed, 1 skipped, 0 failed**. The skip remains
  the existing optional persisted-API replay requiring `WOOFI_ACCEPTANCE_PACKET`.
  Nine new frontend cases cover flags/localhost, transport, source age, cohort
  rejection, sorting, EN/VI Board presentation, production/forwarded route denial,
  shell acquisition exclusion and a scoped invalid-packet state.
- Typecheck and isolated optimized Next.js webpack production build: **PASS**.
  App/lib source hashes match the isolated build snapshot. The build used a closed
  backend target and disabled flags, without changing any existing .next directory
  or starting a server. Production route denial is tested at the page boundary;
  no HTTP/browser claim is substituted for that test.

The two existing render harnesses gained the new optional component import seam;
their assertions were not weakened. Initial incomplete-scaffold/render-harness
failures were corrected before the complete final passing runs.

Build and evidence artifacts are under
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/ssi-provisional-contract-v1-OIhNhs/`.

## Remaining public-release gates

1. Authoritative endpoint-specific units/scaling and venue/day-effective scope for
   MasterData; publication, corrections and session behavior. Owner conventions
   cannot be relabelled provider-confirmed.
2. Summary shares/value semantics, detailed matching/auction/odd-lot/negotiated
   inclusion, cumulative reset/corrections/finality, and source as-of/latency or an
   explicitly approved date-only display policy. No all-market coverage claim.
3. Applicable SSI/venue display and redistribution scope for the intended audience,
   attribution, storage and conditions. Prior owner-reported permission remains
   recognized; it does not become a public field certificate through this code.
4. Separately authorized bounded normal-session acceptance of actual aligned
   observations, selected-sample coverage, cold load and partial/stale/error cases.
   The saved ACB example and simulated timestamp tests are not live acceptance.
5. Reviewed integration into the existing acquisition/cache lifecycle, without
   extra workers or per-row polling; then normal review, release/backup/runtime
   isolation gates and separate controlled-release authorization.

No ICB or financial activation, production Supervisor/Collector/SQLite/pin change,
SSI request/cooldown change, preview lifecycle operation, push or deployment.
Technical Pilot and FPT automation were not touched; OFF/PAUSED remain required.
