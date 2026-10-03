# Technical Benchmark Population Direction Review — V4

**Status:** FINAL DIRECTION DRAFT — OWNER APPROVAL / IMPLEMENTATION READY; OFFICIAL SAMPLING STILL PENDING COHORT SOURCE CAPTURE  
**Project:** VN30 Intelligence Agent  
**Scope:** Technical Materiality Benchmark V1  
**Recommended direction:** Option C — Hybrid, with explicit safeguards

---

## 1. Primary decision

The primary Technical Materiality benchmark is intended to answer:

> **For the stocks the product serves, does the Technical Materiality engine correctly identify and rank meaningful historical changes across market regimes?**

It is **not** intended to answer:

> “Would a VN30 product reconstructed point-in-time have monitored exactly the historical VN30 universe on every date?”

Therefore:

- the **primary Technical benchmark** will use a frozen deployment cohort;
- point-in-time historical VN30 membership will be retained as metadata and a secondary universe/replay evaluation;
- historical VN30 membership will **not** remain a hard eligibility gate for the primary Technical benchmark.

This change re-scopes B2 rather than deleting it.

---

## 2. Cohort definition — fixed before sampling

### 2.1 Cohort reference date

The intended frozen deployment cohort is:

> **VN30 composition effective 2026-08-03**, corresponding to the July 2026 VN30 review cycle.

This date is chosen because it is the latest completed VN30 constituent review before this benchmark-population decision.

### 2.2 Cohort source

The authoritative source must be:

> **HOSE’s official VN30 constituent announcement/list for the July 2026 review, effective 2026-08-03.**

Before official Development sampling, the repository must contain a cohort-freeze artifact with:

- cohort version;
- effective date = `2026-08-03`;
- freeze/capture timestamp;
- all 30 tickers;
- exact official HOSE source URL/path;
- source document identifier/title;
- raw file SHA-256;
- normalized ticker-list SHA-256;
- normalization procedure;
- owner approval reference.

### 2.3 Current evidence status

The effective date and July 2026 review are externally corroborated, but the exact official full-constituent HOSE source file has **not yet been captured and hashed in the benchmark repository**.

Therefore:

> **The direction can be approved, but official benchmark sampling remains blocked until the exact HOSE cohort source is captured and the cohort artifact is frozen.**

No substitute based only on a current API, broker list, or inferred changes may silently become the frozen cohort.

### 2.4 Bias disclosure

Because the cohort is defined using a later/current deployment population, it is inherently a **survivor-selected cohort** relative to 2020–2024.

This is deliberate and must be stated explicitly.

The primary benchmark evaluates Technical Materiality on the stocks served by the frozen deployment cohort. It does not claim to represent the full historical VN30 population.

---

## 3. What previous work remains valid

### Fully reusable

The following remain valid without semantic change:

- D1 factual abnormality rules;
- D3 monitoring context;
- D4 episode continuity;
- D5 Attention Budget / delivery semantics;
- D6 reviewer/study design except precise universe wording;
- Decision Review Protocol;
- benchmark framework;
- D1 fact computation;
- episode logic;
- PIT and prefix-invariance protections;
- deterministic serialization and rebuild;
- synthetic smoke package;
- protected-data boundary;
- corporate-action, calendar, provenance and protected-exclusion requirements.

### Reusable with a changed role

The following remain useful:

- B2 historical-membership research;
- verified historical VN30 documents and hashes;
- historical-membership certificate schema;
- historical-membership metadata fields.

Their new role is:

- descriptive metadata;
- secondary universe/replay evaluation;
- ex-member/stress analysis;
- future product-universe validation.

### Narrow changes likely required

Only the following should change:

- D2 population eligibility rule;
- benchmark-spec/D6 sampling-universe wording;
- admission-gate rules/tests that make B2 mandatory for the primary Technical benchmark;
- cohort-freeze and listing-history guards.

No official 120 Development cases have been generated, Fresh Validation has not been selected, and the holdout remains sealed.

---

## 4. Historical membership metadata — descriptive only

For each benchmark stock-day, point-in-time VN30 membership should be stored where evidence permits as:

- `YES`
- `NO`
- `UNKNOWN`

Rules:

- never infer `YES` or `NO` from missing evidence;
- missing evidence remains `UNKNOWN`;
- membership status does not determine primary Technical benchmark eligibility;
- every non-UNKNOWN value must retain provenance.

### 4.1 No causal inference from these groups

Diagnostics may summarize results by:

- known historical member;
- known historical non-member;
- unknown membership.

However, these comparisons are **descriptive only**.

Reason:

- UNKNOWN evidence is likely concentrated in earlier years where archival coverage is weaker;
- membership status is therefore confounded with calendar time and market regime;
- the benchmark has limited sample size;
- further splitting by event family produces small cells.

