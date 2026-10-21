# Measured data coverage

## Financial Intelligence V4 — current, 2026-10-21

V4 supersedes the historical checkpoints below: **341 source/accounting and
reporting-metadata-qualified observations (216 reported, 125 derived), 70 supported
definitions out of 77 canonical definitions, ten saved issuers**. Qualified original
histories cover FPT 2022–24, TCB 2023–25, VCB 2024–25, HPG 2024–25 flows/2025 balance
and MWG pre-audit 2024. VNM/SSI remain useful partial provider coverage.
Original captures and revisions remain preserved; metric-level gaps stay visible.
FPT dated ordinary BVPS is supported for 2023/24; P/E/P/B/earnings yield remain
unavailable without matched prices, shares and corporate-action evidence.
The bank comparison is **TCB/VCB, 2/22 observed banks, 15 FY2025 metrics**;
observed-industry ranks/percentiles are suppressed. Historical sector totals stay
disabled. No WiData or paid subscription is required.

Supported private launchers and live HTTP checks PASS. Actual integrated-browser
desktop checks PASS for exercised flows; mobile, tooltips, exhaustive retries and
full live-market context remain PENDING. Backend **1,600 + 32 subtests**, frontend
**334 passed + one existing skip**, typecheck/build and real contracts/static
rendering PASS. PIT/public-rights/fully-verified counts remain separately zero.
See [V4 delivery](FINANCIAL_INTELLIGENCE_V4_DELIVERY.md),
[feature comparison](SSTOCK_FEATURE_COMPARISON_V4.md),
[acceptance and manual checklist](DASHBOARD_VERIFICATION_V4.md),
[coverage](validation/free-data-v4/VERIFIED_METRIC_COVERAGE.csv), and
[valuation decisions](VALUATION_EVIDENCE_AUDIT.md).

## Historical record (superseded by V4 above)

## V3 coverage — historical V3 checkpoint

64 distinct supported definitions: 34 reported and 30 derived. Three original-
report issuers supply 175 SOURCE_VERIFIED, ACCOUNTING_VERIFIED and separately
REPORTING_METADATA_COMPLETE observations (113 reported / 62 derived). PIT/public
rights/fully-verified counts stay zero. Nine issuers total; selected qualified
annual sources cover 2024–25, HPG closing balance only 2025. Original provider
2018–25 annual and 2018-Q1–2026-Q2 quarterly captures remain available. Preferred
views have 2,615 presentations; original 2,816 remain selectable; all-source union
3,023 includes 32 partial VHM CafeF observations and repeated source views.
Twenty-five of 27 preferred API views are populated; VHM quarter/TTM are empty.
Fifteen qualified TCB/VCB FY2025 peer metrics cover two of 22 observed banks;
other members remain missing. Historical membership/totals are disabled.
[Counts and metadata origins](validation/free-data-v3/EVIDENCE_RECOVERY_COUNTS.json),
[per-metric CSV](validation/free-data-v3/VERIFIED_METRIC_COVERAGE.csv),
[delivery](FINANCIAL_INTELLIGENCE_V3_DELIVERY.md).

## Prior bdc70ad coverage

| Selection / evidence | Observations | Source verified | Accounting verified | PIT / public rights / fully verified |
|---|---:|---:|---:|---:|
| Original eight issuers, 24 views | 2,816 | 0 | 0 | 0 / 0 / 0 |
| Preferred nine issuers, 27 views | 2,660 | 100 | 100 | 0 / 0 / 0 |
| Original-report subset of preferred views | 100 (63 reported + 37 derived) | 100 | 100 | 0 / 0 / 0 |
| New CafeF VHM subset | 32 (eight fields × four annual periods) | 0 | 0 | 0 / 0 / 0 |

These are metric-period presentations, including repeated quarter/TTM balances,
not counts of distinct metric definitions. Baseline distinct source-metric IDs:
2,352; preferred: 2,196. The original provider view remains available: the union
of selectable presentations is 2,948 = 2,816 + 100 + 32. Shorter reviewed annual
history is selected as a whole, with no silent source splicing.

