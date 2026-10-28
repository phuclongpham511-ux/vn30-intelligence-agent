# Technical Stock-Day Design Audit

Original design date: 2026-10-02. Governance updates follow below. Earlier sections are historical delivery records; the latest appended governance update is authoritative for current readiness. No benchmark data, labels, model outputs or implementation are created.

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

## D1 governance update — 2026-10-03

Authority: project owner's supplied instruction `24ef14c9-8221-4148-b104-1efd632cc169/Pasted text.txt` explicitly approves D1. Baseline for this documentation change is commit `54289b4`; no task commit is required for consistency review. The existing local-only documentation scope overrides to-spec's generic issue-publication template; code-review applies as two-axis documentation audit, not architecture redesign.

Current status: **D1 APPROVED; D2–D6 BLOCKING; D7 later model-evaluation work. Benchmark generation remains BLOCKED.** No subsequent decision is resolved by this update.

Approved semantics: absolute daily return and HIGH daily volume each compared to their own prior comparable empirical 95th percentile; at or above is EXISTS, below with valid evidence is DOES_NOT_EXIST, insufficient/invalid required evidence is UNRESOLVED. Use up to 252 valid prior trading-session observations, minimum 60, current excluded. Preserve signed price direction; market-relative evidence does not determine existence, and price cannot manufacture unusual volume. Severity, contextual relevance, safety, ranking and display remain separate.

Read-only source inspection found one current own-history methodology: `src/evaluation/context.py` uses midrank `(less + 0.5*equal)/n`, corroborated by `tests/test_historical_evaluation.py` and `docs/SECTION2_PHASE2_REPORT.md`. It is not an inverse percentile threshold and its tied-value behavior cannot substitute for inclusive quantile comparison. Source/documentation searches did not find incompatible inverse-quantile implementations. D1 explicitly specifies nearest-rank inverse empirical CDF `q95=h_(ceil(95*n/100))`, one-based, no interpolation. This is documented mechanical definition, not a change to the legacy midrank helper. The D1 valid-observation window is also explicitly distinguished from legacy slice-before-null-filter context. No code was executed to generate scores or benchmarks.

Changed documents: new `TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md`; updates to `TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md`, `TECHNICAL_ANNOTATION_HANDBOOK_V1.md`, and this audit. Evaluation Contract V2 remains unchanged; D1 fulfills its requirement for a separately approved factual predicate.

Resumable status:

- Source/governance inspection: COMPLETE.
- Decision and linked-document edits: COMPLETE.
- Standards / Spec consistency audit: COMPLETE; both independent axes report zero findings.
- Final scope, D2–D7/rubric preservation and source-hash verification: COMPLETE. D2–D7 decision rows and Handbook intrinsic severity section match `54289b4` exactly; local links and whitespace checks pass. Only the three specified tracked documents plus the new D1 record changed in this task. No production/source changes.

On resume, inspect only these four document changes against `54289b4`; finish audit and verification without opening datasets or proceeding to D2. Original delivered hashes above are historical, not hashes of the updated versions.

### D1 Standards audit

No actionable findings. The approved predicate and its deterministic inverse-quantile mechanics remain separate from legacy midrank, severity, contextual relevance, ranking and display. PIT/null/provenance rules and dynamic ticker scope are preserved. D2–D6 remain blockers and D7 remains later work.

### D1 Spec audit

No findings. All requested semantics and decision-record sections are present, including equality, absolute price return, high-volume scope, current exclusion, 252/60 history limits, market-relative independence and explicit UNRESOLVED handling. Mechanical nearest-rank definition is documented rather than falsely described as an existing quantile implementation. No datasets or protected cases were accessed by either audit.

### D1 verification receipt

