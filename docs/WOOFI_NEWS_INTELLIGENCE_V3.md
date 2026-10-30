# Woofi News Intelligence V3

Development source checkpoint, 27 October 2026. Canonical runtime/collector,
product databases and unrelated WIP are not updated by this work.

## Source expansion

Reviewed all 20 registry entries and the shared RSS adapter. Added two specialized
feeds advertised in the [official Vietstock RSS directory](https://vietstock.vn/rss):

| Source | Checked UTC | Items / dated / supplied text | URL overlap with existing 30-item stock feed | Feed SHA256 |
| --- | --- | --- | --- | --- |
| `vietstock_business` — `/737/doanh-nghiep/hoat-dong-kinh-doanh.rss` | 2026-10-27 11:32:13.049361 | 20 / 20 / 20 | 0 | `63e69adeed2c78d664304bf76f1c1f211fbf896e3f87ee2fea7fbb692a0320ea` |
| `vietstock_dividends` — `/738/doanh-nghiep/co-tuc.rss` | 2026-10-27 11:32:13.121284 | 20 / 20 / 20 | 0 | `244e3b831a2d67932615527406c9396fb48cf3cd70b92e1ea382cb79d4fe1c4e` |

The bounded public validation used the existing TLS-verifying RSS parser after
checking robots.txt for the exact paths. No article-page acquisition or database
ingestion occurred. Both feeds retain `publisher_group=vietstock`; 22 configured
feeds do not mean two additional independent publishers. Existing canonical-URL
deduplication, scheduling/backoff and source-health telemetry are reused. Future
health is unknown until the separately deployed worker actually processes them.
PetroTimes and Diễn đàn Doanh nghiệp public pages did not expose a validated RSS
link in the inspected markup; no guessed feed was registered. Bnews has a public
directory but was not enabled in this pass given overlap and unresolved reuse terms.

## Company evidence and search

- Reuse issuer-context tagging, cached ordinary-equity metadata and immutable
  publisher text receipts. Explicit comma/conjunction stock lists and market/industry
  ticker mentions are supported, with currency/common-word/role/brand guards.
- Two reviewed alias entries reuse the existing alias mechanism: Techcombank/TCB
  ([issuer disclosures](https://techcombank.com/nha-dau-tu/cong-bo-thong-tin/thong-tin-khac))
  and Tập đoàn Hòa Phát / Hoa Phat Group / HPG
  ([issuer introduction](https://www.hoaphat.com.vn/introduce)). Names still require
  unique ownership and membership in the current cached listed-equity universe.
- Market/Industry classification retains precedence. Cards validate proofs from
  every current Story member, including receipt-backed supplied text. A corrected
  representative cannot borrow stale-title proofs. Ticker links need no live price.
- The existing worker projection version refreshes the bounded 96-hour/10,000-Story
  derivative cache idempotently when deployed. Original articles/receipts are not
  destructively retagged, and HTTP neither fetches nor retags evidence.
- Existing `/news/feed` and `/news/feed/page` accept bounded `q` and optional `ALL`
  category. Defaults remain compatible. Search ranks exact evidenced issuer/name
  matches, headline phrases, exact topic/sector labels and available supplied text;
  multiword queries require all terms. Later receipts cannot leak into old snapshots.
  This is search relevance, not investment importance or financial inference.
- One full-width search field replaces the filter panel, heading description and
  source-status panel. Input is immediate; requests debounce 300 ms. New queries
  search all categories, tabs narrow them. URL/history/reload and legacy ticker
  links preserve useful query context. Old results are withheld during query changes.
  Source diagnostics remain at `/news/sources`; independent Community is preserved.

## Validation and limits

Validation: **191 relevant backend tests passed; 363 frontend tests passed with
one existing skip; optimized webpack build and TypeScript typecheck passed**.
All 16 pre-existing WIP file hashes are unchanged. Synthetic tests cover
source/date/dedup behavior, all three ticker categories, aliases/ambiguity, title and
supplied-text search, snapshot isolation, category/history/debounce, filter removal,
EN/VI and existing component contracts. Build/typecheck run in an isolated source
copy using existing dependencies; no private `.env` or captures are copied.

Browser acceptance of this development build remains pending. The running pinned
release is not updated and cannot establish acceptance of these changes. Responsive
layout uses existing theme tokens, a shrinking full-width input and accessible
native search controls; actual desktop/mobile light/dark checks are still required
before a separately authorized runtime update.

Search covers only retained headlines and bounded publisher-supplied summary/content,
not arbitrary full articles. Unavailable bodies, unreviewed aliases and uncertain
company identities remain unavailable. Existing archive horizon/category coverage
and source access limits remain; no provider packages, Bronze or LLM are introduced.
