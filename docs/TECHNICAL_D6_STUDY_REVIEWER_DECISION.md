# D6 — Study & Reviewer Design V1

Status: **D6 — APPROVED** by the project owner's supplied decision. Documentation only. No sampling, annotation, data access, model work or evaluation is performed here.

## 1. Approved research quota

| Partition / component | Stock-days | Purpose |
|---|---:|---|
| Development / Pilot | 120 | Development evidence and diagnostics |
| Representative component | 80 | Ordinary deployment-like stock-days |
| Enriched diagnostic component | 40 | Difficult/informative conditions, not prevalence |
| Fresh Validation | 60 | Reserved evaluation after required freezes |

The representative component is drawn from the D2-authorized eligible frame, independently of detector output, model score and human label. The enriched component may use predeclared evidence-only selection rules: multiple observable technical conditions, missing/quality cases, episode boundaries, raw-versus-market disagreement and potentially high-demand stock-days. It must not use model scores, attention labels or expected human verdicts. Do not manually choose stock-days because they look interesting.

D2 eligibility is established before D6 sampling; enrichment does not redefine the eligible frame or waive PIT, missingness, protected-case or episode restrictions. Representative and enriched results are reported separately. Enriched results are not a deployment prevalence estimate. Count unique stock-days toward quotas; freeze component overlap/deduplication and replacement handling, retain selection lineage and do not double-count a group.

## 2. Reproducible sampling freeze

Before sampling, freeze the eligible frame version, inclusion/exclusion rules, component definitions, deterministic seed, selection algorithm and replacement policy if applicable. Freeze evidence-only enrichment categories/rules and the Reviewer B subset rule before results or labels are observed. Sampling and assignments must be reproducible, with intended versus completed counts and reasons for exclusions/nonresponse preserved.

This decision approves quotas and reviewer design, not actual dates, IDs, seed values, source files or a completed frame. Concrete sampling specifications must be frozen before a separately authorized build; no arbitrary implementation choices are asserted as approved here.

## 3. Fresh Validation and sealed holdout

Reserve **60 stock-days** under a frozen selection rule, separated from Development/Pilot. From reservation onward, protect Fresh Validation from model tuning and iterative D1–D6 redesign. Do not inspect its individual labels/cases during development tuning.

The existing **2025–2026 holdout remains SEALED**. D6 does not authorize opening, enumerating, relabeling or redefining it.

## 4. Independent reviewer design

| Partition | Reviewer A | Reviewer B |
|---|---|---|
| Development / Pilot | 120 / 120 stock-days | Independent deterministic/random 30% subset; target 36 / 120 |
| Fresh Validation | 60 / 60 stock-days | Independent 60 / 60 stock-days |

Freeze the reproducible subset algorithm and seed; do not select double-review groups because of Reviewer A's labels or disagreement. Record component coverage of that subset rather than inventing an additional allocation quota.

Reviewer B must not see Reviewer A's labels before completing the independent raw pass. Neither reviewer may see model scores, candidate scores, predicted ranking, detector-emitted status or another reviewer's labels before independent submission. Review complete stock-days using identical frozen packets and the approved handbook; preserve reviewer identity/version and blinding provenance.

## 5. Raw review and adjudication

Independent raw annotations are append-only and preserved:

**Reviewer A raw + Reviewer B raw → adjudication → final reference label.**

Never overwrite or erase disagreement. Adjudication preserves original judgments, rationale, adjudicated result, adjudicator identity/version and unresolved status when evidence is insufficient. Record adjudication separately with lineage; do not force a label to complete metrics. Independent agreement is measured on raw passes, not adjudicated consensus. Singly reviewed Development groups are not silently counted as double-reviewed agreement observations.

## 6. Agreement diagnostics

Do not introduce one arbitrary global threshold such as “80% agreement = PASS”. Report by judgment type:

| Judgment | Diagnostics |
|---|---|
| Factual existence | Exact agreement |
| Severity / contextual relevance | Exact agreement; one-level disagreement; large disagreement >= 2 levels |
| Episode / duplicate / relationship | Exact relation agreement; unresolved/disputed relation rate |

Also report unresolved rates, disagreement reasons, denominators and affected groups. Explicitly distinguish comparable paired ordinal judgments from missing/unresolved ones; do not convert missing evidence into zero. Preserve other existing judgment/mapping diagnostics without claiming a single pass threshold.

These diagnostics feed the [Technical Decision Review Protocol V1](TECHNICAL_DECISION_REVIEW_PROTOCOL.md), especially Reliability, Clarity and Operationalizability. They do not by themselves establish model acceptance or statistical adequacy.

## 7. Sample-size and uncertainty status

**120 Development + 60 Fresh Validation** is the approved V1 research quota, not a universally optimal statistical sample size or a power guarantee. Report uncertainty and coverage limitations with denominators; do not treat stock-days, repeated episodes, same-session observations or pair counts as independent where they are dependent. Concrete uncertainty procedures and comparison populations must be predeclared before the relevant analysis; no new numerical precision target is invented here.

If Development evidence shows inadequate uncertainty or coverage, review D6 through the Decision Review Protocol. Do not silently increase/decrease quotas after observing results. Any decision revision requires **D6 V2**, preserving the approved V1 and declaring impact/rebuild scope.

## 8. Split / episode isolation

[D4](TECHNICAL_D4_EPISODE_POLICY_DECISION.md) remains authoritative. One episode must not cross Development and Fresh Validation. A crossing episode or unresolved continuity near the boundary requires quarantine of affected stock-days from Fresh Validation. Do not split an episode, substitute a fixed arbitrary day-gap, or move protected/reserved validation cases into Development to meet quotas. Any permitted replacement follows the frozen rule and preserves exclusion lineage; infeasible quotas are reported rather than filled by weakening D4.

## 9. Permitted development use and validation lifecycle

Subject to separate authorization, Development/Pilot evidence may support benchmark/reviewer diagnostics, Decision Review of D1–D6, model development, debugging and justified Dn V2 design. These permitted future uses are not execution authorization in this documentation task.

Fresh Validation is for evaluation after D-family decisions, benchmark construction and required candidate/model behavior are frozen. Do not iteratively tune against the same Fresh Validation set.

If Fresh Validation exposes a severe design defect:

1. Record the validation failure.
2. Invalidate that validation cycle.
3. Return to Development.
4. Conduct Decision Review using Development evidence.
5. Create an approved Dn V2 if justified.
6. Reserve a **NEW Fresh Validation set** after the revised freeze.

Do not reuse the failed Fresh Validation set for iterative redesign. Sealed holdout is not Decision Review evidence.

## 10. Readiness and authorization

**D1 APPROVED; D2 APPROVED; D3 APPROVED; D4 APPROVED; D5 APPROVED; D6 APPROVED; D7 LATER MODEL-EVALUATION ACCEPTANCE.** D1–D5 semantics are unchanged. D1–D6 design blockers are resolved.

**BENCHMARK GENERATION IS STILL NOT AUTHORIZED.** A separate explicit Benchmark Generation Authorization is required, with concrete sampling/reviewer specifications and existing construction integrity gates satisfied. D7 is not resolved here; no benchmark data is generated and no model comparison is authorized.
