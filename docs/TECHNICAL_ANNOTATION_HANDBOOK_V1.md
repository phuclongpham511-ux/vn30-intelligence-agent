# Technical Annotation Handbook V1

Date: 2026-10-02; D1/D2 governance updates: 2026-10-03. Status: **prospective handbook; readiness B — decisions required before pilot**. This handbook defines human judgments for a future complete stock-day benchmark. It creates no labels and does not reinterpret historical V1–V3 attention/verdicts.

Primary authority: [Evaluation Contract V2](TECHNICAL_MATERIALITY_EVALUATION_CONTRACT_V2.md). Companion: [Stock-Day Benchmark Specification V1](TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md), especially its normative glossary, artifact fields and D1–D7 decision register. The [Architecture Review](TECHNICAL_MATERIALITY_ARCHITECTURE_REVIEW.md) explains why these judgments must be separated. If this handbook conflicts with Contract V2, stop the affected annotation and record a design defect; do not silently choose a new interpretation.

The task is: **“What changed today in this stock that deserves my attention?”** [D3 — APPROVED](TECHNICAL_D3_MONITORING_CONTEXT_DECISION.md) represents one user monitoring one stock at EOD, one ticker/date/cutoff, technical domain only. Portfolio position, unrealized gain/loss, investment thesis, risk tolerance, personalized preferences, fundamentals, news and cross-stock ranking are out of scope. Use `prior_exposure_mode = CONTROLLED_AS_IF_EMPTY`: assume no previous system technical insight was shown, as a controlled scenario rather than observed behavior. Do not fabricate delivery/acknowledgement history or infer that yesterday's event was seen. PIT-safe market history and recurrence are separate and may be visible. Only today's predicate-defined factual changes enter today's event set; yesterday's MA cross followed by unchanged ordering is contextual history, not a new cross. Attention is not expected return, bullishness or investment advice. Positive and negative direction describe facts, not desirability. This is a technical, single-stock, end-of-day task; it does not cover cross-stock portfolio ranking or other domains.

Terminology is identical to the Benchmark Spec: an **opportunity** is an independent factual check; an **event** is a factual transition/abnormal condition; an **emitted candidate** is system output; a **reference event** is an independently adjudicated exists opportunity. A **stock-day** includes the full opportunity inventory at its cutoff, while the **ranking group** is the conditional emitted/retained/rankable population. An **episode** is a cutoff-supported continuing change/state within the same event family and instrument, and an **insight unit** is one coherent change preserving source reference-event IDs. **Severity** is intrinsic attention; **contextual relevance** is usefulness now; **retention** is a disposition; **required delivery** is a separate policy-grounded obligation. **Unresolved** is not zero/no. **Top 1–3** means at most three ordinary display slots, excluding overflow.

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
| Recurrence / episode / prior exposure | PIT-safe market/technical state and recurrence, plus explicit CONTROLLED_AS_IF_EMPTY scenario; no prior delivered content/timestamps or acknowledgement logs in V1 |
| Quality/provenance | Source, adjustment/vintage, fixture/data-gap/staleness flags, timestamp assurance and limitations |

Must not see: model/candidate identity, severity/Base/S/N/C scores, model thresholds, predicted attention, predicted order, final Materiality output, calibration results, detector-emitted status, future prices or episode outcomes, future news/fundamentals, later alerts/user responses, or validation/holdout split status. **Approved factual predicate boundaries (MA/RSI and D1 q95) are allowed**; the ban concerns model materiality/eligibility/display thresholds. Administrative aliases must not encode algorithm or split. Custodian-only candidate linkage must not leak through file names, notes or ordering.