- Evaluation Contract V2 unchanged SHA-256: `52dd579e720bf0e22b54a38180b1862e8f980cc91b66b700a9dcc705e89a80e0`.
- New D1 decision SHA-256: `8f94757f54a8b77cb9fe36660e95fa30b9ff5ac37a68af275d1185bc6ab3587b`.
- Updated Benchmark Spec SHA-256: `2c345abd6ca11263c9d9e5181a27c5c4113d71cce8dce4ff321053bf6ec102c6`.
- Updated Handbook SHA-256: `a080f490476cc97415fd192586395d99e3fcc5ab87bcf5e18d9fc877a7f01abe`.
- Inspected context/replay/test/report source text unchanged against `54289b4`; `git diff --check` passes.
- No benchmark cases, annotations, scores or model evaluation generated; no tuning, production edits, V4/V5, frontend tests/build, protected-data access or Final Validation. No D2 work started.

D1 audit summary: Standards 0 findings; Spec 0 findings. **D1 APPROVED; D2 next blocker; benchmark generation BLOCKED.**

## D2 governance update — 2026-10-03

Authority: project owner's supplied instruction `c200b700-dc4e-4e2e-a08d-647ebd026c8b/Pasted text.txt` explicitly approves D2. Current state: **D1 APPROVED; D2 APPROVED; D3–D6 BLOCKING; D7 LATER EVALUATION CALIBRATION. Benchmark generation remains BLOCKED.** D3 is next; no D3 work is authorized here.

This update creates `TECHNICAL_D2_DATA_FRAME_PIT_DECISION.md` and updates Benchmark Spec, Handbook evidence visibility/readiness, and this audit only. The earlier uncommitted D1 work is preserved. Pre-D2 baselines: D1 SHA-256 `8f94757f54a8b77cb9fe36660e95fa30b9ff5ac37a68af275d1185bc6ab3587b`; Benchmark Spec `2c345abd6ca11263c9d9e5181a27c5c4113d71cce8dce4ff321053bf6ec102c6`; Handbook `a080f490476cc97415fd192586395d99e3fcc5ab87bcf5e18d9fc877a7f01abe`. `54289b4` is the tracked Git anchor, but its diff also contains the prior D1 changes; audit must distinguish them.

Approved frame: stock-days strictly before 2025-01-01 with reliable as-of historical VN30 membership; no current-membership substitution. Closed Validation V1/V2 and completed V3 reviewed cases are not fresh annotation input; use metadata-only exclusions before loading. Holdout 2025–2026 stays sealed, uninspected and unenumerated. D6 retains sample size, actual dates, allocations and representative/enriched design; no signal/model/expected-label selection under D2.

Approved cutoff: 23:59:59 Asia/Ho_Chi_Minh on the trading date. EOD_AVAILABILITY_ASSUMPTION explicitly means assurance=assumed, not audited publication timing. Preserve observation/assumed availability/source/snapshot/download/adjustment/quality metadata; only cutoff-visible inputs, no future filling or future repairs. D1 prior-only 252/60 history is unchanged. VN30 exact interval gaps stay null; essential transition/comparability gaps stay unresolved. Versioned verified comparable adjusted series must itself satisfy PIT. No intraday/alert-latency assessment is claimed.

Repository inspection is source-only: `src/evaluation/models.py`, `src/evaluation/replay.py`, and `scripts/prepare_development_v3.py`. Existing EOD-assumption enum and timestamp precedent are compatible; legacy current universe, unknown-adjustment warnings and supplied-row adjacency do not establish D2 membership/comparability/continuity. An existing run cannot be certified merely by prior use. No direct source conflict makes the approved policy impossible; future builders must validate rather than weaken it. No raw datasets, case manifests, labels, snapshots or provider/network data were loaded.

The spec's source-snapshot identity is clarified as cutoff-stable logical source/subset identity for prefix checks; full-container hashes remain in run provenance. This avoids making earlier IDs depend on appended future rows while preserving complete source provenance. D6's enriched-sampling ideas remain unapproved and must explicitly respect/reconcile the D2 selection boundary; no exception is silently granted now.

Skill use: to-spec synthesis is limited to the user's requested local documentation, overriding generic issue-publication instructions. Code-review runs separate Standards and Spec consistency audits of this change, not architecture redesign. No implementation or production test suite is required.

Resumable status:

