# Targeted Overview and Heatmap refinement — local development

Development base: `79cbe4661c4139609017f582de0b55a93a0f5682`.
Production pin: `1d7706a90f9270fa91e245c671ccb7ed9ce98777` (unchanged).
User product acceptance remains PENDING. Nothing pushed, integrated or deployed.

## Implementation and review

Overview replaces the sparse right column with full-width sample context, paired
largest-advance/decline tables, compact research navigation and content-sized News.
Selection controls use an inspectable disclosure. Direction and rankings require
at least two fresh, finite-percentage observations sharing a known session and
trading date; existing quote qualification remains authoritative. Stale/missing
observations and failed transports never become current movers. Values remain
source values; the small distribution strip shows counts, not an index return.

Market Focus reuses the existing persisted `/news/feed` Market Brief/Company reads
and qualification policy. Compact mode bounds publication/labelled observation age
to 24 hours and preserves publisher, original headline, timestamp, URL and existing
category. It creates no quote lease for News chips. No new acquisition, scheduler,
causation, sentiment, FOMO or financial calculation. Read-only production inspection
found six records in each bounded category; a saved projection rendered three
original Market Brief headlines in isolated replay. This is persisted News reuse,
not live SSI quote qualification.

Market Heatmap defaults to 10 desktop columns of 78px-high equal-area cells and
three mobile columns of 80px-high cells. Compact cells emphasize ticker and signed
percentage. A separate keyboard/touch source button opens price, original source,
time, trading date, session and reference evidence. Detailed mode retains price and
time in larger cells. Density is local presentation state, with no upstream call.
Watchlist retains its existing detailed-cell default; Stock Research is unchanged.

The five exact percentage bins and neutral stale/missing/error semantics remain.
Optional movement groups are counted from the filtered loaded sample, never sectors.
Equal area means layout, not capitalization, volume, strength or importance.
The ordinary Board retains its columns, sorting and three-panel desktop structure.
Only its shared coverage label changes to Selected index + Visible sample + actual
quote counts. Failed initial/refresh requests show unknown coverage, including when
previous values remain visible neutrally.

Browser-demonstrated corrections: move Overview filters behind a compact disclosure
after they delayed the first mobile stock row; reduce empty News to a compact row;
fix a confirmed empty universe showing perpetual quote loading despite no symbols.
The largest declines now sort most negative first, with deterministic ticker ties.

## Actual browser evidence and measured tradeoffs

All prices and index values in controlled UI captures are SIMULATED, with an
explicit banner. No synthetic fallback is present in application data paths.
Only the isolated 3400 frontend and no-DB/no-provider 3401 fixture were used.
Existing static evidence hosting is on 3450; it is not an alternative app runtime.

Viewports: 1440x900 desktop and 390x844 mobile CSS pixels. EN/VI and light/dark
controls, sorting, VN100 sample scope, movement groups, ticker navigation, source
dialog/Enter/Escape/focus return, tap/click controls and overflow were exercised.
Touch accessibility was checked in the mobile browser, not on physical hardware.

| Measurement (EN, same fixture/scopes) | Before | After |
|---|---:|---:|
| First Overview stock row, desktop | 405.8px | 400.8px |
| First Overview stock row, mobile | 415.6px | 438.3px |
| Fully visible desktop Heatmap cells | 24 | 30 compact / 24 detailed |
| Fully visible mobile Heatmap cells | 9 | 12 compact / 9 detailed |
| Desktop tile height | 104px | 78px compact / 104px detailed |
| Mobile tile height | 108px | 80px compact / 108px detailed |

The two old empty desktop panels used approximately 111,886 square CSS pixels
(490.7px x 228px). The new empty News row is approximately 53,577 square CSS pixels
(1388px x 38.6px), about 52% less panel area. The unused fixed right column is gone.
Mobile's first stock row is 22.7px later in EN and 38.1px later in VI than the EN
baseline due to explicit sample/freshness context. No horizontal overflow was seen;
the eight individual mover rows, optional News and disclosures still require normal
vertical scrolling. These are observed layout measurements, not speed claims.

Controlled states: mixed positive/negative/zero; confirmed missing; stale; slow
six-second loading followed by resolution; 26-second simulated response causing the
existing 20-second frontend timeout; HTTP error with unknown coverage; empty universe.
All stale/missing tiles stayed neutral. Fixture movement groups were 14/9/5/2;
three density changes left quote GET count unchanged at 96. Numeric Board ascending
sort began with BID at -1.5%; VN100 explicitly read Visible sample:29/30 quotes.

The fast batch screenshot experiment returned some stale frames. Those files are
not acceptance evidence. The gallery uses individually stabilized `verified-*`
captures and the original viewport-correct before captures only. DOM matrix and
geometry records are separate. All final paired images were inspected directly.

Artifacts live at:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/market-refinement/`.
Gallery: `http://127.0.0.1:3450/refinement-v21/index.html`.
Actual development UI: `http://127.0.0.1:3400/#market-overview`.

## Validation and runtime boundary

Focused public presentation seams: session alignment, missing/failed coverage,
numeric sorting, exact five-bin thresholds, neutral stale/unknown values and source
identity retention. Final frontend regression: 178 passed, one skipped, no failures.
Typecheck and supported webpack build pass. Browser engineering acceptance passes
within these fixture and persisted-News replay limits; USER_PRODUCT_PASS is not claimed.

Final read-only production evidence: Supervisor25552 valid in unchanged generation
`c01fa21027ca4ebabfe21efed0f0ab7a`, Backend19224/8000 and Frontend1316/3000 HTTP200,
Collector root13152/native28208, one ingestion-lock holder, no unknown DB holders,
SQLite integrity ok and zero foreign-key violations. Technical Pilot OFF; FPT PAUSED.
No production lifecycle action, database write, schedule/cooldown/credential change,
application deployment or GitHub push occurred. Runtime status can naturally advance
while this unrelated development task runs; this is a point-in-time observation.

Sector classification/aggregation, capitalization sizing, qualified session volume
and live-session SSI acceptance remain outside this refinement. No sleep/resume
reliability claim is made. Next action is user review of this local development UI;
integration and production release require separate authorization and release gates.
