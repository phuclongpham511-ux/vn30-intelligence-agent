# D2 Population Decision Review V2 → V3

Date: 2026-10-03. Outcome: **REVISE**. Governing baseline: local HEAD `91232b00a3c9e9b124f5570c449254bf22e2de04`. Review follows the [Decision Review Protocol](TECHNICAL_DECISION_REVIEW_PROTOCOL.md).

Decision basis: the owner-approved [Technical Benchmark Population Direction Review V4](TECHNICAL_BENCHMARK_POPULATION_DIRECTION_REVIEW_V4.md), preserved verbatim as supplied by the owner during Step A.1. Execution authority: owner's “Technical Benchmark Population Revision — Implementation Step A” (`1666d3a3-9c59-436a-98ed-bad9df1f28c6/Pasted text.txt`). At Step A, the separate V4 document was unavailable locally; Step A.1 now records the supplied decision basis without revising this decision's population semantics.

## Problem and causal attribution

[D2 V2](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md) §2 requires certified historical VN30 membership for every selected stock-day and §3 excludes or leaves unresolved unestablished membership. That directly restricts the primary population to a historical index universe. The approved primary objective instead evaluates Technical Materiality on a frozen deployment cohort across 2020–2024 regimes. The mandatory membership gate therefore answers a different population question and unnecessarily makes primary eligibility depend on historical-index archive completeness.

This is a population/claim-design revision, not a workaround for poor engine metrics. Incomplete source availability alone would not justify loosening PIT safety. No evidence here implicates D1 predicates, reviewer reliability, detector quality, scoring, or sampling outcomes. Those alternative layers are unchanged; no individual cases, data or performance results were inspected to make this decision.

## Common quality rubric for the reviewed V2 population assumption

| Dimension | Rating | Direct evidence / rationale |
|---|---|---|
| Clarity | 3 | V2 §§2–3 explicitly require historical membership |
| Operationalizability | 1 | Mandatory membership certification blocks the approved primary objective even when all other stock-day evidence is admissible |
| Evidence Support | 2 | Direct V2 wording and owner-approved target population establish the mismatch; no empirical generalization claim |
| Reliability | N/A | No reviewer/case study inspected |
| Product Alignment | 1 | Historical-index population differs from the approved frozen deployment-cohort question |
| Robustness | 2 | PIT protections are strong, but population claims need explicit expansion boundaries |
| Integrity / Leakage Safety | 3 | V2 isolation protections are preserved, with no validation/holdout-driven revision |

Ratings concern policy text, not case-level measurements; no case denominator applies and no aggregate health score is calculated.

## Decision and impact

**REVISE → [D2 V3 APPROVED / ACTIVE](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md).** Historical membership becomes YES / NO / UNKNOWN evaluation metadata and secondary universe/replay evidence. It is neither primary eligibility nor a detection/scoring/ranking feature. The frozen deployment cohort becomes the primary population. Its capture/source freeze is still pending.

Impact: **MEDIUM** for future population eligibility and scope of performance claims. Prior D2 versions and historical study artifacts remain preserved. No existing labels or engine results are invalidated or rewritten. Any prospective frame definition relying on mandatory historical membership must be revised/versioned before real execution; no official frame is built here. Step A deliberately leaves the conservative legacy admission/preflight B2 structures and real-data loader lock unchanged. This policy revision alone cannot activate that loader.

D1 and D3–D5 remain byte-for-byte unchanged. D6 receives only a population-reference clarification; its 120 Development (80 representative / 40 enriched), 60 Fresh Validation, reviewer coverage, whole-episode isolation and protected-validation policies remain unchanged. D2 V3 retains unrelated PIT, EOD, comparability, warm-up, calendar, provenance and protected-data requirements.

## Enforcement and execution boundary

Safeguard 6 is checked through synthetic semantic alias invariance (including two interleaved streams with swapped aliases), an engine-only static identity guard, and exact engine input-schema boundaries. Generic symbol lookups and identity/provenance remain allowed. The static guard is deliberately conservative and does not prove absence of arbitrary dynamic indirection; no new scoring abstraction is introduced.

Expansion requires fresh Expansion Validation, acceptance criteria frozen before results, and PASS / FAIL / INCONCLUSIVE outcomes. No numerical gates are invented. Code portability does not imply validation portability; otherwise eligible research output outside validated scope is **UNVALIDATED_FOR_THIS_POPULATION**.

**Official sampling remains BLOCKED until deployment cohort source capture and freeze**, remaining data/provenance requirements and applicable execution authorization. No cohort capture, historical VN30 acquisition, official Development generation, Fresh Validation selection, holdout access, expansion dataset or model tuning is performed.
