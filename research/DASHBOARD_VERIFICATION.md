# Dashboard verification — free real data, 21 October 2026

Current V3 results supersede the checkpoint below: **175 verified observations,
64 supported definitions, and 15 qualified TCB/VCB peer metrics**. See
[V3 delivery](FINANCIAL_INTELLIGENCE_V3_DELIVERY.md),
[current comparison](SSTOCK_FEATURE_COMPARISON_V3.md), and
[current manual acceptance](DASHBOARD_VERIFICATION_V3.md). Runtime remains PENDING.

## Prior bdc70ad checkpoint record

**Offline API/contracts/rendering PASS. Current-code runtime, browser and mobile
visual acceptance PENDING.** No process was launched or restarted in this mission.
The SStock catalogue is reused as the product benchmark, without proprietary
code/branding or a WiData requirement.

| Product area | Real data now usable | Correct limits |
|---|---|---|
| Financial overview / revenue / profit | HPG 2024–25 original annual revenue/PAT/parent PAT; TCB bank income/PAT; original provider histories; VHM partial profit | CafeF gross sales is not net revenue; missing series do not become zero |
| Growth | HPG annual revenue/PAT/parent PAT/margin change; TCB income/PAT/loans/deposits growth | No unknown-scope VCI cross-period promotion; HPG Q4 and later audited revisions not mixed |
| Balance / statements | HPG 2025, TCB 2024–25 original scoped rows; original provider statement tables; VHM four annual periods | HPG opening 01/01/2025 is not relabelled 31/12/2024; original source labels/columns retained |
| Cash-flow panel | HPG and TCB original operating/investing/financing cash flows; HPG FCF/conversion; existing provider amounts | Financing is not net change. FX-aware endpoint checks pass; source signs retained |
| Profitability panel | HPG annual gross/net margins; TCB 2025 average-balance ROE/ROA | HPG average-balance returns/turnover still lack qualified prior closing balances |
| Liquidity / leverage panel | HPG 2025 current, quick, debt/equity, working capital and liability/asset ratios | Banking does not receive industrial current/quick ratios or fabricated generic metrics |
| Bank funding panel | TCB loans/deposits/accounting ratio and growth; original VCB reported amounts | Accounting loans/deposits is not regulatory LDR. CASA/NIM/NPL etc stay unsupported |
| Industry / peer tables | 61 categories, eight with saved issuer observations; 406 actual SSI pairs; coverage/source/quality per metric | No actual compatible two-company ranks, sector sums or classification history |
| Dividends | Three official FPT cash notices, source links, record/payment and notice dates | Incomplete coverage, no ex-date or yield inferred; payment date is not proof of payment |
| Valuation | Existing information architecture and unavailable indicators | No P/E/P/B history without matched prices/shares/equity and source vintages |

## Executed validation

- 54 actual stock API projections: preferred and original-provider selections,
  nine issuers, annual/quarterly/TTM. Source ownership, hashes, units/basis, exact
  projection values, private/no-store boundaries and foreign Host rejection pass.
- All 54 bodies pass frontend financial/panel contracts and are rejected by the
  normal public consumer. Independent original-report margin, FCF, liquidity,
  debt/equity and loan/deposit arithmetic checks pass.
- All 61 industry responses pass coverage/missing counts; unqualified observations
  have null rank/percentile; historical totals remain null. Both languages render
  the actual tables with source and period, without nonfinite financial values.
- Nine real dividend API bodies pass private boundaries and existing action-model
  server rendering in English/Vietnamese. FPT has three notices; eight others show
  incomplete empty coverage. Public consumers render none of the private records.
- Units, signed cash values, fraction percentages, multiples, tiny values and true
  zero retain existing regression coverage. TCB EPS is VND/share, not scaled by
  the million-VND statement heading. No missing period or amount is filled.
- Frontend regressions: 328 pass, one existing skip. Typecheck and webpack build
  pass. Exact backend results are in validation/free-data-v2/TEST_RESULTS.json.

