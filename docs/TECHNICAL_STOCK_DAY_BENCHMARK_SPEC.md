# Technical Stock-Day Benchmark Specification V1

Date: 2026-10-02; D1/D2 governance updates: 2026-10-03. Status: **design complete with explicit authorization blockers; not ready for generation or annotation**. Normative requirements below apply to a future separately authorized study. This document creates no sample, evidence packet, label, detector, score or production change.

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

**D3 — APPROVED:** [Monitoring Context V1](TECHNICAL_D3_MONITORING_CONTEXT_DECISION.md) fixes the task as one user monitoring one stock at EOD: “What changed today in this stock that deserves my attention?” Scope is one ticker/date/EOD cutoff, technical domain only. Portfolio position, unrealized gain/loss, investment thesis, risk tolerance, personalized preferences, fundamentals, news and cross-stock ranking are out of scope. Every group uses `prior_exposure_mode = CONTROLLED_AS_IF_EMPTY`: no prior system insight is considered shown. This is a controlled scenario, not observed user behavior. PIT-safe market/technical history and recurrence remain separate from user exposure. Only today's factual changes enter today's event set under the approved predicates; continuing yesterday's MA ordering does not create a new cross.

The benchmark must support event diagnostics and complete-group metrics simultaneously. Good survivor ranking cannot hide detector losses. Retained evidence is not delivered evidence. Severity, contextual relevance, retention and required delivery remain separate judgments.

### Approved D5 attention and delivery policy

[D5 - APPROVED](TECHNICAL_D5_DELIVERY_POLICY_DECISION.md): ordinary Technical V1 output is maximum 3 ranked useful insights per stock-day, with no filler when only 1 or 2 exist. Complete evidence with no useful change means zero cards and `NO_MEANINGFUL_TECHNICAL_CHANGE`; insufficient/unresolved evidence means zero ordinary cards and `TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE`. Missing evidence never means nothing happened. Preserve the full reference set and rank the complete eligible set; beyond slot 3 is overflow for capacity/evaluation diagnostics, with no ordinary Top-3 exposure credit.

For ordinary Technical V1 insights, `required_delivery = NO` (machine value `no`) under the approved policy. Severity 3 does not force display, bypass the budget or create an overflow alert/notification. V1 assesses only the current EOD response: push/email/SMS, urgent escalation, acknowledgement tracking, later notification deadlines and mandatory overflow routes are out of scope. No positive delivery-obligation denominator means the corresponding metric is undefined/not applicable, not a safety pass. Material/critical retention and display coverage remain separate.

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
| Episode | One cutoff-supported continuing change/state within the same event family and instrument, with an anchor and evidence-based continuation/closure; cross-family events do not automatically share an episode |
| Insight unit | One coherent change represented by an explicit set of source reference-event IDs and minimum facts needed to communicate it faithfully |
| Attention-budget output | Actual ordered zero-to-three ordinary insight cards under D5, plus separately recorded diagnostic overflow; no mandatory alert route in V1 |
| Unresolved opportunity | A known in-scope check for which factual existence cannot be established; includes insufficient and unavailable evidence with distinct reasons |
| No-useful-change day | Complete, adjudicated stock-day with no positively relevant reference insight for the stated task; differs from no-material day, no-event day and unknown-data day |
| Severity | Intrinsic event attention `a` in 0–3, independent of competition for a slot |
| Contextual relevance | Usefulness now `r` in 0–3 given full stock-day and prior-exposure context, separately judged for events and insights |
| Retention | Explicit judgment about rankability, unresolved tracking, invalid scope or duplicate linkage; not predicted display priority |
| Required delivery | Policy-grounded delivery obligation, separate from severity/ranking. D5 V1 resolves ordinary Technical insights to NO; no mandatory notification/overflow route |
| Unresolved | A substantive decision is unavailable, insufficiently supported or not adjudicated; never equivalent to false, no, zero or an empty array |
| Top 1–3 | Capacity of at most three ordinary displayed insight slots; zero is permitted and overflow does not count as one of these slots |

Stable identifiers must be versioned and deterministic. Use full SHA-256 of a canonical UTF-8 JSON identity tuple (sorted keys, fixed timestamp and numeric serialization declared in the build manifest), with an entity namespace. IDs must not depend on labels, scores, rank or mutable notes. Persist the identity tuple; detect collisions and fail the build rather than truncate silently.

- `group_id`: namespace, instrument ID, exchange/session, cutoff/timezone, source snapshot ID and monitoring-task version. Use stable instrument identity plus ticker-at-date to handle symbol changes.
- `opportunity_id`: group ID, family, predicate version and predeclared sub-opportunity key. No label belongs in the key. `reference_event_id` is an alias of an existing opportunity ID once existence is adjudicated, not a rewritten row.
- `candidate_id`: preserve original immutable ID; new output identity includes run version, group, family, direction/state and source-observation fingerprint. Equal representations keep separate emission IDs plus duplicate links. Preserve legacy `case_id` when present; never assign a replay identity to an undetected opportunity.
- `episode_id`: namespace, instrument, event family and first cutoff-supported anchor opportunity under D4. Preserve direction/regime where applicable, continuation/closure evidence and unresolved relationships. A later link/revision cannot change earlier cutoff evidence. Retrospective split-component IDs are separate.
- `insight_id`: group ID, annotation version and canonical member event IDs. A changed grouping creates a superseding mapping version; original event IDs remain intact.
- `annotation_id`: subject kind/ID, reviewer pseudonym, handbook version, pass and revision. Each revision names the superseded record; raw records are append-only.