Therefore:

> Differences between `YES / NO / UNKNOWN` groups must not be interpreted as causal evidence that historical membership caused better or worse model performance.

These diagnostics are only signals that may justify further review.

---

## 5. Secondary universe evaluation — owner and trigger

### 5.1 Owner

The **Project Owner / Benchmark Owner** owns the decision to trigger or complete the secondary universe evaluation.

This is a personal project, so this is explicitly a **self-approval structure**.

That limitation must be recorded rather than hidden.

### 5.2 Evidence considered for an early trigger

No arbitrary numeric threshold is introduced in V1.

An early review may be triggered when the owner documents evidence such as:

- persistent directional performance differences across membership-metadata groups;
- concentration of errors in early-history or particular calendar regimes;
- material coverage imbalance toward long-lived/current constituents;
- repeated reviewer concerns that cases from non-member/unknown periods are qualitatively different;
- listing-age or data-quality patterns that plausibly affect benchmark interpretation;
- a future product claim requiring historical VN30 representativeness.

The owner must record:

- evidence source;
- affected cases/groups;
- denominator/sample size;
- whether the pattern is repeated or isolated;
- plausible alternative explanations, especially calendar-time confounding;
- decision: `TRIGGER`, `DO_NOT_TRIGGER`, or `INCONCLUSIVE`.

### 5.3 Mandatory trigger

The secondary universe evaluation must be completed before any claim that:

- results represent historical VN30 membership point-in-time;
- the product has been historically replayed as a VN30 product;
- the benchmark represents all stocks that were members of VN30 during 2020–2024.

---

## 6. Listing and early-history eligibility

A frozen-cohort stock may have been listed after the start of the 2020–2024 benchmark frame.

Two separate conditions must be handled.

### 6.1 Pre-listing period

A stock-day is **ineligible** when the security was not yet listed/trading.

No:

- backfill;
- nearest-date substitution;
- synthetic pre-listing history;
- provider-gap interpretation as listing history.

Listing/trading status must be provenance-backed.

### 6.2 Early post-listing period

For the **representative primary sampling frame**, a stock-day becomes eligible only when there are at least:

> **60 prior valid comparable trading sessions**

This aligns with the minimum D1 historical window and ensures sufficient history for:

- D1 factual abnormality;
- MA20 / MA50;
- RSI14;
- episode/state initialization.

Therefore ordinary representative cases with fewer than 60 prior valid comparable sessions are excluded rather than retained with structurally missing core technical context.

### 6.3 Enriched diagnostic exception

Early-history cases with fewer than 60 prior valid sessions may appear only in the **predeclared enriched diagnostic component** when the purpose is explicitly to test:

- insufficient-history handling;
- unavailable/incomplete technical evidence;
- fail-closed behavior.

Such cases must be labeled as diagnostic and must not be treated as ordinary representative Technical Materiality cases.

---

## 7. Claim limitation — must travel with every result

The benchmark’s permitted conclusion is:

> **The Technical Materiality engine was evaluated on a frozen VN30 deployment cohort across historical market regimes in 2020–2024. The primary benchmark does not reproduce or claim representativeness of point-in-time historical VN30 membership.**

This statement must appear in:

1. the governing decision document;
2. the benchmark manifest;
3. the Development benchmark package;
4. the Fresh Validation manifest/package;
5. the final evaluation report template;
6. any model-acceptance report that uses this benchmark.

It must not exist only in a governance document.

A result artifact missing this scope statement is incomplete.

---

## 8. Survivorship-bias statement

Current control level:

> **LOW–MEDIUM**

Reason:

- the frozen deployment cohort is survivor-selected relative to the 2020–2024 period;
- historical membership metadata is incomplete;
- the secondary universe evaluation has not yet been built.

The control level may only be described as stronger after actual secondary-universe evidence exists.

The benchmark must not silently upgrade this assessment.

---

## 9. Updated trade-offs

| Criterion | A: Historical PIT VN30 | C: Hybrid — current design |
|---|---:|---:|
| Technical-engine focus | Medium | High |
| Historical deployment realism in primary benchmark | High | Low |
| Survivorship-bias control today | High | Low–Medium |
| Historical replay support | Direct | Secondary/deferred |
| Immediate data-acquisition burden | High / open-ended | Low–Medium |
| B2 blocks primary benchmark | Yes | No |
| Reuse of completed work | High | High |
| Separation of technical truth and universe management | Medium | High |
| Claim scope | Historical VN30 | Frozen deployment cohort only |

---


## 10. Safeguard 6 — Universe-agnostic engine, population-specific validation

The Technical Materiality engine must remain **universe-agnostic by implementation**, while its validation claims remain **population-specific by evidence**.

