# Technical Stock-Day Benchmark Specification V1

Date: 2026-10-02. Status: **design complete with explicit authorization blockers; not ready for generation or annotation**. Normative requirements below apply to a future separately authorized study. This document creates no sample, evidence packet, label, detector, score or production change.

Authority: [Evaluation Contract V2](TECHNICAL_MATERIALITY_EVALUATION_CONTRACT_V2.md) is primary; [Architecture Review](TECHNICAL_MATERIALITY_ARCHITECTURE_REVIEW.md) supplies the rationale. The companion [Annotation Handbook V1](TECHNICAL_ANNOTATION_HANDBOOK_V1.md) uses the same terms and decision register. Existing V1–V3 artifacts and outcomes remain immutable. A_T50 is only a temporary research baseline, without an approved stock-day ranking/display wrapper.

## 1. Benchmark objective

Evaluate: **“Given a stock the user is monitoring, what changed today that deserves attention?”** The primary unit is one monitored ticker, one exchange trading session, one declared end-of-day decision cutoff and the complete in-scope opportunity/candidate inventory available at that cutoff. Isolated event rows cannot substitute for this unit.

| Layer | Necessary reference evidence / labels | Evaluation population |
|---|---|---|
| Event Detection | Independent opportunities, factual existence, predicate/version, one-to-one matching, known negatives and unknowns | All enumerated opportunities; emitted-output precision also includes invalid/duplicate outputs |
| Safety / Eligibility | Intrinsic severity, retention disposition, required-delivery obligation and explicit stage trace | Emitted events for conditional retention; all reference events for end-to-end retention |
| Continuous Severity | Event-level intrinsic attention 0–3, evidence uncertainty and model score availability | Labeled events with observed scores, plus explicit coverage and matched-case comparisons |
| Ranking | Full stock-day context, prior exposure, event contextual relevance, ties | Complete conditional retained group; genuine competitors only |
| Dedup / episodes | Factual identity, episode relationship, independently adjudicated event-to-insight map | Source events and distinct reference insights, including upstream omissions |
| Attention Budget Top 1–3 | Insight contextual relevance, faithful-coverage requirements, required delivery and actual display/route logs | Full end-to-end reference insight set versus actually displayed up-to-three slots |

The benchmark must support event diagnostics and complete-group metrics simultaneously. Good survivor ranking cannot hide detector losses. Retained evidence is not delivered evidence. Severity, contextual relevance, retention and required delivery remain separate judgments.

## 2. Benchmark unit definitions

The following glossary is normative for both documents.

| Term | Operational definition |
|---|---|
| Stock-day | One monitored ticker and exchange session, evaluated at one declared cutoff and fixed monitoring task; includes complete opportunities even when no event exists |
| Decision cutoff | Timezone-aware instant by which every input used for the decision must have been available; observation date alone is insufficient |
| Opportunity | A detector-independent, in-scope check for a specified technical fact on that stock-day, including a check whose truth is negative or unavailable |
| Event | One factual technical transition or abnormal condition under the approved family predicate; importance is a different property |
| Emitted candidate | Immutable system output claiming or representing an event/observation, whether ultimately valid, invalid, duplicate or unresolved |
| Reference event | Independently adjudicated `exists` opportunity under the frozen predicate; may have no matching emitted candidate |
| Ranking group | Emitted, retained, rankable candidates for the same stock-day/cutoff, monitoring task and prior-exposure state; conditional membership is recorded separately from the full reference inventory |
| Episode | A cutoff-supported continuing change/state linking events over time or families; not merely equal ticker/type or a short recurrence interval |
| Insight unit | One coherent change represented by an explicit set of source reference-event IDs and minimum facts needed to communicate it faithfully |
| Attention-budget output | Actual ordered list of zero to three displayed insights, with separately recorded overflow/exception routes |
| Unresolved opportunity | A known in-scope check for which factual existence cannot be established; includes insufficient and unavailable evidence with distinct reasons |
| No-useful-change day | Complete, adjudicated stock-day with no positively relevant reference insight for the stated task; differs from no-material day, no-event day and unknown-data day |
| Severity | Intrinsic event attention `a` in 0–3, independent of competition for a slot |
| Contextual relevance | Usefulness now `r` in 0–3 given full stock-day and prior-exposure context, separately judged for events and insights |
| Retention | Explicit judgment about rankability, unresolved tracking, invalid scope or duplicate linkage; not predicted display priority |
| Required delivery | Separate policy-grounded yes/no/unresolved obligation to communicate an item through a defined route by a defined deadline |
| Unresolved | A substantive decision is unavailable, insufficiently supported or not adjudicated; never equivalent to false, no, zero or an empty array |
| Top 1–3 | Capacity of at most three ordinary displayed insight slots; zero is permitted and overflow does not count as one of these slots |

