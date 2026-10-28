# D2 — Technical Benchmark Data Frame & PIT Policy V2

Date: 2026-10-03. **D2 V2 — APPROVED / ACTIVE** by the project owner through the supplied D2 V2 instruction. D2 V1 → REVISED; D2 V2 is the active D2 authority for future benchmark generation. This documentation revision does not itself authorize data loading, sampling or benchmark execution. Existing owner authorization remains subject to applicable phase scope and real-data B1–B6 certification.

Version lineage: [preserved D2 V1](TECHNICAL_D2_DATA_FRAME_PIT_DECISION.md) → [Decision Review: REVISE, impact LOW](TECHNICAL_D2_DECISION_REVIEW_V1_TO_V2.md) → D2 V2. V1 is superseded for future benchmark generation; its original bytes and historical governance provenance remain preserved.

Authority: [Evaluation Contract V2](TECHNICAL_MATERIALITY_EVALUATION_CONTRACT_V2.md), [Benchmark Spec](TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md), [Annotation Handbook](TECHNICAL_ANNOTATION_HANDBOOK_V1.md), and the unchanged [D1 decision](TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md). This record supersedes earlier D2-pending readiness statements, including the historical status recorded in D1; it does not edit D1 or change its predicates.

## 1. Purpose

D2 answers: **“What historical stock-day data is allowed to enter the benchmark, and what information is allowed to be visible at that day's decision cutoff?”** It defines admissibility and point-in-time (PIT) evidence policy. It does not select interesting dates or determine factual severity, contextual relevance, episode structure, delivery obligations or model behavior.

## 2. Authorized research frame

The official benchmark stock-day frame is **2020-01-01 <= session_date < 2025-01-01**. Official Development/Pilot stock-days must come from 2020–2024. Future Fresh Validation stock-days must also come from this frame under the approved D6 sampling/split rules. Historical VN30 membership must be certified for every selected stock-day. The existing **2025–2026 holdout remains SEALED**: do not open, inspect, enumerate or redefine it. These bounds are an allowed-frame rule, not authorization to read every earlier record.

Existing closed Validation V1/V2 individual cases and completed V3 reviewed cases must not be reused as fresh annotation cases. Future builders must obtain metadata-only exclusion manifests/IDs where available, without reopening protected labels/evidence to identify exclusions. A complete group containing a protected reviewed event cannot be made fresh by removing that event: quarantine the overlapping stock-day pending a certified metadata exclusion decision. Unknown overlap/freshness blocks admission; do not guess from ticker/date alone or relabel under a new ID.

Approved D6 controls sample size, actual selected stock-days, development/fresh-validation allocation and representative/enriched design. This revision fixes the lower date bound only; it selects no cohort or stock-days and changes no D6 quota or allocation. Future execution requires a frozen allowlist of exact authorized source ranges, snapshots, instruments and paths, including warmup; D2 policy approval is not a dataset-integrity certificate.

### Benchmark stock-days versus warm-up / lookback data

**BENCHMARK STOCK-DAY FRAME:** `2020-01-01 <= session_date < 2025-01-01`.

**WARM-UP / LOOKBACK DATA:** Earlier pre-2020 observations MAY be used only when PIT-valid and explicitly authorized for D1 prior 60–252-session distributions, MA20/MA50, RSI14, or episode/state initialization where required. A pre-2020 warm-up observation is not eligible to become an official benchmark stock-day and does not expand the sampling frame. It must still satisfy D2 provenance, comparability, availability and protected-data rules. Freeze its authorized ranges/snapshots/instruments/paths before loading; do not silently use unauthorized warm-up data.

### B2 historical-membership certification scope

Future B2 certification needs the VN30 basket in force at the start of 2020 and all membership changes affecting 2020–2024: regular review changes, interim replacements where applicable, effective dates and provenance. The opening basket may require an announcement issued before 2020; publication date is not membership effective date. This revision neither reconstructs nor certifies a membership dataset and does not mark B2 PASS. Any authorized warm-up remains subject to the unchanged D2 evidence rules.

## 3. Historical-universe policy

Use historical **VN30 membership as of each stock-day** wherever reliable historical evidence is available. Preserve stable instrument identity, ticker at date, exchange, session date, membership source/version and effective membership status/date. Record identifier changes without ticker-specific business logic.