- Governing-document/source inspection: COMPLETE.
- Decision and linked-document drafting: COMPLETE.
- Independent Standards / Spec audit: COMPLETE; both axes report zero findings.
- Final invariant/hash/scope checks: COMPLETE; D1/Contract/source hashes unchanged, Handbook protected sections unchanged, D3–D7 decision rows unchanged, all 17 D2 sections and local links verified, whitespace check passed.

Resume by verifying the unchanged D1 and Contract hashes, reviewing these four documents and finishing the incomplete audit only. Do not build a benchmark or proceed to D3.

### D2 Standards audit

No actionable findings. Frame, historical membership, exact EOD cutoff, timing assurance, prior-only history, benchmark alignment and essential comparability/null rules agree across the documents. Cutoff-stable identity preserves prefix invariance with full-container provenance kept separately. Legacy limitations are recorded without certifying datasets or changing production. D1 is unchanged; later decisions and human rubrics are preserved.

### D2 Spec audit

No findings. All 17 required sections are present; cutoff-visible evidence, pre-load protection, current exclusion, 252/60 history, corporate-action handling and complete prefix checks match the approved instruction. D6 sampling, including enrichment, remains unresolved and not implicitly authorized. Neither audit accessed datasets/protected cases or ran evaluation.

### D2 verification receipt

- D1 unchanged SHA-256: `8f94757f54a8b77cb9fe36660e95fa30b9ff5ac37a68af275d1185bc6ab3587b`.
- Evaluation Contract V2 unchanged SHA-256: `52dd579e720bf0e22b54a38180b1862e8f980cc91b66b700a9dcc705e89a80e0`.
- D2 decision SHA-256: `bb1786c5bb6724c7b662a089286b1d730de51f46eaf21f1807368c0699fb6823`.
- Updated Benchmark Spec SHA-256: `976612f41f473f90cf864195742b2ae4de353b3d2f081f9546f2395832944ba9`.
- Updated Handbook SHA-256: `edb85f09b5f8a9cc0f5b0ecf10bf6db7fcf37c4b6745c7ea4e6c7653bf00ee66`.
- Inspected models/replay/V3-preparation source bytes unchanged against start-of-task hashes. No production edits or executed provider/generator code.
- Handbook sections 4–9 and 13 (severity, contextual relevance, retention, delivery, episodes, insights and reviewer design) unchanged against pre-D2 section hashes; D3–D7 register rows unchanged against the tracked baseline.
- No sampling, evidence packets, annotations, scores, tuning, validation execution, protected-data/holdout access or enumeration, Final Validation, or frontend tests/build. No D3 work started.

D2 audit summary: Standards 0 findings; Spec 0 findings. **D1/D2 APPROVED; D3 next blocker; benchmark generation remains BLOCKED.**

## D3 documentation update

D3 is approved by the project owner. Current state: **D1 APPROVED; D2 APPROVED; D3 APPROVED; D4 BLOCKING; D5 BLOCKING; D6 BLOCKING; D7 LATER. Benchmark generation remains BLOCKED.** Earlier status entries are historical; this entry supersedes D3-pending readiness only.

Created `TECHNICAL_D3_MONITORING_CONTEXT_DECISION.md`; updated only D3-related task/exposure/today-only guidance in Benchmark Spec and Handbook, plus this audit. V1 uses one-user/one-stock technical EOD monitoring and `prior_exposure_mode = CONTROLLED_AS_IF_EMPTY`. No real prior delivery is asserted. PIT-safe market history and recurrence remain distinct from user exposure; no previous alert/acknowledgement is invented. Past events enter as context, not new events unless today's approved predicate fires. Portfolio/thesis/preferences and other domains remain out of scope.

Lightweight consistency check: PASS. D3 meaning/mode and scope agree across edited docs; D1/D2 and D4–D7 decision rows unchanged. Direct conflicts found and corrected: previous requirements for a prior-exposure ledger and an already-delivered example conflicted with the approved controlled-empty V1 scenario. No residual direct conflict. Only the three authorized existing documents were read; no skills, agents, repo-wide searches, datasets/cases, holdout, scoring/evaluation or production work. Stop at D3.

