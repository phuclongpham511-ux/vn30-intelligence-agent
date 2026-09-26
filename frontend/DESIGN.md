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
- amber for warnings, incomplete evidence, or data-quality limitations;
- neutral gray/slate for unavailable or secondary data.

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

## Interaction

- English-only UI.
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
7. Does the change preserve English-only UI?
8. Did we avoid unnecessary new dependencies?
