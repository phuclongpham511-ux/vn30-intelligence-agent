# Market Workspace UI refinement V2

Date: 2026-10-19. Base: `090abb0fb64ab394f73fabe8553a663dfc35c432`.
Branch: `codex/woofi-market-board-correction`; clean base verified before edits.

## Implemented increment

1. **Navigation:** the existing primary nav gains a native expand/collapse button,
   icons and text labels. Collapse keeps the three route links, active underline,
   `aria-current`, accessible names and label tooltips. Mobile ≤900px always shows
   the three labels even if desktop was collapsed, with no extra sidebar/drawer.
   No storage keys or route semantics change; transitions honor reduced motion.
2. **Hot Topics thumbnails:** `TopStory` now independently controls thumbnail
   presentation and text-only ticker context. Hot Topics requests thumbnails but
   still mounts no additional quote consumer. `storyImages` is unchanged: valid
   representative image first, then existing same-Story candidates; an unrelated
   preferred URL cannot enter the list. `NewsThumbnail` retains error progression
   and adds an opt-in fixed placeholder after invalid/missing/exhausted images.
   Homepage frames are 72×54 desktop, 56×42 mobile (4:3); fallback uses a neutral
   ImageOff icon, never unrelated artwork. Headline/source/link/ranking and 3/2
   initial visibility remain unchanged.
3. **Board movement:** only the percentage cell receives a rectangular full-cell
   background. The same central resolver supplies qualified ceiling/advance/
   reference/decline/floor or neutral stale/missing/unknown/error. Text stays right
   aligned/tabular; source numbers, sorting, filtering, price columns and KL/GT
   remain intact. Overview movers also reuse this resolver/cell styling. No limit
   event is inferred from a percentage. Fill selectors out-rank the existing row
   hover background, so hovering cannot remove a qualified movement fill.
4. **VN-Index:** only Overview enables the prominent presentation: 32px desktop,
   28px mobile value, absolute change in points, percentage, visible source/event
   time in ICT, session and freshness. The original index hook, refresh schedule,
   calculation and source observations are unchanged. Board/Heatmap keep the
   original compact context presentation.
5. **Mascot:** uses the existing approved owner-provided transparent wolf/dog set,
   without editing/generating artwork. Six target states reuse bullish/bearish/
   neutral/scanning/curiosity/uncertain poses. Known fresh absolute index direction
   selects rising/falling/neutral; pending read selects loading; completed absence
   selects noMatches; failed initial read selects dataUnavailable. Stale or failed
   refresh with a retained observation selects marketUncertain, never fresh-direction
   artwork. Fixed 64px desktop/48px mobile space avoids a jumping primary value.
   Existing adjacent text conveys the state; illustrations remain decorative to
   assistive technology. This is not a sentiment model or investment signal.

## Files and reuse

- `AppShell.tsx`: enhance existing PrimaryNavigation; locale/theme/internal shell
  contracts retained.
- `HotTopics.tsx`, `TopStory.tsx`, `NewsThumbnail.tsx`: existing thumbnail pipeline,
  optional reserved fallback; no API, representative, source or financial changes.
- `MarketContext.tsx`, `MarketWorkspace.tsx`, `marketIndex.ts`: pure index display
  seam and UI-state mapping; one existing index hook, no new polling.
- `QuoteMap.tsx`, `MarketOverview.tsx`, `price-state.css`: full movement cells,
  existing price resolver and tokens; no changes to `lib/priceState.ts`.
- `market-workspace.css`, `translations.ts`: scoped responsive styling and two
  new EN/VI navigation action labels.
- Existing integration tests adapted for the now-approved thumbnail/label markup;
  new `market-workspace-refinement.test.mjs` adds 16 focused cases.
- `CONTEXT.md` and `frontend/DESIGN.md` record the approved refinement.

The Hot Topics endpoint remains `/api/news/hot?limit=4`, with its existing 72-hour,
minimum-two-independent-publisher contract and unchanged server ranking. Focus
retains its two existing feed reads, qualified Company/Market Brief selection and
24-hour window. Datasets are not merged. No scraping, source request, worker,
schema, provisional SSI activation, Watchlist review or acquisition change.

## Validation and limits

| Check | Result |
|---|---|
| New refinement tests | **16 PASS** |
| Focused combined integration/price/news regression | **60 PASS** |
| Full frontend `npm test` | **292 total: 291 PASS, 1 SKIP, 0 FAIL** |
| `npm run typecheck` | **PASS** |
| Optimized production `npm run build` | **PASS** |
| Backend tests | Not rerun: backend untouched |
| Actual desktop/mobile browser rendering | **PENDING** — Cloud Browser unavailable |

The one skip is the existing optional real persisted-API Stock Detail replay;
no external replay or browser session was activated. Full test results include
the new cases; the focused counts are not additional unique cases.

Tests cover navigation callbacks/routes and accessible labels; responsive rules
that retain mobile labels; thumbnail representative priority, unsafe URLs,
progressive load failure and reserved fallback; long headline/source retention;
index values and time/session in EN/VI; mascot mapping and approved file presence;
all nine Board states without source mutation; neutral stale/unknown guards and
Heatmap rendering; full-cell fill rules with theme tokens and ≥4.5:1 contrast for
all five colored states in both market themes (also neutral text contrast).
CSS/SSR/hook tests establish source behavior, not visual acceptance or measured
browser layout shifts. Existing price/SSI gates, Watchlist, research and News
regressions remain in the full suite.

Evidence logs:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/market-workspace-refinement-v2-20261019/`.

## Reference and remaining visual gate

Reused SStock research and saved board/Quick News images from October 16–17,
documented in `docs/DEEP_INTERACTIVE_PRODUCT_RESEARCH_V1.md` and the prior Hot
Topics design review. Useful principles are dense aligned numeric columns,
clear hierarchy and readable color areas. The implementation uses only Woofi's
tokens, approved assets and existing data contracts; no SStock code/assets,
proprietary taxonomy or new research/probes. No new SStock browser observation.

Cloud Browser is not exposed in this session. No local browser was opened and no
preview launch was retried after the previous host-policy refusal. The earlier
prepared 090abb0 preview does **not** contain this refinement; do not treat its
screenshots as evidence for this checkpoint. No new screenshot or visual PASS.

Optional operator-controlled acceptance, after a current isolated preview is
prepared/permitted: check 1440×900, 1024×768, 768×1024, 390×844 and 320px, VI/EN,
both themes. Toggle desktop nav, follow each destination, then resize while
collapsed. Check real same-Story thumbnail, missing/invalid/failed image fallback,
long headline wrapping, 3/2 limit/expansion; inspect index value/source/session and
all mascot states; confirm full-width/height percentage-cell fills, hover contrast,
sorting and source dialogs; verify Compact/Detailed Heatmap unchanged. Use saved
or clearly labelled synthetic evidence only; never substitute unrelated images.
The existing offline snapshot builder/API allowlist is the safe preparation path;
do not point a preview at production 8000 or its ingestion refresh endpoint.

No missing mascot assets: all 13 registered images are present. News thumbnail
coverage still depends on source metadata; missing images intentionally remain
neutral placeholders, without scraping replacements.

## Production boundary

Read-only configuration recheck still pins production to
`e80e36f24e38ac65a109245afbedd6204470ac30`. No changes to production files, P1
Supervisor, Collector, SQLite, ownership/ingestion locks, source pin, cooldowns,
Technical Pilot or FPT automation. No push, merge, deployment or server lifecycle
operation. Source implementation is complete; release remains gated by actual
visual acceptance and separate release authorization.