Reference events, candidates, episodes and insights use explicit linkage tables, not ID equality inferred from ticker/date. Administrative split/run identifiers are hidden from annotators.

## 3. Stock-day sampling frame

**D2 V3 — APPROVED / ACTIVE:** [Data Frame & PIT Policy V3](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md) permits official Development/Pilot and future Fresh Validation stock-days only within **2020-01-01 <= session_date < 2025-01-01**, within the frozen deployment cohort, subject to evidence validity and protected-case exclusion. Sealed 2025–2026 is not opened, inspected, enumerated or redefined. Closed Validation V1/V2 individuals and completed V3 reviewed cases cannot be reused as fresh annotation cases. Use certified metadata-only exclusion manifests/IDs; never open protected evidence/labels merely to identify exclusions. Unknown freshness blocks admission. Quarantine overlapping complete groups rather than deleting protected members to make a group appear fresh.

D2 approves the frame policy, not a sample or source dataset. **Official sampling remains BLOCKED until the deployment cohort source is captured and frozen.** The primary claim concerns this deployment cohort across historical regimes, not the historical index universe. D2 V3 Safeguard 6 prohibits membership or ticker-specific engine behavior. Expansion claims require fresh Expansion Validation with acceptance criteria frozen before results (PASS/FAIL/INCONCLUSIVE); code portability does not imply validation portability. Outside the validated population, research output is UNVALIDATED_FOR_THIS_POPULATION. D6 controls sample size, exact stock-days, development/fresh-validation allocations and representative/enriched sampling. Before a future build, freeze the exact authorized dates/warmup, snapshots, instruments and paths in an input allowlist; frame eligibility alone does not authorize loading every file. Pre-2020 warm-up may be used only when separately authorized and PIT-valid; it cannot become an official benchmark stock-day or expand the sampling frame.

| Frame element | Approved policy / future verification |
|---|---|
| Ticker universe | Frozen deployment cohort across 2020–2024; cohort source must be captured and frozen before sampling. Preserve stable instrument ID, ticker at date, exchange and session. Historical VN30 membership = YES / NO / UNKNOWN is secondary evaluation metadata with available source/version/effective interval; not a primary eligibility gate or engine feature. Never claim current membership is historical truth |
| Calendar | Versioned exchange calendar and valid comparable trading observations; distinguish holidays, suspensions/no trade and provider loss. No synthetic bars |
| Cutoff | EOD only: **23:59:59 Asia/Ho_Chi_Minh on the trading date**. No intraday detection/alert-latency claim |
| Warmup / history | D1 unchanged: up to previous 252 valid comparable sessions, minimum 60, current excluded. Preserve actual selected sessions, counts/gaps and D1's distinction from legacy context windows; insufficient evidence means UNRESOLVED |
| Indicators | MA20/MA50/RSI14 may use the valid cutoff-visible current bar. Previous/current transition observations must be consecutive and comparable under calendar policy; missing bars are not ordinary adjacency. Unestablished continuity means UNRESOLVED unless an approved family rule explicitly resolves it |
| Benchmark | VN30(t-1) and VN30(t) match the stock return's exact interval and cutoff policy. No future/nearest-later/forward-filled values. Missing benchmark yields null context and reason, not automatic invalidation of own-history D1 |
| Corporate actions | Preserve adjustment semantics. Non-comparable price pairs from corporate actions or mixed series mean UNRESOLVED unless a versioned verified comparable adjusted series satisfies PIT. Non-comparable volume/share units likewise mean UNRESOLVED; no future-knowledge repair |
| Missing data | Missing current/prior bar, insufficient history, benchmark gaps, continuity/adjustment uncertainty, corruption, suspension and provider loss stay explicit. Essential missing evidence means UNRESOLVED; optional missing context stays null. No zero/prior/future/no-event substitution |
| Exclusions | Protected inputs, unsupported instrument/session/membership, fixture contamination, failed PIT and invalid evidence retain explicit reasons and frame accounting; absence of scores is not a frame exclusion |
| Availability | Without audited daily OHLCV publication time, use **EOD_AVAILABILITY_ASSUMPTION**, assumed available_at at cutoff, assurance=assumed; preserve provider/snapshot/download/adjustment/quality metadata. Applicable audited timing is separate and cannot be overridden by an earlier assumption |

Only available_at<=cutoff inputs are visible. Same date does not prove market-close publication. The daily-bar assumption is not a license to admit later revisions or future corporate-action adjustments. Freeze provider/version, snapshot identity, raw hashes, calendar, VN30 source/version and assumption version. Legacy datasets require D2 integrity verification; prior V0–V3 use is insufficient. Corrections require new versions/manifests without mutating originals.