Under [D2 V2 — APPROVED / ACTIVE](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md), annotators may see only evidence visible by **23:59:59 Asia/Ho_Chi_Minh on the trading date**. The official stock-day frame is `2020-01-01 <= session_date < 2025-01-01`; separately authorized PIT-valid pre-2020 warm-up does not become benchmark stock-days or expand sampling eligibility; membership and protected-case exclusions are custodian checks, not permission to reveal split status. Distinguish **audited publication time**, **EOD_AVAILABILITY_ASSUMPTION / assurance=assumed**, and **unavailable evidence**. A daily observation date or download timestamp does not prove market-close publication. Preserve source/snapshot, assumed available_at, adjustment semantics and quality flags in the view; do not describe assumed timing as verified.

MA/RSI may include the valid cutoff-visible current bar, but D1 references still exclude today and require 60–252 valid comparable prior observations. Missing transition continuity or essential price/volume comparability produces UNRESOLVED. Mechanical corporate-action discontinuities are not genuine abnormal returns without a verified comparable PIT-valid series. Missing aligned VN30(t-1)/VN30(t) leaves market context null with a reason, not an automatic negative/unresolved D1 event. Do not fill evidence from prior/future values or outside research. D2 makes no intraday/alert-latency claim and does not alter any attention, episode or delivery judgment.

Do not research the ticker externally while labeling; external hindsight can contaminate the packet. If a necessary fact is missing, file an evidence request and leave affected judgments unresolved. Current evidence cannot be corrected from memory. Suspected bias from recognizing a historical episode is recorded in reviewer provenance and considered in adjudication.

## 2. Annotation order

Follow this order for every complete stock-day. Preserve stage timestamps and revisions; a later judgment must not silently overwrite an earlier one.

1. **Factual existence:** adjudicate each opportunity under its approved predicate; distinguish does-not-exist, invalid/out-of-scope and unresolved.
2. **Intrinsic severity:** assess existing events on 0–3 using event magnitude and quality-supported context. Lock this first-pass judgment before considering slot competition.
3. **Retention / eligibility:** record retain-for-ranking, retain-unresolved or invalid/out-of-scope. A suspected duplicate is provisional until step 5, with an explicit pending-link reason.
4. **Contextual relevance:** judge each existing event in the full stock-day/task/prior-exposure context. Record preliminary relevance independently of the number of available slots.
5. **Duplicate / same-episode relations:** identify exact factual duplication, shared episode, related distinct and separate events, or unresolved relation. Finalize duplicate retention links, preserving the prior judgment.
6. **Insight units:** construct the complete reference insight set, not just a top three. Independently label insight contextual relevance. Confirm/finalize event relevance after relationship adjudication; record any change from step 4 and its evidence. Do not copy insight relevance to all member events.
7. **Required delivery:** record the approved D5 value NO for ordinary Technical V1 insights, with policy/version; do not infer an obligation from severity or rank.
8. **Uncertainty:** record judgment-specific certainty, unavailable inputs and unresolved disagreement. Certainty may be noted earlier; this step verifies it across all stages.
9. **Rationale:** finalize brief evidence-linked explanations distinguishing existence, magnitude, context, duplication and delivery. Confirm completeness and expected empty state.

Then construct the human ordering/reference in §10. Ties and full insight membership must be finalized before extracting Top 1 or Top 3. The confirmation pass in step 6 is necessary because duplicate relationships can alter contextual usefulness; it never permits back-fitting intrinsic severity to a desired ranking. Reviewers annotate independently before discussion.

## 3. Factual event existence

Use `exists`, `does_not_exist`, or `unresolved`, plus an applicability/invalidity reason. `Exists` means the factual predicate holds; it does not mean high attention. `Does_not_exist` means adequate evidence demonstrates the predicate does not hold. `Unresolved` means truth is not established, including absent required evidence or an unapproved predicate. Out-of-scope and corrupt/fixture evidence are separately coded, not treated as known negative opportunities for detector accuracy.

