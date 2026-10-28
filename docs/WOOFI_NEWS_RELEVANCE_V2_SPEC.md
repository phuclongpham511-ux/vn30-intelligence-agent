# News relevance and stock research UX V2

Baseline: `12fff386a8138ac33d5f2b29fe1804ea574caa94`. Development only;
canonical runtime and Downloads WIP are outside this change.

## Implementation plan and acceptance contract

1. Audit a consistent archived product snapshot, separating fetch receipt,
   publication, first persistence and displayed freshness. Keep exact exclusion
   reasons and per-category October 9–11 counts in the validation artifacts.
2. Remove image-only eligibility from research projections and reads. Keep
   Vietnam/finance classification, 72-hour age, independent-publisher Hot gate,
   deterministic representative, source images and snapshot pagination. Broken
   images remove only the image. Polling/ownership/cooldowns remain unchanged.
3. Retain bounded publisher-supplied feed summary/content as additive immutable
   text receipts, bound to article identity, exact title and canonical URL. Resolve
   whole-token legal identities/verified aliases and explicit stock context
   against listed equities. Body evidence is sentence-scoped; currency and
   ecosystem mentions alone abstain. No new article-page crawler or upstream
   requests. Proofs identify evidence origin, text excerpt and receipt hash.
   HTTP uses worker-built proofs; a policy version invalidates old projections.
4. Render one representative headline linking directly to the publisher, with
   attribution/date and qualified ticker chips using existing batched SSI demand.
   No primary Evidence action/report count; inspectable detail route remains.
5. Replace Home Investor Attention with at most three recent qualified company
   or market news highlights. Order by publication, use no sentiment/importance
   score, exclude raw forum posts. Explain eligibility in secondary disclosure;
   preserve Community navigation/pipeline and restrained empty/error states.
6. Make Watchlist ticker-first: cached quote, one stock link, concise unread
   headlines and discussion titles. Keep every loaded unread item visible,
   independent explicit per-item review behind one Review & evidence disclosure,
   correction-aware local receipts, source freshness and Technical assurance.
   Quiet sections collapse; followed quiet stocks remain visible.
7. Validate isolated persisted data, label newly fetched feed metadata LIVE_SOURCE
   and deterministic replay/fixtures separately. Run focused/full backend,
   frontend tests, typecheck, build, API contracts and browser desktop/mobile,
   EN/VI and themes. Save before/after screenshots. Independent Standards and
   Spec reviews must resolve P1/P2 before the final clean local checkpoint.

No D1/D4/D5, Technical EOD policy, credential management, collector scheduling,
FPT automation, runtime ownership, push, deployment or live database changes.
