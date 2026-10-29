# VN30 Intelligence Agent — Frontend Design Contract
## Stock Research overview — 29 October 2026

While Bronze clarification and Vnstock v5 migration are paused, the company
overview starts with a compact financial picture before price context and stored
company developments. Reuse the existing validated financial display projection,
metric qualification, period, unit and evidence disclosures. Overview and the
financial analysis tab retain one loader, cache and frequency selection; switching
presentation does not create a second financial consumer. Other research tabs
remain lazy. Unknown values stay unavailable, source-reported personal data stays
within its existing server-authorized scope, and DEMO remains visibly labelled.

Use the existing theme tokens, three financial groups on desktop and stacked
groups on mobile. Loading, transport failure, missing coverage and absent display
qualification remain distinct. This is frontend source work; release activation
and real-data acceptance are separate from offline preview checks.



## Owner correction — full-row market fills (19 October 2026)

Latest owner preference supersedes the muted pastel experiment: restore the original mint green/red/gold/purple/cyan row hues with dark semibold numeric text in both themes; compact 28px desktop rows, 36px mobile. Qualified advancing/declining rows use a continuous percentage shading scale, capped at 7 percentage points for presentation only (not an inferred exchange limit). The corrected ramp starts near-neutral, reaches the approved original hue at 3%, then deepens to the 7% visual cap. 1% and 2% must have at least a 30-channel RGB separation in the presentation regression; the earlier narrow ramp was too subtle. Missing/inconsistent percentages use the light base; stale/missing/unknown/error remain neutral. Explicit hover retains the row fill. Ceiling/floor/reference retain the original purple/cyan/gold hues. Heatmap, data qualification and trading semantics remain unchanged.

The owner's third reference screenshot supersedes the V2 movement-cell-only instruction: fill the entire stock row in the Board and Overview mover tables, with a compact gap and rounded outer corners. Reuse the centralized price-state resolver and contrast-safe theme palette. Stale/missing/unknown/error rows stay neutral. Heatmap, sorting, source dialogs and data contracts are unchanged. This source correction requires new visual acceptance; existing running preview builds do not update automatically.

## Market Workspace UI refinement V2 — 2026-10-19

Desktop primary navigation expands to icons + labels or collapses to labelled,
focusable icon links with an explicit navigation toggle. Mobile always exposes
all three destination labels, including after a desktop collapse. Keep the
compact header, active underline and reduced-motion support; no wide sidebar.

Homepage Hot Topics uses the existing same-Story thumbnail pipeline alongside
headlines, with fixed 4:3 frames and a neutral reserved fallback. Retain 3/2 initial
headlines, original source/links/ranking and no additional quote consumer.

Board and overview mover tables fill only the movement cell, using the centralized
qualified price state: ceiling purple, advance green, reference gold/yellow,
decline red, floor cyan; uncertain/stale/missing/error remain neutral. Right-align
tabular numbers; no whole-row tint or pills. Stock Detail keeps the same resolver.
Heatmap bins, equal-area geometry, density, controls and data remain unchanged.

Overview alone gives VN-Index a compact 32px desktop/28px mobile value, visible
absolute/percentage movement and source/time/session/freshness. Reuse the approved
mascot poses at 64px/48px: known fresh direction, loading, empty or unavailable;
stale/unverified observations must not receive a fresh-direction expression.
The artwork is an observation/UI cue, not a sentiment score or forecast.

This supersedes the preceding V1 presentation details where they differ. Source
validation is recorded in `docs/MARKET_WORKSPACE_UI_REFINEMENT_V2.md`; actual
Cloud Browser acceptance remains PENDING. No local-browser fallback or deployment.

## Approved Hot Topics and primary navigation integration — 2026-10-19

Public routes share visible Market / News / Watchlist links (VI: Thị trường /
Tin tức / Theo dõi), inline on desktop and a labelled second header row on mobile.
No primary destination depends on a hamburger or the old wide sidebar. Existing
News/Watchlist content, routes and browser-local review semantics are unchanged.