| Family | Required factual check |
|---|---|
| MA cross | Previous/current MA20−MA50 changes from <=0 to >0 or >=0 to <0, under the declared adjacency/source rules. A very small spread can be a valid crossing |
| RSI entry | Previous RSI<=70 and current>70, or previous>=30 and current<30. Remaining in an outer regime is not a new entry; equality at the current boundary is not an entry |
| Abnormal price move | Apply approved D1: absolute daily stock return >= prior absolute-return empirical q95 is EXISTS; below is DOES_NOT_EXIST; insufficient/invalid required evidence is UNRESOLVED. Preserve signed up/down direction (genuine zero stays zero/neutral). Market-relative evidence does not determine existence |
| Unusual volume | Apply approved D1: current daily volume >= prior comparable volume empirical q95 is EXISTS; below is DOES_NOT_EXIST; insufficient/invalid required evidence is UNRESOLVED. HIGH volume only; low-volume abnormality is out of scope. Price cannot establish volume abnormality |

[D1 — APPROVED](TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md) uses up to the previous 252 valid comparable trading-session observations, minimum 60, excluding the current observation. Empirical q95 is the sorted one-based historical value at ceil(95*n/100), without interpolation; equality is EXISTS. Do not compare the legacy midrank context value to 0.95 or round evidence before comparison. The predicate and its frozen comparison evidence may be shown to annotators; it is not a candidate score.

Do not invent a price/volume cutoff from past reviewer notes, model formulas or candidate names. Do not mark an objectively weak but valid transition nonexistent. If required evidence is absent, a plausible event remains unresolved; confidence language cannot turn it into a factual positive. Human disagreement between supported interpretations is preserved for adjudication, not averaged into a pseudo-event.

## 4. Intrinsic severity

Assess **the event itself**, without asking whether it wins today's slot. Record integer `a` in 0–3, or null with a reason. Normalize to `a/3` only in later evaluation; annotators do not produce continuous model scores.

| Level | Human rubric |
|---|---|
| 0 — negligible / no meaningful attention | An existing event carries negligible substantive change under the approved predicate. Mechanical validity alone provides no meaningful attention value |
| 1 — low attention | A discernible, supportable change merits limited notice; its event-specific magnitude or abnormality is modest, even if a transition is valid |
| 2 — materially noteworthy | The event itself represents a meaningful change supported by its primary evidence and appropriate history/context; understanding it materially improves awareness of what changed |
| 3 — highly important / critical attention | The event itself represents an exceptionally consequential or pronounced technical change under the common rubric, strongly supported by primary evidence. This label does not by itself impose an urgent delivery deadline |

These are ordinal anchors, not new numerical detector/severity thresholds. If the rubric cannot distinguish adjacent levels reliably, record low certainty/disagreement; do not invent private thresholds. Apply the approved D6 independent review and judgment-specific diagnostics; actual annotation still requires separate generation/pilot authorization.

Magnitude and own-history unusualness are distinct: a statistically unusual tiny move may remain modest, while a large raw move can deserve attention even when market-aligned. Market-relative evidence adds attribution/comparison, not universally superior truth. A signed residual is not proof of a company-specific cause. Supporting signals may strengthen understanding of the target event when relevant, but cannot replace its primary evidence or count correlated indicators as independent confirmations.

Recurrence and prior exposure belong primarily to contextual relevance. Do not lower an otherwise identical intrinsic event merely because it was shown yesterday. Distinguish a fresh factual change from an unchanged state; factual re-entry may depend on prior state, while how often it repeated affects usefulness now. If the actual new increment is smaller, that smaller measured event magnitude can justify different severity; explain the factual difference rather than applying an implicit recurrence penalty.

Uncertain evidence does not imply low severity. Use null when intrinsic severity cannot be assessed, or an explicitly uncertain supported level if enough primary evidence remains; never multiply the human label by reviewer confidence. Absent sector/market evidence alone need not prevent judging a fully evidenced MA transition, but absence of essential magnitude evidence can prevent its severity judgment.

`Does_not_exist` or out-of-scope items have severity null/not-applicable, not attention 0. Factual unresolved items have severity null/unresolved for evaluation; a concern may be documented in the rationale without inventing an ordinary severity label. Historical V1–V3 labels remain authoritative under their original, sometimes recurrence-sensitive rubric; this prospective factorization does not relabel them.

## 5. Contextual relevance

