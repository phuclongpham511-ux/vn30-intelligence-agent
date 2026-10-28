# Woofi live data readiness V1

Reviewed 2026-10-18 against application checkpoint
`62a4f11618d46f4b06668b32ff4b62d6465f38e8`.

Decision: **PARTIAL readiness; no additional live activation.** Existing product
approval is retained. New field families do not inherit qualification from a
successful SDK request, an accepted replay, or a different SSI endpoint.
Offline Replay Acceptance V1 is PASS; it is not repeated or promoted to live
acceptance here. No browser/server operation or provider request was performed.

## Evidence actually reused

| ID | Existing evidence | What this review establishes |
| --- | --- | --- |
| E1 | [SSI field qualification](SSI_MARKET_DATA_QUALIFICATION.md); saved `ssi-qualification/evidence.json`, `analysis.json`, `alignment-checks.json`, `FINAL_REPORT.md` | All four SHA-256 receipts still match. Recounted the five saved October 17 responses, without repeating any request. SDK evidence is 3.2.1, matching the project pin; not a new installed-runtime/entitlement inspection. |
| E2 | [Recorded SSI product qualification](../research/provenance/technical_data_readiness_v1/SOURCE_DECISION.md), section “SSI provider-confirmed qualification update — recorded 2026-10-07”; `CONTEXT.md`, SSI product qualification | Prior product approval covers current/live presentation and current adjusted historical charts/indicators. Existing normalization is prices VND ×1, daily volume shares ×1. This is the owner's supplied provider confirmation, not independently retrieved correspondence. |
| E3 | [Historical storage/use authorization](TECHNICAL_EOD_PERSISTENCE_V1.md), Authorization and scope | October 10 owner-reported SSI permission covers authorized API use, historical storage/retention, processing, derived analytics, redistribution and commercial use within Woofi. The former historical storage blocker is resolved at that recorded authority level. |
| E4 | [Financial qualification](FUNDAMENTAL_ANALYSIS_V1_INCREMENT.md), [normalizer audit](FUNDAMENTAL_DATA_ENGINE_V1.md); nine saved FPT/PNJ/VCB annual/quarterly/TTM display packets and their original engine captures | Recomputed all nine original input hashes against the earlier audit; all match. Saved display packets contain 120 UNQUALIFIED and 51 UNAVAILABLE metric slots, zero QUALIFIED. These are nine responses for three issuers, not broader coverage. |
| E5 | [V2.2 source contract](MARKET_WORKSPACE_V22_INCREMENT.md); current provider, universe, price resolver and financial presentation code | Implementation readiness is separate from data availability, contractual qualification, display rights and normal-session acceptance. |

Machine-readable audit, file hashes, exact saved response coverage and financial
receipts: [LIVE_DATA_READINESS_V1.json](LIVE_DATA_READINESS_V1.json). External
artifact roots are recorded there; original evidence is unchanged. Source review
does not re-certify production health, current caches, credentials or entitlement.

## Rights reconciliation

Do not repeat the obsolete claim that all SSI historical storage rights are
unresolved: E3 is later than the unresolved October 7 entry in E2. Retain the
distinction between owner-reported permission and independently reviewed legal
documentation. This review neither invalidates existing product authorization
nor grants a broader license.

E1 explicitly leaves the newly investigated SecuritiesSummary, limits and ICB
display scope unresolved. E3 concerns the historical operational slice; it does
not resolve endpoint-specific units, ICB taxonomy rights, account/product scope
or intended-audience conditions for the new families. A scope addendum or an
applicable existing agreement that actually covers those fields is sufficient;
do not require a new license if the existing one demonstrably applies. Record
the evidence, source/account/product, permitted audience/use, conditions and
effective/expiry scope without storing credentials.

VCI/vnstock financial display rights require their own applicable evidence. SSI
permission and an installed open-source SDK do not establish VCI content rights.

## Field activation matrix

QUALIFIED below means the **existing product contract** and its recorded use
scope, not today's freshness or a new live acceptance result. PARTIAL means real
evidence exists but named requirements remain. BLOCKED describes activation,
not an assertion that the provider lacks the data. Work is proposed, not applied.

