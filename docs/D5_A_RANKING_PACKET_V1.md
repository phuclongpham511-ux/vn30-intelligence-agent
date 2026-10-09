# D5-A ranking and Technical Daily Signal Packet V1

This backend-only slice implements the owner's D5-A instruction over D1/D4 V1.
It does not activate official Materiality calibration or the PIT benchmark.
No routes, database, worker, Watchlist, frontend or notifications are introduced.

## Public seam and caller obligations

```python
from src.materiality import evaluate_d4_market_events, build_technical_daily_packet

evaluation = evaluate_d4_market_events(
    snapshot, ticker, session, generated_at=evaluation_as_of,
    contexts=existing_v0_contexts, corporate_actions=existing_repository,
)
packet = build_technical_daily_packet(evaluation, generated_at=generation_time)
json_text = packet.to_json()
```

D5 consumes a typed `D4MarketEvaluation`, without rerunning D1, indicators,
episodes or scoring. The input source/calendar/completion/visibility contract is
unchanged from [D1 runtime](D1_FACTUAL_RUNTIME_V1.md) and
[D4 runtime](D4_RUNTIME_EPISODES_V1.md). Source data is caller-supplied; neither
function fetches data or establishes a complete exchange calendar.

`evaluation_as_of` must be an explicit aware upstream timestamp. Generation must
be aware and no earlier than that timestamp. Only sessions before its Vietnam
calendar date are admitted, matching existing completed-daily policy. Supplying
a later generation time cannot introduce later source or CA knowledge. Legacy
V0/unbound D4 objects, noncanonical D1 predicates, unknown transition/pattern
versions, future factual cutoffs and unsupported score versions are rejected.
Missing family checks remain unresolved; unknown scores remain null.

D3's benchmark `CONTROLLED_AS_IF_EMPTY` is not claimed as a real user's delivery
history. The runtime constructs no exposure ledger. The consumer supplies existing
cutoff-safe factual recurrence contexts; regeneration neither resets Novelty nor
records a delivery in EventMemory.

## Additive D4 compatibility adaptation

`D4MarketEvaluation` now records `evaluation_as_of`, `data_provenance`,
`is_fixture`, `pattern_decisions` and `indicator_check_reasons` with defaults for
construction compatibility. Old D4 objects without a knowledge timestamp must
be evaluated through the existing runtime before D5 consumption.

The original four factual dictionaries, event candidates/scores, episode IDs,
history/revision logic and evaluation-ID formula are unchanged. The added
Bollinger checks use the same prepared native indicators and detector candidates:

- A confirmed event from the unchanged detector establishes EXISTS.
- A resolved negative D1 volume gate, genuine zero confirmation volume or
  zero-width current bands establishes DOES_NOT_EXIST for the conjunction.
- Unresolved volume, missing indicator pair/warm-up or an incomplete possible
  three-observation touch window remains UNRESOLVED.
- Complete inputs without an emitted confirmed pattern establish DOES_NOT_EXIST.

The conservative negative check can remain unresolved where a more elaborate
short-circuit analysis might prove a negative. It never fabricates a positive.
Indicator observations and their digest plus the common volume decision reference
are retained. This is not another Bollinger detector or episode policy. MA/RSI
diagnostics distinguish warm-up from missing native source/consecutive evidence
without changing the frozen transition truth or D4 identity.

## Eligibility and inventory

Only matching ticker/session observations enter `all_current_session_events`.
Prior events and other tickers do not re-enter the stock-day. Approved identifiers:

- `abnormal_price_move`, `unusual_volume`: canonical current D1 EXISTS.
- `ma_cross`, `rsi_regime_entry`: verified current transition EXISTS, with an
  actual emitted transition candidate; persistent ordering/regime is not an event.
- `bollinger_lower_reversal_volume`, `bollinger_upper_reversal_volume`: confirmed
  upstream pattern, shared D1 volume EXISTS and separate positive-volume evidence.

References and candidate scope/type must agree with upstream checks. A CLOSED
lifecycle is not promoted to a new event. Current factual events with established
continuation or unresolved episode continuity remain eligible, preserving those
limitations. Bollinger retains NOT_APPLICABLE episode metadata.

Fixture, missing evidence and incompatible/excluded candidates remain inspectable
in inventory with explicit ineligibility reasons. Duplicate current event IDs fail
instead of silently erasing one. Missing significance excludes an event from V0
scoring but does **not** exclude its verified fact from D5 ranking.

Each event preserves factual/episode IDs, anchor, continuity, prior unresolved and
closed links, source evidence, normalized scoring inputs, S/N/C/Base V0, V0
exclusions/reasons, CA context and ranking position. A shared BB/volume reference
means reused evidence, not independent observations. Distinct events stay distinct;
no extra score channel, independent-volume credit or grouping engine is added.

## Ranking and budget

Ranking version: `d5-a-base-s-n-c-type-id-v1`.

Lexicographic comparator: Base V0 descending, Significance V0 descending, Novelty
V0 descending, Confidence V0 descending, event type ascending, event ID ascending.
At **each** numerical component every finite observed value (including genuine
zero) sorts before missing; missing stays null. A missing Base can still be ordered
by subsequent observed components. Invalid/nonfinite/out-of-range scores fail.
No rounding, approximate equality, alternate scoring formula or display threshold
is introduced. This is provisional ordering, not official calibration.

