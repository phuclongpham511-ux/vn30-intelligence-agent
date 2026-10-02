# Technical Annotation Handbook V1

Date: 2026-10-02. Status: **prospective handbook; readiness B — decisions required before pilot**. This handbook defines human judgments for a future complete stock-day benchmark. It creates no labels and does not reinterpret historical V1–V3 attention/verdicts.

Primary authority: [Evaluation Contract V2](TECHNICAL_MATERIALITY_EVALUATION_CONTRACT_V2.md). Companion: [Stock-Day Benchmark Specification V1](TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md), especially its normative glossary, artifact fields and D1–D7 decision register. The [Architecture Review](TECHNICAL_MATERIALITY_ARCHITECTURE_REVIEW.md) explains why these judgments must be separated. If this handbook conflicts with Contract V2, stop the affected annotation and record a design defect; do not silently choose a new interpretation.

The task is: **“Given a stock the user is monitoring, what changed today that deserves attention?”** Attention is not expected return, bullishness or investment advice. Positive and negative direction describe facts, not desirability. This is a technical, single-stock, end-of-day task; it does not cover cross-stock portfolio ranking or other domains.

Terminology is identical to the Benchmark Spec: an **opportunity** is an independent factual check; an **event** is a factual transition/abnormal condition; an **emitted candidate** is system output; a **reference event** is an independently adjudicated exists opportunity. A **stock-day** includes the full opportunity inventory at its cutoff, while the **ranking group** is the conditional emitted/retained/rankable population. An **episode** is a cutoff-supported continuing change/state, and an **insight unit** is one coherent change preserving source reference-event IDs. **Severity** is intrinsic attention; **contextual relevance** is usefulness now; **retention** is a disposition; **required delivery** is a separate policy-grounded obligation. **Unresolved** is not zero/no. **Top 1–3** means at most three ordinary display slots, excluding overflow.

## 1. Annotator view

Every reviewer receives the same complete, frozen evidence packet and administrative item order for the stock-day. Review opportunities whether or not a detector emitted them; do not treat the visible inventory as a model-selected shortlist. The presentation must not identify emitted versus missed items. Evidence values are deterministic computations with units/provenance, not AI-recomputed numbers.

| May see | Conditions |
|---|---|
| Ticker, session/date, cutoff/timezone, task | Instrument identity and declared monitoring scenario; dates are necessary PIT context |
| Raw OHLCV, signed raw return and absolute magnitude | Available by cutoff; previous comparable observations and adjustment semantics included |
| Own-history context | Window, observation count, distributions/percentiles/z-scores as available; explicit short/missing history |
| Market-relative context | Benchmark pair/return, signed excess and historical abnormality; preserve raw versus residual distinction |
| Volume / MA / RSI | Raw shares, trailing mean/ratio, previous/current averages/RSI, transition boundaries and magnitude/depth evidence |
| Sector/economic context | Only if in scope, cutoff-valid and sourced; otherwise explicit unavailable, never fabricated |
| Recurrence / episode / prior exposure | Past-only histories and as-of state, prior delivered content/timestamps if the signed task uses it; evidence of history completeness |
| Quality/provenance | Source, adjustment/vintage, fixture/data-gap/staleness flags, timestamp assurance and limitations |

Must not see: model/candidate identity, severity/Base/S/N/C scores, model thresholds, predicted attention, predicted order, final Materiality output, calibration results, detector-emitted status, future prices or episode outcomes, future news/fundamentals, later alerts/user responses, or validation/holdout split status. **Factual MA/RSI predicate boundaries are allowed**; the ban concerns model materiality/eligibility/display thresholds. Administrative aliases must not encode algorithm or split. Custodian-only candidate linkage must not leak through file names, notes or ordering.

Do not research the ticker externally while labeling; external hindsight can contaminate the packet. If a necessary fact is missing, file an evidence request and leave affected judgments unresolved. Current evidence cannot be corrected from memory. Suspected bias from recognizing a historical episode is recorded in reviewer provenance and considered in adjudication.

## 2. Annotation order

Follow this order for every complete stock-day. Preserve stage timestamps and revisions; a later judgment must not silently overwrite an earlier one.

