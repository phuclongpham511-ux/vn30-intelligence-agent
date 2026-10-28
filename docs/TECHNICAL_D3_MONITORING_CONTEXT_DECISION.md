# D3 — Monitoring Task & Prior Exposure Policy V1

Status: **D3 — APPROVED** by the project owner. Scope: documentation only. Governing links: [Benchmark Spec](TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md), [Annotation Handbook](TECHNICAL_ANNOTATION_HANDBOOK_V1.md), [Design Audit](TECHNICAL_STOCK_DAY_DESIGN_AUDIT.md).

## 1. Monitoring task

Benchmark V1 represents **one user monitoring one stock at end of day**. The question is: **“What changed today in this stock that deserves my attention?”** Ranking scope is one ticker, one trading date, one EOD cutoff and the technical domain only.

Portfolio position, unrealized gain/loss, investment thesis, risk tolerance, personalized preferences, fundamentals, news and cross-stock ranking are out of scope. D3 introduces no new cutoff or factual predicate; the established D1/D2 rules continue to apply.

## 2. Prior user exposure

Use **`prior_exposure_mode = CONTROLLED_AS_IF_EMPTY`** for every Benchmark V1 group. This controlled scenario assumes that the user has not previously been shown technical insights by the system. It is not a factual claim about real user behavior.

No historical delivery or acknowledgement log is available in this scenario. Record the explicit controlled mode, rather than claiming an audited empty real-world ledger. Do not fabricate logs or infer “the user probably saw this yesterday.” Future audited exposure scenarios are outside D3 V1.

## 3. Market history is separate

PIT-safe previous RSI/MA state, prior abnormal-volume observations and factual recurrence evidence may be visible. These describe **market history**, not **user exposure history**. An earlier factual event does not establish that the user saw it. Preserve recurrence without deriving a delivery or acknowledgement record from it.

## 4. Today's factual changes

Only today's factual changes enter today's event set, under the approved event predicates. A prior event does not automatically re-enter today's set.

If an MA cross occurred yesterday and MA20 remains above MA50 today, today has no new `ma_cross` merely because that state continues. The previous crossing/state may supply context. A new transition requires the approved predicate to fire again. This rule does not resolve D4 episode boundaries or change existing predicates.

## 5. Exposure, novelty and relevance

No event is treated as already shown to the user. Do not reduce novelty or contextual relevance using assumed prior delivery. Factual recurrence may still inform the approved contextual judgment, independently of user exposure. D3 specifies no scoring formula, recurrence penalty or revised attention rubric.

Within-day duplication and episode interpretation remain governed by their existing, still-unresolved design decisions; controlled empty prior exposure does not make correlated current signals independent information.

## 6. Annotation and future packet requirements

The task/scenario record must explicitly identify the one-stock technical EOD task and `CONTROLLED_AS_IF_EMPTY`. Annotators may see cutoff-valid market history and recurrence, but no invented previous delivery/acknowledgement evidence. Treat real-world prior exposure as unassessed; do not confuse the controlled assumption with observed behavior.

The full opportunity inventory may include factual negatives and unresolved checks. The reference event set contains today's adjudicated factual changes; past events remain contextual links. No cases, packets or annotations are created by this document.

## 7. Readiness and stopping point

**D1 APPROVED; D2 APPROVED; D3 APPROVED; D4–D6 BLOCKING; D7 LATER. Benchmark generation remains BLOCKED.** This decision authorizes the D3 documentation update only. No dataset/case inspection, holdout access, scoring/evaluation, production changes or benchmark generation occurs. Stop after the lightweight documentation check; do not proceed to D4.
