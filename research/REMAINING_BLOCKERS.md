# Remaining metric-specific blockers — 21 October 2026

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

## Current metric-specific limits

| Limit | Classification | Exact missing evidence / useful behavior |
|---|---|---|
| Original VCI metadata | Missing metadata | Qualified original units/currency/scope/fiscal boundaries remain absent; preserve useful partial provider histories without promoting their verification |
| Deeper original annual/quarterly coverage | Missing data; licensing/access for denied originals | Reviewed original quarterly flow histories and more VNM/SSI statements are absent; HPG 2024 PDF and SSI 2025 PDF returned 403, preserved in response audit; existing amounts and qualified periods remain usable |
| VNM accounting model | Missing metadata/data | Accessible IFRS summary is not a complete VAS filing; the VAS link has only two audit pages. Keep CafeF summary partial, do not mix accounting models |
| P/E/P/B/earnings yield | Missing data/metadata | No matched saved SSI price, actual share count and corporate-action basis; provide dated accounting BVPS/EPS only |
| More bank peers | Missing data | Only TCB/VCB have comparable FY2025 originals: 2/22, 15 metrics. Show pair statistics and missing coverage; no industry ranks |
| Historical sector analytics | Missing metadata | Undated SSI taxonomy/version/effective history; no historical membership or sector totals |
| Point-in-time claims | Missing metadata | Qualified publication/revision availability timestamps absent; current source/accounting evidence remains separate |
| Public redistribution | Licensing/access | Public-display approval is not established by free access or educational use; authorized private views remain available |
| Mobile and remaining browser interactions | Environment/capability restriction | No exposed integrated-browser viewport control; mobile, tooltips and exhaustive retry acceptance remain PENDING with reproducible steps |
| Live market/company context | Environment/technical | Core development backend 8431 absent; saved private financial/dividend views work independently |

The old preview policy rejection did not recur under the supported V4 launchers.
Live private runtime and bounded desktop acceptance passed without an override.
The [V4 acceptance checklist](DASHBOARD_VERIFICATION_V4.md) defines remaining work.

## Historical record (superseded by V4 above)

Historical V3 results superseded the checkpoint below: **175 verified observations,
64 supported definitions, and 15 qualified TCB/VCB peer metrics**. See
[V3 delivery](FINANCIAL_INTELLIGENCE_V3_DELIVERY.md),
[current comparison](SSTOCK_FEATURE_COMPARISON_V3.md), and
[current manual acceptance](DASHBOARD_VERIFICATION_V3.md). Runtime remains PENDING.

## Prior bdc70ad checkpoint record

SStock is the product/UI benchmark. WiData is not a prerequisite. Free original
reports, CafeF and VSDC now supply useful real-data increments; no paid access is
required. This table describes remaining limits, not a reason to blank unrelated
working dashboards. See [activated coverage](FREE_DATA_DELIVERY_REPORT.md).

