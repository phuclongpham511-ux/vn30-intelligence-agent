# SSI Market Board: price bands and matched totals

Public-documentation review: 2026-10-18. Base source checkpoint:
`92a769d48ebfb16bd16e7ee9a742c9dbf4d12932`.

**PRICE_BAND_QUALIFICATION: PARTIAL. KL_GT_QUALIFICATION: PARTIAL.**
Activation remains blocked. This closes specific documentation questions only;
it does not repeat Live Data Readiness V1 or certify current data/account access.
No authenticated API, stream, credentials, production or browser was accessed.

## Authoritative evidence and the new findings

| ID | Official public source, inspected on the review date | Applicable finding and limit |
| --- | --- | --- |
| D1 | [V3 MasterData REST](https://developers.ssi.com.vn/docs/api-reference/data-masterData) | The endpoint supplies the three named prices by trading date. Omitted date bounds select the latest available date, not a guarantee of today's date. Its published example includes symbol, exchange, tradingDate and the three prices; it does not declare their currency/multiplier or a source-update timestamp. |
| D2 | [V3 release notes](https://developers.ssi.com.vn/docs/api-reference/release-notes), v3.2.0 | MasterData is explicitly introduced as beginning-of-day reference data. This closes its intended daily/reference role, not exact availability time, immutability or correction rules. The current portal also documents later v3.3.1 features; Woofi's saved SDK evidence/pin is 3.2.1. Do not infer installed support or entitlement to new features. |
| D3 | [V3 SecuritiesSummary REST](https://developers.ssi.com.vn/docs/api-reference/data-securitiesSummary) | Summary is per instrument/index and trading day. `totalMatch`/`totalMatchValue` are present, separately from `totalDeal`/`totalDealValue`; the published response has a trading date but no per-row as-of/revision timestamp. It supplies no explicit shares/lots or monetary scaling declaration. |
| D4 | [Python SDK models](https://developers.ssi.com.vn/docs/sdk/python/utilities), SecuritiesSummary | The SDK describes total_match as total matched quantity and total_match_value as total matched value. This confirms field meaning, not physical units, odd-lot scope or exclusion guarantees. Numeric types alone do not establish units. |
| D5 | [V3 Market Data stream](https://developers.ssi.com.vn/docs/api-reference/subscribeUnsubscribeMarketData), Trade, Indexsummary, Put, Oddlot and Market | Trade `p` is explicitly denominated in dong and `v` is the day's matched-volume total. Separate put/oddlot channels exist. Indexsummary explicitly assigns shares/dong to tmq/tmv; those are INDEX fields, not the requested per-stock REST fields. Market examples contain date/board and limits without an explicit limit unit. There is no documented conversion from those illustrative limit values to REST MasterData. |
| D6 | [Market Data FAQ](https://developers.ssi.com.vn/docs/faq/market-data) | REST updates periodically; event-driven WebSocket is a different channel. Market Data uses shared models across cash equities and derivatives. Neither fact specifies endpoint-specific refresh latency, applicable venue coverage or units. |
| D7 | [Terms and environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) | API availability outside trading hours does not mean prices continue updating. The page requires service terms and rate-limit compliance but supplies no affirmative Woofi field-specific redistribution grant. General session tables do not establish every venue/holiday/suspension rule. |
| D8 | [V2-to-V3 FAQ](https://developers.ssi.com.vn/docs/faq/v2-to-v3-migration) | V2 and V3 are distinct integration contracts. Older FastConnect Data Volume/Value/TotalVol descriptions are not direct proof for the differently named V3 REST fields. No migration or SDK upgrade is undertaken. |

The stream page was initially inaccessible through a direct web-tool open, then
successfully read through the official release-note link. This is public document
retrieval only; no Send/API Explorer operation or market-data request was made.
Official Trading/FCO price examples and older V2 documentation were excluded as
unit certificates for V3 MasterData/SecuritiesSummary.

## Reused observations, without another probe

[Existing receipts](SSI_MARKET_DATA_QUALIFICATION.md) and
[verified audit](LIVE_DATA_READINESS_V1.json) bind the saved October 17 responses:
ACB MasterData for 2026-10-16 has ceiling 22000, floor 19200 and refPrice 20600.
The same-day ACB summary has totalMatch 5160300 and totalMatchValue 106488260000
in one record. Those are evidence of returned fields, not unit conversion proof.
Negotiated fields are null, not evidence of zero negotiated trading.
MasterData page 1 covers 15/30 saved VN30 members, not full VN30 or all venues.
No saved historical receipt is relabelled as a current-session observation.

## Exact qualification decisions

Statuses apply to the stated proposition. UNKNOWN is not a finding of denial,
absence or contradiction. PARTIAL is not permission to activate.

| Requirement | Status | Resolved evidence / precise remaining gap | SSI question |
| --- | --- | --- | --- |
| Meaning of ceiling/floor/refPrice | CONFIRMED | D1 identifies these as daily price-band/reference fields. | — |
| MasterData price units/scaling | UNKNOWN | No explicit endpoint/asset-class unit declaration in D1/D2. Trade-p units in D5 do not close it. | Q1 |
| Ordinary-equity exchange applicability | PARTIAL | Saved HOSE evidence and D5 market-board examples exist; exact REST scope on HOSE/HNX/UPCOM and special securities/days is not established. | Q2 |
| MasterData trading-day effectiveness | PARTIAL | D1/D2 confirm date-keyed beginning-of-day reference intent. Activation cutoff, all-session validity and corrections are unspecified. | Q2 |
| Session behavior and freshness | PARTIAL | D6/D7 distinguish REST updates and closed hours; MasterData publication time, cache lag, revision/fallback rules remain unknown. | Q3 |
| Price-band display/redistribution scope | UNKNOWN for this extension | Prior owner-reported Woofi permission remains recognized, but the saved field review has no applicable scope attachment for these fields. Public service terms do not settle it. | Q8 |
| Summary quantity/value field meaning | CONFIRMED | D3/D4 identify matched totals in one instrument/day record. | — |
| Shares versus lots / quantity multiplier | UNKNOWN | Neither integer SDK type nor a security's lotSize establishes the totalMatch unit. | Q4 |
| Monetary unit, multiplier and consideration basis | UNKNOWN | No explicit per-stock REST totalMatchValue unit or fees/taxes rule. Index-summary units are a different contract. | Q4 |
| Regular matching versus other trades | PARTIAL | Matched/negotiated field families and separate stream channels are documented; auction/continuous/odd-lot inclusion and exact exclusions are not. | Q5 |
| Cumulative versus incremental | PARTIAL | Summary is a daily aggregate; Trade-v is explicitly a day total. REST intraday update completeness, reset and correction semantics are not specified. It is not an individual-trade delta. | Q6 |
| Source observation timestamp | PARTIAL | Date-level attribution is confirmed. No per-row source as-of appears in D3 or the saved record. Whether another supported receipt exists remains unknown. Retrieval time cannot replace it. | Q7 |
| Applicable Summary exchanges | PARTIAL | One saved ACB/HOSE record; generic multi-market models do not prove this endpoint's complete ordinary-equity scope. | Q5 |
| Summary display/redistribution scope | UNKNOWN for this extension | No applicable field/audience scope attachment in inspected evidence; prior permission is not revoked or reinterpreted as a denial. | Q8 |

**CONTRADICTED propositions:** “a newly retrieved REST response is necessarily
tick-current” conflicts with D6/D7; “Summary daily totals can be accumulated as
individual trade increments” conflicts with D3/D4. The literal D1 example key
`exchange` also does not match the saved MasterData key `board`. This narrow schema
discrepancy is not evidence that a numeric price is wrong. The numerical unit
hypotheses remain UNKNOWN, not CONTRADICTED.

D5's illustrative trade-price and Market limit values have different apparent
scales. This is a documentation ambiguity, not a measured conversion factor or
proof of an error in actual data. No ×1000, lot-size or cross-channel conversion
is inferred. Index-summary units likewise cannot qualify per-stock totals.

## Consolidated questions to SSI — prepared, not sent

Please answer for the existing account/product's V3 REST contract used with
ssi-sdk 3.2.1, and identify the applicable document/version or agreement scope.
No new key, subscription, test request or SDK upgrade is requested here.

1. **Q1 — MasterData units.** For ordinary HOSE/HNX/UPCOM shares, are ceiling,
   floor and refPrice each VND per share at multiplier 1? In the saved ACB
   2026-10-16 example, does 22000 mean 22,000 VND/share? State any board/security
   exceptions and whether these are the actual effective-day quoted prices,
   rather than an adjusted historical-price series. Clarify the scale difference
   between REST values and the Market-stream documentation examples.
2. **Q2 — Effective day and venues.** Which ordinary-equity venues does MasterData
   cover? Define tradingDate/timezone, availability before opening, validity through
   opening auction, continuous trading, lunch, closing auction and after close.
   Can limits/reference change intraday or be corrected after the session? What
   is returned for holidays, suspensions, new listings or delayed exchange updates?
3. **Q3 — MasterData freshness.** What are publication/refresh/cache-lag rules,
   and is a source publication/update/version receipt available? With omitted
   dates or an unavailable requested day, is an older day returned, no content
   returned or an error returned? How must consumers detect stale/corrected rows?
4. **Q4 — Matched units/value.** Does ACB totalMatch 5160300 mean 5,160,300 shares
   at multiplier 1, and totalMatchValue 106488260000 mean 106,488,260,000 VND?
   Specify currency, scaling, precision/rounding and whether value is gross actual
   matched consideration excluding fees/taxes. Do definitions differ by venue?
5. **Q5 — Trading scope.** For these TWO Summary fields, list coverage of opening/
   closing auctions, continuous matching, odd lots, negotiated/put-through trades
   and any other boards/trade types. Are negotiated trades excluded and reported
   only in totalDeal/totalDealValue? Confirm ordinary HOSE/HNX/UPCOM applicability,
   and how instrument/venue identity is bound when the row has no board field.
6. **Q6 — Daily total lifecycle.** Are both fields cumulative from the start of
   tradingDate to one coherent provider snapshot? Do they persist through lunch,
   reset only on a new trading day, and include matched cancellations/corrections?
   When is a day completed, can totals later decrease/change, and what correction
   or finality guarantee is actually available? Do not require monotonicity if
   legitimate corrections can reduce totals.
7. **Q7 — Summary as-of.** The documented/saved row has only tradingDate. Is a
   supported source observation/update timestamp or snapshot/revision ID available
   for the pair, with timezone/precision and refresh latency? If not, confirm its
   date-only semantics and whether it is an intraday partial aggregate or completed
   daily result. Woofi will retain read time separately and cannot certify tick
   freshness from retrieval alone.
8. **Q8 — Existing rights scope.** Does the previously owner-reported SSI
   authorization for Woofi explicitly cover these MasterData and SecuritiesSummary
   fields, live and historical display, storage/caching, derived presentation and
   redistribution to the intended local/authenticated/public/commercial audiences?
   Identify the existing agreement/permission and any venue licenses, attribution,
   retention, delay, fees or expiry restrictions. If it already covers the scope,
   confirm that scope; do not assume a new purchase or permission is necessary.

The historical storage permission recorded on October 10 remains resolved at its
owner-reported authority level ([record](TECHNICAL_EOD_PERSISTENCE_V1.md)). This
review does not reinstate that old blocker. Q8 asks whether the existing scope
covers this extension, not whether successful technical access implies rights.

## Minimal normal-session validation — NOT AUTHORIZED / NOT RUN

1. First close units, scope and applicable-rights questions. Obtain separate
   authorization naming the normal session, a small existing ordinary-equity
   sample (start with ACB/HOSE), permitted transport, finite read budget and timing.
   Additional venues require their own evidence; a HOSE sample proves none of them.
2. Reuse the canonical authenticated transport and its current cooldowns/rate
   limits. Do not launch another Collector, stream or scheduled loop. The pure
   Summary normalizer is not an acquisition path: any bounded Summary validation
   read/shared-cache integration must be explicitly covered by that authorization.
3. Retain original symbol/venue/day, raw fields, provider/source version, source
   time if supplied, request/receipt times separately and content hashes. Compare
   a quote only with independently effective same-day/unit reference/limits;
   never source limits from adjusted historical closes.
4. Observe a cold load and a second authorized observation after the provider's
   documented refresh interval. Keep the matched pair from one response; inspect
   actual unit/scope agreement and source lag. A dated Summary and a later trade
   remain separate observations. Check session boundary/reset behavior only when
   an authorized window actually covers it; otherwise mark it untested.
5. Verify missing, older-day, partial/error and correction handling without forcing
   provider failures: use naturally observed cases or already saved isolated
   regressions. Do not reset cooldowns, force SSI reads, assume null negotiated
   fields are zero, fabricate timestamps or infer GT from last price × KL.
6. Report sample coverage and untested venues/phases explicitly. If no source
   as-of exists, only a clearly dated, read-at-disclosed summary can be accepted
   after its temporal display contract is reviewed; intraday freshness stays
   unverified. This cannot silently enter the existing tick-time activity DTO.

## Activation and validation result

**ACTIVATION_DECISION: BLOCKED_BY_UNRESOLVED_QUALIFICATION.** Required gates remain
unresolved. Existing real SSI limit colors and unqualified KL/GT remain guarded.
`normalize_summary_pair` still preserves unknown units/source time/rights and
`live_display_eligible=false`; current `resolvePriceState` still requires an
independently qualified compatible limit record. No application or test changed.

Only this focused documentation report is added. Link/claim consistency and
`git diff --check` are the relevant checks; no code tests/build, offline acceptance,
new provider probe, normal-session validation or production inspection is claimed.
No push, merge, deployment, process lifecycle, SQLite, Supervisor, Collector,
runtime pin, SSI configuration/cooldown, Technical Pilot or FPT automation change.