Adequate-history and missing/short-history groups remain separately tagged. Structurally accounted-for missingness may support a later authorized quality study, but cannot establish unknown factual truth. D2 frame membership must not be chosen because of a large move, high volume, detector output, model score or expected label. [D6 — APPROVED](TECHNICAL_D6_STUDY_REVIEWER_DECISION.md) permits predeclared evidence-only enriched sampling within the D2-authorized eligible frame; it does not change frame admissibility or authorize sampling now.

## 4. Stock-day mix / coverage strategy

**Approved D6 quota:** Development/Pilot = **120 stock-days: 80 Representative + 40 Enriched Diagnostic**; reserve **60 Fresh Validation stock-days** separately. Freeze frame version, inclusion/exclusion rules, component definitions, deterministic seed, selection algorithm and replacement policy before sampling. Count unique stock-days, preserve overlap/selection lineage and do not manually select interesting days. These are V1 research quotas, not a universal statistical optimum; Development evidence may justify review only through the Decision Review Protocol and an approved D6 V2.

**A. Prevalence-representative sample:** sample stock-days from the approved frame independent of detector output, candidate count, model score and eventual labels. Freeze the sampling unit, deterministic seed/hash rule, inclusion probability, stratification and any design weights before selection. Include eligible days with no emissions. Report intended versus completed units and nonresponse; never replace unavailable groups with convenient high-signal days without a preregistered replacement procedure and lineage.

**B. Enriched diagnostic/hard-case sample (D6 APPROVED):** select complete eligible stock-days only under frozen evidence-only criteria for the coverage below, after separate generation authorization. Record each rule/version, overlapping reason tags and selection probability if known. Do not use model/candidate scores, attention labels, predicted ranking or expected human verdict. This component estimates behavior in its stated challenge frame, not deployment prevalence; report it separately from Representative results.

| Desired coverage | How it is characterized without using model scores |
|---|---|
| No-event / no-useful-insight / single-event | Sampling includes ordinary days; factual and usefulness categories confirmed after blinded annotation, not selected to force labels |
| Multi-event competitive / high-demand | Evidence indicates multiple factual opportunities; distinguish observed event count from adjudicated distinct-insight demand |
| More than three potentially material insights | Preserve every opportunity on potentially busy days; confirm distinct material insights only by annotation. Four event families bound the current daily scope; do not split one episode or expand event types to manufacture this slice |
| Correlated / duplicate signals | Source identity overlap and simultaneous technical transitions; episode membership must still be adjudicated |
| Missing / quality problems | Declared evidence availability/quality patterns, including benchmark gaps and short history; no artificial Confidence values |
| Raw versus market disagreement | Signed raw/excess returns and own/market context; any numeric enrichment bins require prospective research approval |
| Repeat / ongoing episode | Past-only state changes and recurrence evidence; no future episode outcome or future alert log |

D2 frame admissibility remains unchanged; D6 approves evidence-only enrichment within that frame. Freeze concrete slice rules, allocation, replacement handling and applicable uncertainty procedures before selection/analysis, without inventing a global agreement or precision threshold. Discovery that a desired slice is absent is reported as a coverage limitation, not fixed by changing labels. Preserve a group appearing in both frames once, with both selection memberships; report disjoint/overlap accounting. Do not pool A and B into an unweighted population estimate. Any combined estimate requires a prospectively justified design correction; otherwise report separately.

## 5. Detector-independent opportunity inventory

For every sampled group enumerate a finite family-check inventory from the calendar, raw technical series and frozen factual predicates **before consulting detector outputs**. Under the current single-EOD scope, each of the four families has a daily check; any subdivision requires a predeclared predicate/opportunity key. Inventory all checks including known no-transition, missing, unavailable and unresolved states. A reference process must adjudicate independently from raw evidence; it may reuse numerical analytics definitions but must not import the detector's emitted list or candidate admission decision as truth.

| Family | Evidence required for factual adjudication | Known negative and unresolved handling |
|---|---|---|
| `ma_cross` | Same-source/currency/instrument previous/current MA20 and MA50, dates and derivation; define `before=prior MA20−MA50`, `after=current MA20−MA50`. Existing semantics: upward `before<=0<after`, downward `before>=0>after` | Finite valid pair not crossing is a negative. Equal current averages are not a new crossing. Missing/gapped pair requires declared continuity policy, otherwise unresolved; spread size is not existence |
| `rsi_regime_entry` | Previous/current RSI14 and dates/method; existing semantics upper `prior<=70<current`, lower `prior>=30>current` | Staying beyond a boundary or landing exactly on it is not an entry under these semantics. Missing/ambiguous continuity is unresolved; depth is not existence |
| `abnormal_price_move` | Valid comparable daily stock return and prior absolute-return history, adjustment/session/quality evidence; benchmark/excess context optional for D1 | Approved D1: absolute current return >= historical empirical q95 is EXISTS; below is DOES_NOT_EXIST; insufficient/invalid required evidence is UNRESOLVED. Preserve signed direction separately; market-relative evidence does not determine existence |
| `unusual_volume` | Current comparable daily shares volume and prior comparable volume history, adjustment/session/quality evidence; relative volume/z-score remain context | Approved D1: current volume >= historical empirical q95 is EXISTS; below is DOES_NOT_EXIST; insufficient/invalid required evidence is UNRESOLVED. HIGH volume only; low-volume abnormality is out of scope. Price cannot manufacture volume existence |

