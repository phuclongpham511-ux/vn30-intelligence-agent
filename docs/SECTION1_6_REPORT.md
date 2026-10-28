# Section 1.6 — Financial Visualization Report

Date: 2026-09-24. Checkpoints A–D were retained; final visual QA completed in E.

## 1. Goal and scope
Delivered real OHLCV candlesticks with deterministic technical series, annual financial trends, and a neutral blue research identity. The existing browser → Next.js proxy → FastAPI → services → providers architecture is unchanged. There is one root main.py / FastAPI application. No Materiality Engine, AI, execution or trading recommendations were added.

## 2. References used
- [Lightweight Charts](https://github.com/tradingview/lightweight-charts), [v5 documentation](https://tradingview.github.io/lightweight-charts/docs), [panes](https://tradingview.github.io/lightweight-charts/docs/panes), [React lifecycle](https://tradingview.github.io/lightweight-charts/tutorials/react/advanced).
- [shadcn-fintech](https://github.com/abderrahimghazali/shadcn-fintech): financial card hierarchy and restrained dashboard composition.
- [OpenStock](https://github.com/Open-Dev-Society/OpenStock): information architecture only, no code copied.
- [React wrapper reference](https://github.com/trash-and-fire/lightweight-charts-react-wrapper): lifecycle reference only; wrapper not installed.

## 3. License and attribution
Lightweight Charts 5.2.1 is used directly under Apache-2.0. Built-in TradingView attribution remains enabled. The chart footer includes the TradingView link and the package's [NOTICE](https://raw.githubusercontent.com/tradingview/lightweight-charts/v5.2.1/NOTICE) attribution text.
The MIT dashboard/wrapper references were not copied wholesale. No AGPL OpenStock code/components were copied. Existing repository dependency licenses remain applicable.

## 4. Dependencies
Added exactly lightweight-charts 5.2.1 (and its resolved transitive dependency in package-lock.json). Recharts remains for financial charts. No wrapper, frontend indicator library or additional chart platform was installed.

## 5. Technical-history API
GET /stocks/{symbol}/technical-history?start=YYYY-MM-DD&end=YYYY-MM-DD
- Default end: backend date.today(); default start: end minus 180 calendar days.
- Ordered inclusive visible dates, maximum end-start difference 730 days; no future end.
- Unknown stock 404; invalid/reversed/overlong/future range 422; provider failure sanitized 502.
- Returns TechnicalBar[] oldest to newest: ticker, date, OHLC in VND, volume in shares, ma20/ma50 in VND, rsi14 in [0,100], source and currency.
- Empty provider results remain an empty list. Insufficient warm-up is null.
- The existing /history route and its response contract remain intact.

## 6. Fundamental-history API
GET /stocks/{symbol}/fundamentals/history?limit=4
- Limit defaults to 4, accepted range 1–20; upstream availability determines actual row count.
- Returns annual FundamentalPeriod[] oldest to newest, with period, reported amounts, margins/ROE, YoY growth, margin/ROE changes, ticker, source and currency.
- Only real annual observations; no quarterly interpolation or fake backfill.
- Amounts are VND; growth/margins/ROE are unit fractions; changes are fraction differences.
- Exact prior-year comparisons are computed before applying limit.
- Unknown stock 404, invalid limit 422, provider failure sanitized 502.
- Existing /fundamentals latest snapshot remains compatible.

## 7. Shared formulas and warm-up
rolling_indicators is the sole implementation used by both market_snapshot and technical_history.
SMA20/SMA50 are simple trailing means. RSI14 uses the existing Wilder seed from 14 changes, then (previous average × 13 + current gain/loss) / 14. Flat prices yield 50; no losses yields 100.
This release deliberately initializes within the requested range, rather than silently changing snapshot history with a prefetch. First 19 MA20, 49 MA50 and 14 RSI values remain null when a full untrimmed window begins. The UI explains this.
The default 6M endpoint matches the existing snapshot input window. Tests verify every historical prefix against its same-input snapshot. Different requested windows may initialize Wilder RSI differently; latest RSI across 3M/1Y/2Y need not be numerically identical to the fixed 6M snapshot.
Fundamental snapshot/history share the same comparison helper. Missing exact prior years and zero/negative growth bases produce null, preserving previous definitions.

## 8. Technical chart architecture
One client-side Lightweight Charts instance:
- Price pane: actual candlesticks, backend MA20 and MA50.
- Volume pane: actual shares, direction-colored histogram, independent volume scale.
- RSI pane: backend RSI14, fixed 0–100 scale and 30/70 reference lines.
- Approximate pane proportions 65/15/20; pane resizing disabled for stability.
- Native pan/zoom/crosshair plus Reset view. Crosshair legend shows selected-date OHLCV and indicators; absent crosshair uses latest data.
- Keyboard-operable range buttons and native indicator checkboxes. Hidden volume/RSI series remove their panes; re-enabling restores them without replacing the chart.
- 3M/6M/1Y/2Y fetch 90/180/365/730-day API windows. Dates in the client use Asia/Ho_Chi_Minh.
- Technical requests load independently after overview. Local skeleton, retry and empty states do not replace already loaded header, fundamentals or news.
- Raw technical table follows news, includes the selected range and indicators/source. Unavailable values are dashes.

## 9. Financial dashboard
Independent annual-history request, with local skeleton/error/retry/empty states.
Recharts revenue and net-profit bars use actual years, compact VND axes and exact VND tooltips. Growth bars show signed values, and profitability lines only include metrics with observations. Missing values are not zeros; lines do not connect across nulls.
A compact latest-year summary supports scanning. “View reported data” exposes exact VND amounts, growth, margins, ROE and source. Only real reporting periods appear.

## 10. Visual system
Replaced violet primary tokens with restrained blue and slate surfaces in both themes. Green/red remain financial semantics, MA20 amber, MA50 blue and RSI muted slate. Preserved navigation structure and dark default.
Chart colors follow theme changes, including a DOM-class observer to handle next-themes effect ordering. Market context is a compact six-metric panel. Removed the unused prior area chart and redundant technical/fundamental card components.

## 11. Files changed
- src/schemas/data.py: TechnicalBar, FundamentalPeriod.
- src/analytics/market.py, fundamentals.py: shared rolling/history calculations.
- src/services/data.py, routers/stocks.py: additive history APIs.
- tests/test_history.py: deterministic/API regression coverage.
- frontend/lib/types.ts, chart-data.ts, fundamental-data.ts: contracts and pure adapters.
- frontend/app/components/stock/: TechnicalChart, TechnicalToolbar, TechnicalLegend, FundamentalTrends, MarketSnapshot, RawDataTable; obsolete components removed.
- frontend/app/components/Explore.tsx: new section composition.
- frontend/app/globals.css, components/app-shell/AppShell.tsx: visual tokens and research label.
- frontend/tests/: chart, indicator and fundamental adapter tests.
- frontend/package.json, package-lock.json: pinned official chart library.
- scripts/smoke_visualization.py: opt-in real API/provider smoke.
- README.md, this report, docs/ui/10–16: delivery evidence.
Provider code was not changed.

## 12. Tests and build
Final gate: 57 backend tests passed, 9 frontend tests passed, npm run build passed, npm run typecheck passed, git diff --check passed.
The backend suite is offline with mocked providers. Added coverage includes warm-up boundaries, known Wilder values, every-prefix snapshot equality, annual ordering, exact YoY gaps, invalid comparison bases, missing bank fields/ROE, range validation, unknown stocks and sanitized errors.
Frontend tests cover OHLCV adapters, null indicator omission, real zero preservation, chronological annual data without interpolation, range-day mapping including timezone/leap year, English labels and existing name/link policies.
The existing Starlette/httpx deprecation warning remains; no failed tests.

## 13. Live smoke and browser QA
Command (running local backend required):
```powershell
uv run python -m scripts.smoke_visualization FPT HPG TCB MWG
```
This opt-in command validates/onboards symbols through POST /stocks; it can persist a newly added symbol.

| Ticker | Daily sessions | As of | Annual periods | Result |
| --- | ---: | --- | --- | --- |
| FPT | 123 | 2026-09-24 | 2022–2025 | PASS |
| HPG | 123 | 2026-09-24 | 2022–2025 | PASS |
| TCB | 123 | 2026-09-24 | 2022–2025 | PASS |
| MWG (dynamic, non-seed) | 123 | 2026-09-24 | 2022–2025 | PASS |

Final technical values matched default snapshot MA20, MA50 and RSI14; latest annual values matched the existing fundamental snapshot. Normalized absent sector fields stayed null.
FPT range interaction returned 62 / 123 / 249 / 498 sessions for 3M / 6M / 1Y / 2Y during QA. Crosshair changed date and OHLCV/indicator values; indicator/pane toggles worked. Dark/light and mobile were visually inspected.
At viewports 1440 / 1024 / 768 / 390, document widths were 1425 / 1009 / 753 / 375 respectively, with one chart instance. Raw tables at 390px stayed inside their scroll regions (financial table 861px, technical table 755px). UI includes English labels, fixture news and trusted display-name fallback. MWG was subsequently opened through global search and displayed its ticker without a raw Vietnamese company name. The successful browser flow logged no console errors.

## 14. Screenshots
All are unedited browser captures of the application with real provider observations.
- [10 — Candlestick dark](ui/10-technical-candlestick-dark.png)
- [11 — Indicators and crosshair](ui/11-technical-indicators.png)
- [12 — Technical mobile](ui/12-technical-mobile.png)
- [13 — Financial trends dark](ui/13-fundamental-trends-dark.png)
- [14 — Financial trends light](ui/14-fundamental-trends-light.png)
- [15 — Missing financial data](ui/15-missing-fundamental-data.png)
- [16 — Full stock detail, top](ui/16-full-stock-detail.png)
- [16b — Full stock detail, middle](ui/16-full-stock-detail-middle.png)
- [16c — Full stock detail, bottom](ui/16-full-stock-detail-bottom.png)

The browser fullPage capture failed, and an expanded viewport capture was clipped by the tool. The full-detail evidence is therefore provided as three unedited viewport captures; it is not represented as a successfully stitched full-page image.

## 15. Missing-data examples
TCB has real net-profit history and signed profit growth, but generic revenue, gross/net margins and ROE remain null. Revenue/profitability panels explain unavailability instead of showing zero bars.
FPT/HPG/MWG ROE is unavailable and omitted from the trend legend. Earliest annual YoY lacks an upstream prior-year observation and stays null. Technical warm-up remains blank in plots and a dash in raw evidence.

## 16. Provider limitations
The pinned vnstock community adapter currently provides four annual periods. Generic bank statements are not remapped to interest income. ROE remains unavailable under the previously verified provider contract.
Prices use provider adjustment conventions. During the current trading day, daily OHLCV may be revised upstream; this is not a realtime stream. In-process caching and provider rate limits still apply.
The existing overview request is still all-or-nothing on initial required-provider failure. Additional technical/annual-history fetches do not increase that coupling. Local PostgreSQL/Docker runtime verification remains outside this section as previously recorded.

## 17. Performance and accessibility
Chart construction runs on mount and cleanup removes crosshair listeners and the chart (including its automatic ResizeObserver); the theme observer disconnects separately. Range data updates reuse the instance. No frontend indicator calculations, per-indicator network requests or animated candle recreation.
Responsive containers, labeled chart regions, semantic headings, native checkboxes, pressed range state, focus rings and raw tables supplement the canvas. All modes have inspectable evidence. Manual keyboard/responsive checks are not a complete assistive-technology or long-duration memory audit.

## 18. Section 2 readiness
MaterialitySlot remains immediately beneath StockHeader. No scores, events, ranks, AI text or recommendations were added. Technical and annual historical evidence now support the next section. The visual foundation is ready to be frozen; Section 2 requires its own implementation scope.

## Checkpoints
| Checkpoint | Commit |
| --- | --- |
| A — APIs and analytics | 939cd84 |
| B — candlestick foundation | ccd1c37 |
| C — integrated indicators | cc41e5e |
| D — financial dashboard | 5587a9e |
| E — visual foundation | 72b317c |
| E — report and QA evidence | This documentation commit |
