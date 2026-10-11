# News issuer association correction V1 — 2026-10-11

## Scope and root cause

Correction follows Visual News candidate `61fb13dec04816553440a8262ab8ab1c8df2c28d`
on `codex/woofi-visual-news-v1`, based on canonical
`135a31fa88f4e275015701024dd40bb585cfcb4f`.

The old Tagger accepted an uppercase whole ticker token without sufficient issuer
context. The actual Security universe contains USD (Công trình Đô thị Sóc Trăng),
so currency headlines acquired a real but unrelated equity label. Original tags
were stored on Article/Story, passed into the research projection and trusted by
the related-ticker renderer. The renderer then requested real SSI equity movement:
the quote was real; its relationship to the currency article was false. Story
clustering and SSI numerical computation did not establish that relationship.

## Deterministic policy: issuer-context-v1

The existing Tagger resolves whole-token/whole-phrase evidence through:

- A unique legal/display identity from the current equity metadata, or a unique
  explicitly configured company alias. Shared aliases abstain. No inferred brand
  aliases or new alias dataset is shipped by this correction.
- Qualified stock wording (`cổ phiếu`, `mã cổ phiếu`, `mã chứng khoán`, ticker,
  stock or exchange notation), including an explicit list of known securities.
- A ticker in an issuer-subject position followed by narrowly qualified financial
  or issuer activity: earnings/revenue, share issuance, dividend, debt raising,
  appointment, financial-result publication/planning or bounded share acquisition.

Common currency, ordinary language and role/location abbreviations cannot qualify
through a bare token plus generic activity. The vocabulary describes competing
language meanings rather than banned securities: even USD, VND, IT, ALL or CFO
can qualify through explicit stock context or a unique full issuer identity.
Bare normalized `ma` is insufficient because it conflates mã and mà. Standalone
accented “Mã” needs share-issuance/dividend corroboration. Existing nonambiguous
Community `$XYZ`/`#XYZ` notation remains supported; currency `$USD` abstains.

Evidence consists of symbol, article ID, exact headline, evidence kind, matched
text and policy version. No body is stored, no LLM resolves entities, and no news
causation or sentiment inference is added. Unsupported or uncertain headlines
return no association; this is not a claim of exhaustive language accuracy.

## Legacy safety and ownership

No SQL schema change, live migration, Article/Story rewrite, merge or deletion.
Worker-owned research projection metadata includes the policy version. A version
change rebuilds only the existing derivative cache; a second unchanged rebuild is
a no-op. Normal source cooldowns, collector ownership and HTTP cache-first reads
remain intact. HTTP never re-tags or rebuilds evidence; due visits retain the
existing refresh-intent behavior.

Feed ticker filters, chips and page-scoped SSI demand require qualified article
evidence. Story detail reads the persisted proof and validates the exact current
headline; a corrected headline cannot reuse an old proof. Unverified old ticker
tags remain visible as plain “Unverified” / “Chưa xác minh” labels on the source
Evidence page, with no stock link or SSI demand. Legacy caches fail closed until
the authorized worker rebuilds them after an eventual runtime update. Archived
stories outside the derivative cache retain raw evidence but no qualified link.

## Regression and review

All backend commands use the existing Python environment with `-B`, an isolated
test database, `APP_ENV=test`, fixture provider and empty SSI credential variables.
No live source acquisition or competing collector is started.

- Focused: `python -B -m pytest -q tests/test_news_entities.py tests/test_community.py
  tests/test_research_feed.py tests/test_news_adaptive.py tests/test_news_discovery.py
  tests/test_news_correction.py tests/test_news_pagination.py
  tests/test_watchlist_intelligence.py`: **104 passed**, 11.20 seconds.
- Full backend: `python -B -m pytest -q`: **973 passed**, 262.16 seconds. One existing
  FastAPI/httpx dependency deprecation warning.
- Focused frontend: `node --test tests/news-presentation.test.mjs
  tests/localization.test.mjs tests/research-presentation.test.mjs`: **26 passed**.
- Full frontend: `npm test`: **98 passed**.
- `npm run typecheck`: PASS. `npm run build`: PASS.
- Independent Standards and Spec reviews: zero blocking findings after correcting
  the demonstrated bare mã false positive and earnings-announcement false negatives.

Tests cover USD/VND currency versus explicit issuer, common English words and
Vietnamese abbreviations, substring rejection, legal identity, unique/shared
aliases, multi-issuer and mixed macro/company titles, missing context, revised
earnings continuity, legacy cache/API safety, stale-policy/headline proof rejection,
idempotent derivative rebuilding and actual component rendering in both languages.

## Isolated data and browser acceptance

Evidence directory (outside Git):
`C:/Users/PC/Woofi-visual-news-validation-20261011/entity-correction`.

`validate_snapshot.py` makes a consistent read-only backup of the previously
isolated product snapshot to a new database and records table row counts/SHA256.
`snapshot-audit-final.json` confirms integrity `ok`, only `newsreadcache` changed
during rebuilding, and all raw table hashes/row counts retained, including **2,416
Articles, 2,280 Stories and 30 Dividend records**. Subsequent read calls write only
normal News refresh intent; raw provenance remains unchanged. Second rebuild is a
no-op. Five currency representatives in the current 72-hour projection have no
USD/NDT/VND issuer proof. Six genuine Company rows retain CII, SHS, PNJ, SHB and
VIX/VPB associations.

Backend 8150/frontend 3050 replay previously captured public real SSI DTOs, using
only the copied database and no credentials/collector. This is persisted-source
and SSI-replay acceptance, **not a new live SSI/news acceptance**.

- Actual original headline “Lãi suất tiền đồng và giá USD liên ngân hàng liên tục
  giảm”: no stock chip/link. Evidence retains `USD · Chưa xác minh` as a plain tag.
- Several USD/VND macro titles have publisher/evidence links only.
- Real Company chips retain CII +2.14%, SHS +0.86%, PNJ +6.85%, SHB -0.50%, source
  reference prices and October 9 trading date. Sunday age is disclosed as stale.
  VIX/VPB quotes not captured by the harness stay unavailable, not zero.
- PNJ chip navigates to Stock Detail with the captured real price; uncaptured
  fundamentals are intentionally unavailable. Search → ACB detail shows the
  captured 20,150 VND, -0.98%, SSI history and honest Technical evidence state.
- Existing isolated PNJ membership and review state survive reload; no automatic
  review was performed. Watchlist → PNJ News preserves the ticker filter.
- Desktop light Vietnamese and 390×844 mobile dark English show compact rows,
  same original Vietnamese source headlines and no horizontal overflow.

Screenshots: `usd-legacy-evidence.png`, `company-chips-desktop.png`,
`pnj-mobile-dark-en.png`. Temporary preview processes/tabs were closed and viewport
reset. Generated tracked Next.js reference restored to original HEAD bytes;
pre-existing untracked frontend AGENTS/CLAUDE notes are excluded from the commit.

## Runtime and integration limits

Canonical runtime remains pinned to `135a31fa` with original 3000/8000 processes
and collector. Downloads WIP, FPT pilot/EOD policies, live databases, credentials,
pricing, movement colors and review persistence were not modified. This checkpoint
is code integration only. A future explicitly authorized runtime update must allow
the sole collector to refresh policy-versioned projections before live UI acceptance.