The family-specific return/magnitude normalization and context methodology must be referenced by version and units; undefined denominators yield null. No RSI/MA transition can be established across an unapproved gap as though observations were adjacent sessions. The approved [D2 policy](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md) requires established continuity/comparability; otherwise factual evidence is UNRESOLVED.

**D1 — APPROVED:** [Technical Factual Abnormality V1](TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md) defines the two predicates above. For each family, use the most recent up to 252 valid comparable prior trading-session observations, minimum 60, with current observation excluded. Sort the history and take the one-based order statistic at ceil(95*n/100), with no interpolation; equality counts as EXISTS. This inverse empirical quantile is separate from the existing own-history midrank context. The last-valid-observation D1 window must not silently reuse a different legacy session-row population. Missing/invalid evidence is UNRESOLVED, never false/zero/attention 0. The approved 95th percentile is a factual operational rule, not a tuned, severity or display threshold. Existing candidate types, labels and production behavior remain unchanged. D1-D6 are approved; generation still requires separate explicit authorization.

Known negative opportunities support specificity only for that finite approved check population. Unknown/unavailable checks never count as TN or detector FN. Once independently labeled, a positive without a matching emission is a missed reference event. Multiple emissions of one reference positive earn at most one TP; remaining emissions are duplicate outputs in precision accounting.

## 6. Complete group construction

Future build sequence, with no steps executed by this specification:

1. Freeze authorized frame, sample and task/exposure policy before labels or scores. Record every intended group, including zero-emission and failed-data groups.
2. Assemble cutoff-valid raw data, indicator warmup, benchmark alignment, source/vintage and past-only market recurrence/state history, with the declared CONTROLLED_AS_IF_EMPTY user-exposure scenario; no prior delivery/acknowledgement history is fabricated. Preserve complete bounded inputs needed to reconstruct each fact, not only selected feature summaries.
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
| Availability | Each input has `available_at<=23:59:59 Asia/Ho_Chi_Minh` for the stock-day. Separate audited publication from EOD_AVAILABILITY_ASSUMPTION and unavailable timing; show observation/download dates separately | Block affected group; pervasive invalid policy blocks build |
| Current-row exclusion | Historical reference indices/counts prove current observation excluded; indicator inclusion follows its declared formula | Block affected feature/group, retain failing trace |
| Benchmark alignment | Both observations match the stock return interval and cutoff; preserve benchmark source and vintage | Context null when unavailable; any future fill blocks group |
| EventMemory | Lookup before recording current event; only prior events visible; calendar-day recurrence labeled as such | Block group on current/future self-reference |
| Exposure | Explicit prior_exposure_mode=CONTROLLED_AS_IF_EMPTY; market history is separate; no prior delivery/acknowledgement logs or already-shown inference in V1 | Block fabricated or contaminated exposure context |
| No future information | No future path, future episode resolution, news/fundamentals or future alerts in evidence, rationales or feature pipeline | Block contaminated units and investigate scope |
| Version / adjustments | Immutable source/hash/calendar/VN30/assumption versions; downloaded_at distinct from availability. Required price/volume comparability verified without future repair | Essential unresolved comparability means UNRESOLVED; future-dependent or falsely certified evidence blocks build |
| Protected-data allowlist | Authorized paths/snapshots/instruments and pre-2025 dates before loading; metadata-only exclusions for closed V1/V2 and V3 reviewed cases. No holdout opening/enumeration | Unauthorized access blocks build; no post-read filtering defense |
| Prefix invariance | Reconstruct with data truncated at cutoff and with later allowed data appended; earlier evidence, opportunities, memory, groups and any future system outputs must be identical | Any difference blocks build until versioned repair |
| Determinism / joins | Stable IDs, repeat reconstruction hashes, referential integrity, fixture and source checks | Block build on collisions, nondeterminism or broken references |

D2 prefix checks must preserve historical reference values, D1 threshold inputs, MA/RSI, opportunities, recurrence, benchmark context, stable IDs and the entire cutoff evidence packet. Group snapshot identity means the stable logical source/version plus cutoff-visible subset; hashes of a larger physical container belong in the run/source inventory, not in future-dependent group IDs. Appending allowed future rows must not change an earlier packet through a container hash alone.

Prefix tests may use only separately allowed unprotected data or clearly synthetic fixtures; they must never open holdout merely to test invariance. Future retrospective split linkage may extend an episode component for quarantine, but cannot change the earlier as-of episode facts or annotation packet. Store fail/pass/not-run, expected comparison scope, observed hashes and reasons. Not-run is not pass. Repairs require a correction manifest preserving old bytes; result-dependent data repair is prohibited.

### Approved D4 episode lifecycle

[D4 - APPROVED](TECHNICAL_D4_EPISODE_POLICY_DECISION.md) defines family-specific episodes: anchor at start, continue while the same condition/state continues, close when confirmed ended, and new episode on re-entry after close. No fixed N-day gap rule; missing/non-comparable continuity is UNRESOLVED, never silently bridged or closed.