Stable identifiers must be versioned and deterministic. Use full SHA-256 of a canonical UTF-8 JSON identity tuple (sorted keys, fixed timestamp and numeric serialization declared in the build manifest), with an entity namespace. IDs must not depend on labels, scores, rank or mutable notes. Persist the identity tuple; detect collisions and fail the build rather than truncate silently.

- `group_id`: namespace, instrument ID, exchange/session, cutoff/timezone, source snapshot ID and monitoring-task version. Use stable instrument identity plus ticker-at-date to handle symbol changes.
- `opportunity_id`: group ID, family, predicate version and predeclared sub-opportunity key. No label belongs in the key. `reference_event_id` is an alias of an existing opportunity ID once existence is adjudicated, not a rewritten row.
- `candidate_id`: preserve original immutable ID; new output identity includes run version, group, family, direction/state and source-observation fingerprint. Equal representations keep separate emission IDs plus duplicate links. Preserve legacy `case_id` when present; never assign a replay identity to an undetected opportunity.
- `episode_id`: namespace, instrument and first cutoff-supported anchor opportunity under the approved episode protocol. A later link/revision cannot change earlier cutoff evidence. Retrospective split-component IDs are separate.
- `insight_id`: group ID, annotation version and canonical member event IDs. A changed grouping creates a superseding mapping version; original event IDs remain intact.
- `annotation_id`: subject kind/ID, reviewer pseudonym, handbook version, pass and revision. Each revision names the superseded record; raw records are append-only.

Reference events, candidates, episodes and insights use explicit linkage tables, not ID equality inferred from ticker/date. Administrative split/run identifiers are hidden from annotators.

## 3. Stock-day sampling frame

No exact eligible historical interval, cohort or sample size is approved by this design. **D2 blocks generation** until an owner signs a dated input allowlist: development bounds, fresh-validation reservation, warmup bounds, source snapshots, instruments and calendar. Candidate research dates must be outside sealed 2025–2026 and outside protected closed-validation membership; a date before 2025 is not automatically fresh or authorized. Do not read protected rows to discover usable cases. An authorized custodian may supply a metadata-only exclusion ledger without labels/evidence. If freshness cannot be certified, block the frame.

| Frame element | Future rule |
|---|---|
| Ticker universe | Dynamic, documented universe with historical membership and listing/identifier changes as of each session; no ticker-specific behavior. Current membership cannot be represented as historical membership. Any retrospective survivor universe requires explicit scope approval and a bias limitation |
| Calendar | Versioned exchange calendar, session close and timezone; distinguish holiday, suspension/no trade, missing bar and genuine zero activity. No fabricated daily bars |
| Cutoff | Declared EOD data-ready instant and availability policy, identical task across comparators; exact clock time/vendor-latency assumption requires D2 sign-off |
| Warmup / history | Reuse trailing 252 prior sessions and minimum 60 valid history observations for empirical context. Current observation excluded from reference distributions. Save valid count, actual dates, gaps and window endpoints |
| Indicators | Declare reused deterministic indicator definitions and sufficient warmup separately from empirical history minimum. Current technical bar may enter an indicator only when available by cutoff; retain previous/current observations |
| Benchmark | VN30 observation pair aligned to the stock return interval and available by cutoff; no nearest future benchmark, backfill or implicit zero excess return |
| Missing data | Preserve missing fields as null with reasons. An unavailable family still has an opportunity record. Short history does not become normality. No deletion merely because a score could not be computed |
| Exclusions | Protected input, wrong instrument/session, unsupported scope, fixture contamination, failed availability/PIT or irreconcilable corrupt evidence. Log frame inclusion status and reasons before annotation; retain counts in the intended-frame audit |
| Availability claims | Record audited available_at versus explicitly assumed EOD availability. A proxy timestamp must never be called audited PIT. Unknown revision/adjustment semantics require an approved limitation or quarantine decision before use |

Adequate-history and missing/short-history groups are separately tagged. The latter can test quality handling and unresolved routes but cannot assert known historical abnormality. Selection into either must be prospective and label-independent. Preserve raw provider versions and explicit fixture flags; real benchmark prevalence must not be augmented with fixtures.

## 4. Stock-day mix / coverage strategy

**A. Prevalence-representative sample:** sample stock-days from the approved frame independent of detector output, candidate count, model score and eventual labels. Freeze the sampling unit, deterministic seed/hash rule, inclusion probability, stratification and any design weights before selection. Include eligible days with no emissions. Report intended versus completed units and nonresponse; never replace unavailable groups with convenient high-signal days without a preregistered replacement procedure and lineage.