Never apply today's VN30 membership retrospectively and call it historical. If reliable membership cannot be established, the stock-day is outside the normal research frame or explicitly unresolved under the frozen frame-building policy; it cannot be silently admitted using current membership. Preserve the reason in frame accounting. No historical membership source is acquired or certified by this task.

Use a versioned exchange calendar. Distinguish holidays, valid trading observations, suspensions/no-trade sessions and provider data loss. A dated row or absent row alone cannot establish which state occurred. Calendar/source policy must be recorded before later generation; synthetic bars are prohibited.

## 4. EOD decision cutoff

Scope is end-of-day only. Timezone: **Asia/Ho_Chi_Minh**. Cutoff: **23:59:59 local time on the trading date**. Store the timezone-aware instant and the named timezone, not a server-local timestamp.

The question is what could legitimately be treated as available by that day's end. Same observation date does not prove availability at exchange close. This benchmark does **not evaluate intraday detection or alert latency**. Recognition-time fields in the general evaluation contract may be retained for provenance, but must not produce intraday/latency claims from assumed EOD data.

## 5. Historical daily-data availability assumption

For finalized historical daily OHLCV without an audited vendor publication timestamp, apply **EOD_AVAILABILITY_ASSUMPTION**: treat the bar as available by the declared 23:59:59 Asia/Ho_Chi_Minh cutoff. Version this policy as `d2-eod-availability-v1`; label timestamp assurance **assumed**, never audited/published/verified.

Every affected observation preserves session/observation date, assumed available_at, assumption version, assurance, provider/source, source snapshot/version, downloaded_at if known, adjustment semantics and quality flags. downloaded_at describes retrieval, not historical publication. The assumption does not establish that later vendor revisions or future corporate-action adjustments were known at the historical cutoff.

If audited availability metadata is present, keep it separately with its provenance. An applicable verified publication time governs visibility: a known post-cutoff publication must not be overwritten by an earlier assumed timestamp. For a future source mapping, record which audited field is applicable and the policy basis before use. Do not silently promote an assumed time to audited or discard conflicting evidence. Missing/unknown timing without a permitted daily-bar assumption leaves visibility unresolved.

The repository's existing `availability_basis='end_of_day_assumption'` is a compatible legacy spelling for this assumption, not sufficient proof of all D2 requirements. Preserve original fields and add prospective policy/provenance through the future benchmark contract rather than rewriting replay records.

## 6. PIT visibility rule

For stock-day t, only information with **available_at <= cutoff(t)** may enter its evidence. No later trading-day record or later knowledge may affect existence, history, MA/RSI, recurrence, episode state, contextual evidence, benchmark alignment or any other feature. Derived values inherit the visibility requirements of their inputs. EventMemory remains past-only, lookup before recording the current event; exposure is separate and remains D3.

Later *allowed* records may be present in an authorized raw snapshot, but they must not affect an earlier packet; §14 defines the required prefix test. This is not permission to open a mixed protected snapshot and filter after loading. News/fundamentals or future alerts/user responses cannot be imported as hidden technical context.

## 7. D1 history interaction

D1 remains unchanged: maximum **252 valid comparable prior sessions**, minimum **60**, current observation excluded. For t, both absolute-return and volume reference distributions contain only valid sessions strictly before t. Preserve the approved nearest-rank q95 convention and inclusive equality. Fewer than 60 comparable observations means **UNRESOLVED**, not DOES_NOT_EXIST.

Calendar/availability/adjustment validity constrains what may enter these histories. Record actual session IDs, count, gaps, excluded reasons and endpoints. Do not backfill, invent observations or search beyond the frozen authorized history to reach the minimum. The existing legacy slice-before-null-filter context is not automatically the D1 last-valid-observation population; no stored V0–V3 values are changed.

## 8. Indicator continuity

MA20, MA50 and RSI14 may include the current bar in this EOD task only if that bar is valid and visible under the declared audited/assumed cutoff policy. Their indicator windows/definitions and provenance remain explicit. This does not permit including the current row in D1 historical reference distributions.

MA/RSI transition checks require previous/current observations to be valid consecutive comparable trading observations under the calendar/data policy. Missing provider bars are not ordinary adjacency; suspended/no-trade sessions must be distinguished from data loss. If continuity cannot be established, the factual transition is **UNRESOLVED**, unless an existing approved family rule explicitly resolves it. No such new exception is invented here. Do not create synthetic bars or treat a multi-session move as an ordinary daily pair.

## 9. VN30 benchmark alignment