- Price: consecutive factual abnormal events in the same up/down direction continue an episode; a valid non-abnormal day closes it; an opposite-direction abnormal event closes the old episode and anchors a new one.
- Volume: consecutive factual HIGH-volume events continue; a valid non-abnormal volume day closes; later factual re-entry starts a new episode.
- MA: a factual upward/downward cross anchors a bullish/bearish MA regime; continuing the regime is not a new cross. A reverse factual cross closes the old regime and opens the opposite episode.
- RSI: upper entry continues while RSI>70 and closes on a valid RSI<=70; lower entry continues while RSI<30 and closes on a valid RSI>=30. Later factual re-entry starts a new episode; continuing regimes are not repeated entry events.

Cross-family events retain separate episode identities even when later insight grouping combines related events. No future evidence may rewrite an earlier as-of relationship.

## 8. Split strategy

Design three separate partitions: Development/Pilot (120 stock-days), newly reserved Fresh Validation (60 stock-days), and final holdout. No dates/tickers are allocated here. D2 defines frame admissibility; D4 defines episode isolation; approved D6 requires a frozen selection rule and exact allocation before separately authorized generation. Existing sealed 2025–2026 is neither opened, enumerated, relabeled nor redefined. Closed V1/V2 and completed V3 are not a fresh pool; this design does not authorize their individual cases for tuning.

Assign whole stock-day groups and episode-connected groups to one partition. Under [D4](TECHNICAL_D4_EPISODE_POLICY_DECISION.md), an episode crossing a planned Development/Fresh Validation boundary requires quarantine of the affected episode/groups from Fresh Validation. Unresolved boundary continuity likewise requires quarantine. Do not move protected/reserved validation cases into development to maintain sample size, treat later episode days as fresh independent validation, or use a fixed N-day gap/embargo as a substitute for episode isolation. D6 retains allocation decisions; no random event-row split is permitted.

Past raw observations may be used as warmup for a later partition only under the approved allowlist; their labels, system evaluation outcomes and future exposure must not be features. Carrying an ongoing state into fresh validation must not falsely claim a new independent episode. If a protected component cannot be certified disjoint using a metadata ledger, quarantine the candidate frame segment without reading protected evidence.

Record whether the intended claim concerns future time, new tickers or both; ticker/time disjointness and session-wide market dependence must match that claim. Future uncertainty/resampling units must respect shared ticker, session and episode, not count pairs or four family checks as independent. D6 must predeclare uncertainty method and comparison populations. Report representative and enriched components separately within each split. From reservation onward, validation membership/evidence/labels are access-controlled against development tuning; aggregate completed outcomes do not reopen its cases.

## 9. Benchmark artifact schema

This is a field contract only, not executable schemas. Future artifacts use versioned UTF-8 JSON/JSONL with a manifest declaring canonical serialization, field units, enum versions, null reasons, row ordering and hashes. Every row has `schema_version`, `benchmark_version`, stable ID, provenance reference and creation/revision lineage. Numeric nulls never become zero; empty lists mean known none. Unknown lists require an explicit unresolved status. Enum/code additions require a version change.

### A. Group manifest — `groups.jsonl`

Required: `group_id`, instrument/ticker-at-date, exchange, session/date, cutoff/timezone, frozen deployment-cohort identity/source/version, historical VN30 membership YES/NO/UNKNOWN with effective interval and source/version where available (otherwise null with reason), task version/text, cutoff-stable snapshot IDs, frame/sampling component memberships, inclusion probability (nullable with reason), design-weight reference, seed/rule version, frame status/exclusion reasons, administrative split and split-component IDs, opportunity IDs, candidate IDs, evidence packet/hash, exposure-policy version, inventory/evidence/reference completeness with reasons, intended/processed status, count reconciliation by family, build version. Split and detector identities stay custodian-only.

### B. Reference opportunity inventory — `opportunities.jsonl`

Required: opportunity ID, group/family, predicate version and scope (`observation` versus `abnormal_condition` where relevant), sub-opportunity key, expected evidence IDs, observed direction/state or null, raw-input availability/quality, existence initially `unannotated`, reference annotation link, negative-population eligibility, inventory provenance independent of detector, correction lineage. Do not store a human severity inferred by inventory code. Adjudicated exists/no/unknown belongs to the sidecar, linked here by reference/version.

### C. Emitted candidate inventory — `candidates.jsonl`

Required: immutable candidate/original case ID where present, group, original event type/direction, observation/availability, `recognized_at` and `emitted_at` with time basis/assurance (or null and reason when not observed), evidence IDs, run/predicate/code version, original provenance/fixture flags, matched opportunity ID or mismatch reason, duplicate-emission links, matching decision/version. Preserve original replay objects by immutable reference. If they contain V0 fields, retain them in restricted originals and omit every score/S/N/C field from the blinded packet. No candidate scores are required for benchmark construction.

### D. PIT evidence packet — `evidence.jsonl` and referenced input snapshots

