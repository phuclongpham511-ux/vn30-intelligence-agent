# Industry membership and useful partial analytics

Current V3 results supersede the checkpoint below: **175 verified observations,
64 supported definitions, and 15 qualified TCB/VCB peer metrics**. See
[V3 delivery](FINANCIAL_INTELLIGENCE_V3_DELIVERY.md),
[current comparison](SSTOCK_FEATURE_COMPARISON_V3.md), and
[current manual acceptance](DASHBOARD_VERIFICATION_V3.md). Runtime remains PENDING.

## Prior bdc70ad checkpoint record

21 October 2026. The existing SSI archive supplies **406 ordinary HOSE
memberships / 61 exact category codes**, observed at
`2026-10-17T13:26:47.008268+00:00`. Audit excludes 379 nonordinary rows and finds
zero duplicate memberships/conflicting pairs. Archive digest:
`7daa4ee90df0e8241749e3004326ccd4d6035d1df2725789d67ee6a40d62202b`.
The exact reviewed pairs are already preserved in the existing private review.

SSI documents identify the ICB field family. Version, hierarchy level,
classification validity and historical changes are unknown. A four-digit code
does not establish a particular level or vendor version. Provider receipt time
is not a membership-effective date. No issuer is classified using its name,
financial ratios or an assumed code prefix. No HNX/UPCOM coverage is claimed.

## Enabled private snapshot

New separate contracts `observed-industry-directory-v1` and
`observed-industry-peers-v1` serve the captured snapshot in the existing private
development mode. They cannot enter the effective-dated IndustryTaxonomy path.
The `/industries` page shows all 61 categories, known captured-company counts,
issuer links and a per-metric coverage/missing list. Observation time/source and
unknown effective history remain explicit; the historical date control is hidden
for this contract rather than presenting a false historical selector.

| Captured exact provider code | Membership denominator | Saved issuers | Useful supported sample |
|---|---:|---:|---|
| 8355 | 22 | 2 | TCB/VCB bank amounts; TCB original-report funding, returns and growth |
| 8777 | 21 | 1 | SSI common profit/assets/equity/cash observations; specialist trading and margin notes unavailable |
| 8633 | 56 | 1 | VHM partial gross profit/PAT/balance fields from CafeF |
| 1757 | 11 | 1 | HPG original-report manufacturing amounts, margins/FCF/liquidity |
| 3767 | 2 | 1 | Existing saved company amounts |
| 5379 | 7 | 1 | Existing saved company amounts |
| 9537 | 3 | 1 | Existing saved company amounts |
| 7535 | 25 | 1 | Existing saved company amounts |

Labels are the exact SSI provider names in the private response, not a newly
invented English taxonomy. Only nine issuers have saved financial coverage;
all remaining members appear in per-metric missing counts, never as zero.

## Peer and aggregation rules

Individual eligible observations remain visible even when another issuer lacks
metadata. Their source, consolidation, source/accounting verification and hashes
are disclosed. Unknown-scope provider amounts have no rank or percentile.

Rank/percentile is enabled only for at least two accounting-qualified issuers
with compatible model, scope and actual fiscal input signatures. Private access
must already be authorized; grades cannot authorize access. The real sample
currently has **zero such multi-issuer cohorts**: TCB qualifies but VCB's source
scope remains unknown. Tests validate ranking with explicitly synthetic compatible
inputs, without promoting those fixtures to a real cohort. A second reviewed
bank report is a practical next step, not a prerequisite for the observation table.

`sector_totals=null`, `historical_aggregation_enabled=false` and public eligibility
false are mandatory in this observed contract. Historical aggregation, effective
membership filters, point-in-time backtests and vendor sector valuation remain
disabled until effective dates/classification history and financial inputs are
evidenced. The existing separate qualified aggregation engine remains unchanged.

## Validation

All 61 actual private API responses pass coverage denominators, source/quality
guards and both English/Vietnamese server rendering. Foreign-host/default-off
tests pass; public and historical consumer paths reject these private responses.
Browser/mobile acceptance is PENDING. See
[application validation](validation/free-data-v2/FREE_DATA_APPLICATION_VALIDATION.json)
and [frontend validation](validation/free-data-v2/FREE_DATA_FRONTEND_VALIDATION.json).
