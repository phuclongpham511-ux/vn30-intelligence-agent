# News refresh and thumbnails V2

Implemented 2026-10-08 in the current local repository. This extends Article/Story,
source status, canonical ingestion and existing News categories.

## User behavior

- Publisher News uses a single list with the thumbnail on the left, following the
  arrangement observed at https://sstock.vn/tin-tuc. Woofi retains its own styling.
- Every displayed news row/card has a thumbnail. Explicit RSS image metadata is
  preferred, then an image extracted from the feed description/content. Only URL
  and provenance are saved; description/article bodies are not stored. Image URLs
  from another Story are never substituted. Broken or absent images hide the entire item, as explicitly requested by the
  user. No generic or generated illustration substitutes a source photo. The stored
  evidence remains and the row can reappear when a later acquisition provides an
  image; failed image URLs are retried after a new source observation.
- The initial archive request contains at most 12 Stories. **Show more / Xem thêm**
  requests the next 12 only after a click. Category/filter changes reset to page one.
- Current archives contain publications within 72 hours. An absent publication
  timestamp uses first-seen, labelled as such. Duplicate ingestion does not renew
  age. Persisted evidence is not deleted, and Story detail remains inspectable.
- One existing lexical Story is displayed once, represented by its earliest known
  publication. Unknown publication times sort after known times; ties are resolved
  by canonical URL and ID. Source filters choose among their matching articles;
  other original reporting remains behind a disclosure. Matching remains approximate,
  protecting against conflicting numbers; this is not universal semantic dedup.
- Hot Topics now requires at least two independent publisher groups, per the
  Adaptive News V1 task. A same-Story source image is also required. Repeat fetches/reprints collapsed
  by existing identity rules do not inflate activity. Publisher breadth remains the
  first ranking factor, followed by capped activity and recency. Article counts and
  independent publisher counts are displayed separately. Attention is not truth.

## Refresh and API

An open web session requests `/ingestion/refresh` at mount and every five minutes.
News requests record durable due-source intent; the canonical worker uses adaptive
per-source cadence. See ADAPTIVE_NEWS_INGESTION_V1.md for the current scheduling
and worker requirement.
News archive, stock news, Hot Topics and source status refresh once per minute.
Browser timer throttling can delay refresh in an inactive tab. For acquisition even
when the browser is closed, run the existing canonical worker:

```powershell
uv run python -m scripts.ingest_data --watch
```

No new secret, paid service or manual seeding is required. Existing per-source
failure isolation remains; source status reports actual successful acquisitions.
HTTPS uses certificate validation through the OS trust store. Compressed and
expanded feed sizes are bounded independently. Vietnamese registry names are read
as UTF-8 on Windows. News JSON timestamps include UTC offsets even when SQLite
returns naive UTC values, preventing browser-local misinterpretation.

`GET /news/feed/page` returns `items`, `as_of`, `has_more`, `next_offset`. It accepts
existing category/filter parameters, `limit` capped at 12 and `offset` 0–10000. Follow-up
pages pass the original timezone-aware `as_of`, excluding later ingestions and using
the same 72-hour cutoff. Automatic refresh starts a fresh snapshot and re-requests
only pages already revealed. Failed reads retain the last successfully loaded list.
The original list-returning `/news/feed` remains compatible, adding optional offset.
`/latest` remains the raw Article API; stock UI now uses grouped `/top?require_image=true`.

## Ten additional feeds

The following returned non-empty recent RSS with valid publication dates during
qualification. Related publications share a publisher group (VietnamPlus and Báo
Tin Tức: `vna`; Đầu Tư Chứng Khoán and Thời Báo Tài Chính: `baotaichinhdautu`).

| Publisher | Public RSS |
|---|---|
| Công Thương | https://congthuong.vn/rss/tai-chinh.rss |
| Hà Nội Mới | https://hanoimoi.vn/rss/kinh-te |
| Sài Gòn Giải Phóng | https://www.sggp.org.vn/rss/tai-chinh-chung-khoan-44.rss |
| Tiền Phong | https://tienphong.vn/rss/tai-chinh-chung-khoan-105.rss |
| Nhân Dân | https://nhandan.vn/rss/kinhte-1185.rss |
| VietnamPlus | https://www.vietnamplus.vn/rss/kinhte-311.rss |
| Báo Tin Tức | https://baotintuc.vn/rss/kinh-te-128.rss |
| Thời Báo Tài Chính | https://thoibaotaichinhvietnam.vn/rss_feed/ |
| Báo Chính Phủ | https://baochinhphu.vn/home.rss |
| Đầu Tư Chứng Khoán | https://www.tinnhanhchungkhoan.vn/rss/chung-khoan-1.rss |

Báo Đầu Tư and Người Lao Động candidate feeds were empty and were not enabled.
An incorrect Đầu Tư Chứng Khoán RSS category returned 2021 history; only the verified
current Chứng khoán feed was selected. Acquisition success is not complete semantic
coverage: company eligibility still uses SSI listed ordinary-equity metadata, and
headline classification remains partial. RSS endpoints and external images can fail;
affected stories remain hidden until a usable source image becomes available.

## Validation

- Public ingestion→API tests: earliest representative, independent raw evidence,
  offset validation, stable snapshot pagination during new arrivals, publication
  expiry without evidence deletion, distinct-article Hot Topics and UTC serialization.
- Adapter tests: description images, relative URLs, unsafe/tracker images, source
  date parsing, validating TLS and compressed expansion limits.
- Frontend rendering and EN/VI tests: source text preserved, source thumbnails,
  missing/unsafe image hiding and same-Story image isolation.
- Production build and browser: desktop/mobile, light/dark; live Company archive
  requested 12 Stories; with broken images hidden, the verified Market view
  showed 10 rows initially and 20 unique rows after Show more. At 390px the layout
  had no horizontal overflow. EN/VI source text stayed unchanged.
- Full backend regression: 678 tests passed. Frontend regression: 67 passed;
  typecheck and production build passed.
- The live ingestion check returned success for all 20 enabled sources. Ten new
  feeds added 342 Articles, of which 312 had source image URLs at that check.
