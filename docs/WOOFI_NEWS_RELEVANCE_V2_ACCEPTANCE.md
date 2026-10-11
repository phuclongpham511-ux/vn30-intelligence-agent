# News relevance and stock research UX V2 acceptance

Development checkpoint on `codex/woofi-news-relevance-v2`, based on verified
`origin/main` `12fff386a8138ac33d5f2b29fe1804ea574caa94` (verified again at completion).
No push, deployment or canonical runtime update. The local checkout is
`C:/Users/PC/.codex/worktrees/woofi-news-relevance-v2`.

## Evidence boundaries

- **PERSISTED_DATA:** SQLite supported backup of an already archived canonical
  product snapshot, tested at `C:/Users/PC/Woofi-news-relevance-v2-validation-20261011/isolated.db`.
  The live database was never opened or modified by this development work.
  Archived source SHA-256: `8f699dbf95852bdd0e2ea9796f01fe1ef977a679d3e9e72d96bbc7f8b9a880a6`.
- **LIVE_SOURCE:** one bounded read of the configured public Dân Trí RSS feed,
  retained as `dantri-feed-live.xml` in the validation directory. Original publisher
  article inspected read-only; no authentication bypass or new collector.
- **REPLAY:** that captured feed text applied only to the isolated copy, matching
  exact current article title and canonical URL (96 receipts). Existing article
  publication/first-seen times and source-success receipts were not advanced.
  Browser SSI prices replay prior actual SSI reads, labeled `REPLAY:SSI:…`, with
  October 9 trading dates and stale/closed status. Other quotes remain unavailable.
- **FIXTURE:** unit/regression tests. No fixture is claimed as live acceptance.

The isolated browser used Next development on port 3131 and the replay backend on
8131. The production compiler/build was separately verified. An earlier production
preview start was rejected by automatic tool approval with only “blocked by
policy”; development preview supplied the requested browser validation. Neither
preview service nor an ingestion worker was left running at completion.

## Freshness diagnosis

Baseline audit as-of **2026-10-11 22:23:28 +07**. All table timestamps below are
Vietnam time. The fetch column describes persisted successful source receipts,
not a new collection during this task. “Eligible” means latest publication among
eligible Story members; representative headlines can be earlier.

| View | Latest successful source fetch | Latest candidate publication | Latest candidate persistence | Latest eligible publication | Candidate articles Oct 9 / 10 / 11 | Candidate / displayed Stories |
|---|---|---|---|---|---|---|
| Company | Oct 11 16:46:13 | Oct 10 12:23:00 | Oct 10 21:31:51 | Oct 10 12:23:00 | 6 / 2 / 0 | 6 / 6 |
| Industry | Oct 11 16:46:13 | Oct 9 17:30:00 | Oct 10 21:29:32 | Oct 9 17:30:00 | 2 / 0 / 0 | 2 / 2 |
| Market | Oct 11 16:46:13 | Oct 11 14:58:00 | Oct 11 16:46:12 | Oct 11 14:58:00 | 20 / 12 / 9 | 39 / 36 |
| Hot Topics | Oct 11 16:46:13 | Oct 11 14:58:00 | Oct 11 16:46:12 | Oct 9 23:14:00 | 28 / 14 / 9 | 47 / 4 |

Across all 2,469 persisted Articles, publisher dates Oct 9 / 10 / 11 contain
**339 / 262 / 140** Articles. These are publication-date counts, not newly inserted
rows during this task. The Market/Hot candidate totals also include one Oct 8
Article still inside the rolling 72 hours at the baseline audit.

The common disjoint exclusions are **1,722 outside 72 hours**, **652 with no
qualified research category**, and **43 foreign subjects without Vietnam context**.
There were zero future-publication or foreign-registry/country exclusions in this
snapshot. Exact article identities, titles and reasons are in `freshness-before.json`.
Of the 52 remaining category-qualified Articles, Company excludes 44 as another
category, Industry excludes 50, and Market excludes 10. Thus base article exclusions
per archive are 2,461 / 2,467 / 2,427 respectively, before Story/image rules.
Hot additionally excludes **43 of 47 candidate Stories** for fewer than two
independent publisher groups; that gate stays unchanged.

