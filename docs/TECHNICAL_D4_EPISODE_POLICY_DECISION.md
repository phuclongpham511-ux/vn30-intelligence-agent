# D4 — Episode Continuity & Split Isolation Policy V1

Status: **D4 — APPROVED** by the project owner. Documentation only. Companion documents: [Benchmark Spec](TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md), [Annotation Handbook](TECHNICAL_ANNOTATION_HANDBOOK_V1.md), [Design Audit](TECHNICAL_STOCK_DAY_DESIGN_AUDIT.md).

## 1. Episode identity and lifecycle

An episode is one continuing change/state within the **same event family**, for the same instrument. Its anchor is the episode start. It continues while the same condition/state continues; it closes when that condition/state is confirmed ended. Re-entry after confirmed closure starts a new episode.

Unresolved continuity must not be silently bridged or closed. Record the relationship as **UNRESOLVED** and preserve the evidence gap. Do not use a fixed N-day gap rule. Episode identity and closure use cutoff-valid evidence; later facts cannot rewrite what was known earlier. Preserve original event identities and anchor/continuation/closure links.

## 2. Abnormal price move

Consecutive factual abnormal-price events with the same direction (up or down) belong to the same directional episode. A valid non-abnormal day closes it. A factual abnormal event in the opposite direction closes the previous episode and anchors a new one.

Missing or non-comparable evidence that prevents establishing continuity produces UNRESOLVED episode relationship. It does not establish a non-abnormal day, continued episode or confirmed closure.

## 3. Unusual volume

Consecutive factual **HIGH-volume** abnormal events belong to the same episode. A valid non-abnormal volume day closes it. A later factual high-volume re-entry anchors a new episode.

Missing/non-comparable continuity is UNRESOLVED. No low-volume episode is introduced.

## 4. MA cross

A factual upward MA cross anchors a bullish MA regime episode; a factual downward cross anchors a bearish MA regime episode. These names describe the observed MA ordering, not an investment recommendation.

While the same regime continues, it remains the same episode. Continuing MA ordering does not create another `ma_cross` each day. A reverse factual cross closes the previous regime episode and opens the opposite regime episode. Missing/ambiguous continuity remains UNRESOLVED; do not infer an unobserved reverse transition or closure.

## 5. RSI regime entry

An upper entry (`prior <= 70` and `current > 70`) anchors an upper episode. It continues while RSI remains above 70 and closes on a valid observation returning to `<= 70`. A later factual upper re-entry starts a new episode.

A lower entry (`prior >= 30` and `current < 30`) anchors a lower episode. It continues while RSI remains below 30 and closes on a valid observation returning to `>= 30`. A later factual lower re-entry starts a new episode.

Continuing within either regime is not another entry event. Missing/ambiguous continuity is UNRESOLVED, not a fabricated exit or re-entry.

## 6. Cross-family boundary

Episode identity is family-specific. Price and volume events on the same day do not automatically share an episode. Cross-family relationships may later support human insight grouping, but grouping must preserve separate D4 episode IDs and constituent event IDs. An insight is not synonymous with an episode.

## 7. Development / Fresh Validation isolation

One episode must not cross Development and Fresh Validation as independent assessment examples. If an episode crosses a planned boundary, **quarantine the affected episode/groups from Fresh Validation**. If continuity near the boundary is UNRESOLVED, quarantine affected groups from Fresh Validation too.

Do not treat later days of the same episode as fresh independent validation, move protected/reserved validation cases into development to preserve sample size, or substitute an arbitrary fixed-day embargo for episode isolation. Preserve whole-group membership and the quarantine reason. D6 still controls future allocation; no groups are selected here. Holdout protection is unchanged.

## 8. Readiness and stopping point

**D1 APPROVED; D2 APPROVED; D3 APPROVED; D4 APPROVED; D5 BLOCKING; D6 BLOCKING; D7 LATER. Benchmark generation remains BLOCKED.** D1–D3 semantics are unchanged. No datasets/historical cases, model/scoring/evaluation, production code, holdout, skills or agents are used in this task. Stop after the lightweight documentation consistency check; do not proceed to D5.