Overview places one compact publisher-context area immediately after its sample
summary, before mover details. Default Hot Topics reuses the original 72-hour,
two-independent-publisher contract and server order; Market Focus retains its
separate qualified 24-hour Company/Market Brief contract. Inactive options stop
their existing read-refresh subscription and retain their own results. No merged
feed or additional quote consumer. Initial Hot Topics visibility is three desktop
headlines/two mobile, with an explicit expansion; source text/time and original
publisher/ticker links remain separate. Board/Heatmap keep their full canvas.

This supersedes the older public-route sidebar guidance below. Internal SSI shell
and provisional data guards remain separate. Automated validation is recorded in
`docs/HOT_TOPICS_NAVIGATION_V1.md`; Cloud Browser acceptance is unavailable, so
source completion does not establish visual acceptance or authorize deployment.

## Approved Unified V2.1 market workspace

Targeted refinement: Overview uses compact sample/freshness context, paired
session-comparable mover tables and content-sized persisted-News context rather
than a sparse fixed right column. Workspace Heatmap defaults to small equal-area
ticker/percentage cells with keyboard/touch source detail, plus optional detailed
cells. Keep the ordinary Board architecture and Watchlist detailed default. Label
coverage as the visible/loaded sample, never as full index breadth. See
`docs/MARKET_WORKSPACE_V21_REFINEMENT.md`; user product acceptance remains pending.

The user-approved Unified V2.1 package supersedes earlier Explore composition and
market-route sidebar requirements: compact logo/search/locale/theme header,
Overview / Board / Heatmap navigation and existing Stock Research. News and
Watchlist retain their existing navigation/functionality. Market routes use the
approved restrained slate/teal theme tokens; financial movement colors retain
their independent meanings in both themes.

Default Board is an ordinary sortable three-panel comparison. Optional Advancing,
Declining, Unchanged and Stale / Missing organization uses the loaded filtered
sample only. Counts stay unknown on failed initial transport. Stock maps use five
source-percentage bins with boundaries -1, 0 and +1 percent, neutral stale/missing
states and equal-area cells; no sector taxonomy or capitalization is implied.
Source-time buttons open keyboard/touch accessible original evidence. Preserve
all existing research tabs, qualified charts, financials and original News links;
missing history has an explicit compact state rather than an invented path.

Prototype values/arrays/articles are never product data. Future capabilities remain
inactive behind a compact qualification disclosure. The visual baseline is the
local `unified-v2-1` package; controlled application screenshots are separate from
live-data qualification and from the user's final release authorization.

This file is the visual and interaction contract for the production frontend.

It is inspired by strong patterns from professional financial research products and OpenDesign references, but it is **not** a clone of Stripe, Binance, Kraken, Bloomberg, or any other product.

## Product character

VN30 Intelligence Agent is:

- an equity research workspace;
- an attention-prioritization product;
- data-dense but calm;
- analytical rather than promotional;
- professional rather than theatrical.

It is **not**:

- a crypto trading terminal;
- a marketing landing page;
- a card-heavy SaaS dashboard;
- a BUY/SELL recommendation surface;
- a purple-gradient AI product.

## Core hierarchy

Every important screen should preserve this hierarchy:

```text
Insight
→ Metric
→ Source
```

The most important question is:

> What changed, and why should I pay attention?

Raw metrics and source evidence must remain inspectable without competing visually with the primary insight.

## Visual language

### Color

Base:
- near-black / slate surfaces in dark mode;
- clean neutral surfaces in light mode;
- restrained cool-blue accent for navigation, focus, selection, and research emphasis.

Semantic colors:
- green only for positive observed financial/market changes;
- red only for negative observed financial/market changes;
- yellow/gold for a measured unchanged financial value (zero), with a readable unchanged label or symbol;
- amber for warnings, incomplete evidence, or data-quality limitations;
- neutral gray/slate for unavailable or secondary data.

Movement and freshness are independent: zero does not establish a current session.
Missing percentages stay neutral and never become zero. Light-theme unchanged
uses dark gold for contrast. News ticker chips describe headline associations,
not causation or verified investment impact.

