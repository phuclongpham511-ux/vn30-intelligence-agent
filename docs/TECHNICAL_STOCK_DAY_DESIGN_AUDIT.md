# Technical Stock-Day Design Audit

Date: 2026-10-02. Scope: two prospective research documents only. This file is the optional audit artifact and resumable phase record. No benchmark data, labels, model outputs or implementation are created.

## Inputs and fixed comparison

- User specification: attachment `f3f7deeb-966d-4680-91a0-15528d4f8c82/Pasted text.txt`.
- Primary: `docs/TECHNICAL_MATERIALITY_EVALUATION_CONTRACT_V2.md`, SHA-256 `52dd579e720bf0e22b54a38180b1862e8f980cc91b66b700a9dcc705e89a80e0`.
- Secondary: `docs/TECHNICAL_MATERIALITY_ARCHITECTURE_REVIEW.md`, SHA-256 `fd8157a3f64fd16081ac64521348b78b5e176b482e1faaf9f57ed01fbbc0c637`.
- Vocabulary: `CONTEXT.md`, SHA-256 `6bf4aab8fab12f5b82e3c017d4940c6d823ab09e6b61ea6cf6be70074fa32a7d`.
- Read-only implementation reference: `src/materiality/detectors.py`, to confirm existing transition semantics only.
- Git anchor: `0d4f195ce330febedfe60887cebcad68b92c437b`. Both requested document paths were absent at task start. Audit their complete added contents, not unrelated pre-existing untracked files; no commits form this task's change.

## Skill application

Read `.agents/skills/grill-with-docs/SKILL.md`, `.agents/skills/to-spec/SKILL.md` and `.agents/skills/code-review/SKILL.md`, plus domain/tracker rules. The grill wrapper asks for `grilling` and `domain-modeling`; neither dependency nor a Skill invocation tool is available after searching repository, user and installed plugin skill locations. Phase A therefore performs the user's explicitly requested document interrogation directly; it does not claim those dependencies ran. No skills installed or altered.

For to-spec, the user's explicit two-document structure and local-only scope override the generic issue-publication template and interview/checkpoint. No issue publication or implementation-seam approval is needed for this design-only deliverable. Code-review is limited to a two-axis consistency audit of the two added documents, using the known absent-file baseline, as requested; it must not redesign the architecture or demand a commit.

## Phase A — design-risk checklist, completed before drafting

| Risk interrogated | Finding / treatment required in draft |
|---|---|
| Existence versus importance | Price/volume observation generators lack an approved abnormal-condition predicate; never derive factual existence from severity |
| Independent denominator | Opportunities must precede detector output; a detector-only union cannot establish recall or meaningful TN |
| Freeze timing | Freeze opportunity coverage before annotation; reference positives arise through annotation. Discovered omissions require versioned correction, not hidden post-label membership edits |
| Completeness versus unavailable data | Exhaustive inventory accounting does not guarantee known truth; separate structural, evidence and reference-label completeness |
| Safety semantics | Attention>=2 retention proxy is not a notification obligation; urgency/overflow/acknowledgement policy remains unresolved |
| Severity versus contextual utility | Prior exposure and recurrence must not silently reduce intrinsic magnitude; supporting signals cannot manufacture the target event |
| Episode semantics | Type recurrence is not an episode ID; no approved closure/re-entry/gap rule. No hindsight-connected episode may be fed back as PIT context |
| Splits | Whole groups and episodes, including repeated state, must not become supposedly independent rows; fresh-data eligibility not established |
| Missing truth | Unknown severity/relevance/delivery never becomes 0/no; incomplete groups cannot furnish full-group ideals |
| Blinding | Emitted status, candidate IDs, split names, model score components and presentation order can reveal system behavior |
| Metric units | Event retention, distinct insight recall, actual filled slots and separate overflow need separate numerators/denominators |
| Reviewer reliability | Independent raw labels and adjudication required; agreement sample/acceptance policy not established |
| Coverage realism | >3 insights must be distinct changes within four-family scope; no forced quota or relabeling to create them |
| Implementation boundary | Specify artifacts and future public verification seam; no executable schemas, generated cases, scores or tuning |

## Resumable phase record

