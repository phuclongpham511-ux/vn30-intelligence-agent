# Deep interactive product research — 2026-10-16

Browser mode: Codex Desktop in-app browser, supported `cua_repl` UI APIs.
This is a bounded public-workflow study, not competitor data validation. Old six-product
notes are background only; the interactions below were performed in this run.
Research screenshots/DOM receipts: `C:/Users/PC/.codex/tmp/woofi-deep-research-20261016/`.
They are research evidence only, not product assets. No login, CAPTCHA, subscription
or access restriction was bypassed. No proprietary formula was reverse engineered.

## First-hand interaction log

All observations: October 16, 2026, approximately 17:53–18:05 ICT, desktop 1440x1000
override unless noted. Visible competitor values are examples of their display,
not independently qualified market facts. Confidence: high for performed UI actions,
low/unverified for undisclosed formulas, source rights or internal processing.

| ID / platform / exact URL | Interactions and screen change | Metrics / period / source and method | Evidence / useful pattern / limits |
| --- | --- | --- | --- |
| S1 SStock [board](https://sstock.vn/bang-dien?tab=dien-bien-thi-truong) | Switched from sector board to Market movement; selected liquidity 5D then 20D; pointed/clicked a chart location. Selected period control changed; chart workspace retained context. | Market money flow 464 billion VND, foreign net -534 billion, intraday extrema, liquidity comparison, index contribution. Date Oct16; some panels 14:45 or 16:24. One/two/three aggregate universes must not be assumed equivalent. | `sstock-market-desktop.png`, `sstock-liquidity-20d.png`, `sstock-market-ax.txt`. Juxtapose aggregate and drilldown; plain units/date. No tooltip was qualified on this initial liquidity plot. Flow formula not displayed there. |
| S2 SStock [money flow](https://sstock.vn/dong-tien) | Opened dedicated flow page; switched Strong flow → Filter; applied displayed defaults. | 35 stocks in a sector-count visualization; table has entry date, days in top, short/medium strength, entry/current price and change. Filter date Oct16, strength 80–100 / 70–100 and average20-day volume 400K–200M. Filter began loading; completed result was not qualified before leaving. | `sstock-moneyflow.png`, `sstock-moneyflow-dom.txt`, `sstock-strength-filter.png`. Useful explicit screen criteria / time in cohort; **not** proof of institutional cash flow. Proprietary cohort/strength is NOT REPRODUCIBLE from inspected disclosure. |
| S3 SStock [sector analysis](https://sstock.vn/phan-tich-nganh) | Overview → Stock position; sector selector Bank → Retail; Ranking; clicked PNJ into its research page. | Bank credit/deposit growth and parent-profit comparison, Q3/2026; retail ranking has capitalization, EPS, PE/PB/ROE/ROA. Quarter selector disabled on ranking; did not claim a quarter change. | `sstock-sector-ranking.png`, `sstock-sector-ranking-dom.txt`. Sector → stock research in two selections after entering sector workspace. Good contextual peer navigation; missing newer financial cells displayed as dashes. Classification and denominator calculations not independently audited. |
| S4 SStock [board heatmap](https://sstock.vn/bang-dien?tab=ban-do-nhiet) | Selected Heatmap; clicked Bank tile. | Equal-looking industry tiles, signed percentages, positive green/negative red. Bank +0.74%, Steel -0.79% shown. No sizing/weighting formula or source time on tile qualified. | `sstock-heatmap-drilldown.png`. Click did not navigate or produce a qualified drilldown; do not claim it did. Scannable cross-section, but methodology must accompany any Woofi version. |
| S5 SStock [market strength](https://sstock.vn/thi-truong) | Opened sector-strength history; switched medium → short horizon; hid numeric values. Then Market statistics → sentiment; opened label selector. | Date columns Aug17–Oct16; sector stock counts, color-encoded 0–100-like scores; short/medium gauges 29/24 labelled pessimistic, updated16:24. Label menu offers alternative fear/greed terminology. | `sstock-sector-strength-short.png`, `sstock-sector-strength-colors.png`, `sstock-sector-strength-short-dom.txt`, `sstock-sentiment.png`. Matrix time history and contextual legends useful. Label switching is terminology, not an independent survey. No exact score algorithm disclosed. |
| S6 SStock [investor flows](https://sstock.vn/thi-truong?tab=thong-ke-thi-truong&sub=dong-tien-nha-dau-tu) | Selected Investor flows; HOSE time control 1D →1M; pointer click on Oct16 chart point exposed tooltip. | Billions VND and VN-Index points; foreign/proprietary panels separated. Tooltip displayed Oct16, index1705.91 and cohort values; zero-filled cohorts were not validated as genuine zero. | `sstock-foreign-1m.png`, `sstock-foreign-1m-dom.txt`, `sstock-flow-chart-point.png`. A chart point detail was actually exposed by pointer interaction; pure hover API was unavailable, so hover-only behavior remains NOT_VERIFIED. Loading panels were not treated as completed data. |
| S7 SStock [PNJ](https://sstock.vn/phan-tich-nhanh-co-phieu/PNJ) | Sector ranking →PNJ; stock quote tab →Flow; Fundamentals →Financial statements; Technical →Stockmap. | Quote18800 VND/+3.30%, volume6075400; flow distinguishes active buy/sell, ATO/ATC, foreign and proprietary values; dividend dates/ratios link PDFs. Statements show billions, Q3/22–Q3/26, missing latest cells, WiData attribution. Technical/Stockmap iframes existed; embedded tool behavior not qualified. | `sstock-pnj-overview.png`, `sstock-pnj-overview-dom.txt`, `sstock-pnj-flow-dom.txt`, `sstock-pnj-financials.png`, `sstock-stockmap.png`. Financial header and selected historic OHLC differed in initial view; did not assume synchronized dates or audited accuracy. Document links inspected, PDFs not opened. |
| S8 SStock [FPT](https://sstock.vn/phan-tich-nhanh-co-phieu/FPT) | Global search FPT →stock; Profile tab. | Different identity/sector, quote58200/+0.34%; stock/sector strength history; price-volume, financial navigation, corporate-action archive, profile/ownership dates. | `sstock-fpt-overview.png`, `sstock-fpt-profile.png`. Header stays while research mode changes; do not copy ownership datasets. Profile is source evidence, not current ownership certification. |
| S9 SStock [Quick News](https://sstock.vn/bang-dien?tab=ban-do-nhiet) | Opened side Quick News; VN30 →All changed article set (BSR-led list →general/issuer releases); inspected chip session hints and original source names; tested390x844. | Publisher/time, descending recent list, stock chips/session date, load more/full archive. No arbitrary stock search control inside drawer was qualified; no read receipts tested. | `sstock-quicknews.png`, `sstock-quicknews-all-dom.txt`, `sstock-quicknews-mobile.png`. Fast context-preserving news access; unlike Woofi direct publisher cards, links first enter SStock article route. Did not open that article reader. Mobile drawer directly observed; broad horizontal board remains dense. |
| F1 FireAnt [market](https://fireant.vn/thi-truong) | Homepage→market; sorted Foreign net buy; selected HSX; clicked Watchlist. | FPT became first in observed foreign-sort sample; quote/percentage/capitalization/trading value/volume and foreign net (millions) columns. Closed-session labels. Watchlist route requires login. | `fireant-foreign-sort.png`, `fireant-market-dom.txt`, `fireant-watchlist.png`. Explicit unit-labelled sort and exchange scope reduce scanning. Personalized Watchlist/alerts NOT_VERIFIED. Public community still discussion, not sentiment. |
| V1 VietstockFinance [home](https://finance.vietstock.vn/) | Heatmap search FPT; size menu Trading value →Market cap; used Sector map jump. | Units disclosed: volume million shares, trading value/cap billion VND; overall market time17:26, separate chart times. Sizing menu includes foreign/proprietary, price, financial metrics. | `vietstock-heatmap-search.png`, `vietstock-heatmap-marketcap.png`, `vietstock-sector.png`. Separate area metric from color metric and explain scope. Selection/navigation performed; no authenticated saved list or methodology/complete sector drilldown claim. |
| T1 TradingView [chart](https://www.tradingview.com/chart/) | Homepage Products entry opened actual AAPL chart; range1M changed interval1D→30m; Products→News Flow opened adjacent AAPL-context panel; Add filter opened menu. | Price/volume, separate premarket timestamp, regular-session data, 5-second channel cadence; default list includes delayed labels. News Flow same-as-chart plus Watchlist/Instrument/Market/Corporate activity/Country/Provider filters. | `tradingview-chart-1m.png`, `tradingview-contextual-news.png`, `tradingview-news-filters.png`. Strong context-preserving chart/news workspace. No alert created, list persisted or premium behavior tested. Heatmap not directly tested in this run. |
| K1 Koyfin [home](https://www.koyfin.com/) →[login](https://app.koyfin.com/login) | Followed Log In, rendered email/password/SSO screen. | Actual application behind auth. Marketing dashboards are NOT interactive evidence. | `koyfin-access-boundary.png`. ACCESS=AUTH_REQUIRED; financial dashboards/sector maps/alerts NOT_VERIFIED. No login attempted. |
| A1 Seeking Alpha [home](https://seekingalpha.com/) | Public shell rendered; attempted Sector menu/Technology navigation. | Price/time-range/table shell visible, then PRESS & HOLD challenge prevented controls. | `seekingalpha-browser-blocked.png`. ACCESS=BROWSER_BLOCKED; sector/briefing workflow NOT_VERIFIED. No challenge solved or bypass attempted. Older public-profile research remains historical only. |

## Methodology disclosures actually inspected

At [SStock help](https://sstock.vn/huong-dan-su-dung), clicked Sentiment,
Sector strength map and SStock flow documents. Receipts: `sstock-sentiment-methodology.txt`,
`sstock-strength-methodology.txt`, `sstock-moneyflow-methodology.txt`.
The sentiment description attributes its input to orders across three exchanges;
it is a proprietary market-behavior composite, **not** a sampled opinion survey.
Help describes a custom40-sector taxonomy and daily comparative colors, but does
not supply reproducible score inputs/weights/window rules. Strong-flow help describes
membership in a relative-strength cohort and time since entry, not observed institutional
net purchases. Mark scores **PROPRIETARY / NOT REPRODUCIBLE**. Do not adopt its allocation advice.

## Woofi audit: actual application + code

Audited canonical844df8e using the same in-app browser, normal UI navigation only;
no forced provider refresh, reviews or follows. Home →FPT search→Stock Detail→
Fundamentals/Technical/Dividends; News→Community; Watchlist. Read root AGENTS,
CONTEXT, DESIGN, product brief, Daily Use/Watchlist/Stock Detail contracts and
live/universe/provider/read code. Evidence `woofi-*-before.png` in research directory.

| Area | Classification | Verified state / gap |
| --- | --- | --- |
| Home / Explore / Search | ALREADY IMPLEMENTED | Sourced VN-Index, market context, Hot Topics, Market Focus, ten-row cached universe, exact/prefix issuer search, exchange/index filters, pagination. No cross-sectional price visualization; list scan is the remaining interaction gap. |
| Stock Detail | ALREADY IMPLEMENTED | Five tabs, identity/quote/session, completed daily price/volume ranges and direct research links. More data is not the main gap. |
| Fundamentals | ALREADY IMPLEMENTED | Actual FPT2025 annual VCI results, four sections, annual/quarterly/TTM and units/history controls, revenue/profit/YoY charts and source/formula disclosure. Do not rebuild it. |
| Technical | ALREADY IMPLEMENTED; qualification constrained | Daily chart, MA/BB/RSI, underlying data, accepted evidence with assurance. PilotOFF remains intentional; no changes to D1/D4/D5. |
| News / Community | ALREADY IMPLEMENTED | Source-aware archive/category controls, independent publishers for Hot Topics, publisher direct links, Community Today/24h and ticker filter; discussion labelled unverified. No proxy sentiment needed. |
| Watchlist / Daily Intelligence | ALREADY IMPLEMENTED | Read first shipped; browser-local membership/revision receipts, per-stock detail. Current127-origin Watchlist empty during audit, so actual filled Read first acceptance is the prior release evidence, not a fresh observation here. |
| Dividend / corporate actions | IMPLEMENTED; INCOMPLETE DATA | Source-only VSDC reader and timeline; real FPT view honestly has no stored events. Thirty product records/25 documents exist, not market-wide coverage. Missing data cannot be filled from competitor assets. |
| Sector market view | BLOCKED BY DATA | Security metadata has no complete qualified industry taxonomy; Stock sector fields are sparse; no aligned full-universe sector snapshots/weights. Existing News sector tags are headline labels, not an issuer master. |
| Foreign/proprietary flows and breadth | BLOCKED BY DATA / SOURCE CONTRACT | Some official channels describe raw fields, but current Woofi LiveBatch/index API does not expose qualified flows/counts. No full-market fetch or adapter expansion justified for this slice. |

## Data requirements and legitimate source feasibility

| Capability | Raw inputs / calculation | Existing usable data | Missing / legitimate source candidate / permission / reliability | Decision |
| --- | --- | --- | --- | --- |
| Loaded/followed quote map | Each ticker's last price, source-computed change/% vs reference, source timestamp/session; equal-area tiles, no aggregate calculation | Current LivePrices context, SSI universe and existing bounded leases | No new inputs, call budgets, provider or redistribution; same authorized local presentation | **CAN BUILD NOW** |
| Full sector performance / treemap | Qualified industry membership, current aligned snapshots, defined equal/cap weights; cap requires shares/freefloat and corporate actions | Sparse Stock sector fields; ordinary-equity identity; demand quotes | Official exchange/issuer classification or licensed sector master; point-in-time mappings and redistribution rights must be qualified. VCI reference API candidate, not assumed permitted by package install | NEEDS NEW SOURCE / RESEARCH |
| Market breadth | Exchange-qualified advances/unchanged/declines, eligible-universe/no-trade definitions, same session/time | Existing index value only; no count fields in current public contract | SSI documented MI counts are a candidate, not proven current SDK entitlement/mapping. No sum across unsynchronized loaded stocks advertised as market breadth | NEEDS SOURCE CONTRACT |
| Foreign net flow | Actual buy/sell value by foreign category, net=buy-sell, same period/exchange; separate quantity from value | Not exposed by current live API | SSI documented foreign-room value/volume candidate; current SDK/permission/units/history must be verified. Exchange official disclosures or licensed feed alternative | NEEDS NEW ADAPTER QUALIFICATION |
| Proprietary/institutional flow | Explicit investor category buy/sell value and provenance, no volume substitution | None qualified | Official exchange or licensed provider; timely access and redistribution unknown | BLOCKED BY DATA / RIGHTS |
| Relative price performance | Matched completed sessions, qualified adjusted prices, benchmark, returns and alignment in Python | Existing daily prices / Python per-stock returns | Corporate-action adjustment and synchronized benchmark histories not established for this comparison | NEEDS RESEARCH; never call proprietary strength |
| SStock strength/sentiment | Exact public formula, universe, calibration/windows and permitted raw inputs | Not available | Public explanatory help is not reproducible methodology or licensing | **NOT FEASIBLE AS EQUIVALENT** |
| Trading activity / turnover | Precisely qualified cumulative traded value or volume for same session, share denominator for turnover | Live fields may be absent; one-minute OHLCV volume can describe a bar, not the day | Need cumulative/window semantics and unit fixtures; cannot treat volume as institutional buying | NEEDS DATA SEMANTICS |
| Corporate action timeline | Original VSDC/issuer notices, separate ex/record/payment dates, ratios and corrections | Existing30 source records/25 docs and source-only reader | New notices require source-permission/coverage plan, document provenance and correction handling | ALREADY PARTIAL; coverage project deferred |
| Macro dashboard | Release/vintage-aware official series, units/revisions and dates | None required for selected scope | Statistics Office, SBV, official exchange/issuer IR sources; re-use rights and acquisition contract not yet researched deeply | NEEDS RESEARCH |

Primary source checks (documentation only, not acquisition):
[SSI streaming fields](https://guide.ssi.com.vn/ssi-products/fastconnect-data/streaming-data)
documents foreign buy/sell values and index breadth, distinct from total volume.
[SSI current data FAQ](https://developers.ssi.com.vn/docs/faq/market-data) distinguishes
event-push from REST cadence; does not certify Woofi's existing SDK mapping or new rights.
[Vnstock references](https://www.vnstocks.com/docs/vnstock/tham-chieu-reference) lists
classification/reference capabilities; installed Woofi pins4.0.2, so current5.x docs
are source candidates, not drop-in compatibility evidence.
[Vnstock license](https://www.vnstocks.com/onboard/giay-phep-su-dung) explicitly does not
transfer third-party data rights. [VSDC](https://www.vsd.vn/) is an official notice
candidate; public availability alone is not redistribution authorization.
No provider credentials read/disclosed, new account/subscription purchased or endpoint acquired.

## Prioritized roadmap and selected bounded slice

| Priority | Opportunity | User value / data / cost-risk | Outcome |
| --- | --- | --- | --- |
| 1 | Quote map in existing Explore and optional Watchlist overview | Faster cross-stock visual scan; all required fields already loaded; small UI-only scope, no new financial computation/provider/storage | SELECTED as **one** vertical slice, not two dashboards |
| 2 | Sector drilldown/performance | Strong SStock first-hand value, but classification/alignment/weight/rights gaps | Defer until issuer-master/source qualification |
| 3 | Exchange breadth | Useful context without emotion framing; current API lacks verified counts | Defer candidate adapter qualification; no full-market scan |
| 4 | Foreign-flow value chart | Useful distinct behavior, available only in unqualified candidate channels | Defer permission/semantics validation |
| 5 | Corporate notice coverage | Honest existing UI; adds useful evidence but source coverage work outside a small visualization release | Separate evidence milestone |
| 6 | More Quick News / sentiment / strength | News context already implemented; proprietary inputs unknown | Do not duplicate Read first or invent scores |

### Selected contract before implementation

One reusable equal-tile Price map over **the already loaded Explore page** and an
optional closed Watchlist disclosure over **its existing followed symbols**. Explore
list remains default; switching only changes presentation, retaining search/filter/page,
the same single LivePrices provider and quote cadence. Watchlist full rows and Read first
remain; map never changes unread ordering or receipts. No new request, lease, worker,
database, API or financial formula. No market-wide/sector/portfolio weighting claim.

Every tile: identity/stock link, existing price and movement, explicit current/stale/
unavailable status, timestamp and source/session disclosure. Equal tile area has no
financial magnitude meaning. Fresh movement color is green/red/yellow; missing/stale
background neutral; text/symbols retain independent movement semantics. No hidden
zero imputation, sentiment, strength or causal explanation. Keyboard/touch can access
details; tooltip cannot be the only evidence. Existing source values stay backend truth.

Acceptance: same symbols/prices/status as list; toggles preserve page/filter/search and
do not fetch; direct navigation; unavailable and stale never look current; zero distinct
from missing; EN/VI and both themes; responsive2/3/5-column grid without overflow;
News/Community reviews/Technical unchanged. Meaningful pure/SSR fixture tests plus
one full frontend run/typecheck/build and bounded actual-browser acceptance. One
controlled release only after fresh exact-source, ownership, online-backup and build
gates pass. Stable844df8e remains protected throughout development.

### Source checkpoint validation

Eight new pure/SSR cases cover exact source values/identity, positive/negative/zero/
missing movement, stale/failed/future/previous-day observations, closed-session
labels, neutral missing tiles, source disclosure and EN/VI. Initial red coverage
found a missing VI message; it was added. SSR attribute casing and a test regex
matching the word financial were corrected without weakening the product checks.
Final frontend regression:164 PASS,0 FAIL,1 existing optional Stock Detail replay
SKIP. Typecheck PASS; production webpack build PASS. Tests are synthetic; no claim
of actual new-feature browser acceptance before the controlled release.

Bounded review: default list and its links remain unchanged; map mode is local
presentation state independent of query/group/page. LivePrices remains mounted
once per existing page; its URL, symbols/cadence/lifecycle are unchanged. Map's
context reader has no fetching, acquisition, storage or review action. Unknown
prices/ticker mismatch fail closed; stale values retain age and source with a
neutral tile. No backend/scripts/provider/schema diff. Unrelated frontend/AGENTS.md
and frontend/CLAUDE.md remain preserved untracked instruction artifacts. Runtime
844df8e was independently healthy at17:57 ICT with one qualified Collector,
SQLite integrity/FK PASS, Technical PilotOFF and FPTPAUSED. Production release and
actual-browser evidence will be recorded separately in the runtime release report.


## Product correction after direct user rejection — October16, late evening

The previous selected slice and its passing tests did not establish a useful
market-comparison experience. The user rejected tall cards over10 alphabetically
paged metadata rows. That judgment supersedes the prior design-selection result;
it does not invalidate its recorded automated or operational evidence.

SStock was opened again interactively at1440x900: Nhóm ngành, Bản đồ nhiệt,
group selector All→Group1;390x844 mobile captured. Woofi actual1d7706a was compared
at the same desktop size. Current-source VN30 ordinary browsing yielded30/30
qualified closing observations. Correction source and limitations are recorded in
`MARKET_BOARD_CORRECTION_V1.md`. New interface browser acceptance is NOT_VERIFIED:
preview execution was denied by automatic approval policy and was not retried.
No new source was integrated or deployed in this correction task.
