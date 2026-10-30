# Market Board KL / GT qualification — 2026-10-17

Status: development presentation implemented; SSI live acceptance BLOCKED / PARTIAL.
This extends development checkpoint cb5979fa5e1717d4b634a98490cc391f6da50aa5.
No production deployment, acquisition change, new subscription or schema migration.

Continuation note (2026-10-18): the later five-read SSI qualification is now indexed
in [SSI_MARKET_DATA_QUALIFICATION.md](SSI_MARKET_DATA_QUALIFICATION.md). Endpoint
access and actual paired summary fields have been observed; unit/scope/timing and
rights gates remain. Earlier browser/test evidence below is retained, not rerun.

## Column semantics and source evidence

Reuse of the existing firsthand SStock research found a compact grouped price board
with Mã / SM / Giá / +/- / KL. GT is not visible in the captured board image.
The separately captured foreign-investor screen labels GT Mua / GT Bán under
Giao Dịch Nước Ngoài; these are not evidence of ordinary per-symbol traded value.
SM remains proprietary and is neither copied nor fabricated.

Woofi's explicit target is cumulative regular matched shares (KL) and cumulative
regular matched VND (GT), for the same displayed trading day, excluding put-through.
The new contract retains symbol, date, session, observation time, source, raw field,
raw value, unit, cumulative/interval scope, negotiated-trade inclusion and qualification.
Legacy total_volume/total_value are never qualification fallbacks. GT is never
calculated as latest price multiplied by volume.

The installed provider uses V3 trade.<symbol>, not the legacy V2 capitalized fields.
The [official V3 schema](https://developers.ssi.com.vn/docs/api-reference/subscribeUnsubscribeMarketData)
distinguishes q (last matched quantity) and v (daily cumulative matched quantity).
Interval messages have separate start-time/interval semantics. The installed SDK
maps trade total_volume from v and interval volume from v in different models.
The current trade message has no qualified per-symbol monetary-value field.
V2 TotalVol / TotalVal and DailyStockPrice fields cannot simply be renamed into V3.

The [V3 SDK SecuritiesSummary model](https://developers.ssi.com.vn/docs/sdk/python/utilities)
contains total_match and total_match_value. The existing acquisition/presentation
path does not fetch that endpoint. The subsequent bounded diagnostic read returned
ACB's actual 2026/10/16 `totalMatch="5160300"` and
`totalMatchValue="106488260000"` in one record. This proves access to that request,
not broad entitlement or presentation/redistribution rights. Precise units, detailed
regular-board/odd-lot scope, revision/finality rules and original observation time
remain unqualified. The response contains a trading date, not a tick timestamp.
No summary acquisition loop or additional provider subscription was introduced.
Integration remains gated; never attach this daily pair to a tick just because the
symbol and trading date match. Reuse the saved response rather than repeat the read.

Actual preserved replay evidence has 30 SSI OHLC 1-minute symbols and zero non-null
volume/value observations. It is not same-session tick or GT validation. No actual
live-symbol coverage count for qualified KL/GT can be asserted. Qualification was
performed on Saturday, 2026-10-17; no normal market-session acceptance was performed.

The adapter preserves original v as unverified evidence with unit unknown,
scope unverified_matched and negotiated-trade inclusion unknown. GT stays unavailable.
OHLC bootstrap never inherits trade activity metadata. Interval messages cannot enter
the tick cache. Thus real current data shows em dashes until explicitly qualified.

## Implemented presentation

Desktop retains three compact panels: ticker, price, change %, KL, GT and source
control. Numbers are right-aligned and tabular; observed row height is about 32.4px.
Raw numerical volume/value sorts place unknowns after qualified metrics. Price and
change sorts remain available. Missing metrics are em dashes; genuine zero is zero.
EN uses K/M/B, VI uses K/triệu/tỷ; original precision remains inspectable in source
details. Headers disclose shares/VND and cumulative matched scope.

Mobile retains ticker/price/change and an explicit hint to open the source control
for KL/GT, original units and timestamps. The dialog scrolls within 85vh. Sorting
remains available. Observed 390px page width equals scroll width; no page overflow.
Stock Research reuses the same no-fetch activity component inside source details.
Heatmap area/weights, news cards and unqualified industry groupings are unchanged.

Purple ceiling and cyan floor require exact source-qualified same-date/time limits;
ordinary green/yellow/red semantics remain. No assumed percentage creates a limit.
The current provider adapter does not assert qualified limit metadata.

## Validation and limits

Actual isolated application: 127.0.0.1:3400, fixture backend: 127.0.0.1:3401.
Both are separate from production 3000/8000. All activity fixture evidence is
visibly SIMULATED / NOT SSI. Independent supplied monetary totals are not derived
from fixture prices. No production database is opened by the fixture backend.

Browser checks at 1440x900 and 390x844 exercised EN/VI and light/dark, KL/GT numeric
sorts, zero/missing, stale quote, invalid units/scope/time, unavailable GT, exact
qualified synthetic price limits, source dialog/Escape, and Stock Research navigation.
An all-unqualified case displayed 60 em dashes for 30 symbols' two activity metrics.
The dialog exposed original fixture field, unit, full raw total, source and time.
Synthetic Saturday observations exercise UI contracts only, not trading-calendar proof.
Screenshots alone do not certify SSI units, rights, current session or live coverage.

Focused Python regression: 84 passed; final frontend regression: 182 passed,
one skipped, zero failed. Typecheck and supported webpack build passed.
Tests cover duplicate/out-of-order ticks, lower corrected totals, zero reset,
interval rejection, raw numeric sorting, large values, prior-day/weekend carryover,
stale/missing/invalid metadata and exact qualified limits. Existing timeout/error
handling is reused; no new provider transport was introduced.

Evidence folder:
C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/market-activity/.
Use source-mobile-dark-en.png as the final mobile inspector evidence. The earlier
source-mobile-light-vi.png capture caught an intermediate layout and is excluded.
No claim of physical mobile-device testing or live-market acceptance is made.

## Required gate before live integration / release

1. Retain the already successful bounded access evidence; establish contractual
   entitlement and presentation/redistribution rights for the intended use of
   existing trade data and the candidate per-symbol summary endpoint.
2. Obtain authoritative units and regular-matched/put-through scope for a paired
   volume/value contract. Confirm original timestamp and daily cumulative/reset rules.
3. Authorize any additional endpoint/subscription/acquisition/schema/credential
   work separately if required. Reuse the canonical lifecycle and request bounds.
4. In a normal market session, inspect authorized original responses and compare
   actual same-symbol/day KL/GT, source time, cold load and partial failure behavior.
5. Keep release gated until that live acceptance and normal review/backup gates pass.

MasterData limits and SecuritiesInfo ICB availability were also inspected in the
same completed five-read task. Neither is permission to activate new market colors
or industry grouping. Their exact coverage and separate gates are recorded in the
linked source qualification; do not restart the investigation or infer classifications.

No production process, journal, SQLite content, cooldown, runtime pin, Technical
Pilot flag or FPT automation setting was changed by this development task.
Technical Pilot must remain OFF and FPT PAUSED. No push or deployment occurred.