1. **Factual existence:** adjudicate each opportunity under its approved predicate; distinguish does-not-exist, invalid/out-of-scope and unresolved.
2. **Intrinsic severity:** assess existing events on 0–3 using event magnitude and quality-supported context. Lock this first-pass judgment before considering slot competition.
3. **Retention / eligibility:** record retain-for-ranking, retain-unresolved or invalid/out-of-scope. A suspected duplicate is provisional until step 5, with an explicit pending-link reason.
4. **Contextual relevance:** judge each existing event in the full stock-day/task/prior-exposure context. Record preliminary relevance independently of the number of available slots.
5. **Duplicate / same-episode relations:** identify exact factual duplication, shared episode, related distinct and separate events, or unresolved relation. Finalize duplicate retention links, preserving the prior judgment.
6. **Insight units:** construct the complete reference insight set, not just a top three. Independently label insight contextual relevance. Confirm/finalize event relevance after relationship adjudication; record any change from step 4 and its evidence. Do not copy insight relevance to all member events.
7. **Required delivery:** apply the signed product policy per event/insight; record yes/no/unresolved, route and timing. Severity or a slot position is not the rule.
8. **Uncertainty:** record judgment-specific certainty, unavailable inputs and unresolved disagreement. Certainty may be noted earlier; this step verifies it across all stages.
9. **Rationale:** finalize brief evidence-linked explanations distinguishing existence, magnitude, context, duplication and delivery. Confirm completeness and expected empty state.

Then construct the human ordering/reference in §10. Ties and full insight membership must be finalized before extracting Top 1 or Top 3. The confirmation pass in step 6 is necessary because duplicate relationships can alter contextual usefulness; it never permits back-fitting intrinsic severity to a desired ranking. Reviewers annotate independently before discussion.

## 3. Factual event existence

Use `exists`, `does_not_exist`, or `unresolved`, plus an applicability/invalidity reason. `Exists` means the factual predicate holds; it does not mean high attention. `Does_not_exist` means adequate evidence demonstrates the predicate does not hold. `Unresolved` means truth is not established, including absent required evidence or an unapproved predicate. Out-of-scope and corrupt/fixture evidence are separately coded, not treated as known negative opportunities for detector accuracy.

| Family | Required factual check |
|---|---|
| MA cross | Previous/current MA20−MA50 changes from <=0 to >0 or >=0 to <0, under the declared adjacency/source rules. A very small spread can be a valid crossing |
| RSI entry | Previous RSI<=70 and current>70, or previous>=30 and current<30. Remaining in an outer regime is not a new entry; equality at the current boundary is not an entry |
| Abnormal price move | Observe the signed return and quality/history/benchmark evidence, but abnormal-condition existence requires approved D1. A broad price observation candidate is not proof of an abnormal condition |
| Unusual volume | Observe shares volume and historical reference/magnitude, but unusual-condition existence requires approved D1. Price movement cannot establish volume abnormality |

Do not invent a price/volume cutoff from past reviewer notes, model formulas or candidate names. Do not mark an objectively weak but valid transition nonexistent. If required evidence is absent, a plausible event remains unresolved; confidence language cannot turn it into a factual positive. Human disagreement between supported interpretations is preserved for adjudication, not averaged into a pseudo-event.

## 4. Intrinsic severity

Assess **the event itself**, without asking whether it wins today's slot. Record integer `a` in 0–3, or null with a reason. Normalize to `a/3` only in later evaluation; annotators do not produce continuous model scores.

| Level | Human rubric |
|---|---|
| 0 — negligible / no meaningful attention | An existing event carries negligible substantive change under the approved predicate. Mechanical validity alone provides no meaningful attention value |
| 1 — low attention | A discernible, supportable change merits limited notice; its event-specific magnitude or abnormality is modest, even if a transition is valid |
| 2 — materially noteworthy | The event itself represents a meaningful change supported by its primary evidence and appropriate history/context; understanding it materially improves awareness of what changed |
| 3 — highly important / critical attention | The event itself represents an exceptionally consequential or pronounced technical change under the common rubric, strongly supported by primary evidence. This label does not by itself impose an urgent delivery deadline |

These are ordinal anchors, not new numerical detector/severity thresholds. If the rubric cannot distinguish adjacent levels reliably, record low certainty/disagreement; do not invent private thresholds. D6 must resolve pilot rubric/reviewer procedures before annotation.

Magnitude and own-history unusualness are distinct: a statistically unusual tiny move may remain modest, while a large raw move can deserve attention even when market-aligned. Market-relative evidence adds attribution/comparison, not universally superior truth. A signed residual is not proof of a company-specific cause. Supporting signals may strengthen understanding of the target event when relevant, but cannot replace its primary evidence or count correlated indicators as independent confirmations.

