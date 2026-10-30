# Stock Intelligence integration V1

Base: `42fa3cf143f0f749fc86396f36b4715d5238749f`, existing Market Workspace
development checkout. This connects existing Stock Detail research; no new page,
source, acquisition pipeline or financial interpretation is introduced.

## Existing systems reused

- Existing `/watchlists/intelligence` persisted read, cached issuer identity,
  Company-relevance policy, canonical NewsStory IDs, member revisions and current
  publisher-text/headline proofs.
- Community evidence, F319/source registry and source statuses; Community Pulse's
  existing long-copy deduplication helper. Source eligibility remains unchanged.
- Existing browser storage key/parser, `isUnread`, explicit revision receipts,
  `baselineLegacyReviews` and concurrent-review guard from `reviewBriefingItem`.
- Existing Stock Detail five-tab/hash navigation, company overview, financial
  engine display gates and corporate-action source verification.

## Implemented experience

One retained StockIntelligence panel replaces Stock Detail's separate StockNews
and StockCommunity loaders. Overview shows three stories; Company News shows six
with expansion to the loaded sample. A collapsed community section exposes its
source items progressively. Switching Overview/News reuses the same read rather
than adding duplicate requests. Financial/Actions links use the existing tabs.
Other News/Community surfaces and their shared renderers remain intact.

The panel makes one bounded read on mount/ticker change or explicit refresh.
Its 20-second deadline aborts slow reads. No interval, automatic source refresh,
quote subscription, stock-price request, SSI request or acquisition is added.
The existing endpoint reads persisted Technical diagnostics as part of its common
response; Stock Detail neither displays nor acquires new Technical evidence.

Stories are ordered unreviewed first, then original publication time, with stored
observation/event ordering when publication is unavailable. An optional filter uses
the existing Earnings tag. Announcement/dividend headlines remain original coverage,
not newly inferred corporate-action facts or a financial materiality classification.

Current issuer-context-v2 proofs are inspectable and distinguish explicit ticker
evidence, issuer context and weaker stored ticker matches without detailed proof.
Unrelated instruments, inconsistent representative attribution, unsafe links and
future timestamps are withheld. Publication and first/last observation are separate;
a missing community observation time never inherits its publication timestamp.
Each retained primary item has a safe original link; valid supporting report URLs
remain inspectable. Original language is kept.

Community shows title/extractive original text, source, publication/observation,
available replies/views and original discussion links. Missing counts stay missing;
real zero remains zero. Discussions remain unverified. Engagement, source breadth
and source health never imply sentiment, corroboration, bullishness or materiality.

The existing Pulse dedup helper optionally returns `display_groups` from the same
endpoint via `community_groups=true`. This is display metadata over at most twelve
loaded items; it does not change native IDs, revisions, pagination or source reads.
Repeated long copies share a primary display group with remaining source copies
behind disclosure. Each original source item retains its own explicit review.
Short independent comments are not merged. Default Watchlist request bodies and
responses do not request/compute this grouping and retain their existing behavior.

## Review/window semantics preserved

News uses the canonical rolling 72-hour first-acquisition eligibility window.
An older stable story anchor may remain when another eligible publisher is added;
the client does not renew that anchor or re-filter it into another time window.
Community explicitly uses the existing Watchlist last-24-hour publication window.
Both samples are bounded to twelve source items on the loaded page; has-more,
truncation and omitted attribution keep coverage explicitly incomplete.

Unread state is based on story/item IDs and content revisions, not elapsed time.
Opening links/disclosures does not review anything. Each review acknowledges only
the selected displayed revision for a currently followed stock. It re-reads storage
and preserves another tab's concurrent explicit review. Other stocks, hidden items,
unseen developments and older receipts are not reset. Publisher copies and changed
reply/view counts do not reopen reviewed content; known content corrections do.

The existing legacy baseline upgrades only previously reviewed identities. It
creates no review date and never acknowledges an unread item. Browser storage
failures retain the stored payload and make counts unknown while source evidence
remains independently readable. Follow/unfollow keeps the existing semantics.
A same-window notification synchronizes the existing FollowStock control and new
research context; normal storage/focus events also restore current review state.

## Source and product limits

Source health is labeled **at read**, with the actual source's last successful
fetch and the response's evaluation time. It is not renewed by rendering cached
evidence. Stale/error/never-checked/disabled and unavailable reads remain distinct.
Loaded counts describe observed source items, not complete company activity.
The panel does not certify current F319/News acquisition, publisher truth, complete
relevance coverage or live freshness. No new source retrieval was performed here.
Untitled or untagged coverage may be missing. There is no qualified new taxonomy
for announcements/dividend reports beyond existing source evidence/tags.

The panel supports EN/VI chrome, existing light/dark tokens, wrapping source text
and progressive mobile disclosure. Actual browser acceptance remains **PENDING**;
unit/SSR/build results do not establish desktop/mobile browser acceptance. No denied
preview, browser process, port or host permission operation was retried.

## Executed validation

- Frontend: **238 PASS, 1 optional existing SKIP, 0 FAIL** (239 cases). Existing
  optional persisted-API replay lacks its external evidence configuration. Tests
  cover source attribution, deduplication, windows/anchors, missing/future times,
  UI empty/error/stale states, EN/VI, native-ID review semantics, concurrent storage,
  late responses, cleanup and no new polling or quote lease.
- Backend: **50 PASS**, separately, across Stock Detail integration, Watchlist
  intelligence/monitoring, Community daily and news relevance. Synthetic in-memory
  fixtures verify SELECT-only HTTP access and fail if News/Community/SSI acquisition
  is invoked. Copy grouping leaves all original item IDs/revisions intact.
- Typecheck and optimized webpack build **PASS** in a hash-matched artifact copy;
  source/shared `.next` and runtime environment files are untouched. One existing
  Starlette/httpx deprecation warning remains.

Artifacts/logs:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/stock-intelligence-integration-v1/`.
All new test records are synthetic, not live source acceptance.

No product SQLite, Supervisor, Collector, runtime pin, acquisition ownership,
cooldowns, Technical Pilot or FPT automation change. No push or deployment.
Next gate: permitted browser validation of Overview → Company News → source/review
flows, including real source status, while retaining all financial/action gates.