Avoid:
- broad purple palettes;
- neon crypto aesthetics;
- decorative gradients;
- using green/red as recommendation language.

### Typography

Prioritize:
- tabular numerals for prices, percentages, financial statements, and tables;
- clear hierarchy;
- compact labels;
- readable dense data.

Numbers must align cleanly in columns.

Avoid oversized marketing-style headings inside research workflows.

### Density

Use **dense data, generous chrome**:

- tables and charts may be information-dense;
- surrounding layout should use measured whitespace;
- reduce decorative card nesting;
- avoid one-card-per-metric when a compact metric strip or table communicates better.

### Surfaces

Prefer:
- subtle borders;
- low-noise elevation;
- clear section separation;
- restrained radius.

Avoid:
- excessive floating cards;
- glassmorphism;
- heavy shadows;
- glowing borders;
- decorative blur.

## Layout

### App shell

Desktop-first research shell:

```text
Sidebar
+ compact top/header controls
+ large primary research canvas
```

Sidebar navigation should remain stable and low-noise.

### Stock detail hierarchy

Preferred order:

```text
Stock identity / status
→ Materiality / attention area
→ Technical workspace + market context
→ Fundamental trends
→ News / evidence
→ Raw data
```

Do not move raw evidence ahead of the main research narrative unless the task explicitly requires it.

### Materiality area

When Materiality becomes production-ready, it should communicate:

- what changed;
- why it matters;
- confidence / evidence limitations;
- inspectable supporting metrics;
- source provenance.

Do not display raw S/N/C/Base numbers as the primary user-facing experience unless they materially help the user understand the decision.

Scores are diagnostics first, UI content second.

## Charts

### Price / technical chart

Use TradingView Lightweight Charts.

Requirements:
- candlestick is primary;
- MA20/MA50 overlays remain visually secondary to price;
- volume and RSI use synchronized panes;
- tooltips and legends must not obscure price action;
- green/red represent observed direction only;
- no prediction overlays or trade signals.

### Fundamental charts

Use Recharts.

Requirements:
- emphasize trend and comparability;
- distinguish absolute values from growth rates;
- missing periods remain missing;
- do not imply zero for absent values;
- bank-specific missing generic revenue/margin fields must remain clearly unavailable.

## Tables and metrics

- Use tabular numerals.
- Right-align numeric columns where practical.
- Use concise units.
- Do not repeat the same metric across multiple cards and tables without a clear reason.
- Make null/unavailable states explicit.
- Keep source/as-of information accessible.

News and Hot Topics show one existing deterministic representative per Story,
with an actual same-Story source thumbnail, headline, publisher and publication
time. Additional reporting belongs in the linked Evidence view. Primary illustrated
feeds retain the source-image requirement; raw Evidence remains accessible without
an image. At most three ticker chips appear initially, with existing batched quotes.

Home places the approved mascot immediately left of the VN-Index number. Investor
Attention shows bounded discussion activity and sample coverage, without sentiment
classification when evidence is insufficient. Watchlist puts observed unreviewed
activity first; quiet sections and source/storage diagnostics use disclosure.
Material stale, unavailable and provisional states remain visible.

## Interaction

- English and Vietnamese product UI; source evidence stays in its original language.
- Search and ticker onboarding remain dynamic.
- Loading, empty, retry, and error states are first-class product states.
- Keyboard focus must be visible.
- Responsive behavior must preserve data meaning, not simply stack every card vertically.
- On smaller screens, prioritize the main chart, key insight, and essential metrics.

## Materiality semantics

The frontend must never imply:

```text
high materiality = bullish
low materiality = bearish
```

Materiality means attention-worthiness.

Direction describes the observed event, not an investment recommendation.

## AI surfaces

When AI is later introduced:

- embed assistance in the current stock/portfolio/thesis context;
- do not create a generic detached "Analyze this stock" chatbot as the primary experience;
- AI explanations must cite or expose source evidence;
- deterministic numbers remain backend ground truth.