For events and, independently, insight units, answer: **“Given everything else happening for this stock today, how useful/important is this item to show now?”** Consider the full packet, declared monitoring task, new information, same-episode overlap and known prior exposure.

| Level | Contextual rubric |
|---|---|
| 0 | No useful new information to show now under the task; for example a redundant representation of the same current change |
| 1 | Some incremental information, but limited current priority; suitable evidence to inspect without requiring prominence |
| 2 | Materially useful information now; adds a meaningful change or explanation in this stock-day context |
| 3 | Highest contextual importance under the common rubric; a particularly consequential current update, without inferring a notification deadline |

Do not rank-normalize labels: a day of weak changes need not contain a 3, and many distinct items can all be 2 or 3. Do not cap the number of positive labels at three. An ongoing market episode may have limited incremental information today; a moderate new event can be uniquely informative. Under D3 V1 no event is considered already shown to the user, so assumed prior delivery must not reduce novelty or relevance. A duplicate representation can have low standalone relevance while the coherent combined insight retains high relevance. Required delivery is still judged separately.

D3 V1 explicitly uses CONTROLLED_AS_IF_EMPTY, so prior exposure is a controlled scenario rather than a missing real-world ledger. Do not infer previous delivery or reduce novelty/relevance because a user probably saw a prior event. Factual recurrence remains visible as market history. Annotators cannot imagine portfolio, thesis, risk tolerance or personalized preferences. Unavailable sector context is not evidence of zero sector-relative importance. Final event relevance and independent insight relevance serve different metrics and must both be stored.

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

[D5 - APPROVED](TECHNICAL_D5_DELIVERY_POLICY_DECISION.md) resolves ordinary Technical V1 insights to **required_delivery = NO** (machine `no`). Record this policy/version as the reason; it is not an unresolved judgment. Unknown factual evidence, severity or relevance stays unknown and is never turned into attention zero by this delivery value.

Intrinsic severity, including severity 3, does not force display, bypass the maximum-three budget, create an overflow alert or trigger push/email. Ranking selects the ordinary current EOD response. No push/email/SMS, urgent escalation, acknowledgement tracking, notification deadline beyond the response or mandatory overflow route is introduced. Those require a future product-policy version.

No hard delivery obligations exist in V1. Required-delivery metrics without a positive obligation denominator are undefined/not applicable, not perfect safety coverage. Annotators still preserve material/critical membership and ordinary display omissions; retention and coverage are distinct from mandatory delivery.

## 8. Duplicates / episodes

Use the same relationship enum as the Benchmark Spec:

| Relation | Evidence to require |
|---|---|
| `same_factual_event` | Two representations refer to the same instrument/family/occurrence and underlying fact; retain source IDs and a valid survivor link |
| `same_episode` | Same-family events/state belong to the same cutoff-supported continuing episode under D4; shared timestamps or cross-family correlation do not establish episode identity |
| `related_distinct` | Shared context or correlation exists, but each carries a materially distinct change that must remain inspectable |
| `separate` | Evidence supports distinct changes; no justified duplicate/episode merge |
| `unresolved` | Available evidence or the approved episode protocol cannot settle the relationship |

Recurrence alone does not prove factual duplication. Consecutive same-direction factual price events continue one episode; a valid non-abnormal day closes it, and opposite-direction abnormality closes it and starts a new episode. Consecutive factual HIGH-volume events continue one episode; a valid non-abnormal day closes it and later re-entry starts a new one. Missing continuity is UNRESOLVED.

[D4 - APPROVED](TECHNICAL_D4_EPISODE_POLICY_DECISION.md) defines anchor/start, continuation, confirmed closure and new episode on re-entry. No fixed N-day gap rule. Missing/ambiguous/non-comparable continuity is UNRESOLVED, never silently bridged or closed. A later move cannot rewrite earlier cutoff knowledge. Cross-family events retain separate episode IDs; related events may later share an insight without sharing an episode.


