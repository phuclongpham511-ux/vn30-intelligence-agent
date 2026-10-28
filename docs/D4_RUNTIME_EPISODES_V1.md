# D4 runtime episode integration V1

Public seam: `src.materiality.evaluate_d4_market_events(snapshot, ticker, session,
generated_at=..., contexts=..., corporate_actions=..., previous_evaluation=...)`.
Input source/completion/calendar contracts are unchanged from
`docs/D1_FACTUAL_RUNTIME_V1.md`. No provider calls, browser state, ranking,
delivery, Daily Signal Packet or official calibration are introduced.

## Factual stream and lifecycle

The runtime reconstructs every declared calendar session through the evaluated
session with the existing `prepare_d1_evidence`. Price/volume existence comes
only from D1 V1, never broad V0 candidates. MA/RSI consume the same existing
analytics and exact `transition_inputs` boundary predicates. An unresolved
decision remains separate from a verified negative.

`src/analytics/episodes.py` is extracted from the benchmark lifecycle helper;
the benchmark facade preserves its default output, IDs and contract. Explicit
runtime policy `d4-episode-policy-v1` allows the first verified directional/HIGH
fact to anchor after unresolved minimum-history warm-up when no factual regime
has yet been established. This adaptation is restricted to the V1 path; it does
not join later facts across gaps in an established episode.

- Price: same-direction consecutive factual positives continue; verified normal
  closes; opposite direction closes and anchors a different episode. A valid
  zero-return/q95-zero fact remains neutral and has no directional D4 anchor.
- Volume: consecutive HIGH facts continue; verified normal closes; re-entry
  creates a new anchor. Genuine zero/q95-zero can participate in this HIGH
  predicate, without manufacturing positive shares volume.
- MA: verified cross anchors the directional regime; same ordering continues
  without another cross event; reversal closes/anchors. Equality/ambiguous
  ordering remains unresolved under the existing helper, not a fabricated cross.
- RSI: upper/lower entries anchor; persistent regimes continue without duplicate
  events; verified exits close; later entry anchors anew. Missing evidence is not
  an exit. If a verified new transition follows an unresolved prior episode, it
  can establish a new anchor without inventing the earlier episode's close date;
  the unresolved prior identity/reason remains inspectable.
- Bollinger stays a discrete event with `NOT_APPLICABLE` episode relationship,
  null episode family/ID and an explicit unapproved-policy reason. Its D1 volume
  confirmation, positive-volume pattern rule and price conditions are unchanged.

Continuity uses neighbors in the supplied verified trading-session calendar,
not calendar-day distances. Calendar-declared closures do not break continuity.
Missing/invalid expected sessions never count as normal observations. Unresolved
continuity gives no known episode ID/anchor, does not close or bridge an episode,
and retains the earlier unresolved episode reference where one was established.
After a verified negative resolves the current condition, a later re-entry can
anchor without backdating a closure inside the prior gap.

## Typed result and identities

`D4MarketEvaluation` provides current `factual_decisions`, individual `events`,
four current `episode_states`, chronological `episode_history`, `evaluation_id`,
optional `supersedes_evaluation_id` and typed `revisions`. `results` exposes the
unchanged current scores for compatibility.

An event ID is a semantic digest of ticker/family/session, distinct from the
episode ID's instrument/family/verified anchor/direction digest. Repeated factual
events retain individual IDs and evidence even when sharing an episode. Source
adjusted values alone never define semantic identity. Instrument identity in this
slice is the supplied ticker; historical ticker-renaming reconciliation is not
inferred. Each event carries its factual evidence reference, episode relationship,
anchor where established, continuity references, provenance and policy version.
Continuing regime state remains visible on days without a newly emitted event.

## Restart, revisions and persistence limits

Reconstruction is a pure deterministic replay over the supplied source snapshot.
It requires no new database table, mutable process checkpoint or frontend state.
The same as-of source/calendar input reconstructs identical events/episodes after
restart. Caller-supplied history scope matters: truncated history cannot invent
missing anchors. The straightforward reconstruction repeats D1 over prefixes;
this is a correctness-first backend seam, not a deployed bulk refresh worker.

Evaluation identity hashes the full factual-reference/lifecycle inventory. A
correction therefore produces a distinct evaluation even if the provider fails
to change its version label. Semantic event IDs survive evidence revisions;
changed anchors/relationships are explicit. Optional `previous_evaluation` must
match ticker/session and returns a supersedes link plus evidence-versus-relationship
revision reasons with before/after states. Original results are not mutated or
aliased to subsequently changed input provenance.

There is no automatic durable evaluation archive in this milestone. The caller
must retain previous versioned evaluations/evidence to compare them later. A
fresh query of changed SSI history cannot reconstruct a lost prior vendor vintage.
This implementation does not grant source storage rights or claim official PIT
admissibility. It never overwrites the existing immutable TechnicalContextHistory
record; reusing the same semantic event ID for changed evidence would still be
rejected by that existing mechanism. A future consumer must retain evaluation
versions separately rather than bypassing its immutability checks.

## Scoring and context

D1 candidates and D4 relationships are established before the existing scoring
and post-score corporate-action enrichment. Significance, Novelty, Confidence,
Base Materiality and midrank mappings remain unchanged. Existing EventMemory's
calendar-day last-event recurrence is not episode lifecycle. D4 does not populate
or replace `days_since_similar_event`, invent exposure history or alter its V0
Novelty formula; scoring still uses explicitly supplied recurrence context.
Corporate-action metadata cannot create/close/change an episode or factual event.

Tests: `tests/test_d4_runtime.py` exercises the public seam, synthetic exact
indicator boundaries, continuity, correction, source isolation and fresh-process
reconstruction. Existing D1/benchmark/replay/scoring/Bollinger/action tests remain
intact. No protected cases or labels are used.
