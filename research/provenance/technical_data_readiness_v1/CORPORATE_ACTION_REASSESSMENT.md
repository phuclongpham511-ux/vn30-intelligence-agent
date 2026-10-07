# Corporate-action-aware Technical validation — 2026-10-08

**Status: PARTIAL. Decision: D — INSUFFICIENT_EVIDENCE.** Exact vendor PIT is
**CALIBRATION_BLOCKER_ONLY** under the current official benchmark contract; it
is not a blocker for already-approved current adjusted-price indicators. No
calibration, production policy change, threshold tuning or benchmark admission.
Git base: `b5f3c89fab02c42623cacacfb3dbb0ab07cca2d3`.

## Hypothesis and interpretation

Test whether SSI current adjusted history plus verified action context can replace
exact vendor vintages for the Technical decisions actually implemented. Exchange
ex-date reference adjustment and vendor back-adjustment of earlier OHLC are
different operations. SSI's owner-supplied confirmation covers cash dividends,
stock dividends/bonus, additional issuance and rights, but not volume semantics.
Neither that confirmation nor missing formulas implies unusable product prices.

The bounded evidence below supports continuity in three windows, not universal
decision invariance or a calibrated exclusion rule. Current-vintage continuity
cannot measure changes between unavailable vendor vintages. A coincident event
is not a labeled mechanical artifact. No causal contamination/suppression rate
can be inferred merely from overlap counts.

## Sources actually inspected

Source access checked in this task; no authenticated/private website scraping,
robots bypass, new package dependency or production scraper was introduced.