Recurrence and prior exposure belong primarily to contextual relevance. Do not lower an otherwise identical intrinsic event merely because it was shown yesterday. Distinguish a fresh factual change from an unchanged state; factual re-entry may depend on prior state, while how often it repeated affects usefulness now. If the actual new increment is smaller, that smaller measured event magnitude can justify different severity; explain the factual difference rather than applying an implicit recurrence penalty.

Uncertain evidence does not imply low severity. Use null when intrinsic severity cannot be assessed, or an explicitly uncertain supported level if enough primary evidence remains; never multiply the human label by reviewer confidence. Absent sector/market evidence alone need not prevent judging a fully evidenced MA transition, but absence of essential magnitude evidence can prevent its severity judgment.

`Does_not_exist` or out-of-scope items have severity null/not-applicable, not attention 0. Factual unresolved items have severity null/unresolved for evaluation; a concern may be documented in the rationale without inventing an ordinary severity label. Historical V1–V3 labels remain authoritative under their original, sometimes recurrence-sensitive rubric; this prospective factorization does not relabel them.

## 5. Contextual relevance

For events and, independently, insight units, answer: **“Given everything else happening for this stock today, how useful/important is this item to show now?”** Consider the full packet, declared monitoring task, new information, same-episode overlap and known prior exposure.

| Level | Contextual rubric |
|---|---|
| 0 | No useful new information to show now under the task; for example fully redundant content already faithfully explained |
| 1 | Some incremental information, but limited current priority; suitable evidence to inspect without requiring prominence |
| 2 | Materially useful information now; adds a meaningful change or explanation in this stock-day context |
| 3 | Highest contextual importance under the common rubric; a particularly consequential current update, without inferring a notification deadline |

Do not rank-normalize labels: a day of weak changes need not contain a 3, and many distinct items can all be 2 or 3. Do not cap the number of positive labels at three. A severe already-explained episode may have low incremental relevance; a moderate new event can be uniquely informative. A duplicate representation can have low standalone relevance while the coherent combined insight retains high relevance. Required delivery is still judged separately.

Unknown prior exposure is not “never shown.” If that uncertainty changes the judgment materially, relevance remains unresolved. D3 must prescribe the evidence/scenario; annotators cannot imagine individual users' preferences. Unavailable sector context is not evidence of zero sector-relative importance. Final event relevance and independent insight relevance serve different metrics and must both be stored.

## 6. Retention / safety

| Judgment | Meaning / required annotation |
|---|---|
| `retain_for_ranking` | Supported in-scope event has usable evidence; low intrinsic/contextual attention alone does not silently delete it |
| `retain_unresolved` | Evidence or existence/interpretation prevents an ordinary judgment; preserve identity, reason and tracking requirement |
| `invalid_out_of_scope` | Demonstrated invalidity or excluded scope under the declared policy; log evidence and applicable rule |
| `linked_duplicate` | Same factual information represented redundantly; link to a valid survivor and keep source identity. Similar episode alone is insufficient to delete a distinct event |

Separately record **may omit from ordinary ranking** (`yes|no|unresolved`), **requires explicit tracking** (`yes|no|unresolved`) and the delivery-obligation link. Omission permission concerns the ordinary ranking surface only; it is not permission to erase the audit record or evade an obligation. A valid duplicate may be omitted only with faithful surviving representation; an uncertain unresolved item may require tracking despite no ordinary rank. Where product policy does not establish permission, answer unresolved.

Intrinsic attention>=2 is the research material-retention target; attention=3 is reported separately. Neither defines a required Top-3 slot. Accounted-for unresolved tracking is different from being rankable and different from being delivered. Annotators must not bless a route merely because a system retained an internal row. In future metrics, an exclusion log is not retention coverage; unknown labels are not TN.

## 7. Required delivery

This field cannot support a safety claim until **D5** is signed. For each relevant event/insight record:

- Required delivery: yes/no/unresolved, with policy version, reason and cited evidence.
- Urgency class and deadline/time basis when defined by policy; otherwise null with policy-unresolved reason.
- Whether ordinary Top-3 display is mandatory, or a named overflow/escalation route is acceptable.
- Acceptable exception/deferment, visibility and acknowledgement requirements, plus what facts must be communicated faithfully.
- Linked source events, insight IDs and uncertainty/adjudication record.