For a valid stock return interval t-1 → t, use **VN30(t-1)** and **VN30(t)** for those same interval endpoints. Both observations must have valid source/version, comparability and visibility under the cutoff policy. Daily benchmark availability must carry its audited or explicitly assumed basis; do not infer publication merely from the date.

No future VN30, nearest later session, forward-fill, prior-value substitution or missing-as-zero. If a valid aligned pair is unavailable, market-relative context is **null / unresolved context**, with the specific reason. An otherwise fully evidenced own-history D1 event remains ascertainable; missing benchmark context does not automatically invalidate it. Signed raw and excess returns remain separate evidence.

## 10. Corporate-action comparability

Mechanical price discontinuities from splits, reverse splits, bonus/share distributions, rights adjustments, other corporate-action mechanics or inconsistent adjusted/unadjusted series must not be treated as genuine abnormal technical price moves.

When prior/current prices are not demonstrably comparable, price-return factual evidence is **UNRESOLVED**, unless a versioned, verified comparable adjusted series exists and satisfies the same cutoff policy. Preserve adjustment semantics and evidence of verification. A generic `adjusted` label is not proof that a later back-adjustment was historically available. Do not repair history using future knowledge or mutate an original series.

If share-count/unit changes or provider adjustments make historical volume non-comparable, unusual-volume factual existence is **UNRESOLVED** until comparability is established. Unknown semantics remain explicit. Where those semantics prevent establishing required comparability, a warning flag alone is insufficient to admit the comparison. Optional missing context can remain null, but essential invalid price/volume evidence cannot produce a factual negative or positive.

## 11. Missing-data handling

Record explicit states/reasons, including current bar missing, prior comparable bar missing, insufficient history, VN30 missing, continuity uncertain, adjustment semantics unresolved, source corruption, suspended trading and provider data gap. Preserve known versus assumed versus unavailable evidence, rather than collapsing them into one quality score.

Missing essential existence evidence means **UNRESOLVED**. Missing benchmark context may leave other evidence usable with market context null. Never substitute zero, prior observation, nearest future observation, normal or no-event. Genuine zero values require valid session/source interpretation; they cannot stand in for absence. Structurally accounted-for missingness can support a later authorized quality-study group; incomplete truth cannot produce a complete reference ideal or confident no-useful-change label.

## 12. Source/snapshot provenance

Any later build must freeze provider and available version, download/snapshot identity, raw input hashes, calendar version, VN30 source/version, adjustment semantics and availability-assumption version. Freeze universe membership provenance and exact input allowlist too. Store unknown metadata explicitly; do not fabricate vendor versions or download times.

Reuse an existing dataset only after it passes D2 integrity checks. Prior use in V0–V3 is not proof of D2 validity. Raw snapshots remain immutable; corrections create a new version plus correction manifest with reason, scope, original/new hashes and invalidation of affected derived outputs.

Full container/download hashes belong in the run/source inventory. Cutoff evidence must separately identify its stable authorized snapshot/version and hash the actual cutoff-visible input subset. For prefix tests, use the same logical source/version and cutoff identity; attaching additional allowed future rows to a container must not alter earlier group IDs or packets solely through a new whole-container hash. Preserve both provenance levels without using future-dependent container metadata as an earlier feature/ID. A genuine source correction is a new version, not an invariant-preserving append.

### Inherited V1 repository compatibility findings (historical; no new source inspection)

| Existing convention inspected | D2 consequence; no code changed |
|---|---|
| `src/evaluation/models.py`: timezone-aware available_at; published/end_of_day_assumption/unknown; manifest adjustment metadata | Compatible concepts, but not a complete membership/calendar/assurance/comparability audit |
| `scripts/prepare_development_v3.py`: daily 23:59:59 EOD assumption; current VN30 acquisition | EOD precedent is compatible; current universe cannot be reused as historical membership evidence |
| `src/evaluation/replay.py`: exact benchmark endpoint matching, availability checks, no benchmark fill | Reusable integrity principle, subject to D2 session/clock/source validity |
| Replay appends `adjustment_semantics_unknown` and may continue; adjacent supplied rows are not proof of exchange-session continuity | A legacy run is not D2-certified. Essential unresolved comparability/continuity must instead remain unresolved in a future D2 reference build |
| Legacy replay processes at observation availability time; generic contract contains recognition-time metrics | Future D2 groups use fixed EOD cutoff, not arbitrary replay clock, and make no intraday/alert-latency claim |
| Benchmark group identity contains snapshot identity | Use cutoff-stable evidence identity as above; whole-container hash changes alone cannot change prefix-test group IDs |