## Reference patterns

Useful OpenDesign ideas:
- Stripe: controlled density and generous surrounding chrome;
- Mission Control: information-dense monitoring layout;
- Binance: strong financial numeral treatment;
- trading-analysis-dashboard template: research-workspace composition.

Use these as pattern references only.

Do not copy brand colors, logos, proprietary identity, or an entire reference design system.

## Implementation constraints

Current frontend stack remains:

- Next.js;
- React;
- TypeScript;
- Tailwind CSS;
- shadcn/ui;
- Lucide;
- TradingView Lightweight Charts;
- Recharts.

Do not introduce another UI framework just to apply this design contract.

A design refinement should normally modify existing components/tokens before adding new dependencies.

## Design review checklist

Before accepting a frontend change, verify:

1. Does it make the important information easier to find?
2. Does it reduce rather than increase visual noise?
3. Is the UI still recognizably a research product, not a trading game?
4. Are missing data and evidence limitations honest?
5. Are charts and numbers easier to compare?
6. Is Materiality represented as attention-worthiness rather than recommendation?
7. Does the change support English and Vietnamese product chrome while preserving original source evidence?
8. Did we avoid unnecessary new dependencies?

## News Relevance and Stock Research UX V2 (current development contract)

These rules supersede earlier image-required archive presentation. Keep one
deterministic representative per Story and open its original publisher headline
directly, with ticker links as separate siblings. Images are optional; preserve
the neutral fallback. Primary cards show source and publication time, without
Evidence/report-count actions. Put inspectable evidence in a secondary Source
archive. Body-based issuer chips require a current URL-bound receipt, a supporting
excerpt and observation time; unsupported stored tags remain unverified text.

Home Market Focus has at most three recent qualified Company/Market Brief Stories.
Do not rank it by forum activity, sentiment or a fabricated importance score.
Watchlist centers ticker, observed price/direction and loaded unread activity.
Quiet stocks remain visible. Keep all loaded unread items visible; place review,
evidence, archive and coverage detail in secondary disclosures. Reviewing one
source never reviews another, and no navigation or expansion changes review state.
All new product chrome supports VI/EN and both themes. Financial movement colors
remain independent of freshness and never imply news causation.

Watchlist may lead with a compact Read first queue of at most three distinct
unreviewed News/Community identities from its loaded page, ordered by original
publication (or explicitly labelled first observation). This is a reading order,
not an importance score. Show followed-stock context, source/time and limitations;
keep full stock rows, quiet stocks and Technical assurance below. Only an explicit
review acknowledges the displayed ticker-item revisions; navigation never does.

### Market board correction (source checkpoint; browser gate pending)

Supersedes the failed tall-card Price map contract. Explore defaults to the
qualified VN30 membership and one bounded30-symbol page; All equities, search,
exchange/index filters and pagination remain explicit. Use compact financial rows
in contiguous desktop columns, right-aligned source price/change, neutral source
time controls, and a separate compact equal-area heatmap. Layout switches, sorting
and evidence disclosures share the existing page quote context and never acquire
again. Watchlist keeps its current followed-symbol lease and review hierarchy.

Source-backed scopes are index memberships, not fabricated issuer sectors.
Counts describe current observations in this loaded selection only, not exchange
breadth. No capitalization sizing, strength, flow, sentiment or aggregate return.
Missing prices never become zero. Pending requests must say loading; confirmed
missing/stale observations remain neutral. Original date/session/source/reference
must remain inspectable with keyboard and touch. Do not promote minute-bar volume
to session volume. Keep methodology in one disclosure instead of repeated cards.
Preserve VI/EN, both themes, research links, review semantics and unknown states.

Source tests/build are not visual acceptance. Production release requires actual
new-code desktop/mobile browser inspection, numerical comparison, no overlap,
useful default coverage and bounded30-symbol cold/read lifecycle qualification.
Preview execution was denied by automatic policy in this task; no alternative
preview launcher or canonical deployment can substitute for that missing gate.
