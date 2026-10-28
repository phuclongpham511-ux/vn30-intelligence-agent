# Woofi visual-first UI/UX and News freshness V1

## Checkpoint and scope

Status: implementation and feasible acceptance passed; local only, no push,
deployment or canonical runtime cutover. Feature worktree:
`C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/vn30-intelligence-agent`, branch
`codex/woofi-visual-news-v1`, based on verified remote
`135a31fa88f4e275015701024dd40bb585cfcb4f`. The feature checkpoint is the commit
containing this report; its exact SHA is recorded in the external verification
receipt and final handoff (avoids a self-referencing commit hash).

No backend application/schema/provider, ingestion policy, D1/D4/D5, Technical EOD,
live database, credentials or mascot assets were changed. Existing API contracts
are reused; the only new route is the frontend Evidence view.

## Reference and delivered behavior

The existing SStock session was inspected at `/tin-tuc` and AAA detail after
viewing the public sign-in screen. Useful patterns: photo beside headline,
compact source/time, ticker percentages with session tooltips, tabs and gradual
loading. Some reference thumbnails were broken. No authentication automation,
proprietary code, assets or complete layout were copied.

- **News / Hot:** one deterministic existing representative per displayed Story;
  no primary other-reporting expansion. Actual same-Story thumbnails only.
  Source/date remain visible; all publisher evidence is in the linked detail.
  Raw evidence remains readable when its source image is absent or broken.
- **Related stocks:** up to three unique representative-article associations,
  Stock Detail links, actual existing batched SSI percent changes. Additional
  associations remain inspectable in Evidence. No causal or impact classification.
  Unknown stays a neutral dash; stale changes retain their reference date.
- **Investor Attention:** actual unique sampled discussions, at most five active
  tickers, two extractive topics, detail links and coverage. One observed discussion
  does not justify a sentiment label. Original messages remain in detail only.
- **VN-Index:** approved wolf directly left, number primary, direction/points/%
  and compact source/session/date/stale status; only available aggregates.
- **Movement:** shared green/red/yellow/neutral semantics; text/symbols supplement
  color. Yellow requires a measured zero, independently of session freshness.
  Metadata-only Search has no invented quote or colored return.
- **Watchlist:** unreviewed observed activity first; quiet News/Community and
  Technical sections compact/collapsed where appropriate; source and storage
  explanations secondary. No automatic review or new event sentiment. Existing
  factual IDs, explicit review and correction-aware behavior remain unchanged.
- **Density:** Home, News, Hot, Community, Stock Detail and Watchlist now place
  evidence and financial values above diagnostics. Source/freshness details remain
  reachable; material uncertainty remains visible. Search already used concise
  dynamic ticker/company metadata and was retained.

## News freshness diagnosis

Consistent read-only online backup captured 2026-10-11 05:37:10 UTC (12:37 Vietnam).
Live data was not altered. Copied database integrity passed, with 2,416 Articles,
2,280 Stories and 30 Dividend corporate-action records retained. Recomputing the
existing research builder against that copy produced identical identities and
ordering to persisted rows in all three categories:

| Category | Eligible count | Newest representative publication, Vietnam |
| --- | ---: | --- |
| Company | 8 | Oct 10 12:23 — CII bond financing |
| Industry | 3 | Oct 9 17:30 — Gia Lai technology/startup event |
| Market | 55 | Oct 11 10:41 — Q3 earnings and VN-Index |

Latest source success was Oct 11 10:45:11 and projection 10:45:13. Twenty feeds
were healthy at capture. Weekend policy is 360 minutes, with next due times around
16:41–16:45; healthy does not mean continuous acquisition. No collector was added
or scheduling/cooldown overridden.

The last-48-hour raw sample contained 573 Articles: 526 had no research category,
36 Market, 7 Company, 2 Industry and 2 lacked an image. Seventeen cached Articles
were Oct 10 or newer (16 Market, 1 Company, none Industry). Existing conservative
classification explains the sparse newer Industry/Company feed. Hot promotion
ranks coverage and bounded activity rather than pure recency. A representative's
earliest publication can precede its Story's latest-member ordering timestamp.
Two Market images failed in browser; the existing source-photo policy hid those
primary rows while their raw evidence remained stored. No date or article was
fabricated. The copied pre-existing corrected CafeF legacy Stories are retained;
this task does not migrate/delete historical duplicates.

The frontend previously retained its loaded snapshot until explicit refresh.
News archive, Hot and Stock News now re-read persisted APIs every minute while
visible and on focus/visibility return. Hidden tabs pause interval work; cleanup
removes listeners and aborts old requests. Existing busy guard and pagination
`as_of` remain; refresh rebuilds only the depth already revealed. No source
acquisition is introduced by this frontend timer.

## Validation and provenance of evidence

Evidence folder (outside Git):
`C:/Users/PC/Woofi-visual-news-validation-20261011`.