**B. Enriched diagnostic/hard-case sample:** select complete stock-days using predeclared evidence-only criteria for the coverage below. Record each rule/version, overlapping reason tags and selection probability if known. Do not use candidate severity/rank or expected human verdict. This component estimates behavior in its stated challenge frame, not deployment prevalence.

| Desired coverage | How it is characterized without using model scores |
|---|---|
| No-event / no-useful-insight / single-event | Sampling includes ordinary days; factual and usefulness categories confirmed after blinded annotation, not selected to force labels |
| Multi-event competitive / high-demand | Evidence indicates multiple factual opportunities; distinguish observed event count from adjudicated distinct-insight demand |
| More than three potentially material insights | Preserve every opportunity on potentially busy days; confirm distinct material insights only by annotation. Four event families bound the current daily scope; do not split one episode or expand event types to manufacture this slice |
| Correlated / duplicate signals | Source identity overlap and simultaneous technical transitions; episode membership must still be adjudicated |
| Missing / quality problems | Declared evidence availability/quality patterns, including benchmark gaps and short history; no artificial Confidence values |
| Raw versus market disagreement | Signed raw/excess returns and own/market context; any numeric enrichment bins require prospective research approval |
| Repeat / ongoing episode | Past-only state changes and recurrence evidence; no future episode outcome or future alert log |

No numeric quotas are established. D6 must approve budget, precision/uncertainty objectives, slice rules, pilot allocation and stopping criteria before sampling. Discovery that a desired slice is absent is reported as a coverage limitation, not fixed by changing labels. Preserve a group appearing in both frames once, with both selection memberships; report disjoint/overlap accounting. Do not pool A and B into an unweighted population estimate. Any combined estimate requires a prospectively justified design correction; otherwise report separately.

## 5. Detector-independent opportunity inventory

For every sampled group enumerate a finite family-check inventory from the calendar, raw technical series and frozen factual predicates **before consulting detector outputs**. Under the current single-EOD scope, each of the four families has a daily check; any subdivision requires a predeclared predicate/opportunity key. Inventory all checks including known no-transition, missing, unavailable and unresolved states. A reference process must adjudicate independently from raw evidence; it may reuse numerical analytics definitions but must not import the detector's emitted list or candidate admission decision as truth.

| Family | Evidence required for factual adjudication | Known negative and unresolved handling |
|---|---|---|
| `ma_cross` | Same-source/currency/instrument previous/current MA20 and MA50, dates and derivation; define `before=prior MA20−MA50`, `after=current MA20−MA50`. Existing semantics: upward `before<=0<after`, downward `before>=0>after` | Finite valid pair not crossing is a negative. Equal current averages are not a new crossing. Missing/gapped pair requires declared continuity policy, otherwise unresolved; spread size is not existence |
| `rsi_regime_entry` | Previous/current RSI14 and dates/method; existing semantics upper `prior<=70<current`, lower `prior>=30>current` | Staying beyond a boundary or landing exactly on it is not an entry under these semantics. Missing/ambiguous continuity is unresolved; depth is not existence |
| `abnormal_price_move` | Prior/current valid comparable closes, signed fractional raw return, own-history sample, benchmark pair and signed excess context where available, adjustment/quality evidence | Broad price observation and abnormal-condition truth must be separate fields. D1 must approve abnormal-condition predicate, treatment of market alignment and required context. Until then abnormal existence is unresolved, not negative or inferred from attention |
| `unusual_volume` | Current shares volume, prior trailing reference window/count/mean, relative-volume denominator, historical distribution/z-score where valid, volume adjustment/session comparability | Observed volume is not automatically an unusual-volume condition. D1 must decide elevated versus low-volume scope, role of relative magnitude/distribution and availability prerequisites. No new numeric cutoff is supplied |

The family-specific return/magnitude normalization and context methodology must be referenced by version and units; undefined denominators yield null. No RSI/MA transition can be established across an unapproved gap as though observations were adjacent sessions. D2 must approve continuity and corporate-action treatment.

**D1 exact unresolved decision:** specify, for price and volume separately, which observable condition makes the named abnormal event factually exist; whether absolute magnitude, own-history, benchmark evidence or a combination is necessary; equality/direction rules; and when evidence is inadequate to declare no event. This is a factual rubric, not a severity or display threshold. Product/domain approval and research operationalization precede generation. Existing candidate types remain unchanged and carry their original broad-observation meaning; do not count such an output as a certified anomaly TP without the approved matching semantics.