HPG contributes 31 canonical reported cells and two extra FX reconciliation
cells; TCB contributes 32 canonical cells. Known original VND/unit, consolidation
and fiscal boundaries unlock annual calculations. Publication vintage stays
unknown, never inferred from download/approval time. Original provider records
are unchanged. CafeF's reviewed transport scale is inferred; its original unit,
currency and scope remain unknown and its unsupported derivations stay withheld.

Industry: 406 observed HOSE memberships / 61 categories, eight categories with
one or more saved issuers, zero real compatible multi-issuer ranking cohorts.
All 61 API bodies and both-language renders pass. Three official FPT dividend
notices are available; other issuer histories are unsampled, not known empty.
No historical aggregation or market-wide coverage percentage is asserted.

See [field-level matrix](validation/free-data-v2/FIELD_LEVEL_EVIDENCE_MATRIX.csv),
[preferred-view matrix](validation/free-data-v2/ACTIVATED_VIEW_EVIDENCE_MATRIX.csv),
[per-metric counts](validation/free-data-v2/VERIFIED_METRIC_COVERAGE.csv),
[counts/metadata origins](validation/free-data-v2/EVIDENCE_RECOVERY_COUNTS.json)
and [application checks](validation/free-data-v2/FREE_DATA_APPLICATION_VALIDATION.json).
Private inputs remain ignored. Runtime/browser/mobile PENDING.

## Prior 86000d3 activation coverage

The same eight immutable captures now populate a validated private research
bundle, including canonical TCB/SSI captures. All 24 actual saved-data API bodies
(eight issuers × annual/quarterly/TTM, eight displayed periods) pass the frontend
research contract and are rejected by the normal public consumer.

The per-period activation matrix contains 11,520 checks: 7,507 PARTIALLY_VERIFIED,
4,013 UNAVAILABLE and zero VERIFIED. Only 2,816 supported single-reported values
are eligible for local research; these span 25 distinct mapped fields, not 25
fully verified or publicly activated metrics. Original fiscal/scope/unit/
publication metadata remains unchanged and unknown where absent.

The archived SSI HOSE response supplies 406 observed ordinary-equity code/name
pairs across 61 exact codes, zero duplicates/conflicts; 379 nonordinary rows are
excluded. This is a dated receipt snapshot, not effective-dated industry membership.
HNX/UPCOM remain unsampled. The private review dataset is not a runtime taxonomy.
Read-only existing-development API inspection additionally measured 1,519 cached
security identities and 25 registered stocks, with 0/25 legacy sector/industry
tags populated. That API exposes no qualified taxonomy metadata. Archive and
current-cache counts are different cohorts and are not combined into a coverage
percentage. See validation/EXISTING_UNIVERSE_AUDIT.json.
See validation/REAL_METRIC_ACTIVATION_MATRIX.csv,
validation/REAL_DATA_API_VALIDATION.json and data/INDUSTRY_MEMBERSHIP_REVIEW.json.

## Original V1 coverage census

Read research/data/OBSERVED_SAMPLE.json for exact per-ticker ranges and research/data/DATA_COVERAGE_MATRIX.csv for field-level numerators and denominators. Eight sample issuers, three statements each, 1,008 statement observations total: 756 reused and 252 newly captured through the existing adapter. This is not a production DB census or all-listed-equity coverage.

All 1,008 lack qualified consolidation/original-unit/publication metadata. The adapter's known transport unit convention is distinct from original metadata. Real public qualification is zero in this measured sample. The private revision journal contains 23,040 normalized period-metric versions across annual/quarterly/TTM projections (most recent 20 periods per frequency, eight annual where available). Its unavailable/blocked values remain null. These are metric-version records, not 23,040 verified financial facts.

No actual issuer-to-industry taxonomy was available in the baseline. Real industry coverage is unactivated. Synthetic tests/preview prove arithmetic, cohort exclusions, rank and missing coverage, not production market completeness. Official PNJ saved-text comparison is separate and does not qualify VCI consolidation or public rights.