| FIELD | SOURCE | EVIDENCE | QUALIFICATION_STATUS | MISSING_REQUIREMENTS | SAFE_DISPLAY_BEHAVIOR | IMPLEMENTATION_WORK |
| --- | --- | --- | --- | --- | --- | --- |
| `symbol`, VI/EN company name, `exchange`, ordinary-equity identity | SecuritiesInfo/securitiesByBoard → persisted `Security` | E1 returned 406 explicit Stock records on HOSE, plus 30 VN30/100 VN100 records; E2 existing product path. Adapter explicitly admits Stock on HOSE/HNX/UPCOM. | QUALIFIED existing identity contract; current cache/coverage not revalidated. | Normal canonical-cache freshness/partial-failure acceptance. E1 does not prove HNX/UPCOM completeness. Names may be absent. | Original source name/exchange; missing names remain missing. `last_synced_at` is cache synchronization, not issuer publication or listing effectiveness. | Existing `SecurityMetadata`, universe cache, search and company header already consume these fields. No adapter/schema change for the first slice. |
| `last_price`, `price_unit` | Raw SSI trade `p`; quiet-symbol bootstrap uses `OHLC 1m.close`, with a distinct source tag | E2 existing current-price approval; `src/providers/ssi/live.py` normalizes positive finite prices as VND. | QUALIFIED existing product price contract; present-session delivery PENDING. | Observe actual canonical response, coverage, source age and cold load in a normal market session. Do not infer market-wide coverage from E1. | VND ×1, actual source/time; stale/unknown/error stays explicit. A one-minute bar close is not relabelled as an individual trade. | Existing shared live lease/cache and `LivePrice` suffice. No extra subscription, per-row read or provider fallback. |
| `reference_price` / raw MasterData `refPrice` | SSI MasterData | E1 ACB 2026-10-16 refPrice 20600; same-date summary/previous saved OHLC alignment. Existing `_references()` retains date/reference. | PARTIAL for additional field-level activation; existing reference consumer is unchanged under prior product approval. | Explicit MasterData price unit/multiplier and day-effective/session compatibility contract. Numerical agreement alone does not close it. | Do not substitute adjusted prior close or another session's reference. Newly qualified reference requires same instrument, date and unit as its quote. | After qualification, retain provenance/unit/effective-date evidence in the existing reference cache; no new endpoint. |
| `change`, `change_percent` and ordinary direction | Existing Python `normalize_trade`: last minus same-day reference; percent = difference/reference ×100 | E2 existing presentation; code passes reference only when its date matches the source trade/bar date. | Existing calculation contract implemented; additional qualification PARTIAL while reference evidence above remains incomplete. | Positively qualified reference/price pair; normal-session behavior and partial failures. Do not describe these values as source-computed changes. | Null reference produces null change, never zero. No adjusted-history return substituted for intraday movement. Unknown comparison stays unknown. | Reuse backend calculation and current frontend resolver; no new numerical implementation. Do not broaden activation to a newly unqualified reference. |
| `updated_at`, `trading_date`, `source`, freshness/session | Trade `t` or minute-bar `tradingDate`; local `as_of` is a separate read time | Existing timestamp parser and source-age logic; E1 has dated historical metadata, not live ticks. | QUALIFIED timestamp/freshness contract for existing quote path; actual live acceptance PENDING. | Current normal-session source observations; no recent local receipt can certify a stale provider observation. Holiday/venue-specific session facts are not established by wall clock alone. | ICT/UTC+7 source time, exact source date; retain stale/missing/error and unknown session. Source age is per observation. | Existing 120-second active/unknown quote age check, day matching and existing break/close handling remain. No new clock/poll loop. |
| `ceiling`, `floor` with day-effective reference | SSI MasterData | E1 page 1 has 1000/1979 records, 15/30 returned VN30 members; all 15 have positive ordered limits. ACB floor/ref/ceiling = 19200/20600/22000 on 2026-10-16. | PARTIAL data; activation BLOCKED. | Explicit unit/multiplier; board/day-effective applicability; intended display scope; normal-session compatibility. No page-2 absence claim. | No ceiling/floor classification from percentage changes or adjusted daily prices. Never borrow a quote timestamp for a date-only limit. | Extend existing `_references()` cache and live DTO after qualification. Current `PriceLimits`/`resolvePriceState` ALREADY supports qualified `effectiveness='trading_day'`, matching symbol/date/VND/reference. No resolver redesign or new endpoint is needed. |
| KL `totalMatch`; raw daily trade `v` | Preferred SecuritiesSummary same-record pair; `v` is a separate daily cumulative candidate, `q` an individual quantity | E1 ACB 2026-10-16 `totalMatch='5160300'`. Installed SDK mapping and supplied daily-stream description are already recorded. | PARTIAL; activation BLOCKED. | Explicit shares-versus-lots/multiplier, regular-board/odd-lot and negotiated scope, interval/reset/correction/finality semantics, rights and session acceptance. Daily historical-volume units cannot automatically qualify this field. | Keep unavailable KL as em dash. `lotSize=100` is not evidence for multiplying/dividing KL. Do not merge summary totals with tick-time `v`. | Existing pure `normalize_summary_pair` preserves exact/raw values, unknown units and `live_display_eligible=false`. A separately reviewed dated-summary display contract and bounded shared acquisition/cache authorization are needed; no per-row requests or worker. |
| GT `totalMatchValue` | SAME SecuritiesSummary observation as `totalMatch` | E1 ACB same row `totalMatchValue='106488260000'`; `totalDeal` and `totalDealValue` are null. | PARTIAL; activation BLOCKED. | Monetary unit/multiplier, matched-board/odd-lot inclusion, temporal/finality and rights gates as above. Date-only values are not a tick snapshot. | Keep GT unavailable. Never last-price × volume. Negotiated null is unknown, not zero; do not mix two observation times or add unknown negotiated totals. | Reuse paired normalizer. Publish a separately dated pair only after the summary temporal contract is qualified; do not fabricate `observed_at` to satisfy current tick-activity DTO. |
| Daily adjusted `open`, `high`, `low`, `close` | Existing SSI V3 OHLC `timeFrame=1d` through `get_history` | E2 adjusted product qualification; E3 historical-use permission. Current query-time series, prices VND ×1, completed dates before today in Vietnam. | QUALIFIED for existing product charts/current indicators, not PIT benchmark/finality certification. | Normal connected-consumer acceptance and visible basis disclosure before extending chart use. No new source investigation into unavailable private adjustment formulas. | Identify currently adjusted historical series and last completed session; no current intraday/limit join. Cash/share/rights/issuance adjustments are provider-confirmed; factors/vintages/revision chronology are not supplied. | Reuse bounded history/cache and existing chart. `MarketBar` carries source/currency but no explicit adjustment-vintage receipt; any expanded display should add source-qualified adjusted/query-time disclosure through the existing chart contract, not invent a vintage. Not required in the first slice. |
| Daily historical `volume` | Existing SSI daily OHLC `volume` | E2 prior product normalization shares ×1. This differs from Summary/stream units. | Existing product units QUALIFIED; cross-action historical volume comparability PARTIAL. | Adjustment/action coverage needed for claims requiring comparable share units across actions; not required to display the original dated observation honestly. | Preserve shares and session date. Do not imply adjusted volume, PIT validity, or use this as today's matched total. | No new normalization; retain the existing stricter research/provisional gates. |
| `icbCode`, `icbName`, official industry grouping | SSI SecuritiesInfo | E1 paired VN30 30/30, VN100 100/100, HOSE ordinary stocks 406/406; 431/785 across all HOSE instruments. | PARTIAL availability; grouping activation BLOCKED. | Taxonomy version, classification level, parent/hierarchy contract, classification effective/update policy and applicable display/redistribution rights. No broader equity/HNX/UPCOM or longitudinal completeness evidence. | Preserve exact provider code/name when qualified; missing is Unclassified. Four-character codes do not establish a hierarchy. DEMO categories remain synthetic and isolated. | Existing Security persistence has no ICB fields. After gates pass, reviewed metadata/schema extension and canonical universe refresh retain code/name plus taxonomy/effectiveness/provenance. Reuse Board organization; no scraping, new worker, code-prefix sectors or inferred industry returns. |
| Revenue, PAT, EPS, profitability, assets/liabilities/equity, cash flow | Existing vnstock:VCI statements/metadata and Python engine | E4 nine saved annual/quarterly/TTM packets, latest annual 2025 and quarter 2026-Q2, all consolidation null. | UNQUALIFIED live metric display; no saved QUALIFIED values. | Explicit per-statement consolidated/standalone basis; authoritative units/codes where unresolved; issuer fiscal boundaries; publication timezone/precision and latest-available/revision evidence; applicable VCI content rights. | Existing UNQUALIFIED/UNAVAILABLE distinction, null metrics/charts/comparisons, original receipts and raw evidence disclosure remain. Read time is not publication time. | Keep `display_financial_response` and client guards unchanged. After evidence, map only actual provider basis/publication metadata in existing normalizer; never infer it from ticker, company name or matching unknowns. |
| Market cap, P/E, P/B, BVPS | No compatible qualified valuation input set | E4 existing engine exposes these as UNAVAILABLE. SecuritiesInfo `listedShare` is not automatically outstanding/free-float/weighted-average shares. | UNAVAILABLE. | Compatible price/date/adjustment basis, shares/book value/parent earnings and period conventions with source rights. Reported EPS is not automatically a P/E denominator. | Em dash with reason; no proxy valuation or financial-health score. | No activation or new formula. Revisit existing valuation slots only after a complete compatible input contract exists. |