These are reuse limitations, not a logical impossibility in the approved policy. No dataset was opened or certified and no existing generator is approved to run unchanged. D1 and Evaluation Contract V2 remain byte-for-byte unchanged.

## 13. Protected-data isolation

Before any future loader runs, enforce an explicit allowlist of date ranges, source snapshots, instruments and permitted repository paths. Protected content must be excluded **before loading**. Post-read filtering is not protection. If an otherwise allowed file mixes protected content and safe content, obtain a separately authorized safe snapshot from the custodian rather than opening it to discover exclusions.

Holdout 2025–2026 remains sealed, without enumeration. Closed Validation V1/V2 individual evidence/labels remain protected from tuning/relabeling; completed V3 reviewed cases/labels are not fresh semantic reannotation input. Use certified metadata-only exclusion manifests, not payload scans. Aggregate historical reports may remain evidence of completed work, not a license to reopen cases. No such exclusion manifest or protected data is accessed in this documentation task.

## 14. Prefix invariance

A future build must demonstrate: **could the exact same evidence for t have been constructed if all data after t were absent?** Compare an authorized source prefix truncated at t with the same source/version plus later allowed data. Visibility must still filter any late-published record, even if its observation date is earlier.

For t, require identical historical reference values, D1 threshold inputs, MA/RSI values, factual opportunities, recurrence state, benchmark context, stable IDs and evidence packet. Include episode/context evidence where applicable under later decisions. Keep logical source and cutoff-subset identity stable; record differing physical container hashes outside the packet comparison as §12 specifies, not as an excuse to omit semantic fields from comparison.

Any difference indicates future dependence and blocks the affected build until a versioned correction is audited. Preserve test inputs, comparison scope, hashes and reasons; not-run does not equal passed. Only allowed unprotected future data may be appended; never use holdout for this test. **No prefix build or benchmark execution runs in this task.**

## 15. Sampling boundary

D2 constructs an eligible frame only. A stock-day must not be selected under D2 because it has a large price move, high volume, detector emission, interesting model score or expected high human label. Ordinary, no-event, single-event, multi-event and quality/missingness days must remain possible frame members where eligibility is established.

The approved D6 decision governs actual sample sizes/dates, development/fresh-validation allocation and representative versus enriched sampling. Its evidence-only enrichment operates within the D2 eligible frame and does not expand it. This D2 revision changes no D6 selection rule and authorizes no signal-heavy selection. No quotas, seeds, strata, selected groups or revised split allocations are created here.

## 16. Non-goals

No sampling, evidence packets, labels, candidate scoring, model tuning, production changes, V4/V5, Validation V1/V2 individual access, holdout access/enumeration, or Final Validation. No external data acquisition, no dataset migration/correction and no frontend tests/build. D1/D3/D4/D5/D6 semantics are unchanged by this revision; D7 remains later work. No existing calibration or validation outcome is reopened.

## 17. Approval status and unchanged rules

**D2 V1 → REVISED. D2 V2 → APPROVED / ACTIVE.** The only policy change is the explicit official stock-day lower bound and related research-frame/warm-up/certification wording. Sections 3–14 retain V1 rules; the repository compatibility findings are inherited historical findings, not a new inspection.

D2 V2 does not change:

- EOD cutoff = 23:59:59 Asia/Ho_Chi_Minh;
- EOD_AVAILABILITY_ASSUMPTION semantics or `d2-eod-availability-v1`;
- `available_at <= cutoff`, no future fill or future-dependent repair;
- historical VN30 membership and VN30 t-1 → t alignment;
- corporate-action comparability and source/version provenance requirements;
- exchange-calendar and protected-case exclusion requirements;
- sealed 2025–2026 holdout protection;
- current-row exclusion and D1 minimum 60 / maximum 252 prior-history rules;
- Fresh Validation anti-tuning rules under the approved D6 and Decision Review Protocol.

**D1 APPROVED; D2 V2 APPROVED; D3 APPROVED; D4 APPROVED; D5 APPROVED; D6 APPROVED; D7 LATER.** Benchmark generation remains subject to real-data B1–B6 certification and applicable execution authorization. D2 V2 is not a data-integrity certificate or permission to enable real-data loading.