| Source | Verified information / boundary |
|---|---|
| [VNM issuer notice, mirrored by Vietstock](https://static2.vietstock.vn/vietstock/2020/8/6/20200806_20200806%20-%20VNM%20-%20CBTT%20ngay%20DKCC%20chot%20danh%20sach%20tra%20co%20tuc.pdf) | Issuer notice dated 2020-08-03: ticker VNM, record 2020-09-30, cash 2,000 VND/share, bonus 5:1. This is an issuer document, not a vendor methodology certificate. |
| [Dan Tri contemporaneous report](https://fica.dantri.com.vn/chung-khoan/co-dong-vinamilk-huong-loc-co-tuc-gia-co-phieu-bat-tang-manh-20200929010525937.htm) | Explicit VNM ex-date 2020-09-29, cash amount; secondary date confirmation. |
| [VSDC GAS notice 161638](https://www.vsd.vn/vi/ad/161638), [SHS contemporaneous report](https://archive.shs.com.vn/Sites/QuoteVN/SiteRoot/reportattach/20230912_172533_Market%20Lens%20Final%20New%2012-09-2023.pdf) | Depository record date 2023-09-25; SHS explicitly supplies ex-date 2023-09-22 and 20% bonus. VSD page retrieval was intermittent; no stable machine feed certified. |
| [HDB notice reported by Vietstock via 24HMoney](https://24hmoney.vn/news/hdbank-chot-quyen-chia-co-tuc-2021-ty-le-25-c4a1629620.html), [VSD calendar](https://www.vsd.vn/lich-giao-dich?date=28%2F09%2F2022&tab=LICH_THQ) | Secondary article body: ex 2022-09-27, record 2022-09-28, stock dividend 25%. VSD indexed calendar confirms record date/type; complete calendar body was unavailable. |
| [VSDC GAS notice 174104](https://web.vsd.vn/vi/ad/174104), [Cophieu68 historical action annotation](https://cophieu68.vn/quote/history.php?cP=6&id=gas) | Depository indexed notice identifies cash plus capital-from-equity distribution; secondary annotation supplies ex 2024-09-13, cash 60% of par and 2% bonus. Full VSD body could not be retrieved (502/timeouts). Terms/date remain secondary-backed, not production-certified; pagination can move. |
| [ACBS SSI rights notice](https://acbs.com.vn/tin-tuc/chi-tiet/thong-bao-thuc-hien-quyen-mua-phat-hanh-them-ssi-1015000270-nc7204e5a), [linked VSD notice](https://vsd.vn/vi/ad/151355) | ACBS body verifies record 2022-06-23, rights 2:1, subscription 15,000 VND, rights ID MIRSSI221 and subscription dates. Ex-date not asserted from record-date subtraction. SSI prices were not acquired for this study because protected episode scope remains unresolved. |

Official sources expose useful action terms but record date alone does not prove
the exchange ex-date. Announcement/payment/additional listing dates are not
interchangeable with ex-dates. Rights issuance is a subtype of additional issuance;
ESOP/private placements cannot be assigned an ex-date formula automatically.
No separate verified split/reverse-split sample was found in this bounded search.
The existing SSI provider has no corporate-action lookup. Existing news/community
sources provide disclosures, not a complete effective-dated action calendar.

## Scope, acquisition and sample

The immutable 30-symbol cohort was loaded through `load_cohort`; pinned B6
identity-only manifests were verified through `load_certified_ledger`. No reviewed
payload/label was opened. Because episode bounds are unresolved, this small study
conservatively selects issuers absent from every protected record. This is a
research sampling restriction, **not** a proposal to exclude entire issuers from
calibration. No 2025–2026 historical observations or pre-2020 warmup were requested.

The four price request ranges were frozen in `corporate_action_study.py` before
acquisition. Each begins April 1 of its event year and ends on the date below.
This task explicitly authorizes descriptive acquisition; it does not enable or
bypass the disabled official benchmark loader or certify B3/B4/B5. The generic
production SSI provider and normalization were reused unchanged.

| Issuer | Ex-date | Action components | Request end | Result |
|---|---|---|---|---|
| VNM | 2020-09-29 | cash + bonus | 2020-10-09 | Rejected by existing `MarketBar`: invalid OHLC range |
| HDB | 2022-09-27 | stock dividend | 2022-10-07 | 131 valid rows |
| GAS | 2023-09-22 | bonus | 2023-10-06 | 130 valid rows |
| GAS | 2024-09-13 | cash + bonus | 2024-09-27 | 124 valid rows; secondary-backed terms |

Requested: 3 issuers, 4 ex-dates, 6 action components, 2020/2022/2023/2024.
Measured: **2 issuers, 3 ex-dates, 4 action components, 2022–2024**, 385 input
rows and 33 event-window sessions. Rights/additional issuance has source evidence
but **zero measured windows**. VNM is missing, not a clean/zero-event observation.
The diagnostic subclass confirmed only `Invalid OHLC range`; it did not repair,
drop bad rows or change the provider. No raw bar dump was retained.

Observed sample frequency: HDB/2022 one date/one component; GAS/2023 one/one;
GAS/2024 one/two. VNM/2020 has one documented date/two components but no valid
price window. **Annual incidence is not estimable:** dates were purposively
selected, not a complete issuer-year census. These counts do not establish rarity.

Acquisition completed `2026-10-07T17:11:32.932455Z` (2026-10-08 Vietnam).
Normalized input hashes (canonical JSON generated by the harness):

- HDB: `832948857e81f888bc5cd685ac9c725016966ba5745b6345c201ac1bbdbcbc97`
- GAS/2023: `a85d077e667b7644b143dd07e3184984ac6514357dd7f013bca70d8ff7831bca`
- GAS/2024: `9dca83fe80c4fb8a4ec1884ca70fd1552c9e8c878e3d9257abe2afcdcda9b807`

Hashes detect a later changed query; they cannot reproduce unavailable vintages.
Only derived research diagnostics are emitted; no long-term SSI snapshot archive
is created. Long-term raw/normalized retention rights remain unresolved.

## Numeric price and volume results

T±5 means actual observed SSI trading rows; calendar continuity is not independently
certified. No weekend subtraction or record-date snapping. Existing analytics and
detectors are called on chronological prefixes, with prior-only context (minimum
60 observations, configured trailing lookback 252). The finite prefixes have only
113–122 prior rows at T; this is not a full 252-session or whole-era replay.
Market-relative context is missing, not zero. No materiality scores are calibrated.

All percentages below are computed from the adjusted series. Range means
`(high-low)/previous close`; BB width is `(upper-lower)/SMA50`.

| At T | HDB/2022 | GAS/2023 | GAS/2024 |
|---|---:|---:|---:|
| Close return | +2.8785% | +2.4266% | -2.3345% |
| 5-session return | -2.7218% | -0.4705% | -2.9152% |
| 20-session return | -8.2700% | +10.9216% | -0.4288% |
| High/low range | 3.7313% | 2.4790% | 2.4975% |
| MA20/MA50 minus one | 0.7943% | 4.2679% | 3.7769% |
| RSI14 | 39.7824 | 67.2926 | 44.4682 |
| BB width | 15.8503% | 17.9844% | 14.3529% |
| Annualized 20-session volatility | 26.8836% | 23.5274% | 16.3438% |
| Min/max daily return across T±5 | -3.9164% / +2.8785% | -2.2936% / +3.3962% | -2.3345% / +0.9604% |
| Volume / prior mean at T | 0.6667 | 1.3844 | 1.6044 |
| Volume midrank at T | 0.2951 | 0.8487 | 0.8584 |
| Mean volume T+1..+5 / T-5..-1 | 1.4573 | 1.0597 | 0.6729 |

The 25% and 20% free-share distributions would mechanically reduce an otherwise
unchanged *unadjusted* price by 20% and 16.67%, respectively. Such negative steps
are absent in these two adjusted windows. This is consistent with back-adjustment
removing the large mechanical jump, not a reconstruction of SSI factors. Combined
cash/bonus GAS/2024 has no verified raw-price counterfactual. All three windows
remain subject to actual market movement and later revisions.

Volume does not show a common multiplier or consistent pre/post pattern. No q95
volume event appears in the 33 sessions. This does **not** prove adjusted volumes
or comparability: delivery/listing/tradability of new shares may occur later than
ex-date. A ±3 window cannot certify that longer relative-volume baselines are safe.
Both Bollinger reversal events require a volume gate, so their qualification cannot
be treated as price-only even though Significance reuses return context.

## Event overlap and candidate windows

Production V0 emits abnormal-price and unusual-volume **candidates on every
eligible session**, without a q95 detection threshold. Report them separately
from an explicitly descriptive subset requiring own-history midrank >= .95 for
those two types; retain all MA/RSI/BB events in that subset. This subset is **not**
D1's nearest-rank q95 predicate and is not a new detector or calibrated label.
Each cell is inside/outside, restricted to the 33 T±5 observation sessions.
Outside does not mean verified action-free, because action calendars are incomplete.

| Existing candidate type | T | ±1 | ±2 | ±3 |
|---|---:|---:|---:|---:|
| abnormal_price_move | 3/30 | 9/24 | 15/18 | 21/12 |
| unusual_volume | 3/30 | 9/24 | 15/18 | 21/12 |
| ma_cross | 0/1 | 0/1 | 1/0 | 1/0 |
| rsi_regime_entry | 0/0 | 0/0 | 0/0 | 0/0 |
| bollinger_lower_reversal_volume | 0/0 | 0/0 | 0/0 | 0/0 |
| bollinger_upper_reversal_volume | 0/0 | 0/0 | 0/0 | 0/0 |
| Total (67) | 6/61 | 18/49 | 31/36 | 43/24 |
| Percent inside | 8.96% | 26.87% | 46.27% | 64.18% |

Descriptive q95 subset: three price events (all GAS/2023), one MA event (HDB),
zero volume/RSI/BB events. Inside/outside totals: **1/3, 1/3, 2/2, 2/2** for
T/±1/±2/±3, respectively (25%, 25%, 50%, 50% of four events).
Price counts are 1/2 at every candidate width; MA counts are 0/1, 0/1, 1/0, 1/0.

Blanket suppression would remove those counts, but the number of actual artifacts
removed and unrelated events unnecessarily suppressed is **unknown**. In particular,
the positive GAS return at T cannot be labeled invalid simply because it is an
ex-date. No smallest defensible exclusion window emerges from these observations.

## Synthetic audit versus real observations

The previous synthetic older-price factor .5 creates a very large boundary. The
observed ±5 return ranges above are much smaller; those specific large artificial
steps are not seen here. This agrees with the prior correctly-adjusted split control:
adjustment can remove artifacts. It does not prove historical SSI revisions are
uniform, nor estimate how often a real revision changes an event. No paired vendor
vintages/raw reconstruction exist in this sample. Synthetic worst-case flip rates
must **not** be used as empirical SSI production error rates; three clean-looking
current-vintage windows must not be used as proof that those risks never occur.

## PIT reassessment and recommended policy

- **Product Technical: YES** for existing factual current adjusted-price indicators,
  with current data provenance and existing validity checks. This was already
  approved; this study does not validate calibrated Materiality, historical volume
  semantics or all BB event behavior. Exact old vendor bytes are not necessary to
  describe the currently observed series.
- **Historical calibration: CONDITIONAL, currently NO admission.** Exact old bytes
  need not be a universal scientific requirement for invariant transforms, but
  source-backed decision equivalence has not been established here. Official
  calibration remains blocked by comparability/vintage/continuity evidence. No
  official run is authorized by this report.
- **PIT classification: CALIBRATION_BLOCKER_ONLY**, scoped to the existing official
  PIT-sensitive benchmark. Existing product qualification is unchanged. **Decision D**
  describes this action-aware policy study, not a revocation of product approval.
- **Simple constraint: none selected.** KEEP + CONTEXT is a sensible future factual
  display once verified dates are available. No deletion, down-weight, calibration
  exclusion or new boolean implying complete action coverage is implemented.

The proposed policy cannot yet cover all five requested action categories: no
rights/additional-issuance price window, one rejected combined-action window,
incomplete calendar coverage, partly secondary ex-date evidence, and no artifact
ground truth. A larger study needs independently verified action-free comparisons
and share-delivery timing; counting coincidences alone cannot identify contamination.
Consequently no corporate-action production lookup/model or research exclusion
helper is justified yet. SOURCE_DECISION and CONTEXT remain unchanged; the previous
audit is preserved, not overwritten.

## Independent engine questions

**Numerical fragility: unresolved, reproduced.** `context.percentile` uses exact
float `<` and `==`. The existing geometric-return test reproduces >.4 Significance
changes under uniform .75 scaling with identical semantic events. A fixed decimal
quantum or epsilon would change true ordering without a declared measurement
resolution; raw ULP comparison does not bound error from return cancellation and
rolling indicator chains. No principled small tolerance was established in this
study, so no arbitrary epsilon or Significance redesign was shipped.

**Event identity: unchanged.** `ReplayCase.case_id` hashes dataset/config/candidate
including evidence. It identifies an immutable replay observation/version; changing
it would risk protected labels and stored joins. Semantic matching by ticker,
type, confirmation date (and direction when relevant) can be used for comparisons
without replacing that ID. Existing EventMemory already keys recurrence by
ticker/type/time rather than raw price hashes. No demonstrated product dedup defect
requires a migration. Raw evidence and dataset versions remain inspectable.

Forward validation can record events, engine/data version and observation timestamp
plus verified action context, preserving later corrections as new versions. Unknown
action coverage must remain unknown. Such event logging can measure recurrence and
noise prospectively, but cannot reproduce absent inputs or establish usefulness
without independent evaluation. SSI retention rights remain unresolved; no snapshot
archive, scheduler or storage-policy change is included.

## Execution, tests and changes

Research harness: `uv run --no-sync python -m research.provenance.technical_data_readiness_v1.corporate_action_study`.
Uses the existing provider; emits derived diagnostics and normalized hashes only.
No import-time acquisition. A fresh run may differ because SSI serves current history.

`uv run --no-sync python -B -m pytest -q -p no:cacheprovider tests/test_corporate_action_study.py tests/test_analytics.py tests/test_materiality.py tests/test_historical_evaluation.py tests/test_evaluation.py tests/test_technical_benchmark.py tests/test_benchmark_admission.py tests/test_benchmark_population.py tests/test_certified_exclusions.py tests/test_technical_universe_boundary.py tests/test_decision_invariance_audit.py`
— **240 passed**, one existing Starlette/httpx deprecation warning.

New tests cover protected/cohort/date admission to the research request, exact and
±1/±2/±3 observed-session counts, weekends, missing dates and absent event types.
No runtime behavior changed, so runtime corporate-action model tests are not
applicable; frontend build and full unrelated backend suite were not run.

Only this report, the bounded harness and its tests belong to this task. Existing
ingestion/UI changes and other untracked research remain untouched. No calibration,
Watchlist work, indicator addition, provider alteration, cohort/holdout modification,
raw snapshot archive, secret inclusion or push.

**Next:** complete a protected-safe, verified rights/additional-issuance sample and
resolve the rejected VNM window before selecting an action-aware exclusion policy.

## Operational decision — 2026-10-08

The owner approved corporate-action-aware **context**, not exclusion or a further
PIT research gate. V1 keeps SSI adjusted indicators and all detector/scoring rules
unchanged. Verified exact ex-date matches use actual Woofi receipt time; revisions
and late context append separate evidence without rewriting original events.
Missing evidence remains UNKNOWN. The prior studies above remain historical
evidence, not a claim of current product suppression policy or a general Product
blocker. Official calibration and vendor-vintage certification are not performed.
Implementation, source limits and verification are recorded in
[`docs/CORPORATE_ACTION_CONTEXT_V1.md`](../../../docs/CORPORATE_ACTION_CONTEXT_V1.md).