## D4 documentation update

D4 is approved by the project owner. Current state: **D1 APPROVED; D2 APPROVED; D3 APPROVED; D4 APPROVED; D5 BLOCKING; D6 BLOCKING; D7 LATER. Benchmark generation remains BLOCKED.** Earlier readiness records are historical.

Created `TECHNICAL_D4_EPISODE_POLICY_DECISION.md`; updated only D4 episode/split-related definitions and readiness in Benchmark Spec/Handbook, plus this audit. Episodes are same-family: anchor, continuation, confirmed closure and re-entry. Direction reversal starts a new price episode; volume is HIGH-volume only; MA/RSI continuation is not a repeated transition event. Unresolved continuity is neither bridged nor closed, and no fixed N-day rule applies. Cross-family insight grouping preserves separate episode IDs. Cross-boundary or uncertain episodes/groups are quarantined from Fresh Validation, without moving reserved cases to development.

Lightweight documentation consistency check: PASS after correcting case-sensitive HIGH-volume wording in the decision record. Family-specific lifecycle, direction reversal, unresolved continuity, no repeated MA/RSI transition events, no fixed-gap shortcut, separate cross-family identities and Fresh Validation quarantine agree across edited documents. Direct conflicts corrected: previous cross-family episode definition and optional migration of boundary episodes to development. No residual direct conflict found. D1-D3 semantics remain intact; D5/D6 remain blockers. No datasets/cases, holdout, model/scoring/evaluation, production work, skills, agents or repo-wide search occurred. Stop at D4.

## D5 documentation update

**D1 APPROVED; D2 APPROVED; D3 APPROVED; D4 APPROVED; D5 APPROVED; D6 BLOCKING; D7 LATER. Benchmark generation remains BLOCKED.** Earlier delivery/readiness notes are historical and superseded for D5 V1.

Created `TECHNICAL_D5_DELIVERY_POLICY_DECISION.md`; updated D5 attention/empty-state/overflow/delivery sections in Benchmark Spec and Handbook, plus this audit. Ordinary output is maximum 3, no filler; complete no-useful-change yields NO_MEANINGFUL_TECHNICAL_CHANGE, incomplete/unresolved evidence yields TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE, both with zero ordinary cards. Preserve full reference/overflow without Top-3 exposure credit. Ordinary Technical V1 required_delivery=NO; severity 3 creates no mandatory display or notification. Current EOD response only; no push/email/SMS/escalation/acknowledgement or mandatory overflow route. D1-D4 semantics unchanged.

Narrow consistency check: PASS. D5 semantics match across edited docs; D1-D4 and D6/D7 decision rows preserved. Direct conflicts fixed: formerly unresolved delivery policy and mandatory notification/overflow fields, plus ambiguous empty-state names. Zero obligations do not produce a perfect delivery metric. No datasets/cases, source inspection, holdout, models/evaluation, skills/agents or repo-wide analysis. Stop at D5.

## D-family Decision Review Protocol V1

Created [Technical Decision Review Protocol V1](TECHNICAL_DECISION_REVIEW_PROTOCOL.md). D1–D6 are versioned hypotheses/contracts; changes require Decision Review using the common seven-dimension rubric. The summary score is diagnostic only; Integrity is a hard gate and Integrity=0 blocks KEEP. Poor model performance alone cannot trigger D revision. Fresh validation/holdout cannot be used for iterative D tuning; severe validation design defects invalidate the cycle, return to development review, and require a new fresh validation set. D7 model acceptance remains separate.

**D1–D5 APPROVED; D6 BLOCKING; D7 LATER; benchmark generation BLOCKED.** Approved semantics remain unchanged. The prospective full D1–D6 freeze is not a claim that D6 is resolved now. The audit header's stale D2-only readiness pointer is corrected; historical records remain preserved. Only this audit and a minimal Benchmark Spec reference are updated; the Annotation Handbook is unchanged. One narrow documentation consistency check: PASS (16 checks); current D1–D7 readiness rows preserved. No data/cases, source code, model/evaluation, fresh validation or holdout work; no skills/sub-agents or broad audit. Stop before D6.