## Financial qualification details

The engine's units are VND monetary amounts, VND/share EPS, fractional rates and
dimensionless multiples; display millions/billions do not scale EPS. The prior
normalizer audit supports known VCI code/label/unit mappings and independent
annual/quarterly flow conventions. Its source boundary still defaults omitted
`currency`/`unit` to the audited VND contract. Those defaults and passing tests are
not independent issuer-filing verification and cannot qualify a different provider
or changed endpoint unit.

Source `yearReport`/`lengthReport` identifies reported year/quarter, not an invented
fiscal end date. Annual and quarterly reports remain separate; four-quarter TTM
requires contiguous compatible flows. Quarterly `basis='standalone'` describes
noncumulative quarter flow, not standalone-company consolidation. Existing saved
`publicDate`/`updateDate`/`createDate` strings do not supply an authenticated timezone
or prove the current latest filing. Historical revisions in those strings are not
a PIT archive. No figures are enabled while consolidation is unknown.

## Smallest activation plan

1. **Candidate first slice:** cached ordinary-equity identity/name/exchange and
   existing last price with original source, trading date, timestamp and explicit
   freshness/session status. Existing reference/direction remain subject to their
   own contract; do not make new reference/limit claims to complete this slice.
   KL/GT, real ICB, valuation and unqualified financial metrics stay guarded.
   Daily adjusted charts are an already approved separate product path, not a
   dependency for first-slice quote display.