Known negative opportunities support specificity only for that finite approved check population. Unknown/unavailable checks never count as TN or detector FN. Once independently labeled, a positive without a matching emission is a missed reference event. Multiple emissions of one reference positive earn at most one TP; remaining emissions are duplicate outputs in precision accounting.

## 6. Complete group construction

Future build sequence, with no steps executed by this specification:

1. Freeze authorized frame, sample and task/exposure policy before labels or scores. Record every intended group, including zero-emission and failed-data groups.
2. Assemble cutoff-valid raw data, indicator warmup, benchmark alignment, source/vintage and past-only recurrence/exposure history. Preserve complete bounded inputs needed to reconstruct each fact, not only selected feature summaries.
3. Enumerate all family opportunities independently. Separately capture every emission from the declared detector run, without severity filtering. Prohibit top-N or event-type caps at this stage.
4. Freeze deterministic opportunity display order, e.g. a committed hash permutation of group/opportunity IDs with seed declared before labeling. Keep the same order for all reviewers; it is an administrative order, never a priority. Candidate administrative inventory is ordered by stable IDs. Do not reveal which opportunities emitted candidates.
5. Join by exact instrument, session/cutoff, family, predicate-compatible direction/state and occurrence key. No timing tolerance or cross-type substitution. Freeze matching policy before evaluation. Keep unmatched, invalid, duplicate and unresolved outputs explicitly. A duplicate-emission tie is resolved by the predeclared stable candidate-ID order, without labels or scores.
6. Verify all families have checks, all emissions have evidence and opportunity links or an explicit mismatch record, and all source intervals are accounted for. Unknown family truth is distinct from a missing inventory row.
7. Freeze evidence and structural membership before annotation. Reference events/insights are then derived by independent annotation, preserving the frozen opportunity universe. A reviewer-discovered missing opportunity is an inventory defect: block the group, preserve the report and old version, rebuild a corrected version with a fresh blind annotation pass before evaluation. Never append a favorable reference after seeing results.

Three separate completeness fields are mandatory:

- `inventory_complete`: structural checks and emissions exhaustively accounted for under the declared scope.
- `evidence_complete`: all factual/contextual inputs necessary for adjudication available; inventory can be complete even when this is false.
- `reference_complete`: all judgments/mappings needed for the named metric resolved. No unresolved reference ideal is treated as complete.

A missing family row or unexplained emission fails structural completeness and blocks annotation readiness. A fully accounted-for unavailable family can enter an explicitly authorized quality study; full-reference ranking metrics remain unavailable where truth/relevance is unresolved. Completeness is bounded by the frozen four-family scope, not a claim that all market events were captured.

## 7. PIT / leakage controls

| Mandatory check | Required evidence | Failure action |
|---|---|---|
| Availability | Each observation, revision, context and exposure used has `available_at<=cutoff` under the signed policy; show observation time separately | Block affected group; pervasive invalid policy blocks build |
| Current-row exclusion | Historical reference indices/counts prove current observation excluded; indicator inclusion follows its declared formula | Block affected feature/group, retain failing trace |
| Benchmark alignment | Both observations match the stock return interval and cutoff; preserve benchmark source and vintage | Context null when unavailable; any future fill blocks group |
| EventMemory | Lookup before recording current event; only prior events visible; calendar-day recurrence labeled as such | Block group on current/future self-reference |
| Exposure | Separate prior delivery/acknowledgement ledger, only entries available before cutoff; no later user response | Block contaminated contextual packet |
| No future information | No future path, future episode resolution, news/fundamentals or future alerts in evidence, rationales or feature pipeline | Block contaminated units and investigate scope |
| Version / adjustments | Immutable input hashes, provider/version, downloaded_at distinct from available_at, adjustment basis and revision policy | Block unsupported reconstruction claims; approved limitations stay visible |
| Protected-data allowlist | Paths, snapshot IDs, instruments and date ranges explicitly allowed before loaders run; metadata exclusion ledger version recorded | Unauthorized access blocks build; no post-read filtering defense |
| Prefix invariance | Reconstruct with data truncated at cutoff and with later allowed data appended; earlier evidence, opportunities, memory, groups and any future system outputs must be identical | Any difference blocks build until versioned repair |
| Determinism / joins | Stable IDs, repeat reconstruction hashes, referential integrity, fixture and source checks | Block build on collisions, nondeterminism or broken references |

Prefix tests may use only separately allowed unprotected data or clearly synthetic fixtures; they must never open holdout merely to test invariance. Future retrospective split linkage may extend an episode component for quarantine, but cannot change the earlier as-of episode facts or annotation packet. Store fail/pass/not-run, expected comparison scope, observed hashes and reasons. Not-run is not pass. Repairs require a correction manifest preserving old bytes; result-dependent data repair is prohibited.

