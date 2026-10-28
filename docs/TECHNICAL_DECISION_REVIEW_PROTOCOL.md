# Technical D-Family Decision Review Protocol V1

Status: **V1 FORMALIZED** from the owner's supplied protocol. Documentation only; no D review, revision, benchmark generation or evaluation is performed or authorized here.

## 1. Purpose and current scope

D1–D6 are versioned research/product hypotheses and contracts, not permanent universal truths. This protocol asks: if development/pilot evidence shows a problem, which D should remain frozen and which D is justified to change? A bad model result alone MUST NOT justify changing D1–D6.

Current readiness: **D1–D6 APPROVED; D7 LATER MODEL-EVALUATION ACCEPTANCE; benchmark generation NOT AUTHORIZED**. See [approved D6 V1](TECHNICAL_D6_STUDY_REVIEWER_DECISION.md). Existing D1–D5 semantics remain unchanged. The lifecycle remains prospective pending separate development/pilot authorization and actual execution freezes; approved decisions alone do not establish completed frozen artifacts.

## 2. Common seven-dimension quality rubric

Every reviewed D uses the same seven dimensions and scale:

| Rating | Meaning |
|---|---|
| 3 — STRONG | Clear evidence supports the current decision |
| 2 — ACCEPTABLE | Operational and usable, with known limitations that are not materially damaging |
| 1 — WEAK | Systematic concern warrants further investigation or possible revision |
| 0 — FAILED | Materially incorrect, infeasible, inconsistent, unsafe, or demonstrably causes a major problem |
| N/A | Insufficient evidence to evaluate this dimension; not zero or a passing rating |

| Dimension | Review question | Evidence to examine |
|---|---|---|
| A. Clarity | Can independent people apply the decision with the same interpretation? | Ambiguity, contradictory rules, undefined terminology, edge conditions |
| B. Operationalizability | Can it be implemented and evaluated within permitted data, process and product scope? | Feasibility, required evidence availability, reproducibility, practical execution |
| C. Evidence Support | Does development/pilot evidence directly support keeping this decision? | Evidence about the decision itself; model performance alone does not establish support |
| D. Reliability | Is it applied consistently across cases, reviewers, stocks, dates and relevant conditions? | Reviewer consistency, reproducibility, systematic disagreement, unstable interpretation |
| E. Product Alignment | Does it still represent the product question and intended experience? | Product/task fit; do not optimize for benchmark convenience |
| F. Robustness | Does it behave sensibly under edge cases, missingness, different market regimes and unusual valid conditions? | Systematic fragility rather than isolated rare cases |
| G. Integrity / Leakage Safety | Does it preserve PIT validity, protected-data isolation, split integrity and semantic separation? | Integrity of evidence and boundaries; this dimension is a hard gate |

**Integrity = 0 blocks KEEP regardless of the other ratings or total score.**

## 3. Evidence required for ratings

Every non-N/A rating must record the rating, evidence source, denominator where applicable, affected cases/groups, observed pattern and rationale. Do not assign weak/failed ratings from vague impressions. Record why evidence is insufficient for N/A; missing evidence must not be fabricated.

Illustrative record structure, not an observed result:

```text
Dimension: Reliability
Rating: 1
Observed: 18 / 64 episode groups unresolved
Pattern: across 7 tickers
Cause evidence: directly traced to D4 continuity semantics
Alternative causes considered: provider gaps, reviewer error
Rationale: describe the material effect and supporting evidence
```

## 4. Optional Decision Health Score

`Decision Health Score = sum(valid dimension points) / (3 × number of non-N/A dimensions)`.

The score is **diagnostic only** and must not independently determine KEEP, REVISE or INCONCLUSIVE. Report the dimension ratings and evidence alongside it; all-N/A leaves the score undefined. Do not optimize D decisions to maximize the score. Even 18/21 with Integrity = 0 cannot be KEEP.

## 5. Review outcomes

Every reviewed D receives exactly one outcome:

| Outcome | Requirements and consequence |
|---|---|
| KEEP | Normally requires Integrity >= 2, Clarity >= 2, Operationalizability >= 2, no material core dimension = 0, sufficient direct evidence, and no systematic defect attributable to this D. A high average cannot override a failed hard gate |
| REVISE | Requires direct evidence that the D itself materially causes a problem. Examples: Integrity = 0; Clarity 0/1 causing material ambiguity; Operationalizability 0/1 preventing valid use; Reliability 0/1 showing systematic inconsistency; Product Alignment 0/1 failing the intended task; Robustness 0/1 causing repeated material failure. Poor downstream model metrics alone are insufficient |
| INCONCLUSIVE | Evidence cannot distinguish a D defect from data, annotation, sampling, implementation or downstream model problems, or important dimensions remain N/A. Does not authorize tuning or revision; the current D version remains frozen pending adequate development evidence |

A weak rating alone does not establish causal attribution or automatically authorize a change. Unresolved integrity risk does not authorize affected work to continue merely because the version remains frozen.

## 6. Causal attribution before REVISE

1. Define the observed failure.
2. Identify the layer where it first appears.
3. Provide evidence linking it specifically to the D decision.
4. Consider plausible alternative causes.
5. Explain why changing this D is justified.

Alternatives include bad source data, detector implementation, benchmark incompleteness, annotation error, sampling design, insufficient statistical power, severity model, ranking model, and UI/output implementation. Do not modify upstream semantics to repair downstream performance.

## 7. D-specific diagnostics

These supply decision-specific evidence; they do not replace or add dimensions to the common rubric.

