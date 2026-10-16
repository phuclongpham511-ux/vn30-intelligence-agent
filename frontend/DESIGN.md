# VN30 Intelligence Agent — Frontend Design Contract

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
