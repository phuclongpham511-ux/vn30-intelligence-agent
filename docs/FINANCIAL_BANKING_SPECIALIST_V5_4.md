# Financial Intelligence V5.4 — banking specialist growth

## Outcome

The existing private financial research path now plots customer-loan and
customer-deposit growth for the seven saved bank issuers: TCB, VCB, ACB, BID,
CTG, MBB and VPB. It reuses VCI line codes `bsb104` and `bsb113`, the existing
financial engine, period selector, charts, statement tables and observed-bank
comparison API. No provider was added or called, no saved capture was changed,
and no financial engine was duplicated.

Annual rates are `(current year-end balance - prior year-end balance) / prior
year-end balance`. Quarterly rates use the same calculation against either the
same quarter one year earlier (YoY) or the immediately preceding quarter
(QoQ). The engine requires both exact source periods, a positive prior balance,
the same statement line and compatible source references. Missing periods and
non-positive bases remain null. The series describe source-mapped customer-loan
and deposit balances; they are not regulatory credit-growth quotas.

## Saved coverage

| Issuer | Preferred annual source and history | VCI annual alternative | VCI quarterly periods | Annual loan/deposit YoY observations | Quarterly YoY / QoQ observations |
|---|---|---|---|---:|---:|
| TCB | Reviewed issuer reports, 2023–2025 | 2018–2025 | 2018-Q1–2026-Q2 (34) | 1 / 1 | 30 / 33 each |
| VCB | Audited issuer report, 2024–2025 | 2018–2025 | 2018-Q1–2026-Q2 (34) | 1 / 1 | 30 / 33 each |
| ACB | VCI, 2022–2025 (4) | — | 2025-Q3–2026-Q2 (4) | 3 / 3 | 0 / 3 each |
| BID | VCI, 2022–2025 (4) | — | 2025-Q3–2026-Q2 (4) | 3 / 3 | 0 / 3 each |
| CTG | VCI, 2022–2025 (4) | — | 2025-Q3–2026-Q2 (4) | 3 / 3 | 0 / 3 each |
| MBB | VCI, 2022–2025 (4) | — | 2025-Q3–2026-Q2 (4) | 3 / 3 | 0 / 3 each |
| VPB | VCI, 2022–2025 (4) | — | 2025-Q4–2026-Q3 (4) | 3 / 3 | 0 / 3 each |

The VCI alternative remains selectable for TCB and VCB when a user wants its
longer annual provider history. The preferred TCB/VCB annual views continue to
use the previously reviewed issuer-report packets; no provider values are
spliced into those histories. Quarterly views use the existing VCI histories.

All seven issuers have customer-loan and deposit amounts in the selected
histories. Annual provider histories for ACB, BID, CTG, MBB and VPB yield three
period-to-period rates per line. Their latest quarterly captures yield three
QoQ rates per line; a matching prior-year quarter is not saved, so quarterly
YoY stays unavailable. TCB and VCB's longer VCI histories yield 30 YoY and 33
QoQ values per line. These counts are computed observations, not a claim that
every period has every source field.

## Evidence and presentation

The new **Bank credit and deposit growth** panel appears in the existing
Financial overview, performance and health sections. It uses the selected
annual or quarterly periods, keeps percentages on a separate percentage axis,
and offers the existing keyboard-accessible per-series controls and source
disclosure. YoY and QoQ are separate series; there is no interpolation or
zero-fill.

For private VCI research, a calculation is shown as `PARTIALLY_VERIFIED` only
when both exact period records pass the adapter, ownership, field-code, unit,
value, record-hash, receipt-hash and prior-period checks. The period values and
formula inputs remain in the financial evidence object and source statements.
Its verification dimensions are unchanged: missing consolidation scope,
original fiscal boundaries, publication time, original-document page review and
public display permission remain disclosed. The special partial display is
limited to the authorized personal-research response; public consumers still
withhold it. It does not assert accounting verification or public rights.

Source-reported values and calculations stay distinct. A calculation is not
renamed as a reported provider growth metric. Amounts remain VND source lines;
rates remain fractions formatted as percentages. The existing reporting period,
statement basis, source and line-code evidence remain inspectable.

## Specialist metric coverage

| Metric | Available evidence | V5.4 handling |
|---|---|---|
| Customer-loan growth | All seven from saved VCI balances; reviewed TCB/VCB annual comparisons also exist | Calculated exact-period YoY/QoQ; VCI rates appear only in private research as partially verified |
| Customer-deposit growth | All seven from saved VCI balances; reviewed TCB/VCB annual comparisons also exist | Same guarded calculation and presentation as customer loans |
| Non-performing loans | TCB 2024–2025 original notes | Existing grades 3–5 / matching classified-loan calculation retained; not generalized to other banks |
| Loan-loss coverage | TCB 2024–2025 original notes | Existing matching allowance / grades 3–5 calculation retained; securities-margin allowance remains excluded |
| Demand-deposit share | TCB 2024–2025 original notes | Existing accounting share retained; it is not labelled as a provider or regulatory CASA definition |
| Accounting loans / deposits | TCB 2023–2025 and VCB 2024–2025 reviewed statements | Existing accounting ratio remains explicitly distinct from regulatory LDR |
| NIM | No matched average earning-asset base and qualified interest-income definition in the saved packets | Unavailable; net interest income alone is insufficient |
| Cost of funds | No compatible average interest-bearing funding base and interest-cost definition in the saved packets | Unavailable |
| Regulatory LDR, CASA and peer NPL/LLR for the other six banks | No reviewed compatible denominators or source-reported specialist fields in the saved evidence | Unavailable; accounting proxies are not substituted |

The saved VCB audited 2025 report was also checked for searchable note text. Its
84-page scan provided no selectable note text through the installed reader, and
the already reviewed extraction covers statements rather than the needed loan
quality or demand-deposit notes. No VCB specialist values were inferred from
that absence. No VCI ratio endpoint or new provider was queried.

## Bank comparison coverage

The existing SSI-observed bank membership set contains 22 symbols; seven have
saved financial packets. For FY2025 customer-loan and deposit growth, seven
individual values are available in the private comparison response, but only
TCB and VCB pass the comparison evidence gates. They are labelled as a
**two-company comparison**, with `2/22` comparable/observed-industry members.
The other five VCI values remain visible as source-backed individual
observations with `comparison_eligible=false`; they do not enter the pair
distribution. This is not a qualified sector ranking or complete banking
industry statistic.

For 2026-Q2 QoQ growth, seven of 22 banks have observations and zero are
comparison-eligible. For 2026-Q2 YoY growth, TCB and VCB have observations and
zero are comparison-eligible. Historical sector aggregation remains disabled.

## Validation and limits

Focused coverage used only the ignored `.local/free-data-v4-ready` saved
packets. It read all seven issuers in annual and quarterly modes, checked
computed-rate counts and latest verification grades, and exercised the FY2025
and 2026-Q2 observed-bank comparison projections. No provider acquisition or
preview restart was run. Backend and frontend test suites, typecheck and build
results are recorded in the V5.4 delivery commit and final task report.

The full backend suite passed: **1,624 tests and 32 subtests** (one existing
Starlette/httpx deprecation warning). The full frontend suite passed **338
tests** with one existing skip. Typecheck, production build and `git diff
--check` passed. Focused tests cover exact formula inputs, source/receipt hashes,
partial verification display, and fail-closed handling for public responses.

Visual browser acceptance is **PENDING**. The preview was not restarted. Public
distribution remains disabled for personal VCI evidence; this change does not
alter the original source-rights policy.