This distinction is mandatory.

### 10.1 Allowed stock-specific behavior

The engine MAY use ticker identity as a key for retrieving the stock's own PIT-safe history and state.

It MAY compute stock-local statistics using the same algorithm for every eligible stock, for example:

- rolling return distributions;
- stock-specific price/volume percentiles or z-scores;
- rolling volume baselines;
- MA / RSI state;
- event recurrence and Novelty derived from that stock's own PIT-safe history;
- episode state keyed by instrument.

This is not ticker-specific model logic. It is the same procedure applied to different data.

### 10.2 Prohibited ticker/index-specific behavior

The Technical Materiality engine MUST NOT contain:

- ticker-specific constants;
- ticker-specific thresholds;
- ticker-specific exceptions;
- ticker allowlists/blocklists controlling Materiality semantics;
- branches such as `if ticker == ...`;
- index-specific thresholds or special cases such as `if VN30 ...`;
- VN30/VN100 membership status as a scoring/detection/ranking input;
- any rule that changes factual abnormality, severity, Novelty, Confidence or ranking merely because of index membership.

Universe membership belongs upstream in product/universe resolution or downstream in evaluation metadata. It is not an engine feature.

### 10.3 Cheap enforcement tests

Three low-cost checks are required.

#### A. Label-invariance test

Construct equivalent PIT-safe input histories and change only the instrument label/ticker alias.

The semantic Technical Materiality output must remain identical.

Identity/provenance fields that are expected to contain the ticker, such as event IDs or display symbols, may differ and must be excluded from the semantic comparison.

A stronger permutation test should also assign two historical data streams to different aliases and confirm that results follow the data, not the ticker name.

#### B. Static scan

Scan Technical Materiality engine source code for:

- hard-coded known ticker literals used in logic;
- index identifiers such as `VN30`, `VN100` or membership-specific branches;
- ticker-specific threshold/config tables.

Generic fields such as `symbol`/`ticker` are allowed for identity, indexing, provenance and state lookup. The prohibition is on **behavior branching or parameterization by identity**.

Test fixtures and evaluation metadata are outside this prohibition when they are not imported into engine behavior.

#### C. Schema boundary test

Point-in-time membership metadata such as:

- `historical_membership_status = YES | NO | UNKNOWN`;
- index name;
- cohort membership;

must not appear in the Technical Materiality engine input schema.

Those fields may exist only in:

- universe-resolution inputs upstream;
- benchmark/evaluation metadata;
- reporting/diagnostic artifacts.

### 10.4 Code portability is not validation portability

Passing Safeguard 6 means the code is not artificially tied to VN30.

It does **not** prove that calibration or model quality generalizes to a new population.

Shared parameters can still be population-sensitive because a new universe may differ systematically in:

- liquidity;
- volatility;
- turnover/volume distributions;
- market capitalization;
- listing age;
- suspension/provider-gap frequency;
- corporate-action patterns;
- exchange trading rules and price limits;
- data quality and history length.

As a current Vietnamese-market example, normal price bands differ by venue: HOSE uses ±7% for ordinary listed shares/ETFs, while HNX states ±10% for listed shares and ±15% for UPCoM. These market-structure differences can alter observed return distributions and are one reason a move from a HOSE-heavy VN30 population to a broader population must not be assumed equivalent.

These values are examples of population-shift mechanisms, not hard-coded engine parameters. Expansion reviews must use the then-current official market rules.

### 10.5 Expansion Validation policy

A meaningful population expansion — for example VN30 to VN100, or expansion across exchanges/market structures — requires **Expansion Validation** before validated-performance claims are extended to that population.

Expansion Validation must:

1. use data/cases not used for development or calibration of the current engine version;
2. define the target expansion cohort before inspecting evaluation outcomes;
3. define acceptance metrics and pass/fail/inconclusive rules **before** opening the expansion evaluation results;
4. include data-quality and population-shift diagnostics relevant to the expansion;
5. distinguish implementation failure from population/calibration shift;
6. return `INCONCLUSIVE` rather than silently approving when evidence is insufficient.

A new universe does not automatically require a new model. The sequence is:

`existing engine -> fresh expansion validation -> approve / recalibrate / revise only the affected layer`

### 10.6 Status of outputs on an unvalidated population

The engine may be technically capable of producing output for an eligible stock outside the validated cohort.

Until Expansion Validation is completed, such output has status:

> **UNVALIDATED_FOR_THIS_POPULATION**

Policy meaning:

- it may be used for internal/exploratory research;
- it must not inherit the validated claims of the frozen benchmark cohort;
- it must not be described as proven equivalent to performance on the validated population;
- production enablement for a materially expanded population requires an explicit owner decision under the expansion-validation protocol.