Do not invent deadlines, presume attention 3 always means immediate notification, or use “no” when policy is absent. A rationale can record concern without asserting an obligation unsupported by policy. Delivery yes at contextual relevance 0 is not automatically inconsistent: prior exposure might reduce relevance but an outstanding obligation can remain. Adjudicate under policy instead of editing severity/relevance to remove the conflict.

The full-contract pilot is blocked until obligation and empty/overflow policies exist. A narrower pilot omitting delivery would need separately approved scope and could make no end-to-end safety claim. Overflow obligations must remain visible in the reference ledger even when more than three require communication.

## 8. Duplicates / episodes

Use the same relationship enum as the Benchmark Spec:

| Relation | Evidence to require |
|---|---|
| `same_factual_event` | Two representations refer to the same instrument/family/occurrence and underlying fact; retain source IDs and a valid survivor link |
| `same_episode` | Different valid technical events express one cutoff-supported continuing change/state; coherent evidence links them, not just simultaneous timestamps |
| `related_distinct` | Shared context or correlation exists, but each carries a materially distinct change that must remain inspectable |
| `separate` | Evidence supports distinct changes; no justified duplicate/episode merge |
| `unresolved` | Available evidence or the approved episode protocol cannot settle the relationship |

Same ticker/type within one calendar day is recurrence, not proof of duplication. A price move and RSI entry derived from the same OHLCV can be related without proving two independent causes or confirmations. Opposite direction or a new regime does not automatically close an episode unless the approved protocol says so.

D4 must define anchor, continuation, closure, reversal/re-entry and allowed evidence; no numeric episode gap is supplied here. Use only information available at the cutoff. A later move cannot retrospectively tell a reviewer that an earlier event “began” a known future episode. Custodians may later link split components conservatively to prevent leakage, but that linkage is never shown as past knowledge.

Each relation records event IDs, as-of cutoff, evidence, rationale and adjudicator/version. Exact-duplicate survivor chains must resolve without cycles. Related-distinct must not be silently made transitive into a single insight. Preserve conflicting relations until adjudication; a tentative episode link does not authorize deleting an event.

## 9. Insight unit construction

Construct the **complete end-to-end reference insight set**, including valid events the detector missed. Group events only when one faithful explanation can express a coherent change/episode while preserving every materially distinct constituent fact. Record owning event IDs, coherent description and minimum communicated facts per member. Related supporting facts may be cited across insights, but each reference event has one owning insight or an explicit adjudicated context-only/non-new-update disposition; do not double-count its gain.

A merged insight must not bury a critical constituent behind a generic sentence or an invisible evidence link. Shared indicators cannot be presented as independent corroboration merely because several event types fired. Distinct events requiring distinct explanations remain separate even if grouping would fit the budget. Do not force insight count to three.

Independently annotate insight contextual relevance; do not sum, average or maximize constituent relevance mechanically. Intrinsic material/critical insight membership is a separate reference rule: contains an attention>=2 / attention=3 event. Unknown member severity must remain flagged; if it prevents deciding membership, that membership is unresolved rather than false.

Ambiguous merge/split cases require relation evidence and adjudication before product metrics are valid. Preserve both proposed maps and their rationale. If the packet lacks evidence needed to adjudicate, mark the group reference-incomplete; do not choose the grouping that favors a model. Later system-output faithfulness is assessed blind to model identity under a frozen protocol, after reference labels are frozen, without rewriting the gold map.

## 10. Top-1 / Top-3 human reference

Build the full weak ordering from final contextual relevance on all reference insights. Equal relevance forms an acceptable tie class; no strict preference is implied inside it. An administrative stable-ID order may render the packet, but must not become gold preference or break a label tie in a model's favor. Preserve a complete reference list and ties before deriving the first one/three useful positions.

- Fewer than three useful insights: show only the available useful reference content; no filler negatives. Positive relevance can support a human useful-content reference, while `r>=2` is the separate contextual-material metric target. This does not set a model display threshold.
- Zero useful insights: reference ordinary output is empty when the complete group's insight relevance is all zero. A day containing only relevance 1 differs from a no-useful-change day, even though contextual-material recall is undefined.
- No evidence: use a distinct data-unavailable/unresolved expected state; never label it a confident no-useful-change day.
- More than three material insights: retain the full gold set, ties and demand; report capacity pressure. Do not relabel the fourth to low relevance to make recall attainable.
- Required-event overflow: preserve obligations and acceptable routes separately; overflow does not earn ordinary Top-3 exposure credit.
- Duplicate content: count a reference insight once. A second representation does not create a second relevant slot or independent event confirmation.