MA: a factual upward/downward cross anchors the bullish/bearish MA regime. Continuing that regime is the same episode, not a daily cross; a reverse factual cross closes the previous episode and starts the opposite one. RSI: upper entry continues while RSI>70 and closes on valid RSI<=70; lower entry continues while RSI<30 and closes on valid RSI>=30. Later factual re-entry starts a new episode; continuing state does not create another entry. Missing/ambiguous state continuity is UNRESOLVED.

An episode spanning Development/Fresh Validation, or unresolved continuity near that boundary, requires quarantine of affected episode/groups from Fresh Validation. Do not move protected/reserved groups into development or apply a fixed-day embargo to simulate isolation. This is a later construction constraint, not permission to inspect or allocate groups now.

Each relation records event IDs, as-of cutoff, evidence, rationale and adjudicator/version. Exact-duplicate survivor chains must resolve without cycles. Related-distinct must not be silently made transitive into a single insight. Preserve conflicting relations until adjudication; a tentative episode link does not authorize deleting an event.

## 9. Insight unit construction

Construct the **complete end-to-end reference insight set**, including valid events the detector missed. Group events only when one faithful explanation can express a coherent change/episode while preserving every materially distinct constituent fact. Record owning event IDs, coherent description and minimum communicated facts per member. Related supporting facts may be cited across insights, but each reference event has one owning insight or an explicit adjudicated context-only/non-new-update disposition; do not double-count its gain.

A merged insight must not bury a critical constituent behind a generic sentence or an invisible evidence link. Shared indicators cannot be presented as independent corroboration merely because several event types fired. Distinct events requiring distinct explanations remain separate even if grouping would fit the budget. Do not force insight count to three.

Independently annotate insight contextual relevance; do not sum, average or maximize constituent relevance mechanically. Intrinsic material/critical insight membership is a separate reference rule: contains an attention>=2 / attention=3 event. Unknown member severity must remain flagged; if it prevents deciding membership, that membership is unresolved rather than false.

Ambiguous merge/split cases require relation evidence and adjudication before product metrics are valid. Preserve both proposed maps and their rationale. If the packet lacks evidence needed to adjudicate, mark the group reference-incomplete; do not choose the grouping that favors a model. Later system-output faithfulness is assessed blind to model identity under a frozen protocol, after reference labels are frozen, without rewriting the gold map.

## 10. Top-1 / Top-3 human reference

Build the full weak ordering from final contextual relevance on all reference insights. Equal relevance forms an acceptable tie class; no strict preference is implied inside it. An administrative stable-ID order may render the packet, but must not become gold preference or break a label tie in a model's favor. Preserve a complete reference list and ties before deriving the first one/three useful positions.

- Fewer than three useful insights: return only 1 or 2 when that is the useful count; no filler. The maximum ordinary output is 3 ranked insights. This policy does not set a numeric model display threshold or alter contextual labels.
- Zero useful insights with complete evidence: zero ordinary cards and expected state `NO_MEANINGFUL_TECHNICAL_CHANGE`. Do not confuse no-useful-change with no-material or no-event; keep existing relevance semantics.
- Insufficient/unresolved evidence: zero ordinary cards and expected state `TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE`, distinct from complete no-change. Missing evidence is not evidence that nothing happened.
- More than three useful/material insights: preserve the full reference set, rank the complete eligible set, display only Top 3 and retain later insights as diagnostic overflow. Do not lower labels to fit capacity; overflow earns no ordinary Top-3 exposure credit.
- Required delivery: NO for ordinary Technical V1 insights. Severity 3 does not create a mandatory Top-3 slot, overflow alert or notification. Overflow is diagnostic, with no mandatory route.
- Duplicate content: count a reference insight once. A second representation does not create a second relevant slot or independent event confirmation.

For conditional event-ranking evaluation, custodians later project final event labels onto the complete emitted/retained/rankable population from the system ledger. Annotators must not see that membership or rejudge relevance to favor survivors. Conditional ideals use all members of that declared group, not merely returned items; end-to-end product ideals use the full independent reference insight set. Unresolved reference membership/relevance prevents a full-group ideal and must be reported.