- Phase A: COMPLETE. Governing docs read; risks recorded above.
- Phase B: COMPLETE. Both requested documents saved; D1–D7 explicitly separate policy/research blockers from specified integrity requirements.
- Phase C: COMPLETE. Independent Standards and Spec agents audited only the two added documents. Findings corrected and independently verified closed; no architecture redesign.
- Final verification: COMPLETE. All three governing hashes unchanged; 12 benchmark and 17 handbook numbered sections; six local links valid; shared D1–D7 present; Markdown fences balanced. No tracked-file changes; this task adds only these two documents and this optional audit record.

On resumption, verify the three input hashes above, read the existing drafts, and continue the first incomplete phase. Do not restart a completed phase or inspect evaluation datasets.

## Standards

Initial finding: Benchmark Spec's Precision@3 paragraph changed Contract V2's intrinsic-material, qualifying-slot numerator to contextual relevance and distinct-insight counts. Restored intrinsic-material qualification, one positive credit at most per filled slot and no repeated-coverage credit. Mirrored in Handbook §10. Independent closure review: **0 residual findings**. No additional actionable repository-standard defects identified.

## Spec

Initial findings: the same Precision@3 mismatch, plus absent explicit recognition/emission timestamps for the contract's late-recognition metric. Candidate inventory and future stage ledger now require recognized_at/emitted_at with clock/time basis/assurance or null reason. Offline wall time is explicitly not historical recognition; modeled timing is labeled, and unavailable timing remains unavailable with coverage. Independent closure review: **0 residual findings**. All required sections and field/metric needs accounted for.

## Cross-document traceability

| Labels / evidence | Collection in Benchmark Spec | Production in Handbook | Future purpose |
|---|---|---|---|
| Opportunity/existence/applicability | §5, §9 B/E | §3, §11–12 | Detector recall/precision and meaningful negative/unknown accounting |
| Intrinsic severity and uncertainty | §9 E | §4, §12 | a/3 severity error, ordinal/bias/coverage; intrinsic material/critical membership |
| Contextual event and insight relevance / ties | §9 E/G | §5, §9–10 | Conditional ranking and full insight NDCG/recall/burden |
| Retention / omission / tracking | §9 E and future stage ledger | §6 | Rankable versus accounted-for safety, separate from actual delivery |
| Required delivery / route / timing | §9 H and future stage ledger | §7 | Independent obligation denominator and delivered/acknowledged coverage |
| Duplicate / episode / ownership | §9 F/G | §8–9 | Distinct gain, event conservation, faithful coverage and split isolation |
| Price attribution and signed channels | §9 D/E | §11 A | Raw-versus-residual diagnostics without causal or universal-channel assumptions |
| Empty states / completeness | §6, §9 E/I | §10, §12, §14 | Valid ideals, no-material/no-useful-change burden and unknown-data distinction |
| Reviewer versions / raw / adjudication | §9 E, §10 | §13, §16 | Independence, disagreement and freeze audit; not model features |
| System output / recognition / delivery log | §9 future outputs | §9, §16 output-faithfulness procedure | Later observed system behavior, never fabricated by human target labels |

Terms are shared through the Benchmark Spec's normative glossary and restated consistently in Handbook's opening. No protected datasets, V1/V2 individual cases or V3 case examples were read for this task. The only implementation source read was the existing detector to verify unchanged MA/RSI predicates. No internet research was needed to synthesize the supplied governing contract. No schema/test/model implementation, cases, labels, scores, tuning, frontend tests/build, production change, holdout access or Final Validation occurred.

## Delivered state

- `docs/TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md`: SHA-256 `9b4dd274b183a31e045a15e9af39ff0f0e1970abf3b21583bbb69bce3f7a466b`.
- `docs/TECHNICAL_ANNOTATION_HANDBOOK_V1.md`: SHA-256 `0e417e930d6686c2d3c717eb843076db4cf98810e5164bc9d2643c1e041a380f`.
- Benchmark readiness: structurally specified, generation blocked on D1–D6 and separate authorization.
- Handbook readiness: B, policy/research decisions required before pilot.
- D7 concerns later model-evaluation acceptance, not a reason to invent annotation thresholds.
- Next step: owner decisions and document approval; generation/pilot require a subsequent explicit authorization. At completion of the design task, files remained local/uncommitted; no GitHub publication had been performed. The user's subsequent Git publication request authorizes publishing these documents and their two governing documents without changing research readiness or authorizing benchmark generation.

Audit summary: Standards — 1 initial finding, 0 residual; Spec — 2 initial findings, 0 residual. The shared precision defect was corrected once in each affected document, not treated as two independent metric problems.
