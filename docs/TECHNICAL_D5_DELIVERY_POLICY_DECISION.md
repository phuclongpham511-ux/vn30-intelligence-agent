# D5 — Attention Budget, Empty State & Delivery Policy V1

Status: **D5 — APPROVED** by the project owner. Documentation only. Companion documents: [Benchmark Spec](TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md), [Annotation Handbook](TECHNICAL_ANNOTATION_HANDBOOK_V1.md), [Design Audit](TECHNICAL_STOCK_DAY_DESIGN_AUDIT.md).

## 1. Attention budget

Ordinary Technical V1 output has **maximum 3 insights per stock-day**. Ranking determines which useful insights occupy the available slots. If only one or two useful insights exist, show only those one or two. **No filler** to reach three. This policy introduces no numeric scoring/display threshold and does not change the human severity or contextual relevance rubric.

## 2. Empty states

| Evidence / reference condition | Ordinary output | Expected state |
|---|---|---|
| Usable evidence establishes useful technical change | 1–3 ranked insights, bounded by useful count | Nonempty technical response |
| Evidence is complete and no useful technical change exists | Zero insight cards | `NO_MEANINGFUL_TECHNICAL_CHANGE` |
| Evidence is insufficient or unresolved | Zero ordinary insight cards | `TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE` |

The last two states must never be merged. Missing evidence is not proof that nothing happened. An insufficient/unresolved evidence state cannot be presented as a complete no-change assessment, even when partial observations are available. Keep evidence/label completeness and missingness reasons explicit; no fabricated reference labels or ideal ordering.

## 3. Overflow

If more than three useful/material insights exist, preserve the **full reference insight set** and rank the complete eligible set. Ordinary UI shows only Top 3; items beyond slot 3 are overflow. Retain overflow for evaluation and capacity diagnostics, but give it **no ordinary Top-3 exposure credit**.

Do not lower human labels, erase reference members, or merge distinct changes merely because only three slots exist. Overflow here is retained assessment information, not a mandatory notification route. Ordinary display omissions remain observable in the relevant coverage metrics.

## 4. Required delivery

Technical Materiality V1 has **no hard required-delivery obligation**. For ordinary Technical V1 insights, record **`required_delivery = NO`** (machine sidecar value `no`) with this approved policy as the reason. This is a resolved policy, not an unresolved annotation judgment.

Intrinsic severity does not automatically imply mandatory delivery. In particular, **severity = 3** does not bypass the budget, force display, create an overflow alert, or create a push/email notification. Severity, contextual relevance, ranking and delivery remain separate.

Unknown factual existence/severity/relevance stays unknown; a policy-grounded delivery value NO does not convert it into no event or attention 0. Required-delivery metrics with no applicable positive obligations remain undefined/not applicable, not a perfect safety result. Retention and material/critical Top-3 coverage remain separate evaluation responsibilities.

## 5. Delivery surface

V1 evaluates only the **current EOD product response**. Push, email, SMS, urgent escalation, acknowledgement tracking, notification deadlines beyond that response and mandatory overflow routes are out of scope. Do not invent them. A future product policy version may add these obligations; it cannot silently change V1.

## 6. Readiness and stopping point

**D1 APPROVED; D2 APPROVED; D3 APPROVED; D4 APPROVED; D5 APPROVED; D6 BLOCKING; D7 LATER. Benchmark generation remains BLOCKED.** This decision changes D5 documentation only; D1–D4 semantics remain intact. No data/case inspection, holdout access, model/evaluation, production or source-code work occurs. Stop after one narrow documentation consistency check; do not proceed to D6.