| Check | Command / method | Result |
| --- | --- | --- |
| Full backend | canonical venv Python, feature cwd, isolated DATABASE_URL: `python -B -m pytest -q` | 934 passed, one existing Starlette/httpx deprecation warning, 230.44s |
| Full frontend, final | frontend cwd: `npm test` | 96 passed, 0 failed |
| Typecheck, final | `npm run typecheck` | passed |
| Production build, final | `npm run build` | passed, Evidence route included |
| API contracts | 13 bounded reads against feature app and copied DB | valid health, three category pages, Hot, Story, Community/filter, index, batched quotes, universe, ACB overview and Technical status |
| Data safety | SQLite integrity + relevant row counts | passed, 2,416 Articles and 30 Dividend records retained |

Actual authenticated SSI observations used the existing canonical public API:
one batched CII/SHS/PNJ/SHB read, releasing its browser-demand lease, and one ACB
overview. CII +2.14%, SHS +0.86%, PNJ +6.85%, SHB -0.50%; evaluated trading date
Oct 9. ACB overview retained 123 SSI history sessions. Index replay: 1,735.09,
-3.88 / -0.22%, Oct 9. Sunday was not treated as a fresh trading session.

Browser acceptance used isolated feature frontend 3050/backend 8150, actual copied
News/Community and the captured SSI DTOs replayed through the existing contracts.
No harness credentials, collector, outbound SSI or competing crawler. This is
real persisted-data and real SSI-value presentation acceptance, **not** new
intraday/live-collector acceptance. Unknown uncaptured calls deliberately returned
unavailable; stock fundamentals availability was not established by this harness.
Offline labelled fixtures covered zero, missing and stale quote behavior.

Browser evidence:

- Desktop dark EN and light VI Home; mobile light VI Home/News/Watchlist/ACB,
  mobile dark EN Company/Community. Width checks found no horizontal overflow;
  mascot bounds were immediately left of the index number.
- Company showed actual CII/SHS/PNJ/SHB changes and stale Oct 9 dates; uncaptured
  symbols displayed unavailable. One headline per visible card and no reporting
  expansion rows. Evidence link displayed original source evidence.
- Market Show more increased 12 loaded rows to 24 (22 displayed after two broken
  source images), preserving the newest headline and unique Story cards.
- Home MSR discussion link opened the Community view with MSR filter and one
  actual discussion, original Vietnamese text and incomplete/stale source coverage.
  Selecting Last 24 hours on Home retained that window in the MSR count link and
  destination. Applying MSR manually in Community, then changing its window,
  retained the applied filter. Screenshot: `community-window-filter-after.jpg`.
- Watchlist PNJ: three unreviewed items became two only after an explicit review;
  reload retained membership, two unreviewed and review timestamp on isolated origin.
- Refresh proof: only one existing derivative row was temporarily omitted from
  the isolated cache, then the original cache JSON restored. The already-open
  Market page gained its real headline without reload/navigation/server restart.
  Raw article content/publication dates were untouched. Hook tests also verify
  changed snapshot refresh retains 24-row depth and aborts obsolete requests.

## Independent final review

Two parallel read-only reviews used the repository code-review skill, pinned base
135a31fa and the local feature checkpoint. Standards and Spec both passed after
three focused corrections: stale/unavailable index evidence must select an uncertain
mascot; compact Attention must visibly identify fixture-containing samples and
label individual fixture evidence; count/theme links must preserve the selected
Community window. A follow-up check caught a component remount that cleared a
manually applied ticker when switching windows; it was corrected and browser-tested.
Three regression tests cover actual compact fixture rendering and window-to-API
navigation, window canonicalization, and actual hero stale/fresh/unavailable mascot
states. No outstanding findings in either review axis; no unrelated refactoring.

Screenshots: `home-before.jpg`, `home-after-dark-en.jpg`,
`home-after-light-vi.jpg`, `home-mobile-light-vi.jpg`, `news-market-after.jpg`,
`news-mobile-light-vi.jpg`, `news-mobile-dark-en.jpg`, `watchlist-after.jpg`,
`acb-mobile-light-vi.jpg`, `community-mobile-dark-en.jpg`.

## Limits and safe next action

No new sentiment/impact inference, collector freshness guarantee, classification
expansion, live Dividend integration or EOD coverage. Actual upstream photo errors
still hide primary illustrated cards by the owner's existing policy. Ticker
relationships retain the existing backend evidence quality; this frontend does
not independently qualify incidental currency-like ticker matches. API 200 alone
was not treated as proof of freshness. Zero is fixture-validated, not a newly
observed real-source Sunday value. Runtime source remains canonical base135.

Generated Next dev AGENTS/CLAUDE files and next-env bytes were preserved in external
`next-generated/`; generated notes are excluded from the checkpoint. Production
build restored next-env to its tracked baseline. No existing WIP was discarded.

Push readiness requires owner's approval and a fresh ancestry/remote check.
Next safe action: owner review of this local UI checkpoint, followed by authorized
main integration. Evidence supports improved scanability: one photo/headline/source
row rather than nested reports, three compact quote chips, a numeric-first hero,
and one concise activity sample; uncertainty and original evidence remain visible
or directly inspectable. No usability-study or investor-outcome claim is made.