| Area | Classification | Exact remaining evidence | Useful behavior now / next closure |
|---|---|---|---|
| Original VCI units/currency/scope | Missing metadata | Original eight captures still lack qualified original currency/unit, scope and explicit fiscal boundaries. TCB/SSI full original transport is absent | Preserve all original 2,816 amount presentations; select whole HPG/TCB original reports for qualified annual calculations. Never transfer another source's metadata into VCI |
| Qualified quarterly/TTM derivations | Missing metadata / missing data | Original provider flows have unknown scope; reviewed reports cover selected annual fields only | Quarterly and TTM period-end amounts remain useful. Acquire/review qualified quarterly and cumulative boundaries before flow sums, growth and ratios |
| Publication vintage / PIT | Missing metadata | Naive provider strings, approval dates and URL dates are not qualified original publication timestamps; correction release history absent | Current private amounts/calculations are independent of PIT qualification. Retain all receipt times/hashes; no backtest or historical-availability claim |
| Public reuse | Licensing/access | No applicable public source-family permission was recovered for the new original-report/CafeF/VSDC financial views. Existing owner-authorized private use remains recognized | Keep explicit private consumers and no public amount promotion. Apply evidenced existing grants to the relevant source family/audience before public deployment; no blanket educational-use permission |
| SSI taxonomy | Missing metadata / licensing/access | ICB family and exact 406/61 provider pairs known; version, level, effective dates/history and taxonomy-specific public grant remain unresolved | Enable current observed individual tables and missing denominators privately. No prefix hierarchy, historical sums or public taxonomy promotion |
| Qualified peer ranks | Missing data / missing metadata | Only TCB has original-qualified financial data in the two-saved-bank cohort; other captured categories have one issuer | Show individual amounts/source/quality. Review a second compatible original bank report to enable real ranks; unknown-scope amounts do not rank |
| HPG average-balance returns/turnover | Missing data | Reviewed Q4 filing's opening balance is 01/01/2025, not a reviewed prior 31/12/2024 closing balance | 2025 liquidity/leverage and 2024–25 margins/FCF/growth work. Add original audited closing balances and preserve the separate Q4/audited revisions |
| VHM net revenue/ratios | Missing metadata / field semantics | CafeF gross-sales label is not net revenue; original monetary unit/currency/scope unknown | Eight supported reported fields across four annual periods remain partial. Review issuer statements for net revenue and compatible ratio inputs |
| Bank financing | Technical mapping — resolved for reviewed TCB | VCI cfa34 is net cash change, not financing; original TCB statement supplies the actual financing row | TCB original-report financing now works. VCB financing remains missing; never relabel cfa34 or infer from incomplete components |
| Bank specialist metrics | Missing data mapping / missing metadata | TCB original notes contain deposit/loan-quality data, but selected-row mapping, denominator and comparable-period validation for CASA/NPL/LLR/NIM/CAR are not completed | TCB loans/deposits, accounting LDR, ROE/ROA/growth/cash flow work. Map note fields selectively with original row/unit/scope proof, never a generic bank proxy |
| Securities/property specialists | Missing data / missing metadata | Qualified margin/FVTPL/IB funding inputs, property advances/projects and exact revenue-recognition fields not mapped | SSI common amounts and VHM partial balances/profit remain usable; add exact note fields rather than estimates |
| Valuation/dividend yield | Missing data / missing metadata | Compatible price/share vintages, action-adjusted weighted shares, parent equity and yield denominator/history incomplete | Existing valuation empty states remain; three official cash-dividend notices work independently without yield or inferred ex-dates |
| KBS direct read | Technical/access response failure | Normal bounded finance GET returned HTTP 400 / HTML 154 bytes; no financial rows | No integration from a nonexistent payload. Did not retry or bypass; this is not proven to be a licensing denial |
| VNDirect direct read | Access restriction | Normal bounded request returned HTTP 403 / 13 bytes | Stopped; no alternate-host/proxy/impersonation workaround. CafeF/original reports supplied useful alternatives |
| PNJ earlier saved-text proof | Missing metadata | Earlier ten text comparisons lack original binary/page-image proof | Original PNJ amounts remain partial; no promotion from numerical matches alone |
| Preview/runtime acceptance | Environment/policy restriction | Prior automatic approval rejected CreateProcess before startup: “blocked by policy”; no more specific reason supplied | Runtime/browser/mobile PENDING. No new restart, port substitution or alternate launcher. Approved operator checklist in DASHBOARD_VERIFICATION.md |

Read-only port inspection on 2026-10-21 at 03:31:43Z found zero listeners among
3430, 3431, 3546, 3547, 8430, 8431, 8432 and 8546. It does not establish health or
remove the prior approval restriction. No unrelated process/service was changed.

Historical checkpoints' 1,519 cached identities / 25 registered stocks and the
406-issuer archive are different cohorts. This mission does not claim a new live
universe refresh or combine them into a market-coverage percentage.