Contract metric conventions remain unchanged: linear relevance gain, discount `1/log2(position+1)`, group-macro NDCG@1/@3; human ties excluded from pair comparisons, unequal-human model ties worth half. Actual deterministic score-tie order and neutral expected cutoff metrics are both reported later. Positive singleton returned first has NDCG 1, omitted has 0, with pair metric undefined. Empty/all-zero ideal gives undefined NDCG; no positive class gives undefined recall. Actual filled-slot count is the precision denominator, not a compulsory three. Its numerator counts filled slots providing a distinct faithfully communicated intrinsically material reference insight, at most one positive credit per slot and no extra credit for repetition. Contextual wasted-slot rate is a separate diagnostic, not the complement of intrinsic-material precision. Intrinsic-material recall, contextual recall and required-delivery recall are distinct.

## 11. Event-type guidance

### A. `abnormal_price_move`

Separate five observations: signed raw return, absolute raw magnitude, own-history abnormality, market-relative abnormality, and signed excess versus VN30. Inspect benchmark alignment and availability. A large stock decline during a large index decline may be market-aligned yet attention-worthy in absolute terms. A smaller stock move with substantial residual can provide distinct information. Do not declare one channel universally superior or infer cause from residual alone.

Record attribution `market_aligned|stock_relative|mixed|unresolved` with evidence, under the approved rubric. Preserve raw and excess signs: a positive raw move can still underperform, and a negative move can outperform. These attribution labels support channel-disagreement diagnostics, not ticker-specific or causal rules. Unknown benchmark means attribution can be unresolved while raw return is known. D1 controls factual abnormal-condition truth independently of intrinsic/contextual attention.

### B. `unusual_volume`

Volume is primary. Inspect shares, comparable trading session, trailing mean and sample count, relative volume, historical distribution and adjustment/quality context. A ratio alone may be misleading if denominator/history is invalid. Missing relative volume is unknown magnitude, not average or zero volume. Price movement may support interpretation, but cannot manufacture an unusual-volume condition or substitute for volume magnitude. A quiet price response does not negate objectively unusual volume. D1 is approved for HIGH volume only using the empirical q95 predicate. Low-volume abnormality is out of scope; no relative-volume-ratio gate is added. If raw comparable volume and its valid history suffice for q95, a missing optional ratio does not by itself make existence unresolved.

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

**[D6 — APPROVED](TECHNICAL_D6_STUDY_REVIEWER_DECISION.md):** Development/Pilot comprises 120 stock-days (80 Representative + 40 Enriched Diagnostic); Fresh Validation reserves 60 separately. Reviewer A reviews 120/120 Development, Reviewer B independently reviews a reproducible deterministic/random 30% subset (target 36/120); both independently review 60/60 Fresh Validation. Freeze sampling frame/version, inclusion/exclusion rules, component definitions, deterministic seed, algorithm and replacement policy before sampling. Freeze the B subset before labels; no manual selection of interesting days. Quotas are approved research allocations, not a universal statistical optimum.

Representative selection is independent of detector output, model score and human label. Enrichment uses only frozen evidence-based conditions, never model scores, attention labels or expected verdicts; it does not redefine D2 eligibility. Report Representative and Enriched separately; enrichment is not a prevalence estimate. D4 episode isolation/quarantine remains authoritative, with no fixed-day substitute. Neither reviewer sees model/candidate scores, predicted ranking, detector-emitted status or other reviewer labels before independent submission.

Reviewers use pseudonymous IDs, handbook/version/hash and identical frozen packet versions. Record role, timestamps, prior familiarity, training/policy acknowledgement and any assistance. Raw annotations are append-only; freeze them before showing another reviewer's answer. An adjudicator then sees evidence, independent judgments and rationales without model identity/scores; resolve conflicts with policy/rubric citations or retain unresolved. Adjudication may not force an integer simply to complete metrics.