For conditional event-ranking evaluation, custodians later project final event labels onto the complete emitted/retained/rankable population from the system ledger. Annotators must not see that membership or rejudge relevance to favor survivors. Conditional ideals use all members of that declared group, not merely returned items; end-to-end product ideals use the full independent reference insight set. Unresolved reference membership/relevance prevents a full-group ideal and must be reported.

Contract metric conventions remain unchanged: linear relevance gain, discount `1/log2(position+1)`, group-macro NDCG@1/@3; human ties excluded from pair comparisons, unequal-human model ties worth half. Actual deterministic score-tie order and neutral expected cutoff metrics are both reported later. Positive singleton returned first has NDCG 1, omitted has 0, with pair metric undefined. Empty/all-zero ideal gives undefined NDCG; no positive class gives undefined recall. Actual filled-slot count is the precision denominator, not a compulsory three. Its numerator counts filled slots providing a distinct faithfully communicated intrinsically material reference insight, at most one positive credit per slot and no extra credit for repetition. Contextual wasted-slot rate is a separate diagnostic, not the complement of intrinsic-material precision. Intrinsic-material recall, contextual recall and required-delivery recall are distinct.

## 11. Event-type guidance

### A. `abnormal_price_move`

Separate five observations: signed raw return, absolute raw magnitude, own-history abnormality, market-relative abnormality, and signed excess versus VN30. Inspect benchmark alignment and availability. A large stock decline during a large index decline may be market-aligned yet attention-worthy in absolute terms. A smaller stock move with substantial residual can provide distinct information. Do not declare one channel universally superior or infer cause from residual alone.

Record attribution `market_aligned|stock_relative|mixed|unresolved` with evidence, under the approved rubric. Preserve raw and excess signs: a positive raw move can still underperform, and a negative move can outperform. These attribution labels support channel-disagreement diagnostics, not ticker-specific or causal rules. Unknown benchmark means attribution can be unresolved while raw return is known. D1 controls factual abnormal-condition truth independently of intrinsic/contextual attention.

### B. `unusual_volume`

Volume is primary. Inspect shares, comparable trading session, trailing mean and sample count, relative volume, historical distribution and adjustment/quality context. A ratio alone may be misleading if denominator/history is invalid. Missing relative volume is unknown magnitude, not average or zero volume. Price movement may support interpretation, but cannot manufacture an unusual-volume condition or substitute for volume magnitude. A quiet price response does not negate objectively unusual volume. D1 must settle elevated/low-volume factual scope before labeling existence.

### C. `ma_cross`

Check transition validity first, then assess crossover spread and its units/normalization, history and supporting context. A very small valid crossing can deserve low attention without becoming false detection. Same-day market-relative price movement must not be mistaken for a large MA spread. It can affect context without changing what the averages did. Direction describes upward/downward crossing, not BUY/SELL advice. Do not assume a large-looking spread alone warrants a preset attention level.

### D. `rsi_regime_entry`

Distinguish entry validity, depth beyond 70/30, price evidence, volume support and recurrence. Staying in a regime is not re-entry; previous/current values are essential. A marginal crossing can be valid with limited intrinsic magnitude; more depth is additional evidence, not an automatic attention-3 rule. Supporting channels may strengthen interpretation, but correlation is not independent confidence. Separate a new entry from how recently the user saw the episode. Missing history cannot be treated as extreme abnormality.

Across all families, apply the same 0–3 meanings, preserve absolute and relative context, and justify differences in attention by evidence. Do not copy old rejection patterns, candidate coefficients or prior case verdicts as rules.

## 12. Missing / uncertain evidence

| State | Meaning / recording |
|---|---|
| Unknown | Value or truth is unavailable; null plus specific missing/availability reason |
| Insufficient evidence | Some facts exist but cannot support the requested judgment; unresolved plus needed evidence |
| Disagreement | Independent reviewers differ despite their recorded evidence; retain both raw judgments and adjudication outcome |
| Low-confidence annotation | A supported judgment is possible but uncertain; retain value with judgment-specific certainty/reason, never numerically shrink it |
| Not applicable | The judgment has no valid subject, e.g. severity of a known nonexistent event; distinct from unresolved existence |