Evidence: [ASGI validation](validation/free-data-v2/FREE_DATA_APPLICATION_VALIDATION.json),
[preferred frontend](validation/free-data-v2/preferred/REAL_DATA_FRONTEND_VALIDATION.json),
[provider frontend](validation/free-data-v2/provider/REAL_DATA_FRONTEND_VALIDATION.json),
[industry/dividend renders](validation/free-data-v2/FREE_DATA_FRONTEND_VALIDATION.json).
These are in-process and static rendering checks, not browser screenshots or a
running-preview acceptance claim. The earlier 591f665 synthetic browser evidence
belongs to that checkpoint. No new desktop or mobile visual pass is claimed.

## Exact runtime failure and inspection

The previous automatic approval rejection was **“CreateProcess rejected: blocked
by policy”** for the isolated Next preview restart on 127.0.0.1:3547 with BACKEND_URL
pointing to unused 8546. It happened before application startup; no application
stack trace or more-specific policy explanation was supplied. This mission made
no new launch attempt, alternative-port substitution or launcher workaround.

Read-only Get-NetTCPConnection was available and returned zero listeners on the
eight inspected ports at 2026-10-21T03:31:43Z. This replaces the old checkpoint's
listener snapshot, not its policy decision. See
[inspection receipt](validation/free-data-v2/RUNTIME_INSPECTION.json).

## Safe manual acceptance, after normal operator/policy approval

1. Confirm this worktree is feature/financial-data-intelligence. Review the bundle
   index at .local/free-data-v2-final/index.json and its original/report source
   choices. Source documents, HTML bodies and actual amounts remain private.
2. Inspect ports/process ownership in the approved development window. Do not
   stop production or unrelated services. If intended development ports are
   unavailable or startup is still denied, keep runtime PENDING.
3. In the existing supported terminal/launch procedure, start only the intended
   saved-data backend from this worktree (literal loopback, proxy headers disabled,
   transient research DB):

~~~powershell
uv run python -m scripts.serve_personal_financials .local/free-data-v2-final
~~~

4. Supply an approved core development backend on 8431 if the surrounding shell
   needs one; do not repoint production or infer that it is currently running.
   In frontend, after its successful build, use the supported custom local server:

~~~powershell
$env:APP_ENV='development'
$env:BACKEND_URL='http://127.0.0.1:8431'
$env:WOOFI_PERSONAL_RESEARCH='1'
$env:WOOFI_PERSONAL_BACKEND='http://127.0.0.1:8432'
npm run start:personal
~~~

5. Open the approved integrated browser at http://127.0.0.1:3431. On
   /stocks/HPG#stock-fundamentals select annual/preferred: confirm original issuer
   source, 2024–25 profit/margins/cash flow, 2025 liquidity and precise unknown
   fields. Switch evidence to provider: confirm original eight-year history.
   Switch quarterly/TTM: confirm provider history and no unknown-scope flow sums.
6. Inspect TCB annual: original million-VND scaling, EPS VND/share, ROE/ROA,
   loans/deposits/growth and actual financing row. Inspect VHM: four annual periods,
   partial unit/scope labels and absent unsupported net revenue/ratios. Inspect
   FPT/VCB/SSI existing amounts without fabricated specialist ratios.
7. At /industries select banks (8355), securities (8777), real estate (8633) and
   manufacturing (1757). Confirm observation date, metric coverage, missing issuer
   lists, company links, source/scope/quality, no qualified ranks without two
   compatible issuers, and no historical membership date or sector totals.
8. On FPT's dividends/actions view check the three source links, cash per share,
   exact record/payment dates and unknown ex-dates. Another sampled issuer must
   show incomplete coverage rather than a claim that no dividends occurred.
9. Check both languages/themes, desktop and narrow/mobile widths, shared unit and
   period selectors, horizontal tables, chart labels, source details, negative/
   tiny/zero formatting and distinct error/empty states. Compare source cells
   against the pinned original PDF/HTML and record screenshots/period/source.
10. Only after these actual checks mark browser/runtime PASS. A further approval
    denial must retain its exact reason and PENDING status; do not bypass it.

Offline reproduction is in [the runbook](../docs/FINANCIAL_DATA_INTELLIGENCE_V1.md).