## 8. Split strategy

Design three separate partitions: development, newly reserved fresh validation, and final holdout. No dates/tickers are allocated here. D2/D4/D6 must freeze the exact strategy before benchmark generation. Existing sealed 2025–2026 is neither opened nor redefined. Closed V1/V2 and completed V3 are not a fresh pool; this design does not authorize their individual cases for tuning.

Assign whole stock-day groups and all repeated-state/episode-connected groups to one partition. Use chronological blocks and a prospectively defined boundary embargo/episode closure policy; no random event-row splitting. If one episode crosses a boundary, quarantine its affected assessment groups or place the entire allowed component in the earlier development partition under the frozen policy, never steal a reserved validation/holdout unit. No arbitrary fixed day gap is supplied: episode duration and adjacent dependence require D4 calibration before selection.

Past raw observations may be used as warmup for a later partition only under the approved allowlist; their labels, system evaluation outcomes and future exposure must not be features. Carrying an ongoing state into fresh validation must not falsely claim a new independent episode. If a protected component cannot be certified disjoint using a metadata ledger, quarantine the candidate frame segment without reading protected evidence.

Record whether the intended claim concerns future time, new tickers or both; ticker/time disjointness and session-wide market dependence must match that claim. Future uncertainty/resampling units must respect shared ticker, session and episode, not count pairs or four family checks as independent. D6 must predeclare uncertainty method and comparison populations. Report representative and enriched components separately within each split. From reservation onward, validation membership/evidence/labels are access-controlled against development tuning; aggregate completed outcomes do not reopen its cases.

## 9. Benchmark artifact schema

This is a field contract only, not executable schemas. Future artifacts use versioned UTF-8 JSON/JSONL with a manifest declaring canonical serialization, field units, enum versions, null reasons, row ordering and hashes. Every row has `schema_version`, `benchmark_version`, stable ID, provenance reference and creation/revision lineage. Numeric nulls never become zero; empty lists mean known none. Unknown lists require an explicit unresolved status. Enum/code additions require a version change.

### A. Group manifest — `groups.jsonl`

Required: `group_id`, instrument/ticker-at-date, exchange, session/date, cutoff/timezone, task version/text, snapshot IDs, frame/sampling component memberships, inclusion probability (nullable with reason), design-weight reference, seed/rule version, frame status/exclusion reasons, administrative split and split-component IDs, opportunity IDs, candidate IDs, evidence packet/hash, exposure-policy version, inventory/evidence/reference completeness with reasons, intended/processed status, count reconciliation by family, build version. Split and detector identities stay custodian-only.

### B. Reference opportunity inventory — `opportunities.jsonl`

Required: opportunity ID, group/family, predicate version and scope (`observation` versus `abnormal_condition` where relevant), sub-opportunity key, expected evidence IDs, observed direction/state or null, raw-input availability/quality, existence initially `unannotated`, reference annotation link, negative-population eligibility, inventory provenance independent of detector, correction lineage. Do not store a human severity inferred by inventory code. Adjudicated exists/no/unknown belongs to the sidecar, linked here by reference/version.

### C. Emitted candidate inventory — `candidates.jsonl`

Required: immutable candidate/original case ID where present, group, original event type/direction, observation/availability, `recognized_at` and `emitted_at` with time basis/assurance (or null and reason when not observed), evidence IDs, run/predicate/code version, original provenance/fixture flags, matched opportunity ID or mismatch reason, duplicate-emission links, matching decision/version. Preserve original replay objects by immutable reference. If they contain V0 fields, retain them in restricted originals and omit every score/S/N/C field from the blinded packet. No candidate scores are required for benchmark construction.

### D. PIT evidence packet — `evidence.jsonl` and referenced input snapshots

Required: packet/evidence IDs; group; raw OHLCV and valid previous observations; prior/current MA20/50 and RSI14; return definition, signed/absolute raw return; volume shares, trailing mean, ratio, z-score and reference sample/count/window; own-history values/percentiles with sample definition; benchmark pair/return, signed excess and absolute excess, market-relative context/sample; optional sector/economic values with definitions or explicit null reasons; currency/units; observed_at, available_at, timestamp assurance, downloaded_at; source/version/adjustment/fixture/quality flags; calculation-version links and input hashes. Include chronological past event IDs, recurrence days/unit, previous state and as-of episode/exposure references. Preserve null distinguishes no prior event, unknown history and never shown.