Required: packet/evidence IDs; group; raw OHLCV and valid previous observations; prior/current MA20/50 and RSI14; return definition, signed/absolute raw return; volume shares, trailing mean, ratio, z-score and reference sample/count/window; own-history values/percentiles with sample definition; separately named D1 predicate/convention version, current comparison value/unit, selected valid prior session/value IDs, count n, order index k, q95 and validity/exclusion reasons under the D1 decision; benchmark pair/return, signed excess and absolute excess, market-relative context/sample; optional sector/economic values with definitions or explicit null reasons; currency/units; observed_at, available_at, timestamp assurance (audited/assumed/unavailable), EOD_AVAILABILITY_ASSUMPTION policy version and separate audited/assumed availability when applicable, downloaded_at; source/version/adjustment/fixture/quality flags; calculation-version links and input hashes. Include chronological past event IDs, recurrence days/unit, previous state and as-of episode/exposure references. Preserve null distinguishes no prior event, unknown history and never shown.

Exposure payload: task/scenario ID and version; `prior_exposure_mode = CONTROLLED_AS_IF_EMPTY`; explicit controlled-assumption provenance. No past displayed-insight, delivery or acknowledgement log is available or fabricated. Real user behavior is unassessed. Past event IDs, technical state and recurrence belong to market-history context, not an exposure ledger. Future audited exposure is outside D3 V1.

### E. Human annotation sidecar — raw and adjudicated JSONL, separate files

Required: annotation ID, subject kind/ID, group, reviewer pseudonym/role, handbook version/hash, packet hash, pass/revision, timestamp, supersedes ID, independent-human/assisted/adjudicated provenance. Per judgment store value/status, evidence-grounded rationale, evidence IDs, uncertainty (`high|medium|low|unable`) and reason (`missing|insufficient|conflicting|policy_unresolved|none`). Confidence here is reviewer certainty, not engine Confidence.

Event fields: factual existence (`exists|does_not_exist|unresolved`), invalid/out-of-scope distinction, intrinsic severity (`0..3|null`), preliminary contextual relevance (`0..3|null`), final contextual relevance (`0..3|null`), retention (`retain_for_ranking|retain_unresolved|invalid_out_of_scope|linked_duplicate`), omission permission (`yes|no|unresolved`), explicit tracking (`yes|no|unresolved`), delivery-obligation link, relation/mapping links, price attribution (`market_aligned|stock_relative|mixed|unresolved`, price only), attribution rationale. Store applicability per field so `not_applicable` differs from unresolved. Duplicate retention is finalized only after relation adjudication; preserve the preliminary decision.

Group fields: reference-complete state/reasons; no-event and no-useful-change status; expected ordinary response state (`NONEMPTY|NO_MEANINGFUL_TECHNICAL_CHANGE|TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE`) and reason under D5; insight-order equivalence classes, unresolved conflicts and stage completion. Workflow-unresolved annotation is not a no-change label. No historical verdict conversion is performed.

### F. Event-to-episode mapping — `episode_links.jsonl`

Required: link ID/version, source reference-event IDs, episode anchor ID and event family, lifecycle state/anchor/continuation/confirmed-closure evidence and unresolved-continuity reason, relationship (`same_factual_event|same_episode|related_distinct|separate|unresolved`), surviving event ID for exact duplicates, supporting evidence IDs, as-of cutoff, temporal direction, reviewer/adjudication links, rationale, status, supersession. Separate `split_components.jsonl` may carry retrospective leakage-quarantine linkage; never feed it to earlier annotations or model context. Require acyclic duplicate-survivor links and conservation of all original event IDs.

### G. Event-to-insight mapping — `insights.jsonl`

Required: insight ID/group, member reference-event IDs, episode links, coherent-change description, required communicated facts/evidence IDs per member, contextual relevance `0..3|null`, applicability/uncertainty/rationale, intrinsic-material and attention-3 membership flags derived from known member severities (with unknown-status accounting), adjudication/version links, human tie-class/order links, required-delivery links. Every valid reference event has one owning insight or an explicit adjudicated non-new-update/context-only disposition. Cross-links can cite support but must not create double ownership/gain. Unknown membership blocks full product metrics.

### H. Required-delivery annotation — `delivery_obligations.jsonl`

Required: delivery-policy record ID, event/insight/group IDs, policy version/authority and reason. Ordinary Technical V1 insights have required_delivery=NO (machine `no`) under D5. Urgency, notification deadline, mandatory Top-3/overflow route and acknowledgement fields are not applicable in V1; do not fabricate them. Preserve unknown factual/attention labels separately. The generic yes/no/unresolved obligation schema may support a later separately approved policy version, not new V1 obligations.

### I. Completeness / integrity report — `integrity.json`

Required: build/spec/handbook/input hashes, authorization/allowlist/exclusion-ledger versions, intended/eligible/processed/blocked counts, family opportunity reconciliation, emissions/matches/duplicates/misses/unknown totals once adjudicated, completeness dimensions, missingness by cause, PIT/prefix/determinism check records, split/episode isolation, reviewer blinding checks, unresolved decisions, correction lineage and readiness result. Each check names its denominator, affected IDs, evidence and pass/fail/not-run status. Counts before annotation must not pretend factual misses are known.

### Future evaluation outputs required by the contract

