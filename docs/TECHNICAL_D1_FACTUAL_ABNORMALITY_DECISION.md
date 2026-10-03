# D1 — Technical Factual Abnormality V1

Date: 2026-10-03. **D1 — APPROVED** by the project owner through the supplied D1 instruction. This is a documentation/governance decision, not an implementation or benchmark authorization.

Authority: [Evaluation Contract V2](TECHNICAL_MATERIALITY_EVALUATION_CONTRACT_V2.md), [Benchmark Spec](TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md), [Annotation Handbook](TECHNICAL_ANNOTATION_HANDBOOK_V1.md). This decision supplies the previously missing price/volume factual predicates required by Contract V2 §2. It does not change that contract's severity, safety, ranking or delivery metrics.

## 1. Purpose

D1 answers only: **“Did the defined abnormal technical condition factually occur?”** It defines prospective reference existence for `abnormal_price_move` and `unusual_volume`, independently of existing detector emissions. Existing broad observation candidates, replay types, scores and human labels are unchanged; their names do not establish D1 existence retrospectively.

The 95th percentile is an **approved operational factual predicate V1**. It is not learned, a severity/display threshold, a probability, or a universal market truth. Do not tune it against V1/V2/V3 labels or future assessment outcomes.

## 2. Approved price predicate

Let `r_t` be the comparable daily stock return in fractional units and `x_t = abs(r_t)`. For valid comparable prior daily returns, use their absolute values to form history H under §4. Let `q95(H)` be the empirical quantile defined in §9.

- Sufficient valid current/history evidence and `abs(r_t) >= q95(H)`: **EXISTS**.
- Sufficient valid evidence and `abs(r_t) < q95(H)`: **DOES_NOT_EXIST**.
- Insufficient or invalid required comparable current/history evidence: **UNRESOLVED**; do not evaluate a substitute threshold.

Preserve signed raw return and direction separately: up for positive return, down for negative return. Direction does not affect existence. For a valid exactly zero return, retain its factual zero/neutral state rather than fabricating up/down; do not introduce a positive-return-magnitude floor to defeat equality. Any later schema adaptation must preserve that fact without rewriting existing candidate directions.

Daily return requires a valid comparable prior/current price pair. The existing simple fractional return definition may be reused with its version/provenance. A multi-session gap cannot silently become a valid daily return; D2 still governs session continuity and adjustment validity.

## 3. Approved volume predicate

V1 covers unusually **HIGH** daily trading volume only. Let `v_t` be current comparable daily shares volume and H the prior comparable daily volumes under §4.

- Sufficient valid current/history evidence and `v_t >= q95(H)`: **EXISTS**.
- Sufficient valid evidence and `v_t < q95(H)`: **DOES_NOT_EXIST** for this high-volume predicate.
- Insufficient or invalid required comparable current/history evidence: **UNRESOLVED**.

Low-volume abnormality is out of scope, not an additional negative-tail event family. A low current volume with sufficient valid history is a known negative for the high-volume check; no claim is made about whether it is abnormally low. Price movement cannot manufacture a volume event. Relative volume, z-score and price support remain inspectable context; they are not additional D1 eligibility gates.

## 4. Historical-window rules

For each family independently, take the most recent **up to 252 valid comparable trading-session observations strictly before the current session**, within the authorized PIT source/history scope. Require at least **60** such observations. Each session contributes at most one comparable value. Exclude current and future observations before forming H or computing its quantile. Price H contains valid absolute daily returns, not raw closes; volume H contains comparable daily shares volume.

Validity must follow the separately approved D2 source/session/adjustment policy. Never silently skip corrupt values to manufacture sufficient history: preserve selected session IDs, excluded observations and reasons, actual count and endpoints. If validity/comparability of required evidence cannot be established, return UNRESOLVED. Missing benchmark data alone is not a reason to invalidate an otherwise fully evidenced D1 own-history check.