Use reviewer certainty `high|medium|low|unable` separately for existence, severity, relevance, relationships and delivery. `Unable` requires null/unresolved for the affected substantive judgment. These are qualitative annotation records, not calibrated probabilities or score weights. Engine Confidence is not shown and is not inferred from reviewer certainty. The historical Confidence=1 limitation cannot be repaired by fabricating lower engine values.

Never replace null evidence, unknown exposure, missing score or unresolved truth with zero, normal, no-event or safe-to-omit. If an optional channel is absent but primary evidence supports a label, retain the label and limitation. If an essential field is absent, leave the affected label unresolved. Known negative is an affirmative factual conclusion requiring sufficient evidence.

Structural inventory completeness, evidence completeness and reference completeness must remain distinct. Missing reference truth/relevance prevents full-group NDCG and definitive no-material/no-useful-change classification. Known labels can still support explicitly partial event diagnostics with denominators; they cannot imply an end-to-end pass.

## 13. Multi-annotator process

Future pilot groups require independent human first passes before reviewer discussion. D6 must approve reviewer allocation (including multiple independent humans for agreement assessment), qualification, workload, uncertainty objectives and agreement acceptance criteria. No arbitrary agreement threshold or numeric case quota is chosen here.

Reviewers use pseudonymous IDs, handbook/version/hash and identical frozen packet versions. Record role, timestamps, prior familiarity, training/policy acknowledgement and any assistance. Raw annotations are append-only; freeze them before showing another reviewer's answer. An adjudicator then sees evidence, independent judgments and rationales without model identity/scores; resolve conflicts with policy/rubric citations or retain unresolved. Adjudication may not force an integer simply to complete metrics.

Report pre-adjudication agreement separately for factual existence, severity, contextual relevance, retention, required delivery and relations/mappings. Use distributions and ordinal disagreement gaps, agreement on tied preferences and mapping disputes; do not report post-adjudication consensus as independent agreement. The precise statistical agreement/uncertainty procedure is D6, frozen before the pilot; do not select it after observing labels.

AI assistance, if later authorized, requires tool/model/version, prompt/output hashes, fields suggested, evidence available, disclosure and a separate explicit human confirmation record. It does not count as another independent human reviewer. Unassisted and assisted conditions must be distinguished; no silent merging of AI suggestions into raw human labels. This task authorizes no AI labeling or external sharing.

## 14. Annotation consistency checks

These are requirements for a future package audit, not implemented validators:

1. All annotation subjects and evidence references exist in the frozen group; no new post-label membership.
2. `Does_not_exist`/out-of-scope has severity/relevance not-applicable; unresolved existence has ordinary severity unresolved. A valid severity-0/1 event may still exist.
3. Numeric labels are integers 0–3 or explicit null. Certainty cannot serve as a substitute label or engine Confidence.
4. Every opportunity has an existence/applicability disposition; all valid reference events have severity/relevance or explicit unresolved reason.
5. Duplicate links resolve to a valid surviving representation without cycles. Same-episode alone is not a deletion reason.
6. Every owning insight preserves source event IDs and required communicated facts; no source event silently disappears or earns double gain.
7. Material/critical insight flags follow member severity with unknown-status propagation; contextual insight relevance remains independently judged.
8. Required-delivery yes has a policy, reason and evaluable route/timing requirements; unresolved policy cannot be encoded no. No obligation disappears from the reference ledger through budget/grouping.
9. A finalized complete ranking/reference group has no missing relevant membership, relevance or tie class. An affected incomplete group must not supply full-group ideal metrics.
10. No-useful-change and no-event states agree with the complete underlying reference; data-unavailable is separate. More than three positive/material labels is valid.
11. Prior-event recurrence and delivered-exposure histories are separate, past-only and consistent with cutoff. Never infer an alert from an event record.
12. Independent raw records and later adjudication have distinct IDs/lineage; changes are explained, versioned and do not erase disagreements.
13. Rationale cites available evidence rather than future outcomes, candidate scores or expected model performance. Identical rubric terms mean the same thing across four families.
14. Stage completion/revisions follow §2; finalized duplicate/context judgments preserve earlier provisional records. No retroactive severity edit merely to fit a Top-3 reference.

Any defect blocks the affected finalization until repaired or explicitly marked unresolved. A policy defect affecting all groups blocks the pilot, not just one row. There is no “close enough” silent null-to-zero correction.

