# Section 1.5 UI Refresh Report

Completed: 2026-09-23. Scope: presentation and trusted English display metadata. Section 2 is not implemented.

## 1. Design references
The inspected [shadcn fintech reference](https://github.com/abderrahimghazali/shadcn-fintech) informed the restrained sidebar, card hierarchy and financial typography. This is an original implementation in the existing project, not a cloned template.
Implementation references: [shadcn Tailwind v4](https://ui.shadcn.com/docs/tailwind-v4), [manual setup](https://ui.shadcn.com/docs/installation/manual), [theming](https://ui.shadcn.com/docs/theming), [Recharts ResponsiveContainer](https://recharts.github.io/api/ResponsiveContainer/) and [Tooltip](https://recharts.github.io/en-US/api/Tooltip/).

## 2. Dependencies
Added Tailwind CSS / PostCSS integration 4.3.3, PostCSS 8.5.28, Lucide React 1.47.0, next-themes 0.4.6, Recharts 3.10.1, class-variance-authority 0.7.1, clsx 2.1.1 and tailwind-merge 3.7.0. The official shadcn generator created Button, Card, Badge, Input, Skeleton and Sheet and added radix-ui and cn; these are imported by the generated components. Exact dependency resolutions are in package-lock.json. No AI or backend provider dependency was added.

## 3. Design system
Central tokens in app/globals.css define dark charcoal and light neutral surfaces, violet interaction/chart accents, borders and typography. Green/red indicate signed financial values. Tabular numerals align metrics; missing values use an em dash.
Desktop uses a 240px sidebar and 72px sticky header. Cards use 12px corners and a consistent 24px page rhythm. Content stacks at narrower widths; raw tables scroll inside their own container.
Dark is the default. next-themes persists the user selection. The mobile navigation uses a Radix Sheet with focus management and Escape dismissal. Focus rings, a skip link, labeled controls and reduced-motion handling are included.

## 4. Permanent language policy
All application-owned visible text is English, including navigation, search, status, errors, empty states, dates and sample news. Raw provider errors are never rendered. This policy continues beyond Section 1.5.

## 5. Company names
Stock.display_name_en is explicit, trusted display metadata. The UI does not infer language from ASCII, translate names at runtime, or render company_name as a fallback. Missing English metadata means the ticker alone; the search subtitle can say “Stock”.
Existing seed metadata has curated English names. Newly added symbols remain dynamic, with null display metadata until a verified English name is supplied. Raw provider names remain stored for backend integrity. There is no ticker-specific UI branch or fixed supported universe.
VCB was added through the global search during QA. Its provider name is Vietnamese and display_name_en is null; Explore, search and detail showed VCB without the raw name. A frontend regression test also covers arbitrary new metadata and romanized raw names.

## 6. Components
- Foundation: AppShell, theme provider, shadcn Button/Card/Badge/Input/Skeleton/Sheet, shared class utilities.
- Universe: StockUniverse context, TickerSearch combobox, Explore landing cards.
- Detail: StockHeader, PriceChart, MarketSnapshot, MetricRow, TechnicalMetrics, FundamentalsCard, RawDataTable, MaterialitySlot and NewsFeed.
- States: StockStates, Watchlist empty screen and not-found screen.
- Shared presentation utilities format numbers, percentages, dates, names and safe news links.

## 7. Screens
Explore now has global dynamic search and a responsive stock grid. Detail presents identity and source/as-of context, the reserved materiality region, a Recharts daily-close area chart, market and technical metrics, grouped fundamentals, inspectable OHLCV and fixture news. Watchlist accurately explains that monitoring is not yet available.
The chart shows the actual default 180-calendar-day history window; no nonfunctional period controls are displayed.

## 8. Screenshots
Captured from the running application, using real provider data for FPT and VCB:
| Evidence | Image |
| --- | --- |
| Explore, dark desktop | [01](ui/01-explore-dark-desktop.png) |
| Dynamically added VCB / English naming | [02](ui/02-explore-dynamic-ticker.png) |
| FPT detail, dark desktop | [03](ui/03-stock-dark-desktop.png) |
| FPT detail, light desktop | [04](ui/04-stock-light-desktop.png) |
| VCB detail, mobile | [05](ui/05-stock-mobile.png) |
| Actual request loading skeleton | [06](ui/06-loading-state.png) |
| Unregistered ticker / retry error | [07](ui/07-error-state.png) |
| Fundamentals and labeled sample news | [08](ui/08-fundamentals-news.png) |
| Watchlist empty state | [09](ui/09-watchlist-empty.png) |

## 9. Verification
Each implementation checkpoint passed production build, TypeScript and applicable tests before its commit. Final gate:
- Backend: 43 tests passed; provider SDK calls are mocked in this offline suite.
- Frontend: 4 presentation regression tests passed.
- npm run build: passed.
- npm run typecheck: passed.
- Real browser integration: FPT and newly onboarded VCB loaded through the unchanged Next proxy and FastAPI. VCB returned 123 daily bars, as-of September 23, 2026, and annual 2025 fundamentals.
- Search keyboard selection (ArrowDown/Enter), dynamic onboarding, chart date/VND tooltip, theme switching, mobile menu Escape/focus return, raw table expansion, missing ROE, fixture labels and error retry were manually verified.
- No document overflow at 1440, 1024, 768 or 390px viewports. At 390px, the expanded raw table stays within its scroll container.
- The unregistered NOTADDED route showed the English error state; retry remained safe. Backend tests cover sanitized upstream failure responses.
- Browser console error inspection returned no errors on the successful dashboard/empty-state flow.

## 10. Backend changes
Only display metadata was added: nullable display_name_en, an additive/idempotent database column migration and trusted English seed values, with two regression tests. Existing raw company names, dynamic validation, analytics formulas, provider adapters and API routes are preserved. The root main.py remains the only FastAPI app entrypoint.

## 11. Limitations
News remains clearly labeled synthetic fixtures. Watchlists, materiality scoring, AI and realtime prices are not implemented. Financial metrics absent upstream stay missing; no fabricated values or fallback prices are introduced. Newly onboarded tickers may show only their ticker until English metadata is curated.
Overview still fails as a whole when a required provider fails. Live upstream data can change or be rate-limited. Responsive/keyboard checks are manual, not a full assistive-technology audit. The existing Starlette/httpx test deprecation warning remains. PostgreSQL and Docker runtime validation limitations from Section 1 remain unchanged.

## 12. Section 2 location
MaterialitySlot occupies the full width directly after StockHeader and before the price/metrics grid. Its muted “Coming in Section 2” state does not contain mock scores, fake events or AI output.

## Checkpoints
| Checkpoint | Commit |
| --- | --- |
| A — foundation | 3b9afdd |
| B — Explore and English metadata | 2ad90cd |
| C — stock detail | 86fc014 |
| D — states and responsive polish | a9ba480 |
| E — QA, screenshots and report | docs: finalize UI refresh report (this commit) |