Report pre-adjudication factual existence exact agreement; severity/contextual relevance exact agreement, one-level disagreement and large disagreement >=2 levels; episode/duplicate/relationship exact relation agreement and unresolved/disputed relation rates. Also report unresolved rates, reasons, denominators and affected groups, preserving other retention/delivery/tied-preference diagnostics. Do not count singly reviewed groups or adjudicated consensus as independent paired agreement. Raw judgments remain append-only; separate adjudication preserves original labels, rationale, result, adjudicator identity/version and unresolved status. No arbitrary global threshold such as 80% agreement = PASS applies. These diagnostics feed the Decision Review Protocol, especially Reliability, Clarity and Operationalizability. Predeclare applicable uncertainty methods before analysis; missing judgments do not become zero.

Development evidence may support separately authorized diagnostics, Decision Review, model development and debugging. Quota revision requires D6 V2, never a silent post-result change. Fresh Validation is protected from individual-case/label development tuning and iterative D redesign, and evaluated only after D-family, benchmark and required candidate freezes. A severe design defect invalidates that validation cycle: return to Development review, create justified Dn V2, then reserve a NEW Fresh Validation set. Do not repeatedly tune against the failed set. Existing 2025–2026 holdout remains sealed and unenumerated; D6 grants no access.

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
8. D5 V1 delivery value is NO under the approved policy; notification urgency/deadlines, mandatory overflow and acknowledgement are not applicable. Unknown factual labels remain unknown. Any future policy introducing yes requires a separate version; no ordinary V1 insight is silently given a hard obligation.
9. A finalized complete ranking/reference group has no missing relevant membership, relevance or tie class. An affected incomplete group must not supply full-group ideal metrics.
10. No-useful-change and no-event states agree with the complete underlying reference; data-unavailable is separate. More than three positive/material labels is valid.
11. Prior-event recurrence is PIT-safe market history; prior exposure is CONTROLLED_AS_IF_EMPTY. No prior delivery/acknowledgement history is available in V1. Never infer an alert from an event record.
12. Independent raw records and later adjudication have distinct IDs/lineage; changes are explained, versioned and do not erase disagreements.
13. Rationale cites available evidence rather than future outcomes, candidate scores or expected model performance. Identical rubric terms mean the same thing across four families.
14. Stage completion/revisions follow §2; finalized duplicate/context judgments preserve earlier provisional records. No retroactive severity edit merely to fit a Top-3 reference.

Any defect blocks the affected finalization until repaired or explicitly marked unresolved. A policy defect affecting all groups blocks the pilot, not just one row. There is no “close enough” silent null-to-zero correction.

## 15. Practice examples

**Synthetic and illustrative only. These are not sampled stock-days, benchmark labels, detector thresholds or scoring instructions.** No protected or V3 individual case is used.

- **Tiny valid transition:** consecutive valid synthetic MA differences go from slightly negative to slightly positive. Existence and magnitude are separate questions. The reviewer must not mark the transition nonexistent merely because the spread is small, and must not let a large same-day residual rewrite the spread.
- **Continuing market state:** yesterday's synthetic MA cross leaves MA20 above MA50 today. The state remains contextual market history; it does not create a new cross today unless the approved predicate fires again. Under CONTROLLED_AS_IF_EMPTY, do not invent a previous message or discount relevance for assumed prior delivery.
- **Unknown volume denominator:** today's shares count is present but comparable trailing history is absent. Do not label volume average/zero, infer abnormality from price alone, or assert a confident no-useful-change day. Record which factual/severity judgments remain possible and which are unresolved.
- **Capacity and duplication:** a hypothetical complete day contains four independently established distinct material changes plus two duplicate representations. Duplicates do not increase distinct demand; three slots cannot cover four distinct changes. Keep full reference membership and actual omissions visible, with separately adjudicated obligations. Do not merge unrelated changes merely to fit three.

These examples clarify logical boundaries without supplying target numeric labels. Actual practice annotations, if authorized later, must follow the approved protocol and remain separate from assessment data.