This approved D1 window is expressed in **valid observations**. Existing `build_context` slices the previous configured session-feature records before filtering missing values. That stored V0 context population is not automatically the same population as the D1 last-valid-observation window. Preserve both definitions and values; no legacy context is recomputed or overwritten. Do not extend a search beyond the authorized source history to reach 60 or 252. Warmup, authorization, availability and gaps remain D2 responsibilities.

## 5. Exact existence enums

Use the existing sidecar enum spelling; uppercase denotes the same human-facing state:

| Machine value | Display | Meaning |
|---|---|---|
| `exists` | EXISTS | Required evidence valid and current value at or above q95 |
| `does_not_exist` | DOES_NOT_EXIST | Required evidence valid and current value below q95 |
| `unresolved` | UNRESOLVED | Required evidence insufficient/invalid; factual truth not established |

Keep applicability/exclusion reasons separately. `unannotated` remains a workflow status, not a fourth existence truth. Existence is not attention 0–3 or approve/reject/modify. A known negative has no event severity label under the prospective handbook; an unresolved opportunity must not become a negative.

## 6. Missing-data behavior

**UNRESOLVED != DOES_NOT_EXIST.** Reasons include fewer than 60 valid observations, missing current value, missing comparable prior close, non-finite values, non-comparable units/source/session, invalid trading evidence, or unresolved adjustment semantics that make the comparison invalid. Preserve original values/provenance and reason codes. Null, invalid or unknown evidence must never be replaced by zero, normal, false or attention 0.

Zero may be a genuinely observed valid quantity; it is never a missing-data fallback. Whether a zero-volume row is a genuine trading observation, a suspension or a provider placeholder is a D2 validity matter, not resolved here. Invalid evidence must not be admitted merely because the existing midrank helper only filters `None`.

## 7. Market-relative boundary

Market-relative evidence does **not** determine price existence. A large market-aligned raw move can satisfy D1. Strong excess return alone cannot satisfy D1 when absolute own-history price magnitude is below q95. Preserve benchmark return, signed excess and market-relative abnormality, where available, for later severity, attribution/context, ranking and diagnostics.

Missing benchmark context stays null and does not itself turn a fully evidenced own-history positive/negative into UNRESOLVED. Missing required own-history data does require UNRESOLVED even if market evidence is strong. Price/excess evidence likewise cannot create unusual-volume existence.

## 8. Separation from severity/ranking

| Layer | Separate question |
|---|---|
| D1 factual existence | Did the defined abnormal condition occur? |
| Intrinsic severity | How important is the event intrinsically? |
| Contextual relevance | How useful is it now? |
| Ranking | Which event deserves attention first? |
| Attention Budget | Which zero to three insights should actually be shown? |

An EXISTS result does not mandate attention>=2, a rank, required delivery or a display slot. Recurrence does not change this factual predicate; it remains separate contextual evidence. Retention/safety and delivery policies remain governed by Contract V2 and unresolved D5. The existing severity 0–3 rubric is unchanged.

## 9. Reproducibility requirement

### Repository convention found

[`src/evaluation/context.py`](../src/evaluation/context.py) defines `percentile(current, prior, minimum, absolute)` as **empirical midrank**:

`rank(x; H) = (count(h < x) + 0.5 * count(h == x)) / n`.

It transforms price returns to absolute values, leaves volume untransformed, filters `None`, and returns null for insufficient history/current null. [`tests/test_historical_evaluation.py`](../tests/test_historical_evaluation.py) explicitly expects identical values to have rank 0.5. [`SECTION2_PHASE2_REPORT.md`](SECTION2_PHASE2_REPORT.md) documents the same convention. Read-only searches of `src/`, `scripts/`, `tests/` and `docs/` found no competing implemented inverse-quantile convention. Protected datasets and archived case outputs were not searched.

This function returns a **rank of a current value**, not a historical 95th-percentile cutoff. Testing its output against 0.95 would not preserve the owner's at-or-above rule under ties. Therefore it is retained unchanged for its existing context role, not reused as the D1 existence comparison. There are not two conflicting repository quantile implementations to choose between; the missing inverse-quantile definition is made explicit below.

