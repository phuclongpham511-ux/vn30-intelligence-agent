# Financial Data Intelligence V1 — real-data activation, 21 October 2026

Current continuation from 86000d3 adds free saved CafeF, original HPG/TCB report
and VSDC evidence. It activates 100 source/accounting-verified annual
metric-period observations, partial VHM, industry observation tables and three
official dividends. See [current delivery](FREE_DATA_DELIVERY_REPORT.md),
[activation decision](ACTIVATION_DECISION.md), and
[field-level evidence](EVIDENCE_RECOVERY_REPORT.md). The record below is the
earlier 86000d3 checkpoint; its zero supported derivations is superseded only
for the newly reviewed inputs. Runtime acceptance remains PENDING.

## Prior activation record

Base: 591f665 on feature/financial-data-intelligence, existing woofi-financial-data
worktree. **PARTIAL: real saved-data/API and frontend contracts pass; runtime and
new-code browser acceptance remain PENDING. Public activation remains zero.**

## What is now usable

The existing private research reader now accepts both its original raw-capture
format and hash-pinned canonical outputs of the existing VCI adapter. A private,
immutable eight-issuer bundle was prepared under .local/activation-captures.
Six original captures are copied byte-for-byte; TCB/SSI retain the exact canonical
capture bytes from V1. No new provider, financial request, SSI authentication,
SDK upgrade, application DB write or running-service change was made.

The existing /personal-research/financials/{ticker} API was exercised through
in-process ASGI transport against this bundle. All 24 issuer/frequency projections
passed, and their actual responses passed the frontend research parser.
The normal public frontend parser rejected all 24 private responses. Foreign
Host and uncovered-ticker requests remained unavailable.

The authorization boundary is unchanged: explicit owner-authorized local research,
literal loopback host/socket, default-off configuration, no forwarded-header
authorization, private/no-store responses and no live fallback. Supported runtime
must still be restarted through an approved operator procedure before claiming
these new changes are running.

## Metric availability and verification

Each period/metric now has a distinct evidence grade, display eligibility,
public eligibility and exact missing-evidence list. These fields are exposed in
the ordinary display projection and the private response, with VI/EN UI disclosure.
Grades cannot place a withheld value into a response or grant permission.

| Grade | Meaning in this delivery |
|---|---|
| VERIFIED | The required original-unit/currency, reporting scope, fiscal/publication and document/page evidence is complete; access remains a separate check. No measured real metric reaches this grade. |
| PARTIALLY_VERIFIED | A source amount or canonical calculation is reproducible, but required evidence is incomplete. Only supported single reported observations are eligible in authorized private research. |
| UNAVAILABLE | Required values/compatible calculation evidence are absent, invalid or synthetic. No number is substituted. |

Across 11,520 metric-period checks (60 outputs × eight displayed periods × three
frequencies × eight issuers), grades were 7,507 PARTIALLY_VERIFIED and 4,013
UNAVAILABLE, with zero VERIFIED. Only **2,816 single reported observations** are
display-eligible in the private projection. Partial arithmetic evidence does not
make a ratio or comparison eligible.

The union of 25 private reported fields is revenue, gross_profit, net_profit,
profit_parent, eps_reported, operating_income, net_interest_income, total_assets,
total_liabilities, equity, current_assets, current_liabilities, inventory,
cash_equivalents, short_debt, long_debt, customer_loans, customer_deposits,
cash_operating, cash_investing, cash_financing, capex_signed, cash_net_change,
cash_beginning and cash_ending. Availability is issuer/model/period-specific.
EPS is source-reported VND/share, never a reconstructed or summed EPS.

| Source-validated issuer | Model | Latest annual eligible field count | New panel observations across eight annual periods |
|---|---|---:|---|
| FPT, HPG, MWG, PNJ, REE | Nonfinancial | 21 each | Cash flow: 24 each |
| TCB, VCB | Bank | 15 each | Cash flow: 16; lending/deposits: 16 each |
| SSI | Securities/common financial | 12 | Cash flow: 24 |