## 16. Annotation freeze procedure

Exact future order:

**Benchmark evidence freeze → blinded independent annotation → raw-label freeze → adjudication → reconciled-label freeze → metric evaluation.**

Before the first arrow, D1-D6 are approved, but separate explicit Benchmark Generation Authorization is still required. Freeze sources, packets, group membership, order, task context, handbook and assignment, including D6 reproducible sampling and independent reviewer allocation. Candidate scores/ranks remain blinded until reconciled labels are frozen.

Raw-label freeze includes original individual values, uncertainties, rationales, AI-assistance provenance if any, timestamps and hashes. Reconciled-label freeze includes every adjudication/remaining dispute, final event severity/context, retention, mappings, independently judged insight relevance/ties, delivery obligations and completeness eligibility. Preserve the raw archive independently.

Candidate code/config, future stage logs, metric definitions, matching/faithfulness protocol and D7 acceptance gates must be frozen before any model comparison. This handbook does not authorize that comparison. Blind post-output faithfulness adjudication may label communication/matches under its frozen rubric; it cannot revise reference labels or inventory after seeing results. Unknown matches are reported rather than forced to improve coverage.

Evidence defects discovered during annotation suspend affected groups. A corrected packet/rubric creates a new version and requires a new independent blind pass for affected judgments; the old raw labels are preserved as superseded evidence. After unblinding, no rubric repair is an excuse to retune on protected validation or rewrite past outcomes. Follow the separate study stopping/correction policy.

## 17. Annotation Readiness Decision

**D1–D6 design decisions APPROVED; generation/pilot NOT AUTHORIZED.** The handbook is a prospective field/rubric/workflow contract. Separate explicit Benchmark Generation Authorization, frozen execution specifications and construction integrity checks remain required; approval does not certify any generated data or labels.

| Shared ID | Approved decision / execution prerequisite |
|---|---|
| D1 — APPROVED (not a remaining blocker) | [Approved factual predicates](TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md): own-history q95, absolute return / HIGH volume, inclusive equality, prior-only 252 valid observations maximum / 60 minimum; UNRESOLVED for insufficient/invalid evidence |
| D2 V2 — APPROVED / ACTIVE (not a remaining policy blocker) | [Approved frame/PIT policy](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md): 2020–2024 historical VN30 stock-day frame, with authorized warm-up separate from sampling; 23:59:59 Asia/Ho_Chi_Minh; assumed EOD availability explicitly distinguished from audited timing. No pilot packet generated or certified |
| D3 — APPROVED (not a remaining blocker) | [Monitoring Context V1](TECHNICAL_D3_MONITORING_CONTEXT_DECISION.md): one-stock technical EOD monitoring; CONTROLLED_AS_IF_EMPTY; market history distinct from user exposure; today's factual changes only |
| D4 - APPROVED (not a remaining blocker) | [Episode Policy V1](TECHNICAL_D4_EPISODE_POLICY_DECISION.md): family-specific lifecycle; unresolved continuity preserved; Development/Fresh Validation boundary quarantine; no fixed-day shortcut |
| D5 - APPROVED (not a remaining blocker) | [Delivery Policy V1](TECHNICAL_D5_DELIVERY_POLICY_DECISION.md): maximum 3/no filler; distinct no-change and incomplete-data empty states; diagnostic overflow; required_delivery=NO, current EOD response only |
| D6 — APPROVED (not a remaining design blocker) | [Study & Reviewer Design V1](TECHNICAL_D6_STUDY_REVIEWER_DECISION.md): 120 Development (80 Representative + 40 Enriched), 60 Fresh Validation; A covers all, B covers 30% Development and 100% Validation independently; preserved raw labels, typed agreement diagnostics, reproducible frozen sampling and D4 isolation |

D1-D6 design blockers are resolved. D7 remains LATER MODEL-EVALUATION ACCEPTANCE. BENCHMARK GENERATION IS STILL NOT AUTHORIZED pending separate explicit approval; do not start benchmark/model work or proceed to D7.
