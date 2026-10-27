# Woofi News Experience V2

Development checkpoint, 27 October 2026. Supersedes the older four-tab News
navigation description. The canonical runtime has not been updated.

## Editorial News and independent Community

News contains only Industry, Company and Market publisher reporting. It no longer
mounts Community Pulse or exposes discussion filters/cards. The existing backend
research endpoint already reads NewsArticle/NewsStory and accepts only the three
editorial categories; Community has separate storage and APIs. The frontend also
withholds unknown/discussion categories and renders one row per Story identity.

`/community` hosts the existing CommunityPulse component. Existing Today/Last 24
hours, ticker filtering, source/fixture disclosures and error states are reused.
Watchlist and existing discussion links now use this destination. Old
`/news?view=community` bookmarks redirect with their ticker/window before reading
editorial data; publisher-only filters are not transferred. Stock Detail,
Community acquisition/storage and review identities are unchanged.

## Reading the feed

- A uniform, responsive list replaces the featured headline and two-column grid.
  Source headlines are preserved in full, with optional lazy source thumbnails.
- Existing backend chronological order and snapshot pagination remain authoritative.
  There is no new ranking, classification or importance score.
- Each item distinguishes the representative article's publication/first-seen time
  from the latest reporting within its Story. Rechecking a source never makes the
  report new. The feed shows its cutoff snapshot and Vietnam timezone.
- A source disclosure exposes independent publisher count, original article links,
  per-article publication/first-seen times and the existing source archive.
- Existing category/ticker/topic/sector/source filters, qualified ticker chips,
  Watchlist Company-News discovery, source freshness, retry and pagination remain.
  Failed refreshes retain loaded headlines and never present failure as no news.
- New product labels have EN/VI translations and use existing theme tokens.

The feed API has no general qualified summary field. No summary is generated or
borrowed from discussions. Classification and industry coverage remain partial;
source-count diversity is not corroboration of a claim.

## Validation

- Focused navigation/rendering/Community/archive tests: 42 passed.
- Full frontend suite: 361 passed, one existing skip, zero failures.
- Optimized webpack build and TypeScript typecheck: passed in an isolated source
  copy using existing dependencies, without copying environment/private data.
- All 16 pre-existing modified/untracked WIP files retain their original hashes.
- No provider/LLM calls, ingestion, financial calculations or runtime changes were
  made by this task. No deployment, push or merge.

Actual browser acceptance of this new development build remains pending. The
currently running pinned runtime serves its existing release and is not evidence
of acceptance of these source changes. Desktop/mobile and dark/light visual checks
should precede any separately authorized runtime update. The existing browser
scenario's Community destination assertion is updated but was not executed here.
