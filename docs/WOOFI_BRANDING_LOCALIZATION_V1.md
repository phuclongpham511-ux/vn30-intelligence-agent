# Woofi branding, Vietnamese localization and UI cleanup V1

STATUS: PASS

GIT BASE: main at `73c8b7ccf2653d1409a8b7f61e510d80369492c2`. No push performed.

BRANDING: application title/navigation/footer identify Woofi; no old user-facing product name remains. Legitimate VN30 index names and repository/module paths remain.

LOGO: actual supplied `C:/Users/PC/Downloads/Woofi Cute Dog Mascot Logo.png`, copied byte-for-byte into `frontend/public/assets/woofi-logo.png` (1448 × 1086 RGBA; SHA-256 `821ddbb172bc9c76a70937300eaab62bb98011da9e32de4be8a5d6d93ce70f5f`). Browser confirmed local asset loaded at original dimensions. Desktop sidebar and mobile header use the wordmark once. CSS preserves the image ratio and excludes surrounding transparent canvas padding, without editing the asset. Checked light/dark. White-wolf state mascots remain unchanged.

ABOUT WOOFI: subtle sidebar/drawer footer entry, English/Vietnamese description in a Radix dialog. Keyboard focus, close button, Escape dismissal and return to the triggering entry checked, including dialog opened from mobile drawer.

LOCALIZATION: typed dictionary plus shared context, no added dependency or runtime translation service. Stored EN/VI preference takes precedence; otherwise Vietnamese browser locale selects VI and other locales select EN. Browser reload verified both preferences. HTML `lang` updates with the selection. Dates use Vietnam time and locale formatting; numeric display keeps the existing precision and missing/zero distinctions.

TRANSLATED SURFACES: navigation, theme/About/language controls, shared ticker search/history, Explore/universe/index research, News tabs/filters/source coverage, Watchlist/review chrome, Community windows/counts/evidence metadata, Stock Detail navigation/status/error/loading states, technical chart/legend/raw data and reported financial chart/table labels.

SOURCE CONTENT: article titles/excerpts, Community theme summaries/evidence, ticker/company/publisher names, provenance and original quotes remain original. Automated renderer checks include source strings that are also dictionary keys. Browser comparison confirmed all 14 Company-view headlines were identical across EN/VI. Existing source topic taxonomy remains inspectable in its original form.

HEADER: Daily data header element removed. Under 640px the search occupies its own row so the logo, language and theme controls remain usable on narrow screens.

NEWS: Industry → Company → Market → Community Pulse; Ngành → Doanh nghiệp → Thị trường → Cộng đồng. All four views omit duplicated category headings/introductions under their tabs. Internal `briefing` / `MARKET_BRIEF` and all feed queries/semantics remain unchanged.

RESPONSIVE: actual production build in browser; desktop 1265 × 714, mobile 390 × 844 and 320 × 844; English/Vietnamese and both themes. No horizontal page overflow at 390px/320px. Narrow 320px header search increased from roughly 41px to 281px. Checked Explore, News sections, Community, empty Watchlist, live Stock Detail and VN-Index. No browser console errors observed.

TESTS: `uv run pytest -q`: 531 passed, 1 existing Starlette/httpx deprecation warning (38.26s). `npm test`: 51 passed, 0 failed (43 existing plus 8 localization tests). `npm run typecheck`: PASS. `npm run build`: PASS (Next.js 16.3.6 production build). Relevant diff and whitespace review completed.

SSI / TECHNICAL: no backend/provider/normalization/engine/materiality/news classification/ingestion/community extraction/financial computation/watchlist review/retention changes. Chart formatting only; deterministic values and source content retained. The prior absolute `.env` path fix in `src/config/settings.py` is excluded from this checkpoint.

LIMITATIONS: language preference is browser-local, with English SSR until client preference restoration. Evidence and source taxonomy are intentionally not machine translated. Existing stale/partial source coverage remains honestly visible; no ingestion worker was started by this task.

FILES CHANGED: frontend shell/layout and logo; typed translations/context; localized presentation components and News cleanup; localization tests and Market display-label expectation; minimal CONTEXT/AGENTS/design contract updates. No package changes.

GIT STATUS: checkpoint includes only task files. Existing `frontend/next-env.d.ts` dev-type imports and `src/config/settings.py` local dotenv path fix are preserved/excluded; unrelated untracked files remain untouched.

COMMIT: `feat: rebrand product as Woofi and add Vietnamese UI`. No push.

NEXT: review terminology with Vietnamese users before expanding the bilingual dictionary.

## Browser evidence

Screenshots saved outside the repository in `C:/Users/PC/.codex/visualizations/2026/10/07/woofi-v1/`: desktop-light-vi.png, about-vi.png, desktop-news-dark-en.png, desktop-news-dark-vi.png, mobile-stock-light-vi.png, mobile-community-dark-vi.png and mobile-watchlist-light-en.png. The stock and Community proofs reflect the final two-row mobile header.

The temporary frontend production preview and QA tab were stopped/closed. An existing user backend listening on 8000 before QA was reused and preserved.