Exposure payload: task/scenario ID; known/unknown/as-if-empty status; past displayed insight/event IDs and content, delivered/acknowledged times, route and source; ledger completeness as of cutoff. No claimed real exposure may be fabricated. D3 decides audited ledger versus a clearly declared controlled scenario before packets exist.

### E. Human annotation sidecar — raw and adjudicated JSONL, separate files

Required: annotation ID, subject kind/ID, group, reviewer pseudonym/role, handbook version/hash, packet hash, pass/revision, timestamp, supersedes ID, independent-human/assisted/adjudicated provenance. Per judgment store value/status, evidence-grounded rationale, evidence IDs, uncertainty (`high|medium|low|unable`) and reason (`missing|insufficient|conflicting|policy_unresolved|none`). Confidence here is reviewer certainty, not engine Confidence.

Event fields: factual existence (`exists|does_not_exist|unresolved`), invalid/out-of-scope distinction, intrinsic severity (`0..3|null`), preliminary contextual relevance (`0..3|null`), final contextual relevance (`0..3|null`), retention (`retain_for_ranking|retain_unresolved|invalid_out_of_scope|linked_duplicate`), omission permission (`yes|no|unresolved`), explicit tracking (`yes|no|unresolved`), delivery-obligation link, relation/mapping links, price attribution (`market_aligned|stock_relative|mixed|unresolved`, price only), attribution rationale. Store applicability per field so `not_applicable` differs from unresolved. Duplicate retention is finalized only after relation adjudication; preserve the preliminary decision.

Group fields: reference-complete state/reasons; no-event status; no-useful-change status; expected empty-state (`no_useful_change|data_unavailable|nonempty|unresolved`); insight-order equivalence classes, unresolved conflicts and annotation completion by stage. These are derived/confirmed from underlying labels, not additional unrelated targets. No approve/reject/modify translation from historical labels is performed.

### F. Event-to-episode mapping — `episode_links.jsonl`

Required: link ID/version, source reference-event IDs, episode anchor ID, relationship (`same_factual_event|same_episode|related_distinct|separate|unresolved`), surviving event ID for exact duplicates, supporting evidence IDs, as-of cutoff, temporal direction, reviewer/adjudication links, rationale, status, supersession. Separate `split_components.jsonl` may carry retrospective leakage-quarantine linkage; never feed it to earlier annotations or model context. Require acyclic duplicate-survivor links and conservation of all original event IDs.

### G. Event-to-insight mapping — `insights.jsonl`

Required: insight ID/group, member reference-event IDs, episode links, coherent-change description, required communicated facts/evidence IDs per member, contextual relevance `0..3|null`, applicability/uncertainty/rationale, intrinsic-material and attention-3 membership flags derived from known member severities (with unknown-status accounting), adjudication/version links, human tie-class/order links, required-delivery links. Every valid reference event has one owning insight or an explicit adjudicated non-new-update/context-only disposition. Cross-links can cite support but must not create double ownership/gain. Unknown membership blocks full product metrics.

### H. Required-delivery annotation — `delivery_obligations.jsonl`

Required: obligation ID, event/insight/group IDs, `yes|no|unresolved`, reason/evidence, policy version and authority, urgency class/deadline/time basis or null reason, whether ordinary Top 3 is mandatory, acceptable overflow/escalation/exception route, tracking/acknowledgement requirement, route equivalence/faithful-coverage criteria, adjudicator links and uncertainty. No approved policy means unresolved, not no. Attention>=2 or 3 alone cannot populate yes.

### I. Completeness / integrity report — `integrity.json`

Required: build/spec/handbook/input hashes, authorization/allowlist/exclusion-ledger versions, intended/eligible/processed/blocked counts, family opportunity reconciliation, emissions/matches/duplicates/misses/unknown totals once adjudicated, completeness dimensions, missingness by cause, PIT/prefix/determinism check records, split/episode isolation, reviewer blinding checks, unresolved decisions, correction lineage and readiness result. Each check names its denominator, affected IDs, evidence and pass/fail/not-run status. Counts before annotation must not pretend factual misses are known.

### Future evaluation outputs required by the contract

Benchmark truth alone cannot measure actual delivery. A separately authorized system run must later produce an immutable stage ledger: group/candidate/opportunity IDs; detector emission and unmatched output records including actual `recognized_at`/`emitted_at`, timezone, time basis and assurance; every eligibility disposition/reason/time and valid exception route; observed severity or null/status; rank/tie blocks and actual deterministic order; predicted insight membership/text; faithful reference matching/adjudication; actual slot indices and rendered content/time; overflow/escalation, delivery and acknowledgement outcomes or null/status; code/config hashes. These are system observations, not new human target labels, and stay outside blinded benchmark truth. Unknown output adjudication blocks affected metrics rather than becoming a false insight by default.