Benchmark truth alone cannot measure actual display. A separately authorized V1 run must record group/candidate/opportunity IDs; emissions and matching; eligibility disposition and reason; severity or null/status; complete ranks/ties; insight membership/content and faithful reference matches; actual ordinary slot indices/content; expected/actual empty state and reasons; diagnostic overflow beyond slot 3; and code/config hashes. D5 V1 has no mandatory overflow/escalation/notification/acknowledgement ledger. These system observations remain outside blinded benchmark truth; unresolved output adjudication does not become a false insight automatically.

D2 EOD scope does not evaluate intraday detection or alert latency; do not infer those metrics from assumed daily availability. The following general timing requirements apply only to a separately authorized timing assessment. Late recognition compares observed recognition time with the declared decision cutoff, using a compatible clock and the frozen timing protocol. Evidence available_at and event observation date do not establish detector recognition time. Offline execution wall-clock time is not historical recognition time; a simulated recognition time must be explicitly marked modeled, with its protocol. If recognition timing was not observed or validly modeled, report latency as unavailable, with timing coverage, rather than assuming on-time recognition.

| Contract metric family | Required denominator / evidence seam |
|---|---|
| Detection recall / precision / specificity | All known reference positives / adjudicated emitted outputs including duplicate-invalid emissions / approved known-negative checks; unknown counts separate; empty denominator null |
| Rankable and accounted-for retention | Conditional denominator: all emitted adjudicated attention>=2 events; attention=3 separately. Numerators rankable versus rankable plus valid tracked unresolved route. Duplicate emissions do not multiply an event. End-to-end denominator includes non-emitted reference events; trace loss stage |
| Required-delivery recall and age | D5 V1 has no hard delivery obligations: ordinary insights have required_delivery=NO; positive-obligation metrics are undefined/not applicable. Do not infer timely delivery or safety from an empty denominator |
| Severity MAE / ordinal / bias / tails | Known event attention plus observed score, with all eligible labeled events as coverage denominator; per-type and event-macro defined counts. Target a/3; inherited ordinal cuts 1/6, 1/2, 5/6. Legacy penalized utility MAE separately named |
| Pair concordance / NDCG@1,@3 / contextual recall / best hit | Full declared conditional group, final event relevance, comparable outputs/ties. Full group's ideal, not returned-only. Unequal human pairs only; model tie half credit. Comparable coverage required. No-positive recall / zero ideal / incomplete-reference ideal undefined |
| Product recall / precision / missed gain | Full distinct reference insight set including upstream losses, faithful actual first-three coverage. Material/critical membership from events; relevance independently annotated. Precision and wasted slots use actual filled slots m, not three; m=0 undefined |
| Dedup / capacity / empty state | Owning maps, overlap and faithful-coverage facts, actual duplicate slots, M material insights, expected/actual empty reasons. Duplicate slot earns no second gain; capacity ceiling min(3,M)/M when M>0 does not erase actual misses |
| Cross-event / price / quality diagnostics | Signed raw/excess channels, attribution, severity/relevance, type, availability, recurrence/exposure and quality; support same-group cross-type pairs separately from cross-date severity pairs; confidence variation never fabricated |
| Aggregation / uncertainty | Component/frame weights, ticker/date/episode clustering, group size and competitive status; equal-weight defined-group summaries, pair-pooled secondary; unknown counts and prospective uncertainty plan |

Preserve Contract V2's tie-neutral expectations alongside actual deterministic-order values for cutoff ties. Positive singleton NDCG is 1 when returned first and 0 when omitted; pair concordance undefined. All-zero groups have undefined NDCG and are assessed for burden. Missing reference labels invalidate full-group ideals. No-material-day burden uses fully adjudicated days with no intrinsic material insight; no-useful-change requires no positive contextual insight. Filled-slot Precision@3 counts filled first-three slots providing a distinct, faithfully communicated intrinsically material reference insight, divided by m. Each slot receives at most one positive credit, and repeated coverage earns no additional credit. This differs from contextual relevance: a slot can satisfy intrinsic-material precision yet count as low contextual relevance in the wasted-slot diagnostic. Wasted slots include contextual relevance<=1, false and redundant slots once each. Report intrinsic-low-only slots separately. Attention-weighted missed relevance uses the full reference relevance sum; zero total is undefined. Overflow is never included in ordinary Top-3 recall.

The highest useful future verification seam is the **complete frozen benchmark package plus system stage ledger**: a read-only audit must reconstruct joins, denominators and pass/fail/undefined outcomes. Lower-level numerical provenance reuses current deterministic analytics. Tests are specified here only: empty, singleton, tied, incomplete, unavailable, duplicate, over-merged and over-capacity synthetic packages; cutoff-prefix invariance; and event conservation through every stage. No test or schema implementation occurs now.

## 10. Freeze / hash / provenance

**D-family Decision Review:** D1–D6 are versioned hypotheses/contracts. Changes require the [Technical Decision Review Protocol V1](TECHNICAL_DECISION_REVIEW_PROTOCOL.md), using the common seven-dimension rubric. Its summary score is diagnostic only; Integrity has hard-gate status and Integrity=0 blocks KEEP. Poor model performance alone cannot trigger D revision. Fresh validation and holdout cannot be used for iterative D tuning. D1–D6 design blockers are resolved; generation remains unauthorized pending separate explicit approval.