This is a validation-status policy. No UI implementation is required in the current phase.

### 10.7 Relationship to Safeguard 3

There is no contradiction between:

- the engine being universe-agnostic in code; and
- benchmark conclusions being limited to the population actually validated.

The engine's **capability domain** may be broader than its **validated evidence domain**.

Claims follow evidence, not code reach.

---

## 11. Cost of changing direction

Expected bounded work:

1. Decision Review of population semantics.
2. Versioned D2 population-policy update.
3. Minimal Benchmark Spec / D6 reference updates.
4. Capture and freeze the 2026-08-03 deployment cohort.
5. Change historical-membership B2 from mandatory primary certificate to metadata/secondary certificate.
6. Add listing/pre-listing and 60-session primary-eligibility rules.
7. Update only affected admission/sampling tests.
8. Propagate the claim limitation into manifest/report schemas.
9. Add Safeguard 6 label-invariance, static-scan and schema-boundary tests.
10. Freeze the Expansion Validation policy and unvalidated-population status semantics.
11. Re-run the benchmark test suite.

This is a population/admission revision, not a benchmark-engine rewrite.

---

## 12. What must remain unchanged

The hybrid change does **not** relax:

- PIT / no-lookahead requirements;
- source/version provenance;
- corporate-action comparability;
- exchange-calendar requirements;
- protected-case exclusions;
- current-row exclusion;
- EOD cutoff semantics;
- episode rules;
- D1 factual definitions;
- Attention Budget semantics;
- reviewer independence;
- Fresh Validation anti-tuning rules;
- sealed 2025–2026 holdout.

---

## 13. Approval gates before official Development sampling

Official 120-case sampling remains blocked until all of the following are true:

1. population direction is formally approved;
2. exact HOSE July-2026 cohort source is captured;
3. cohort effective `2026-08-03` is frozen and hashed;
4. cohort freeze occurs before any official case sampling;
5. listing/pre-listing provenance guard exists;
6. representative cases require 60 prior valid comparable sessions;
7. historical membership metadata is tri-state and non-inferential;
8. the claim limitation is embedded in benchmark manifests/report templates;
9. Safeguard 6 invariance/static-scan/schema-boundary tests pass;
10. expansion-validation policy is frozen before any population expansion is claimed validated;
11. remaining relevant D2 real-data requirements are certified;
12. protected-data and holdout boundaries remain intact.

---

## 14. Decision

### Recommended direction

**OPTION C — HYBRID**

Primary objective:

> Evaluate Technical Materiality quality on a frozen deployment cohort across 2020–2024 historical regimes.

Secondary objective:

> Evaluate historical VN30 universe validity and survivorship sensitivity separately.

### Explicit limitation

The primary benchmark is intentionally survivor-selected by its frozen deployment cohort.

That trade-off is accepted because the benchmark targets Technical Materiality quality rather than historical investment-performance estimation or exact historical VN30 product replay.

---

## 15. What should not happen yet

Until the cohort source is captured and the population decision is formally approved:

- do not create D2 V3;
- do not change admission code;
- do not generate official Development cases;
- do not select Fresh Validation;
- do not access the holdout;
- do not delete B2 evidence;
- do not run another broad historical-membership archive search;
- do not restart Technical score tuning.

---

## 15. Expansion principle

Benchmark Cohort V1 is an **evaluation population**, not the identity of the Technical Materiality engine.

A future change such as:

`VN30 -> VN100 -> broader HOSE/HNX/UPCoM`

should first be treated as a population/domain expansion.

The default action is not retraining. The default action is:

`freeze expansion cohort -> predeclare expansion acceptance criteria -> evaluate on fresh data -> approve, recalibrate, revise, or remain inconclusive`

This prevents both forms of lock-in:

- input-side lock-in caused by survivor-selected benchmark design;
- output-side lock-in caused by ticker/index-specific engine logic.

---

## 16. Bottom line

The hybrid design is acceptable only with its bias and claim limits made explicit.

The design now records:

- **when** the cohort is intended to be frozen: effective 2026-08-03;
- **what source** must define it: the official HOSE July-2026 VN30 constituent list;
- **what remains unresolved**: the exact official full-list artifact still must be captured and hashed before sampling;
- **how membership diagnostics may be used**: descriptive only;
- **who triggers secondary evaluation**: the Project/Benchmark Owner, with explicit self-approval disclosure and evidence record;
- **how early listing history is handled**: pre-listing excluded, representative sampling requires 60 prior valid comparable sessions;
- **where the benchmark limitation must appear**: in every manifest and final report, not only governance docs.

This keeps the change bounded while preventing the simpler cohort design from becoming an undocumented shortcut.