These are saved-source validation results, not fully verified issuer accounts or
freshness certification. Annual coverage ends in 2025; quarterly in 2026-Q2.
All original 1,008 statement observations remain in the source evidence; the
application response uses eight periods per selected frequency.

## Exact evidence still absent

All sampled statements lack qualified consolidation scope, original unit/currency
and fiscal boundaries. Publication strings are retained but have no qualified
timezone/version semantics. The existing audited VND ×1 adapter contract supports
individual source observations; it is not original-report unit verification.
Fetch/read times are not substituted for publication.

Gross/net margins, ROE/ROA, liquidity/leverage, working-capital/turnover, growth,
FCF, accounting LDR and TTM flow sums remain withheld where those gates fail.
Bank NIM/CASA/NPL/LLR and securities/property specialist fields were not invented.
Bank cfa34 has the observed label “Net Increase/(Decrease) in cash and cash
equivalents”; it must not be exposed as financing cash flow under the generic
nonfinancial mapping. Source definition conflicts remain visible.

The canonical-only TCB/SSI files are validated against source line codes, labels,
values, units, identity, fiscal labels, original date strings and flow basis.
Their immutable file hashes and original receipt/record hashes remain. The loader
does not independently reconstruct their original transport payloads; this is
another reason to retain partial confidence.

## Industry review

The original SSI archive hash was reverified:
7daa4ee90df0e8241749e3004326ccd4d6035d1df2725789d67ee6a40d62202b.
Its HOSE response has 406 ordinary-equity code/name pairs across 61 exact codes;
379 other instruments were excluded, with zero duplicate/conflicting assignments.
HNX/UPCOM were not sampled.

A private reviewed-observation dataset now preserves those pairs, actual receipt
time and record hashes. Classification effective dates, taxonomy level/version,
financial model and aggregation eligibility remain null/false. The review format
is deliberately rejected by IndustryTaxonomy, so an observation date cannot
become a historical membership date. No real sector aggregation is activated.
Existing Security persistence has no ICB columns, and legacy Stock sector/industry
strings have no version/effectiveness evidence. No persisted-current-universe
census was inferred from the archive or fixture seeds.

Separately, two read-only cached endpoints on the existing development backend
reported 1,519 security identities and 25 registered Stock rows. All 25 registered
rows had empty legacy sector/industry tags; the universe item contract has no ICB,
taxonomy-version or effective-date fields. Its last synchronization was
2026-10-19T01:44:34.396987Z. This actual cache audit is not a claim that the new
branch is running, and no provider acquisition or database write was requested.
See [existing-cache audit](validation/EXISTING_UNIVERSE_AUDIT.json).

## Rights and runtime

Existing owner-attested lawful research use and owner-reported SSI permissions
remain recognized. Their applicability to public VCI fundamentals and SSI taxonomy
fields is not established by the inspected evidence. We did not reinterpret
educational/software permission as data redistribution permission.
[Vnstock's scope](https://vnstocks.com/onboard/pham-vi-cong-cu) separates tool
operation from third-party data conditions. [SSI documentation](https://guide.ssi.com.vn/ssi-products/general-information)
describes registration, keys and limits; it is not an account-specific rights grant.
No new terms, account or credentials were accessed.

The prior preview restart failed at tool automatic approval before process
creation, with the stated reason “blocked by policy”. No alternative launcher,
port change or automated restart was attempted in this continuation. Existing
3430/3431/8430/8431/8432 listeners were inspected only. New-code runtime and mobile
visual validation remain PENDING; source contracts and build output do not replace
browser acceptance.

Evidence: [API validation](validation/REAL_DATA_API_VALIDATION.json),
[frontend validation](validation/REAL_DATA_FRONTEND_VALIDATION.json),
[metric matrix](validation/REAL_METRIC_ACTIVATION_MATRIX.csv),
[capture manifest](validation/REAL_DATA_FIXTURE_MANIFEST.json),
[industry review](data/INDUSTRY_MEMBERSHIP_REVIEW.json),
[dashboard checks](DASHBOARD_VERIFICATION.md), and
[remaining blockers](REMAINING_BLOCKERS.md).
