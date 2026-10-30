# SSI Market Data Qualification & Integration V2

Base and unchanged production application: `a98793a159b203d87937ec3c66b8e3e4b45cad41`.
This is a development-only evidence increment, not a production activation.

## Session decision — zero new SSI requests

Clock checked at **2026-10-19 15:58:57 Asia/Ho_Chi_Minh** (08:58:57 UTC, Monday).
The existing HOSE continuous-session gate permits 09:15–11:30 and 13:00–14:30,
with the upper bounds excluded. This observation is outside both windows.
**Provider requests 0; authentication requests 0; live rounds 0; live symbols none.**
ACB/FPT remain the two planned symbols, not newly observed symbols.

Reused calendar evidence: external `ssi-normal-session-v1-20261018-session-unavailable/SESSION_GATE.json`.
It cites the official indexed [HOSE 2026 holiday notice](https://www.hsx.vn/vi/tin-tuc/hose-thong-bao-lich-nghi-giao-dich-nam-2026/2437411)
and [hours document](https://staticfile.hsx.vn/Uploads/UploadDocuments/2372196/2.Thoi%20gian%20giao%20dich.pdf).
Their direct retrieval previously timed out; this task does not claim a fresh
calendar/exceptional-closure certification. Time alone is sufficient to deny
today's requests. No future session is certified or scheduled. Before any later
request, revalidate the actual calendar, continuous window and symbol restrictions.

## Reused evidence and scope

- Five October 17 source reads remain the evidence: VN30/VN100/HOSE SecuritiesInfo,
  October 16 MasterData page one and October 16 ACB SecuritiesSummary. No read repeated.
- Original evidence SHA-256 remains
  `7daa4ee90df0e8241749e3004326ccd4d6035d1df2725789d67ee6a40d62202b`.
- Saved ACB: floor 19200, reference 20600, ceiling 22000; matched quantity 5160300,
  value 106488260000, trading date 2026-10-16. Ordered/finite bands and a plausible
  same-record value/quantity ratio pass the existing internal ×1 contract. This
  does not prove endpoint units, trade inclusion or exchange certification.
- Saved ordinary-equity ICB pairs: VN30 30/30 (13 codes), VN100 100/100 (28 codes),
  HOSE 406/406 (61 codes) from 785 returned instruments. No duplicate/conflicting
  assignment observed within those saved samples. Other instrument types are
  excluded; this is not all-equity coverage. HNX/UPCOM are **not sampled**.
- There are no two independently fetched real Summary rounds in the saved archive.
  Correction/increase/decrease edge cases in tests are explicitly simulated.
  No repeated historical record is presented as two live observations.

## Field-by-field qualification matrix

`VERIFIED` below applies only to explicitly supported technical facts. Overall
field decisions remain separate from evidence availability and display rights.

| Field | Endpoint / original field | Unit and normalization | Evidence / technical status | Limitations and rights applicability | Overall decision / public eligibility |
| --- | --- | --- | --- | --- | --- |
| Ceiling | MasterData / `ceiling` | VND/share ×1, owner convention | Saved ACB positive 22000; same-key/day ordering VERIFIED for that record | Provider-specific units, venue/session/correction behavior and applicable new-field display scope unresolved; no current trade join | PROVISIONAL; INTERNAL_ONLY; public NO |
| Floor | MasterData / `floor` | VND/share ×1, owner convention | Saved ACB positive 19200; ordering VERIFIED for that record | Same limits as ceiling; never infer from percentage or adjusted OHLC | PROVISIONAL; INTERNAL_ONLY; public NO |
| Reference | MasterData / `refPrice` | VND/share ×1, owner convention | Saved ACB 20600 between floor/ceiling; documented beginning-of-day role | Current-session/raw last-trade compatibility, exact units/effectiveness and new-field terms remain unresolved; no adjusted-close substitution | PROVISIONAL; INTERNAL_ONLY; public NO |
| KL | SecuritiesSummary / `totalMatch` | Shares ×1, owner convention; exact integer | Saved ACB 5160300, nonnegative; one coherent daily pair | Shares/lots certificate, board/auction/odd-lot scope, reset/correction/finality and new-field terms unresolved. No all-market claim or summation | PROVISIONAL; INTERNAL_ONLY; public NO |
| GT | Same SecuritiesSummary record / `totalMatchValue` | VND ×1, owner convention | Saved ACB 106488260000; rational value/volume ratio within supplied bands | Monetary scale and detailed trade inclusion remain provisional. No last-price × volume calculation; null negotiated totals stay unknown | PROVISIONAL; INTERNAL_ONLY; public NO |
| Trading date / exchange / symbol | Original `tradingDate`, `board`, `symbol` | Date-only / opaque venue & symbol; exact validated identity | Same symbol/venue/day checks VERIFIED for supplied internal records; existing identity contract remains active | Trading date is not intraday source time. Sample availability is not today's coverage or all-venue entitlement | Existing qualified identity path unchanged; newly joined market records INTERNAL_ONLY |
| Market source time | Optional source timestamp in original receipt | Offset-aware original time, never fabricated | Saved MasterData/Summary have no original intraday timestamp | Date-only historical observations cannot certify live freshness, even with a recent fetch. Source latency/correction policy unresolved | UNAVAILABLE in saved pair; NEEDS_MORE_EVIDENCE; public live-as-of NO |
| Fetch time | Existing receipt `received_at` → `fetched_at` | Offset-aware local receipt time, no exchange-time conversion | Preserved original October 17 retrieval receipt and source-document hash | Verifies retrieval only. Existing quote-path source timestamps are a different, already implemented contract | VERIFIED receipt fact; internal provenance only for these unactivated records |
| Industry code | SecuritiesInfo (securitiesByBoard) / `icbCode` | Exact opaque string, leading zeros preserved; no scaling | Saved pair coverage above; raw code retained, no inferred hierarchy | Taxonomy level/version, update/effective dates, HNX/UPCOM coverage and taxonomy/new-field rights applicability unresolved | Observed pair UNQUALIFIED; NEEDS_MORE_EVIDENCE; public NO |
| Industry label | Same record / `icbName` | Exact original provider label | Nonempty code/name pairs and no observed mapping conflict in saved samples | Listing date is not classification effective date; no sector/parent inference or hardcoded map | Observed pair UNQUALIFIED; NEEDS_MORE_EVIDENCE; public NO |

An invalid identity, currency/unit declaration, band order, source chronology or
implausible pair remains **INVALID** and is rejected, not repaired or rescaled.
The saved accepted ACB example contains no demonstrated numerical contradiction;
it remains provisional. A future contradiction must not silently change ×1 units.

## Rights reconciliation — preserve existing authorization

The [October 10 authorization record](TECHNICAL_EOD_PERSISTENCE_V1.md) reports SSI
permission for authorized API use, historical retention, processing/derived
analytics, third-party redistribution and commercial use **within Woofi**.
The [prior provider qualification](../research/provenance/technical_data_readiness_v1/SOURCE_DECISION.md)
also records existing product/live-price and adjusted-history use. These are
recognized owner-reported grants, not absent rights and not independently reviewed
legal correspondence. This task does not revoke or demand replacement of them.

The existing [readiness reconciliation](LIVE_DATA_READINESS_V1.md#rights-reconciliation)
specifically leaves applicability to the newly investigated Summary, MasterData
and ICB service/taxonomy/audience conditions unresolved. First map any existing
agreement/confirmation to those fields, account/product, audiences, storage/use,
attribution and effective/expiry conditions. An applicable existing grant is
sufficient; request new authorization only if a material uncovered scope remains.
Successful API access and the SDK license alone do not resolve those conditions.
No new SSI authorization was requested in this task.

## Small source increment, no public activation

Two pure functions extend existing `src/services/market_summary.py`; no acquisition,
endpoint, cache writer, schema, worker, scheduler or new UI was added:

1. `compare_provisional_snapshots`: reconstructs both canonical packets from their
   original raw receipts, rejects edited values/public flags and cross-key/date or
   out-of-order receipts. Keeps the latest snapshot as a **replacement**, with exact
   rational deltas and a provisional implied average (not a last-trade price).
   Decreases, source-time regression and band revisions are retained as review
   flags; never clamped, repaired or summed. Missing source time stays unverified.
   Zero volume never divides by zero. `public_display_eligible` and live two-round
   acceptance remain false. No normal-session acceptance is granted by this helper.
2. `audit_icb_metadata`: validates bounded raw ordinary-equity records and original
   document receipts; exact pair/raw values and record hashes remain inspectable.
   Duplicate rows cannot inflate coverage; contradictory assignments/code names or
   incomplete variants cannot produce a usable pair. Taxonomy level/version and
   effective time remain null. All outputs stay internal, including observed pairs.

Existing provider adapters, acquisition/cache behavior, normalizers' public
contracts and production flags are unchanged. No saved real ICB archive was added
to public routes, frontend bundles or repository fixtures.

## Narrow integration path, independently gated fields

- Keep the already qualified identity, existing quote source-time/freshness and
  current direction displays active. New-family uncertainty must not block those
  existing Board/Heatmap features or promote unrelated fields.
- Bands: after applicable field/rights/session gates, retain original day-effective
  metadata/receipts in the existing `_references()` cache. Feed the existing
  qualified PriceLimits DTO/resolver only on a compatible same-key/day/reference
  join. No new endpoint/schema is inherently required; retain unknown/stale states.
- KL/GT: qualify the coherent **pair**, detailed matching scope and date-only/as-of
  policy first. Reuse the existing raw provider transport and shared cache lifecycle
  for explicitly bounded observations. Use the comparator before any reviewed cache
  replacement policy; review decreases/source regressions rather than hiding them.
  Do not wire a per-ticker polling loop or label a date-only pair as tick activity.
- ICB: once taxonomy/update/rights gates pass, extend existing Security metadata/
  persistence with original pair and provenance under a reviewed migration. Reuse
  Board filters/organization and Stock Detail labels; no hardcoded code-prefix
  hierarchy. Heatmap grouping must retain stock labels and equal-area semantics,
  not imply sector returns, money flow or official hierarchy without evidence.

**Additional fields READY_FOR_ACTIVATION: none.** The two evidence helpers are
implemented; they do not turn unresolved data into production-ready facts.

## Validation and next bounded session

Focused Python regression and existing public/internal frontend guard tests ran
offline; result logs and machine-readable findings are in external artifact folder
`ssi-market-integration-v2-20261019`. Edge-case records are simulated and labelled in
tests, not live SSI evidence. Final results: **120 Python tests PASS**, including
14 new cases, plus 32 subtests; **10 frontend guard tests PASS**, no failures.
One existing Starlette/httpx deprecation warning remains. Typecheck PASS.
Frontend, dependencies and API routes
are unchanged: reuse the exact deployed a98793a production build and 18 staged /
18 production route/API checks, rather than rebuild identical frontend source or
rerun the completed offline visual matrix. Browser operations: none.

During a later verified normal continuous session, follow the existing plan:
reuse same-day canonical cache/receipts for ACB/FPT if available; four selected
Summary reads across two time-separated rounds, at most six total requests,
counting wire attempts/retries. Respect existing sessions/cooldowns and stop on
uncertainty, pagination, entitlement/rate limits or missing same-day prerequisites.
No broad MasterData fetch invented as a symbol filter; no new subscription/worker,
forced refresh or longer retry loop. This task schedules no follow-up and makes
no provider requests. Production pin, P1, Collector, SQLite, locks, Pilot and FPT
were not modified. No push, merge or deployment is authorized by this increment.