The baseline UI agreed with the API: newest Company headline Oct 10, Industry
Oct 9, Market Oct 11, and four promoted Hot Topics from Oct 9. Newer qualified
Market reporting was already first, not lost by ordering or initial pagination.
Lexical clustering and the stable earliest-source representative explain why a
card date can predate later reporting within its Story; this is not a fabricated
refresh date. The small number of Industry/Company/Hot matches explains their age.
There is no evidence in this snapshot of a failed collector: all 20 enabled News
feeds had successful receipts and were healthy under their 360-minute weekend
cadence. The archive contains some older Articles first persisted on Oct 10/11;
persistence time is never substituted for publisher publication time.

Three valid Market Stories were suppressed solely for absent source images:

- “Tỷ giá USD ngày 10-10: Duy trì đà tăng cả tuần”
- “Chứng khoán 9-10: PNJ, SHB lấy lại \"phong độ\", khối ngoại bán ròng hơn 9.000 tỷ đồng”
- “Tỷ giá USD ngày 9-10: Giảm mạnh tại các ngân hàng”

V2 displays all three with their real Hà Nội Mới attribution and dates. A broken
image affects only the image. An explicit legacy `/news/top?require_image=true`
request still honors its caller's filter. Source-image suppression was not the
reason the other prominent Oct 9 Hot/Industry cards were old.

After replay, the isolated API returned Company **7**, Industry **2**, Market **38**,
Hot **4** at 22:59 +07. One older Market candidate expired between audits; compare
the exact as-of values rather than interpreting that difference as lost ingestion.
The extra Company Story comes from explicit VPB wording in its publisher summary.
The Masan Story stays Market because existing headline macro/market precedence is
preserved. It gains verified MCH evidence and a relevant Watchlist item.

Automatic refresh passed in the browser: an existing real Masan Story was removed
from **only the isolated derivative cache**, the page loaded without it, and the
original cache row was restored at 23:00:11 +07. The Story returned by 23:01:07 +07
without navigation/manual refresh, keeping its Oct 9 publication time. Underlying
Articles, Stories, text receipts, source receipts, Community and corporate records
were unchanged by this replay. Manual archive refresh also retained 24 revealed
rows after Show more; all API pages reached every eligible unique Story ID in order.

## Entity resolution and source navigation