| D | Evidence warranting review | Insufficient justification |
|---|---|---|
| D1 — Factual Abnormality | Systematic disagreement with factual predicates; predicate does not represent its named event; operational factual ambiguity; repeated invalid borderline behavior | Poor severity/ranking performance |
| D2 — Data Frame / PIT | Approved frame cannot be constructed reliably; systematic availability/adjustment/universe problems; PIT assumptions cannot be audited; material leakage risk | Desire to gain more cases by loosening D2 |
| D3 — Monitoring Context | CONTROLLED_AS_IF_EMPTY no longer represents the target question; scenario prevents valid evaluation of intended user behavior | Poor ranking metrics alone |
| D4 — Episode Policy | Inconsistent boundaries; systematically inappropriate grouping; materially excessive quarantine attributable to D4; ambiguous split isolation | Detector misses alone |
| D5 — Attention Budget / Delivery | Top-3 capacity systematically contradicts intended experience; misleading empty states; demonstrated overflow product problem; future product scope requires true mandatory delivery | Poor model precision/recall |
| D6 — Study / Reviewer Design | Inadequate reviewer reliability; materially incomplete coverage; excessive uncertainty for intended claims; identifiable sampling bias; inadequate adjudication capacity or independence | Candidate-model failure alone |

These are prospective diagnostics, not new findings or revisions of D1–D5.

## 8. Revision impact / blast radius

Separately classify every proposed revision's impact as **LOW, MEDIUM, HIGH or CRITICAL** and record what becomes invalid. Revision impact is **not part of quality scoring**.

| Revision | Potential invalidation |
|---|---|
| D1 | Potentially HIGH/CRITICAL: factual existence labels and downstream truth may require rebuild |
| D2 | Frame membership, evidence packets, PIT guarantees |
| D3 | Contextual relevance and exposure assumptions |
| D4 | Episode links and split isolation |
| D5 | Top-3, empty-state, overflow and delivery evaluation; does not automatically invalidate D1 factual truth |
| D6 | New sampling/reviewer work may be needed without changing event semantics |

Classify the actual proposal with evidence; do not rebuild unaffected artifacts unnecessarily.

## 9. Append-only versioning and review record

Never overwrite an approved D version. Example: **D4 V1 → Decision Review → REVISE → approved D4 V2**. Preserve V1 and its evidence; the approved successor records the exact change.

Every revision must preserve a review record containing:

- D and version reviewed; all rubric ratings and supporting evidence;
- observed problem and alternative causes considered;
- exactly one KEEP / REVISE / INCONCLUSIVE result;
- exact approved change and unchanged semantics;
- revision impact and invalidated artifacts;
- required rebuild, re-annotation and re-evaluation.

Changes require Decision Review and explicit approval of the successor version. Review records and corrections are append-only; preserve original labels, artifacts and earlier releases.

## 10. Evidence boundary

Before fresh validation, Decision Review may use authorized development/pilot benchmark evidence, reviewer disagreement, unresolved/missingness, PIT/data-quality, episode/quarantine, Top-3 capacity/overflow and coverage diagnostics, plus development implementation audits.

**Do NOT use sealed holdout. Do NOT iteratively redesign D1–D6 using individual fresh-validation cases.** This document does not authorize access to any data.

If fresh validation exposes a severe design defect:

1. Record the validation failure.
2. Invalidate that validation cycle.
3. Return to development.
4. Conduct Decision Review using development evidence for revision decisions.
5. Create an approved Dn V2 if justified.
6. Reserve a NEW fresh validation set after the revised design is frozen.

Do not tune repeatedly against the same validation set or recycle its individual cases into iterative semantic development. Validation failure may trigger review, not a case-driven tuning loop. No iterative semantic tuning against holdout is permitted.

## 11. Diagnostic review order

Diagnose approximately upstream → downstream:

**Data/PIT validity → factual event truth → episode/context structure → benchmark/reviewer design → severity → contextual relevance → ranking → Attention Budget/delivery → model/system implementation.**

This guides diagnosis, not an obligation to change an upstream D first. Change only the layer supported by evidence; inspect plausible implementation causes wherever they first appear.

## 12. Prospective lifecycle

After unresolved decisions and separate authorization are satisfied:

```text
D1–D6 V1 FROZEN
    → Development / Pilot Benchmark
    → Decision Review Gate
    → common rubric + D-specific diagnostics
    → KEEP / REVISE / INCONCLUSIVE
```

KEEP retains the reviewed version. INCONCLUSIVE retains the freeze, collects adequate development evidence and returns to review; it does not permit tuning or progression while required evidence is unresolved.

```text
If REVISE:
    → create approved Dn V2
    → declare impact and invalidate only affected artifacts
    → collect new development evidence if required
    → return to Decision Review
When decisions are resolved and applicable readiness gates pass:
    → Freeze again
    → Fresh Validation
    → Final Holdout
```

No iterative semantic tuning against fresh validation or holdout. This lifecycle grants no automatic authorization for generation, validation or holdout access. D1–D6 design blockers are resolved; separate explicit Benchmark Generation Authorization remains required.

## 13. Relation to D7

**Decision Review Protocol != D7.** Decision Review asks whether D1–D6 design decisions themselves remain valid. D7 asks what performance a candidate model/system must achieve given a frozen benchmark/design.

Do not use D7 model thresholds to decide whether D semantics are true. Do not use D-family quality ratings as model-performance gates. This protocol defines no D7 thresholds or model acceptance results.

## 14. Documentation consistency receipt

At protocol creation, one narrow documentation check verified the seven dimensions, 0–3 plus N/A scale, rating evidence, diagnostic-only score, Integrity hard gate, three outcomes, causal revision requirement, non-authorizing INCONCLUSIVE, separate diagnostics/impact, append-only versions, validation/holdout anti-tuning rules, D7 separation and then-unresolved D6. The two existing documents received minimal protocol references; D1–D5 semantics remained unchanged. The subsequent D6 approval updates only current readiness references here, not the review protocol or earlier decisions.