**D6 reviewer design:** Reviewer A reviews 120/120 Development stock-days; Reviewer B independently reviews a frozen deterministic/random 30% subset (target 36/120). Both independently review 60/60 Fresh Validation stock-days. Neither sees model/candidate scores, predicted ranking, detector-emitted status or the other's raw labels before submission. Preserve append-only raw judgments and separate adjudication, including rationale, result, adjudicator identity/version and unresolved status. Report factual exact agreement; severity/contextual exact, one-level and >=2-level disagreements; relation exact agreement and unresolved/disputed rates, with denominators, reasons and affected groups. No single arbitrary global agreement pass threshold applies.

Development evidence supports authorized diagnostics, Decision Review, model development and debugging. Fresh Validation is evaluated only after D-family, construction and required candidate freezes; individual cases/labels cannot support development tuning. A severe validation design defect invalidates the cycle, returns review to Development and requires justified Dn V2 plus a NEW Fresh Validation set. Do not iteratively reuse the failed set.

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
- Approved D3/D5 controlled exposure and current-EOD display policy recorded; verify zero mandatory V1 delivery obligations and the distinct empty states, without severity-to-delivery conversion.

No arbitrary accuracy or global label-agreement pass threshold is introduced. Approved D6 sample quotas are research allocations, not statistical sufficiency guarantees. A quality-problem group may be intentionally included when its unavailability is truthfully represented; that is not permission to waive PIT or structural completeness. Approval for a narrower semantic pilot would require a separately revised scope stating which full-contract claims remain untestable.

## 12. Benchmark Generation Authorization Checklist

Classification is readiness of the requirement, not a claim that future files already exist. `READY` means the design rule is specified; it does not authorize generation. Decision IDs are shared verbatim with Handbook V1.

| ID / requirement | Classification | Exact prerequisite / responsible role |
|---|---|---|
| Primary stock-day unit, four families, null semantics, traceability and metric separation | READY | Defined here and in Contract V2; future build still must verify them |
| D1 — price/volume abnormal-condition existence | READY / APPROVED | Owner-approved own-history empirical q95 predicates; absolute price return and HIGH volume only, inclusive equality, 252 valid priors maximum / 60 minimum, current excluded. See [D1 decision](TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md); no severity-based shortcut |
| D2 V3 — authorized frame and PIT evidence policy | READY / APPROVED / ACTIVE | [D2 decision](TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md): 2020-01-01 <= session_date < 2025-01-01, separately authorized PIT-valid warm-up outside stock-day sampling, frozen deployment cohort (historical membership is secondary metadata), 23:59:59 Asia/Ho_Chi_Minh cutoff, explicit assumed EOD availability, comparable prior-only evidence and pre-load protection. Dataset compliance must still be verified; selection/allocation remains D6 |
| D3 — monitoring task and prior exposure | READY / APPROVED | [D3 decision](TECHNICAL_D3_MONITORING_CONTEXT_DECISION.md): one-stock technical EOD task, CONTROLLED_AS_IF_EMPTY prior exposure, separate PIT-safe market history; only today's predicate-defined changes enter today's event set |
| D4 - episode continuity and split isolation | READY / APPROVED | [D4 decision](TECHNICAL_D4_EPISODE_POLICY_DECISION.md): family-specific anchor/continue/confirmed close/re-entry; unresolved continuity stays unresolved; boundary-crossing or uncertain episodes/groups quarantined from Fresh Validation, without fixed-day rules |
| D5 - attention budget, empty state and delivery | READY / APPROVED | [D5 policy](TECHNICAL_D5_DELIVERY_POLICY_DECISION.md): maximum 3, no filler, distinct complete-no-change versus incomplete-data states, diagnostic overflow without Top-3 credit; ordinary required_delivery=NO, EOD response only |
| D6 — study and reviewer design | READY / APPROVED | [D6 decision](TECHNICAL_D6_STUDY_REVIEWER_DECISION.md): 120 Development (80 Representative + 40 Enriched), 60 Fresh Validation; A reviews all, B reviews 36/120 Development and 60/60 Validation independently; frozen reproducible sampling, raw preservation, typed agreement diagnostics and D4 isolation |
| D7 — later model-evaluation acceptance | REQUIRES RESEARCH CALIBRATION | Freeze layer gates/coverage/uncertainty before candidate evaluation; not needed to invent performance thresholds for the annotation-design task |
| Generation / full-contract pilot authorization | BLOCKING | D1-D6 design blockers resolved; separate explicit Benchmark Generation Authorization and construction integrity checks still required; no benchmark build/data checks have run |
| Model evaluation / prototype / Final Validation | BLOCKING | No authority from this design; requires its own approved lifecycle and D7, without reopening stopped V3 or protected data |

**Benchmark Spec readiness:** D1-D6 APPROVED; design blockers resolved. BENCHMARK GENERATION IS STILL NOT AUTHORIZED pending separate explicit Benchmark Generation Authorization and applicable integrity gates. D7 remains LATER MODEL-EVALUATION ACCEPTANCE; no automatic generation or model work is authorized.
