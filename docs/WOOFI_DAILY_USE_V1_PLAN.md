# Daily use V1: Read first in Watchlist

Base: origin/main `eb6125490125a5180f1bcc795024f9a541814a01`.
Research: WOOFI_DAILY_ATTENTION_COMPETITIVE_RESEARCH_V1.md, 2026-10-16.

## Existing product and verified gap

Home already contains SSI market context, Hot Topics (independent publishers),
Market Focus and Investor Attention. News preserves Story dedup and qualified
issuer links. Watchlist provides exact matched News/Community plus PROVISIONAL
Technical, source health, explicit browser-local receipts and corrections.
Stock Detail supplies research tabs. No replacement of those products is needed.

Audit of `frontend/app/watchlist/page.tsx` found ticker-first rows ordered by
unread count, but no cross-ticker reading queue; all loaded unread items appear in
each stock. Explicit review and evidence require opening a per-stock disclosure.
The actual canonical browser has an empty Watchlist; populated workflow findings
come from code/spec inspection, not a fabricated live personal portfolio.

## Selected vertical slice

“Read first” in the current Watchlist, above full stock rows. Maximum three
unreviewed News/Community identities from the loaded page, ordered by original
publication time (fallback occurrence time explicitly labelled), then identity.
One shared Story is one reading item, with all matching followed ticker links.
Show source name, original time, News vs unverified Community, correction status,
and a brief deterministic reason: reporting/discussion involving followed stocks.
This is a reading order, not an importance ranking or investment recommendation.

Reuse current `loadIntelligence`, `isUnread`, `reviewUpdates`, browser storage and
source diagnostics. No additional HTTP request, backend calculation, migration,
provider or collector. Existing full rows, pagination and Technical stay intact.
No opening/navigation/refresh changes receipts. One explicit review acknowledges
only the displayed revision for each represented ticker; other stocks and hidden
items are untouched. Shared stories may remain unread for a stock reviewed
separately; membership comes from the existing verified read projection.

## Honest states and constraints

- Unreviewed does not mean newly published or important. Dates remain visible.
- Source overdue/error/unknown is visible; persisted items never imply a live read.
- Missing source attribution or inconsistent shared evidence is withheld from the
  brief, with incomplete coverage, and remains inspectable in full stock rows.
- Quiet means no eligible unreviewed News/Community in the loaded page, not no
  market activity. A failed response or unreadable review storage is unknown.
- At most three, including zero; no invented filler. More results and quiet stocks
  remain in the existing list. Technical evidence is not re-ranked as news.
- No financial calculations, sentiment, AI prose or D1/D4/D5 changes.

## Rejected alternatives

New Home briefing/dashboard duplicates Market Focus; since-last-visit timestamps
would conflate navigation with explicit review; daily email/alerts require new
delivery infrastructure; cross-source topic generation duplicates Story/theme
grouping; importance scoring lacks a validated contract. A contextual reading queue
reuses established evidence and solves the narrow scanning problem directly.

## Acceptance

Fixtures prove A new evidence, B return unchanged, C publisher recheck, D known
correction, E stale/missing sources, F several stocks with a quiet stock. Verify
cross-stock identity dedup, source/date preservation, deterministic three-item
limit, explicit receipt persistence and storage failure. Test EN/VI and responsive
wrapping, light/dark, original URLs and stock links. Separate fixture, persisted
and live-source results. No claim of measured user time savings.

Focused tests plus frontend regression/typecheck/production build; bounded browser
acceptance subject to tool approval. No retry of previously denied preview commands
or launcher substitutions. One conditional production cutover after exact SHA,
fresh ownership/integrity/FK/online-backup and rollback gates, via documented
Supervisor controls. Pilot OFF and legacy FPT PAUSED. Never replace newer live data.

## Risks

Loaded pages are bounded, not a complete global feed. News/Community have partial
coverage and no authoritative retraction ledger. Browser-only review has no
cross-device sync. An unavailable feed must not become a quiet result. Runtime
ownership or graceful-stop failure blocks deployment, independent of UI readiness.

## Implementation checkpoint and release gate

Implemented the read queue in `WatchlistBriefing.tsx` with a pure presentation
projection and explicit review helper in `dailyBriefing.ts`. Added source/evidence
anchors to existing Watchlist; no new route or request. Eight new tests exercise
all six scenarios, cross-ticker dedup/three-item ordering, exact review scope,
concurrent receipts, unavailable storage and EN/VI server-rendered markup.

2026-10-16 automated validation: frontend 156 PASS / 0 FAIL / 1 pre-existing
optional persisted Stock Detail replay SKIP; typecheck PASS. The initial focused
run found a test expectation incorrectly requiring English “Fixture” in Vietnamese;
corrected it to assert the existing Vietnamese “Dữ liệu mẫu” label, then ran the
full frontend regression. No application behavior was changed to satisfy that test.
Production `npm run build -- --webpack` PASS, including the existing Watchlist
route and proxies. Build completion is not interactive browser acceptance.

One focused self-review checked the projection against the interaction contract:
no acquisition, immutable inputs, namespaced identity, per-ticker review fencing,
original evidence/time, explicit missing states, no numerical/Technical changes.
No blocking product correctness finding remains in this bounded review; interactive
visual/navigation acceptance is still outstanding. Main integration is deferred
with deployment, rather than treating the runtime gate failure as a product defect.

Canonical SELECT-only API replay at 07:06:41 UTC used persisted FPT/PNJ/VCB
evidence and synthetic in-memory membership/review. Four eligible identities,
three shown; reviewing one left three. Original publication times (October 13–14)
stayed separate from October 16 source-poll and response times. This was not a live
publisher read or a real user's browser acknowledgment. API contracts unchanged.

Browser acceptance of the new UI, desktop/mobile and theme screenshots remains
NOT_VERIFIED. Existing canonical empty Watchlist was directly observed. No old
policy-denied preview command was retried, and no alternative preview server ran.

**Production release blocked:** the initial native ownership audit timed out in
the critical Windows listeners probe (15 seconds). Subsequent bounded read-only
inspection at 07:09:04 UTC found recorded Supervisor PID 20116 absent, while desired
intent remains true. All 14 recorded service members matched PID/creation/executable;
listeners 3000/8000 belonged to recorded frontend/backend; exactly one Collector
execution root (venv redirector 21080 → native 22612), mutex owner 22612. Product DB
holders were backend 30516 and collector 22612, with no unexpected candidate.
Root cause of Supervisor exit is NOT_VERIFIED and outside this product slice.

Runtime pin/HEAD remain `d2c44fb6289623cb682266ea471fb7fece5f9351`; Technical
Pilot OFF, legacy FPT PAUSED, credential references available. SQLite read-only
integrity and FK checks passed at 06:59:46 UTC. No lifecycle controls, config,
ownership, credentials or database changes were made. No cutover attempted; no
deployment backup/rollback action needed. Preserve the running services and use a
separately scoped operational assessment before release. Source checkpoint is
resumable; do not infer deployment success from its build/test results.
