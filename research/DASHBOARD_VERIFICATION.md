# Dashboard verification — real saved evidence, 21 October 2026

Status: **API/data contracts PASS; current-branch runtime and browser/mobile
acceptance PENDING.** The API test transport is in-process and starts no listener.

| Component | Annual and quarterly real data | TTM behavior | Calculation and display decision |
|---|---|---|---|
| Cash flow/reinvestment | FPT/HPG/MWG/PNJ/REE/SSI: operating, investing, financing, 24 points over eight periods per view. TCB/VCB: operating/investing, 16 points. | Unknown-scope flow sums stay withheld. | Reported signed amounts remain VND; missing financing/FCF is not zero. FCF is derived and not activated by raw cash amounts. |
| Profitability history | Zero activated real ratio points in all eight issuers. | Withheld. | Margins and average-balance returns require compatible scope. Bank/securities do not receive industrial margin substitutes. |
| Liquidity/leverage | Zero activated real ratio points; unavailable for financial models where inapplicable. | Withheld. | Existing definitions and positive-denominator checks remain. Raw balance values do not qualify a ratio automatically. |
| Bank loans/deposits | TCB/VCB: two reported period-end series, 16 points over eight periods per view. | Individual period-end amounts remain, never summed. | Accounting loan/deposit ratio remains withheld. The panel does not claim regulatory LDR, NIM, CASA or NPL. |
| Industry/peers | No real qualified cohort enabled. Directory deliberately reports unavailable without reviewed taxonomy. | No historical membership inferred. | Existing matched sums/ratios, exclusions, ranks and percentiles retain automated coverage. Reviewed SSI snapshot cannot enter the taxonomy contract. |

## Verification performed

- Read the real saved sources through the actual saved-data loader and private
  financial API, with source/code/label/unit/date/basis and hash validation.
- Checked 24 personal API bodies against canonical projections, no canonical input
  mutation, single-original-observation lineage for every visible research value,
  private/no-store headers, foreign-Host rejection and uncovered ticker behavior.
- Passed all 24 actual bodies through the frontend financial-data and panel
  validators. All were rejected by the normal public consumer.
- Added per-metric VERIFIED/PARTIALLY_VERIFIED/UNAVAILABLE grades with independent
  display/public eligibility. The UI exposes exact missing evidence without
  promoting an amount or source date.
- Verified small positive/negative amounts render as a threshold when otherwise
  rounded to zero; true zero remains zero. Fractions, multiples and reported EPS
  retain their units. Frontend tests and typecheck/build cover the changed code.
- Confirmed explicit annual/quarterly/TTM labels and existing original-quarter
  statement behavior. No missing values, periods, source scope or publication
  timezone are filled.

The 591f665 browser evidence was synthetic and belongs to that earlier checkpoint.
It does not establish visual acceptance for these real data changes. Responsive
table regions and chart containers are preserved in source, but this continuation
does not claim a new desktop, narrow-pane or mobile browser pass.

## SStock alignment

Woofi retains the observed issuer context, financial task navigation, shared
period/unit controls, amount/ratio distinction, source disclosures and dense
tables. Data availability takes precedence over parity: specialized bank and
securities charts, vendor scores, valuation history and industry totals are not
populated without matching evidence. Source code, branding and proprietary
datasets are not copied.

## Runtime failure and safe operator verification

The recorded failure was tool automatic approval rejecting CreateProcess with
“blocked by policy” for the isolated Next preview restart on 127.0.0.1:3547 with
BACKEND_URL pointing to unused 8546. This occurred before application startup;
there is no application stack trace that explains the policy decision.
The prior preview had been stopped before the normal production build.

Read-only inspection now found existing 3430/3431/8430/8431/8432 loopback listeners
and no 3546/3547/8546 listener. It does not certify their commit or health.
No process was stopped/replaced and no automatic restart, port substitution or
alternate launcher was attempted. See
[inspection receipt](validation/RUNTIME_INSPECTION.json).

The following is an operator procedure after normal policy approval, not an
automated workaround:

1. Review this branch and the source/bundle manifest. Confirm this worktree is
   feature/financial-data-intelligence and production remains untouched.
2. Confirm the intended development services and their owning terminals. Do not
   stop unrelated listeners. If 3431/8432 cannot be made available in an approved
   development maintenance window, leave acceptance PENDING.
3. In that window, stop only the intended development instances using their own
   terminals. Keep existing core 8431 and production 3430/8430 unchanged.
4. From this worktree, use the already-supported saved-research launcher with the
   prepared private bundle. It binds literal loopback, disables proxy-header
   authorization and uses a transient database:

~~~powershell
uv run python -m scripts.serve_personal_financials .local/activation-captures
~~~

5. In the frontend directory, use the supported loopback custom server after
   building. Do not replace it with an unrestricted Next server for private data:

~~~powershell
$env:APP_ENV='development'
$env:BACKEND_URL='http://127.0.0.1:8431'
$env:WOOFI_PERSONAL_RESEARCH='1'
$env:WOOFI_PERSONAL_BACKEND='http://127.0.0.1:8432'
npm run start:personal
~~~

6. In the permitted integrated browser, inspect /stocks/FPT#stock-fundamentals,
   TCB, VCB and SSI; switch annual/quarterly/TTM and amount units. Inspect the new
   verification disclosure, source dates, cash-flow gaps and bank amount histories.
   Confirm ratios/peers remain unavailable, no fake values, and both languages/themes.
7. Inspect desktop and narrow widths, horizontal table scroll, chart labels,
   error/empty states and negative/zero formatting. Compare one visible amount
   against its pinned source record and record screenshot/source/period evidence.
8. Mark runtime/browser acceptance PASS only after those actual checks. If an
   approval denial recurs, retain PENDING and its exact reason; do not bypass it.

Offline reproducibility commands are in
[the runbook](../docs/FINANCIAL_DATA_INTELLIGENCE_V1.md). Passing them does not
complete the operator/browser steps.