## 15. Practice examples

**Synthetic and illustrative only. These are not sampled stock-days, benchmark labels, detector thresholds or scoring instructions.** No protected or V3 individual case is used.

- **Tiny valid transition:** consecutive valid synthetic MA differences go from slightly negative to slightly positive. Existence and magnitude are separate questions. The reviewer must not mark the transition nonexistent merely because the spread is small, and must not let a large same-day residual rewrite the spread.
- **Known severe episode already explained:** a hypothetical event has strong primary evidence, while an audited prior message already explained the continuing episode. Preserve its intrinsic judgment; independently assess whether today's new update adds useful content. Check any outstanding required-delivery obligation under policy instead of assuming prior exposure canceled it.
- **Unknown volume denominator:** today's shares count is present but comparable trailing history is absent. Do not label volume average/zero, infer abnormality from price alone, or assert a confident no-useful-change day. Record which factual/severity judgments remain possible and which are unresolved.
- **Capacity and duplication:** a hypothetical complete day contains four independently established distinct material changes plus two duplicate representations. Duplicates do not increase distinct demand; three slots cannot cover four distinct changes. Keep full reference membership and actual omissions visible, with separately adjudicated obligations. Do not merge unrelated changes merely to fit three.

These examples clarify logical boundaries without supplying target numeric labels. Actual practice annotations, if authorized later, must follow the approved protocol and remain separate from assessment data.

## 16. Annotation freeze procedure

Exact future order:

**Benchmark evidence freeze → blinded independent annotation → raw-label freeze → adjudication → reconciled-label freeze → metric evaluation.**

Before the first arrow, D1–D6 and generation/pilot authorization must be resolved and the package pass the Benchmark Spec's readiness checks. Freeze sources, packet hashes, opportunity/group membership, presentation order, task/exposure assumptions, handbook and assignment. No candidate score or ranking may be opened to annotators/adjudicators before the reconciled-label freeze; custodian access is separated and audited.

Raw-label freeze includes original individual values, uncertainties, rationales, AI-assistance provenance if any, timestamps and hashes. Reconciled-label freeze includes every adjudication/remaining dispute, final event severity/context, retention, mappings, independently judged insight relevance/ties, delivery obligations and completeness eligibility. Preserve the raw archive independently.

Candidate code/config, future stage logs, metric definitions, matching/faithfulness protocol and D7 acceptance gates must be frozen before any model comparison. This handbook does not authorize that comparison. Blind post-output faithfulness adjudication may label communication/matches under its frozen rubric; it cannot revise reference labels or inventory after seeing results. Unknown matches are reported rather than forced to improve coverage.

Evidence defects discovered during annotation suspend affected groups. A corrected packet/rubric creates a new version and requires a new independent blind pass for affected judgments; the old raw labels are preserved as superseded evidence. After unblinding, no rubric repair is an excuse to retune on protected validation or rewrite past outcomes. Follow the separate study stopping/correction policy.

## 17. Annotation Readiness Decision

**B. One or more product/research decisions must be resolved before pilot.** The handbook is structurally complete as a prospective field/rubric/workflow contract, but cannot yet produce reliable full-contract labels without these exact decisions:

| Shared ID | Blocker before pilot |
|---|---|
| D1 | Approve price/volume factual abnormal-condition predicates and negative/unknown rules; broad observations cannot stand in for existence truth |
| D2 | Approve authorized fresh historical frame, cutoff/availability, continuity/adjustment and evidence policy; no allowed pilot packet exists yet |
| D3 | Define the monitoring task, newly observable episode updates and audited versus controlled prior-exposure scenario |
| D4 | Operationalize episode/duplicate/continuation/closure/re-entry rules and partition boundary isolation before reference grouping |
| D5 | Define required delivery, deadlines, route/acknowledgement, ordinary display versus overflow and empty-state policy |
| D6 | Approve pilot budget/selection/uncertainty, independent-human allocation, agreement/adjudication procedures and rubric acceptance |

D7 (layered model-evaluation gates) remains a later required freeze before model evaluation; it does not justify inventing annotation thresholds now. The next step is documented owner resolution of D1–D6 and approval of both document versions. Only a **separate explicit authorization** may then start benchmark generation, integrity audit and blinded pilot annotation in that order. This design stops without cases, labels, scores, implementation, V4/V5, tuning, protected-data access or Final Validation.