Late recognition compares observed recognition time with the declared decision cutoff, using a compatible clock and the frozen timing protocol. Evidence available_at and event observation date do not establish detector recognition time. Offline execution wall-clock time is not historical recognition time; a simulated recognition time must be explicitly marked modeled, with its protocol. If recognition timing was not observed or validly modeled, report latency as unavailable, with timing coverage, rather than assuming on-time recognition.

| Contract metric family | Required denominator / evidence seam |
|---|---|
| Detection recall / precision / specificity | All known reference positives / adjudicated emitted outputs including duplicate-invalid emissions / approved known-negative checks; unknown counts separate; empty denominator null |
| Rankable and accounted-for retention | Conditional denominator: all emitted adjudicated attention>=2 events; attention=3 separately. Numerators rankable versus rankable plus valid tracked unresolved route. Duplicate emissions do not multiply an event. End-to-end denominator includes non-emitted reference events; trace loss stage |
| Required-delivery recall and age | Independently adjudicated obligations with known applicable deadline/route; system delivery/ack logs; not merely flagged items. Unknown obligation/policy/outcome reported, never counted delivered |
| Severity MAE / ordinal / bias / tails | Known event attention plus observed score, with all eligible labeled events as coverage denominator; per-type and event-macro defined counts. Target a/3; inherited ordinal cuts 1/6, 1/2, 5/6. Legacy penalized utility MAE separately named |
| Pair concordance / NDCG@1,@3 / contextual recall / best hit | Full declared conditional group, final event relevance, comparable outputs/ties. Full group's ideal, not returned-only. Unequal human pairs only; model tie half credit. Comparable coverage required. No-positive recall / zero ideal / incomplete-reference ideal undefined |
| Product recall / precision / missed gain | Full distinct reference insight set including upstream losses, faithful actual first-three coverage. Material/critical membership from events; relevance independently annotated. Precision and wasted slots use actual filled slots m, not three; m=0 undefined |
| Dedup / capacity / empty state | Owning maps, overlap and faithful-coverage facts, actual duplicate slots, M material insights, expected/actual empty reasons. Duplicate slot earns no second gain; capacity ceiling min(3,M)/M when M>0 does not erase actual misses |
| Cross-event / price / quality diagnostics | Signed raw/excess channels, attribution, severity/relevance, type, availability, recurrence/exposure and quality; support same-group cross-type pairs separately from cross-date severity pairs; confidence variation never fabricated |
| Aggregation / uncertainty | Component/frame weights, ticker/date/episode clustering, group size and competitive status; equal-weight defined-group summaries, pair-pooled secondary; unknown counts and prospective uncertainty plan |

Preserve Contract V2's tie-neutral expectations alongside actual deterministic-order values for cutoff ties. Positive singleton NDCG is 1 when returned first and 0 when omitted; pair concordance undefined. All-zero groups have undefined NDCG and are assessed for burden. Missing reference labels invalidate full-group ideals. No-material-day burden uses fully adjudicated days with no intrinsic material insight; no-useful-change requires no positive contextual insight. Filled-slot Precision@3 counts filled first-three slots providing a distinct, faithfully communicated intrinsically material reference insight, divided by m. Each slot receives at most one positive credit, and repeated coverage earns no additional credit. This differs from contextual relevance: a slot can satisfy intrinsic-material precision yet count as low contextual relevance in the wasted-slot diagnostic. Wasted slots include contextual relevance<=1, false and redundant slots once each. Report intrinsic-low-only slots separately. Attention-weighted missed relevance uses the full reference relevance sum; zero total is undefined. Overflow is never included in ordinary Top-3 recall.

The highest useful future verification seam is the **complete frozen benchmark package plus system stage ledger**: a read-only audit must reconstruct joins, denominators and pass/fail/undefined outcomes. Lower-level numerical provenance reuses current deterministic analytics. Tests are specified here only: empty, singleton, tied, incomplete, unavailable, duplicate, over-merged and over-capacity synthetic packages; cutoff-prefix invariance; and event conservation through every stage. No test or schema implementation occurs now.

## 10. Freeze / hash / provenance

**Before annotation:** sign authorization and decisions; freeze specification and handbook versions, frame/seed/design, selected stock-days, task/exposure policy, source versions/allowlist, evidence packets, independent opportunity inventory, captured emissions/matching policy, all structural memberships, stable ordering and blinding projection. Store file SHA-256 and ordered row/ID manifests in a signed/owner-attributed root manifest. Matching outcomes requiring factual adjudication remain unresolved until annotation; do not claim ground truth frozen before humans judge it.

