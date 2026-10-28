# D2 Decision Review V1 → V2

Date: 2026-10-03. Review target: **D2 V1 — Technical Benchmark Data Frame & PIT Policy**. Authority: owner's supplied D2 V2 instruction (`cf79ba14-2db5-46a9-a891-ee680bc940ec/Pasted text.txt`) and [Decision Review Protocol V1](TECHNICAL_DECISION_REVIEW_PROTOCOL.md).

## Observed problem and attribution

[D2 V1](TECHNICAL_D2_DATA_FRAME_PIT_DECISION.md) defined only `session_date < 2025-01-01` and explicitly chose no lower bound for official benchmark stock-days. The preceding B2 source audit consequently treated the possible historical-VN30 scope as extending to inception in 2012. This creates unnecessary and material historical-membership certification ambiguity: an Operationalizability defect in the decision itself.

Source accessibility is a separate data limitation; an inaccessible archive does not explain or resolve the missing policy bound. No scoring, reviewer disagreement or model-performance result motivates this revision. Evidence is the V1 policy wording and the preceding read-only B2 audit, not individual validation/holdout cases. No case-level reliability evidence is available.

## Common quality rubric

| Dimension | Rating | Evidence / rationale |
|---|---|---|
| Clarity | 2 | Upper bound is explicit; lower scope remains ambiguous |
| Operationalizability | 1 | Missing lower bound materially broadens B2 certification scope |
| Evidence Support | 2 | Direct policy wording and B2 audit establish the scope defect |
| Reliability | N/A | No case/reviewer reliability study used |
| Product Alignment | 3 | Technical stock-day EOD task remains aligned |
| Robustness | 2 | Existing protections remain; unbounded lower scope impairs execution planning |
| Integrity / Leakage Safety | 3 | Protected exclusions, PIT rules and sealed holdout remain intact |

These ratings are descriptive; no health score is calculated or optimized.

## Decision

**REVISE.** The missing lower bound causes a material scope ambiguity and unnecessarily broad B2 certification. This is not a model-performance-driven revision.

Approved successor: [D2 V2](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md), **APPROVED / ACTIVE** for future benchmark generation. Official Development/Pilot and future Fresh Validation stock-days must satisfy `2020-01-01 <= session_date < 2025-01-01`. D6 sampling/split rules, historical membership certification and protected exclusions continue to apply.

Pre-2020 warm-up may support prior distributions, indicators and episode/state initialization only when separately authorized and PIT-valid. It never becomes an official benchmark stock-day or expands sampling eligibility. All other D2 rules and D1/D3/D4/D5/D6 semantics are unchanged.

## Revision impact

**LOW.** At this review checkpoint, no official 120 Development stock-days have been generated; no Fresh Validation cases have been selected; holdout remains sealed. These are existing checkpoint facts, not newly established through payload inspection. Phase 1 framework and admission-gate logic remain valid; no implementation is changed or newly tested here. The revised frame must be reflected in future authorized input manifests.

No existing official benchmark cases or factual labels require invalidation, rebuild, re-annotation or re-evaluation because the official benchmark has not been generated. D2 V1 bytes and historical governance provenance are preserved. This review and V2 are new records; earlier audit entries remain historical.

## B2 scope consequence and execution boundary

Obtain the basket in force at the start of 2020 and all official membership changes affecting 2020–2024, including regular reviews, interim replacements, effective dates and provenance. Do not infer membership or equate announcement and effective dates. No membership dataset is constructed and B2 is not marked PASS.

Current decisions: **D1 APPROVED; D2 V2 APPROVED; D3 APPROVED; D4 APPROVED; D5 APPROVED; D6 APPROVED; D7 LATER.** Real-data benchmark generation remains subject to B1–B6 certification and applicable execution authorization. No datasets/cases, source code, models, benchmark generation, Fresh Validation or holdout are accessed in this documentation review.