### D1 deterministic convention: empirical inverse CDF / nearest rank

Version identifier: `d1-empirical-q95-nearest-rank-v1`.

For n valid historical values sorted nondecreasingly as `h_(1), …, h_(n)`:

`k = ceil(95*n/100)` using exact integer arithmetic; **`q95(H) = h_(k)`** (one-based index).

Equivalently, q95 is the smallest value whose empirical cumulative proportion is at least 0.95. Use the historical order statistic with **no interpolation**. Compare the current value directly with q95 using `>=`, including equality and ties; do not compare a midrank with 0.95. Do not round values or add a tolerance before comparison. Freeze numerical representation, source/calculation versions and exact evidence values in the future packet so display rounding cannot change the predicate.

This is the D1 documentation's explicit mechanical convention, not a claim that the existing project already implemented nearest-rank quantiles. It realizes the approved percentile threshold without inventing weights, searching labels or altering production. Threshold p=0.95 is fixed by owner approval; no alternative p/interpolation sweep is authorized.

Future packets must preserve predicate/convention version, family, current value/unit, signed price return, selected prior session/value IDs and availability, n, sorted-order index k, q95, validity/exclusion reasons and source/calculation hashes. D1 q95 must be named separately from legacy own-history midrank, with each population recorded. Reconstruction and prefix-invariance requirements remain in the Benchmark Spec; no generator or executable schema is implemented here.

## 10. Examples of edge conditions

These are analytical boundary examples only, not benchmark cases or human labels.

| Condition | Required interpretation |
|---|---|
| n=60 / n=252 valid priors | One-based q95 order index 57 / 240 respectively; current row excluded |
| Current equals q95, including a tied block | EXISTS; no strict-greater-than replacement and no midrank>=0.95 shortcut |
| Current below q95 with valid evidence | DOES_NOT_EXIST regardless of strong market-relative or supporting price evidence |
| Fewer than 60 priors / invalid current | UNRESOLVED, even if observed magnitude looks large |
| All valid priors equal c and current=c | EXISTS under the approved inclusive quantile rule, although midrank would be 0.5. This operational tie behavior does not assert intrinsic importance |
| q95=0 and current=0, both genuinely valid | Equality still qualifies. No hidden minimum magnitude/volume gate is added; zero validity/comparability remains D2, and zero raw return must not be labeled up or down |
| Current included would change the cutoff | Invalid reference construction; discard that comparison and rebuild under the approved exclusion rule before judging |
| Large raw move aligned with VN30 | Apply own-history predicate unchanged; retain alignment for later interpretation |
| Low observed volume below the high-tail q95 | Known negative for high-volume existence, not a label for low-volume abnormality |

Degenerate distributions may produce unintuitive existence results; these follow the approved inclusive predicate. Do not quietly repair them with a learned threshold or extra gate. Any future product revision requires a separate version and approval, without retroactive relabeling.

## 11. Non-goals

No benchmark sampling, labels, scoring, threshold tuning, production detector/scoring changes, candidate creation, V4/V5, protected Validation V1/V2 individual access, 2025–2026 holdout access or Final Validation. D1 does not approve D2–D7, a pilot, an implementation, or use of any new data. No frontend tests/build are needed for this documentation-only change.

## 12. Approval status

**D1 — APPROVED.** Product predicate approved by the project owner; deterministic percentile mechanics explicitly specified here under the instruction to define one reproducible convention. No conflicting inverse-quantile convention was found in the inspected source/documentation scope, and no D1 mechanical ambiguity remains. Repository midrank and D1 inverse quantile have distinct names and purposes.

D2 is the next blocker. D2–D6 remain unresolved blockers for benchmark generation; D7 remains later model-evaluation work. **Benchmark generation remains BLOCKED.** Stop at D1 documentation and consistency audit; do not proceed automatically to D2.