**Before model evaluation:** freeze independent raw annotations first, then adjudication records, reconciled annotations, complete event/episode/insight mappings, reference insight ties/relevance, delivery obligations, completeness eligibility and all metric/acceptance/uncertainty definitions. Freeze candidate behavior and output matching/faithfulness protocol separately. Any required acceptance gate still unset means not ready, not pass. Do not reuse V3 numeric gates by default.

Corrections are append-only new versions with reason, author, affected IDs/hashes and re-annotation/re-evaluation invalidation scope. Never overwrite original replay cases, stored scores, labels or previous releases. If evidence or rubric changes after raw-label freeze, preserve the raw records and obtain a new blind pass for affected groups before evaluation. Audit access logs, who saw which projection and when scores first became available. The protected data custodian approves split isolation using metadata, not investigator access to sealed observations.

## 11. Benchmark readiness gates

Before annotation begins, all applicable checks must pass:

- Approved factual predicates and opportunity population for all four families, including usable negative/unknown semantics.
- Signed data/cutoff/universe/continuity/adjustment/exposure scope and protected-data allowlist; authorized fresh membership.
- Complete structural groups and family inventory, including no-emission checks; evidence-null reasons and declared quality-study handling.
- PIT, prefix invariance, EventMemory ordering, source integrity and deterministic reconstruction verified, not merely scheduled.
- Stable IDs and full link conservation; no unexplained unmatched emission or missing family.
- Frozen handbook, episode protocol, reviewer assignment/adjudication procedure and complete evidence presentation without scores, predicted rank or emitted status.
- Prospective study budget/sampling/uncertainty design, representative versus enriched separation, dependency-aware split/embargo and correction rules.
- Required-delivery and exposure policies resolved for a full-contract pilot; no implicit severity-to-delivery conversion.

No arbitrary accuracy, label-agreement or sample-count threshold is introduced. A quality-problem group may be intentionally included when its unavailability is truthfully represented; that is not permission to waive PIT or structural completeness. Approval for a narrower semantic pilot would require a separately revised scope stating which full-contract claims remain untestable.

## 12. Benchmark Generation Authorization Checklist

Classification is readiness of the requirement, not a claim that future files already exist. `READY` means the design rule is specified; it does not authorize generation. Decision IDs are shared verbatim with Handbook V1.

| ID / requirement | Classification | Exact prerequisite / responsible role |
|---|---|---|
| Primary stock-day unit, four families, null semantics, traceability and metric separation | READY | Defined here and in Contract V2; future build still must verify them |
| D1 — price/volume abnormal-condition existence | REQUIRES PRODUCT DECISION | Domain/product owner signs factual predicates, observation distinction, required channels and negative/unknown semantics; no severity-based shortcut |
| D2 — authorized frame and PIT evidence policy | REQUIRES PRODUCT DECISION | Data/research owner approves exact unprotected periods/universe/snapshots, cutoff, availability assurance, calendar/gap/adjustment rules and fresh split reservations |
| D3 — monitoring task and prior exposure | REQUIRES PRODUCT DECISION | Product owner defines audited exposure or explicit controlled scenario, unknown exposure treatment and newly observable episode updates |
| D4 — episode operationalization and boundary isolation | REQUIRES RESEARCH CALIBRATION | Domain/research review approves anchor, continuation/closure/re-entry, duplicate criteria and embargo/quarantine; no day-count invented here |
| D5 — required delivery / empty / overflow | REQUIRES PRODUCT DECISION | Product owner signs obligation criteria, deadlines, route visibility/acknowledgement, exceptions, empty-state treatment and Top-3 versus overflow obligations |
| D6 — study and reviewer design | REQUIRES RESEARCH CALIBRATION | Research owner approves sample budget/uncertainty, enrichment rules, split dependence, independent reviewer allocation, agreement diagnostics/acceptance and adjudication capacity |
| D7 — later model-evaluation acceptance | REQUIRES RESEARCH CALIBRATION | Freeze layer gates/coverage/uncertainty before candidate evaluation; not needed to invent performance thresholds for the annotation-design task |
| Generation / full-contract pilot authorization | BLOCKING | Resolve D1–D6, approve the two documents and separately authorize generation; none of the required data/build checks has run |
| Model evaluation / prototype / Final Validation | BLOCKING | No authority from this design; requires its own approved lifecycle and D7, without reopening stopped V3 or protected data |

**Benchmark Spec readiness:** structurally specified and auditable; **not ready to generate**. The next step is a documented resolution of D1–D6, not sampling. After those decisions, both document versions must be signed and a separate authorization may permit building and auditing a blinded pilot package. No cases are selected by this specification.