2. **Reuse existing code:** `src/services/universe.py`, `src/providers/ssi/live.py`,
   `src/services/live_market.py`, `routers/stocks.py`, frontend LivePrices lease,
   current CompanyOverview/LivePrice/price resolver. Existing collection owns
   identity updates; existing demand leases own quote requests. No new component,
   background worker, scheduler, polling loop, per-row provider call or schema is
   needed for this candidate slice. No activation code is applied by this review.
3. **Connected acceptance gate:** use only the existing authorized canonical path
   during a positively identified normal Vietnamese trading session. Bound the
   selected cached sample (e.g. the actually returned VN30 members), record source
   coverage and timestamps, cold load, missing/stale/error behavior, partial failure
   and cross-ticker navigation. Acceptance must bind this source checkpoint and the
   actual backend contract/build. Current-session evidence was NOT acquired here.
   Do not reacquire the five E1 probes or reset cooldowns to perform this check.
4. **Keep the replay intact:** the prepared external replay snapshot has rewritten
   offline API handlers, not merely a different backend environment variable.
   Changing its `BACKEND_URL` does not make it live. A separately authorized future
   connected build must use the source tree's existing proxy and an explicitly
   identified permitted backend. Do not point the replay at production, replace
   the running preview, or change runtime configuration as part of readiness.
5. **Database boundary:** cached `/stocks/universe` is a SELECT path. `/stocks/live`
   can acquire/lease SSI observations; it is not a no-acquisition health probe.
   GET `/stocks/{symbol}`, `/history` and `/market` use `require_stock`, which can
   invoke `add_stock` and commit for an otherwise eligible but not-onboarded ticker.
   Do not call them against production as read-only diagnostics. Future isolated
   connected acceptance must use known onboarded records in the authorized data
   context or separately authorize a source-only read-contract correction.
6. **New families:** obtain one consolidated authoritative source/account-scope
   response for remaining limits/KL-GT units and temporal/scope rules plus ICB
   taxonomy/update/rights facts. Reuse saved samples to test those specific
   statements, rather than repeating field discovery. Financial reporting-basis
   and rights evidence belongs to VCI/original filings, not the SSI request.
   Only then implement the named incremental cache/DTO/schema work and run the
   corresponding existing focused contracts before any live acceptance.

## Validation and checkpoint

This review ran deterministic saved-evidence checks, not another product test
campaign: four preserved SSI file hashes match; nine original financial capture
hashes match; qualification counts match the previous audit; no nonqualified
saved summary exposes a value. Raw sample coverage was recomputed, including
15 positive ordered VN30 limit records on the bounded MasterData page.

Only this report and its evidence audit are added. No application, test, dependency,
schema, configuration or acquisition code changed; typecheck/build/regression runs
are not needed for these documentation artifacts. Existing replay tests and the
34-test final acceptance result remain historical evidence, not a new run here.
No new live source is certified and no production/cache/process health is claimed.

No production Supervisor, Collector, SQLite, runtime pin, acquisition state or
cooldown was read or changed. Technical Pilot and FPT automation settings were
not touched; OFF/PAUSED remain required. No push, deployment, server lifecycle
operation or browser acceptance was performed.