## D6 — Study & Reviewer Design V1 approval

**D1 APPROVED; D2 APPROVED; D3 APPROVED; D4 APPROVED; D5 APPROVED; D6 APPROVED; D7 LATER MODEL-EVALUATION ACCEPTANCE.** Earlier D6-pending notes are historical. D1–D6 design blockers are resolved, but **BENCHMARK GENERATION IS STILL NOT AUTHORIZED**: separate explicit Benchmark Generation Authorization and applicable construction integrity checks remain required.

Created [D6 decision](TECHNICAL_D6_STUDY_REVIEWER_DECISION.md). Approved Development quota is 120 stock-days (80 Representative + 40 Enriched Diagnostic), with 60 reserved Fresh Validation stock-days. A reviews all; B independently reviews a reproducible 30% Development subset (36/120) and all Fresh Validation (60/60). Freeze selection/assignment rules before sampling; retain independent append-only raw labels and separate adjudication. Report typed agreement, unresolved rates, reasons and denominators without one arbitrary global agreement gate. Representative/enriched results remain separate; quota adequacy is not asserted as a universal optimum.

Updated only D6 sampling/reviewer/readiness sections in Spec and Handbook, this audit, and minimal stale D6 readiness references in the Decision Review Protocol. Direct conflicts fixed: pending-D6/no-quota statements, unspecified reviewer allocation and readiness that incorrectly retained D6 as a design blocker. Evidence-only enrichment is a sampling component within the unchanged D2 eligible frame, not a frame exception. D1–D5 semantics and D4 isolation remain unchanged. Development supports Decision Review; severe validation defects require a failed-cycle record, Development review and a NEW Fresh Validation set. Existing 2025–2026 holdout remains sealed.

One narrow documentation consistency check: PASS (16 checks). No data/cases, source code, model/scoring/evaluation, fresh validation or holdout access; no skills/sub-agents or repo-wide analysis. No benchmark generation or D7 work.

## D2 V1 → V2 research-frame revision — 2026-10-03

[Decision Review V1 → V2](TECHNICAL_D2_DECISION_REVIEW_V1_TO_V2.md): **REVISE**, impact **LOW**. D2 V1's absent lower bound caused the B2 source audit to treat membership certification scope as extending to VN30 inception in 2012. This is a directly attributable Operationalizability defect, not a model-performance-driven revision. Earlier D2 approval and audit entries remain historical; V1 bytes are preserved.

**D2 V1 → REVISED; [D2 V2](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md) → APPROVED / ACTIVE** for future benchmark generation. Official Development/Pilot and future Fresh Validation stock-days satisfy `2020-01-01 <= session_date < 2025-01-01`. Pre-2020 warm-up is permitted only when PIT-valid and separately authorized for prior distributions, MA/RSI or episode/state initialization; it is not an eligible benchmark stock-day and does not expand sampling. Protected exclusions remain active and 2025–2026 holdout stays sealed.

B2 now needs the basket in force at the start of 2020 and all regular/interim membership changes affecting 2020–2024, with effective dates and provenance. No membership dataset is constructed or certified. Existing checkpoint state: no official Development benchmark generated and no Fresh Validation selected; no official cases/labels require invalidation. Phase 1 framework and admission-gate logic remain valid; no code is inspected, changed or executed here.

**D1 APPROVED; D2 V2 APPROVED; D3 APPROVED; D4 APPROVED; D5 APPROVED; D6 APPROVED; D7 LATER.** Real-data benchmark generation remains subject to B1–B6 certification and applicable execution authorization. This documentation revision does not grant additional execution authority.

Only frame/version references and related warm-up wording are updated in Spec and Handbook. All other D2 rules and D1/D3/D4/D5/D6 semantics remain unchanged. No data/cases, model/evaluation, benchmark generation, Fresh Validation or holdout work occurs.