The [original Dân Trí article](https://dantri.com.vn/kinh-doanh/mot-co-phieu-he-sinh-thai-masan-bi-khoi-ngoai-xa-rong-gan-9600-ty-dong-20261009151859787.htm)
explicitly identifies **MCH** as the principal foreign-selling subject. Its public
full text also mentions MSN separately and several other stocks in the session.
The configured feed's bounded publisher summary explicitly names MCH, and the
persisted SSI ordinary-equity universe identifies MCH as **Công ty Cổ phần Hàng
Tiêu Dùng MaSan**, HOSE, distinct from **MSN / Công ty Cổ phần Tập đoàn Masan**.
Therefore the worker's available summary supports MCH. The implementation does
not ingest the inspected full page or infer MSN from the ecosystem headline.

`issuer-context-v2` retains conservative headline qualification and adds
sentence-scoped explicit stock/unique issuer identity evidence from bounded feed
text. Proofs record deterministic confidence reasons (`explicit_stock` or
`issuer_identity`), origin, supporting excerpt, receipt identity/hash, URL and
observation time. No numeric confidence is invented. Additive `NewsTextReceipt`
rows are append-only and sequential, preserve A→B→A observations, and cannot attach
another URL/publisher's text to a displayed Article. Corrections update the worker
projection; body-aware HTTP reads reuse persisted proofs without fetching text or
running the body resolver. Legacy raw evidence readers retain their prior
headline-only read behavior. Snapshot-time admission
prevents a later summary from being backdated into an earlier read.

Regressions cover MCH recall, distinct MSN identity, no inferred ecosystem ticker,
canonical legal names, unknown/ambiguous identities, USD/VND/NDT and ordinary-word
abstention, article/publisher ownership, bounded supporting excerpts, related-link
exclusion, receipt corrections, image-free pagination and snapshot admission.
The actual original “Thanh khoản chứng khoán vượt 1 tỷ USD, VN-Index vẫn giảm điểm”
Story has no USD issuer link. All seven current currency-USD Market Stories have
zero issuer proofs; `/news/feed?...&ticker=USD` returns empty. The quiet real USD
equity stays available in Watchlist without borrowing those currency headlines.

Cards show one stable representative, real source/date, optional image and verified
ticker chips. Headlines open the publisher in a separate tab with `noopener
noreferrer`; browser verified the Dân Trí destination. Ticker links are siblings
and open Stock Detail separately. There are no primary Evidence/report-count
actions. Full Story source evidence remains reachable inside secondary About this
feed → Source archive and existing detail/Watchlist evidence disclosures.

## Product and browser acceptance

Home Market Focus shows at most three recent Company/Market Brief Stories, with
qualified issuer proof required for Company representatives. It deduplicates by
Story and orders by publisher publication time. The three observed highlights
were dated Oct 11. Raw forum discussions, popularity and sentiment supply no score
or featured content. Quality rules and Community access remain secondary.

Watchlist prioritizes one primary stock link, cached price/direction and all loaded
unread News/Community/Technical items. Empty source sections disappear; quiet stocks
remain. Reviewed history, operational provenance, per-item review and Technical
assurance are secondary and inspectable. Backend source limits and warnings remain
honest. For the real 86-Story cache, five-stock intelligence reads took **0.110–0.134
seconds** in the completion probe; this is not a 10,000-Story capacity guarantee.

| Browser gate | Observed result |
|---|---|
| Direct publisher / separate ticker navigation | PASS; original publisher opened, MCH routed to `/stocks/MCH` |
| Primary cards | PASS; one representative, no Evidence/report counts, optional images |
| MCH / USD | PASS; MCH chip and unread item, no inferred MSN, original currency Story no USD issuer link |
| Price movement | PASS, **REPLAY**; PNJ +6.85% green, SHB −0.50% red; original Oct 9 dates and stale labels; MCH neutral unavailable |
| Market Focus | PASS; three qualified publisher highlights, no forum popularity/sentiment |
| Watchlist review | PASS; explicit one-item PNJ News review changed 3→2 unread, persisted through reload; Community remained unread; disclosures/navigation did not review |
| Quiet stock / unread visibility | PASS; MCH unread visible; real USD security visible without large empty source sections |
| Freshness / ordering / pagination | PASS; API/UI dates agree, full stable API pagination, 24 rows retained after browser refresh, minute replay passed |
| Desktop / mobile | PASS; 1280px desktop and actual 390×844 mobile, no horizontal document overflow |
| Dark/light and EN/VI | PASS; source headlines unchanged; product chrome, number/date conventions and colors render correctly |
| Stock Detail data | Navigation PASS; isolated MCH historical provider correctly shows unavailable with credentials disabled; complete live historical-data acceptance is not claimed |

Community provenance remains separate: the archived snapshot's last success times
are F319 **17:36:34**, 24HMoney **17:34:59**, Chứng Sỹ **17:35:10**, Oct 11 +07.
At validation time these are accurately **stale** under 15-minute Community policy.
Response-check time is not shown as a source fetch/publication time. FireAnt remains
disabled/deferred. No new News/Community freshness was fabricated by replay.

SStock's public sign-in page was accessible, but the owner did not complete manual
sign-in during this task. Authenticated stock exploration could not be inspected.
No credentials were retrieved and no branding/proprietary layout was copied.

## Validation, reviews and preservation

- Focused backend: **125 passed**.
- Full backend: **983 passed**, one existing Starlette/httpx deprecation warning,
  268.03 seconds. Includes protected ingestion/Technical regression suites.
- Frontend: **102 passed**; typecheck **PASS**.
- Final production build: **PASS**, Next 16.3.8, all listed routes generated.
- API contracts: **PASS**, stable complete pagination, bounded proof responses,
  MCH/negative USD gates, intent-only refresh (`pending_worker`, no worker started).
- SQLite integrity: **ok**. Original counts: 2,469 Articles, 2,328 Stories,
  117 Community threads, 30 corporate action records. Additive text receipts: 96.
  Corporate action records, documents and source states match the archived source
  byte-for-value, preserving Dividend provenance. Raw Articles remain unchanged.
- Independent **Standards review PASS** and **Spec review PASS**, no unresolved
  P1/P2. Review findings corrected before completion: receipt currentness/ownership,
  supporting excerpt bounds and related-link exclusion. Spec reviewer independently
  ran 10 new backend regressions, all passing; Standards rechecked final archive
  navigation and V2 documentation. Max-capacity performance remains a future probe.
- Downloads HEAD/index/status/source-hash manifest unchanged. Canonical runtime
  SHA remains `12fff386a8138ac33d5f2b29fe1804ea574caa94`, source clean; runtime config
  and cutover metadata hashes unchanged. Credentials reference unchanged; no
  credentials copied/loaded/logged. FPT automation unchanged and **PAUSED**.
- No D1/D4/D5, Technical EOD, SSI, ownership, source-rate-limit, adaptive polling
  or durable-cooldown source changes. One existing canonical collector execution
  tree remains; no V2 ingestion worker was started. Temporary validation services
  were stopped after checks. No source changes in Downloads and no force push.

Validation artifacts and the exact checkpoint SHA/full required final fields are
recorded in `C:/Users/PC/Woofi-news-relevance-v2-validation-20261011/FINAL_REPORT.md`.
Key machine records: `freshness-before.json`, `freshness-after.json`, `api-final.json`,
`browser-results.json`, `preservation-final.json`, `backend-focused.log`,
`backend-full-final.log`, `frontend-tests-final.log`, `frontend-build-final.log`.

Before screenshots: `before-home-desktop.png`, `before-news-desktop.png`,
`before-watchlist-desktop.png`. After screenshots include `after-home-desktop.png`,
`after-company-desktop.png`, `after-watchlist-desktop.png`,
`after-home-desktop-light-vi.png`, `after-watchlist-desktop-light-vi.png`,
`after-home-mobile-dark-en.png`, `after-home-mobile-light-vi.png`,
`after-watchlist-mobile-light-vi.png`, `after-news-mobile-dark-en.png`,
`after-news-mobile-light-vi-no-image.png`, `original-usd-evidence-mobile.png`,
`refresh-before.png`, `refresh-after.png` (all in that external validation directory).

## Integration limits and next safe action

Ready for owner review and a separately approved integration step. Do not treat this
checkpoint as a runtime rollout. Body/alias coverage is bounded by text actually
available in configured feeds and canonical metadata; no full-page crawler was
added. Clustering/Hot publisher breadth and sector classification remain
conservative. SStock authenticated research, new live SSI/historical-data acceptance
and a 10,000-Story stress probe are not claimed. Zero/unchanged yellow behavior is
covered by existing/new regression tests; this browser replay had no observed
zero-movement quote.

Future approved runtime cutover must back up its then-current DB, add the new text
receipt table through the existing supported table bootstrap, let the sole worker
rebuild versioned projections from available evidence, and verify current ownership
and source freshness. The historical validation copy must never replace newer live
writes. Push, merge, deployment and canonical runtime changes require separate
authorization.