Delivery version: `d5-attention-budget-3-v1`. The complete eligible set is ranked.
Top insights contain its first zero to three events; every remaining eligible ID
is retained in overflow, with no Top-3 exposure claim, filler or required alert.
Every event has `required_delivery = no` with the approved delivery-policy version.
Scores and episode relationships are consumed unchanged, including caller-supplied
recurrence penalties. CA context never participates in this comparator.

## Completeness and empty states

Six typed required family checks retain truth, reason codes, evidence/references,
applicability, fixture flag and **separate delivery completeness**. A missing valid
emission for a positive factual check marks delivery incomplete without rewriting
EXISTS into a factual negative. Original truth/evidence remains inspectable.
No V1 family is silently marked not applicable to avoid a data failure.

- `HAS_INSIGHTS`: at least one eligible event. Additional unresolved family or
  episode evidence remains visible; partial usefulness is not full completeness.
- `NO_MEANINGFUL_TECHNICAL_CHANGE`: zero eligible events, all required checks
  resolved and delivery complete, with no positive factual event missing.
- `TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE`: zero eligible events and at least
  one unresolved family or delivery-completeness discrepancy.

`unresolved_checks` lists affected families, including delivery gaps. Typed check
truth and reasons explain which kind of incompleteness applies. No-change is not
an investment recommendation. Missing score channels alone do not erase a fact.

## Packet identity and serialization

The frozen Pydantic `TechnicalDailySignalPacket` provides ticker/session,
generation and evaluation timestamps, full SHA-256 packet evaluation identity,
upstream evaluation identity, runtime/predicate/episode/score/ranking/delivery
versions, state, family checks, full current inventory, complete ranked IDs,
Top 3, overflow, unresolved checks, provenance and limitations.

`to_json()` uses explicit JSON-mode dates/enums/nulls, sorted keys, compact
separators, UTF-8 semantic encoding and rejects NaN/Infinity. Evidence mappings
are deep-copied from upstream and CA models copied deeply, so subsequent upstream
mutation does not alter the packet. Frozen model fields prevent reassignment;
nested raw evidence mappings follow existing model conventions and must be treated
as read-only by consumers. Use JSON/model dumps to hand data to external consumers.

Packet ID hashes a namespaced canonical packet excluding `generated_at` and the
ID itself. Identical knowledge, events, scores, histories and policy inputs yield
the same semantic ID even when merely generated later. `evaluation_as_of` is
included because it identifies the actual supplied knowledge state. Changed
evidence, scoring inputs or contextual CA payloads yield a different packet
evaluation ID while semantic event and episode identities remain separate.
Inventory, ranking and diagnostics are ordered deterministically, independent of
input iteration and Python hash randomization.

## Verification and boundaries

`tests/test_d5_packet.py` exercises the public D1 → D4 → D5 seam with generated
synthetic ordinary evidence and separate fixture-exclusion coverage. It covers
all comparator levels, missing scores, exact ties, tiny unequal floats, 0–5
event budgets, overflow, negatives/unresolved data, transitions/persistence,
Bollinger shared evidence, continuation/gaps, CA cutoff isolation, source prefix
invariance, input mutation, explicit versions/JSON and fresh process/hash seeds.

Existing D1/D4, benchmark, scoring, Bollinger, historical evaluation and CA tests
remain regression requirements. No protected historical cases or labels are used.

Validation at this checkpoint (2026-10-08), using the reconciled worktree's Python:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_d5_packet.py -q
.venv/Scripts/python.exe -m pytest tests/test_d5_packet.py tests/test_d4_runtime.py tests/test_d1_runtime.py tests/test_technical_benchmark.py tests/test_materiality.py tests/test_bollinger.py tests/test_historical_evaluation.py tests/test_corporate_action_context.py tests/test_corporate_action_edges.py tests/test_corporate_action_curated.py tests/test_corporate_action_history.py tests/test_corporate_action_replay.py tests/test_corporate_action_study.py -q
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m scripts.check_technical_identity
git diff --check
```

The related regression command passed 300 tests before four additional D5 tests
were added. The final full backend suite passed 815 tests (767 pre-existing plus
48 D5 cases), including those additions and the corrected input-order test fixture.
The final focused D5 suite passed 48 tests. Identity guard passed across nine files;
diff and milestone-file whitespace checks passed. Pytest reports one existing
Starlette/httpx deprecation warning. Initial red runs exposed the absent public
seam and fixture setup errors (changing the evaluated date when reversing a
calendar, using an immediate missing prior price instead of a later resolvable
current fact, and an insufficient return for the five-event case); the source
fixtures were corrected without lowering the assertions or changing D1 predicates.

Git safety: branch `codex/technical-development-reconciled`, HEAD
`e64986e0cb011d8af40a122e14d5bb47f540ba22` unchanged. Initial status was 15
modified tracked files and 52 untracked files; final status is 15 and 55, index
empty. Of 67 pre-existing dirty files, 65 retained their exact byte hashes.
Only `src/materiality/__init__.py` (exports) and the untracked
`src/materiality/episodes.py` (additive upstream delivery evidence) changed.
New files: delivery module, D5 tests and this report. No original Downloads
repository, credentials, unrelated WIP, staging, commits or pushes were touched.

D5-B still needs a narrowly scoped completed-EOD consumer with verified source/
calendar evidence and explicit V0 contexts; no bare provider response proves that
contract. Versioned storage/caching and any HTTP/UI integration require that next
slice. SSI historical-vintage certification and official calibration remain
separate constraints; the packet does not remove those limits.
