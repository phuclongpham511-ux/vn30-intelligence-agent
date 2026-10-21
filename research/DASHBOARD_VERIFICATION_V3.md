# V3 real dashboard acceptance

Offline ASGI/contracts/static rendering and regression/build checks PASS.
**Running Woofi, interactive charts, desktop and mobile visual acceptance:
PENDING.** SStock benchmark browsing does not validate Woofi's new code.

The previous tool approval rejection was **“CreateProcess rejected: blocked by
policy”**, before the isolated Next preview started on 127.0.0.1:3547 with unused
backend 8546. No more-specific reason or application stack trace was supplied.
No new restart/port substitution/alternative launcher was attempted. Read-only
inspection at 2026-10-21T04:34:20Z found zero listeners on the eight checked ports;
this does not lift the restriction. Existing supported launchers still enforce
literal loopback, the socket/Host boundary, private/no-store and no provider
acquisition. See [inspection](validation/free-data-v3/RUNTIME_INSPECTION.json).

## Exact manual procedure, only after normal operator/policy approval

1. Confirm the existing financial-data worktree and branch. Review
   `.local/free-data-v3-final/index.json` and selected HPG/TCB/VCB report manifests.
   Original `.local/activation-captures` and V2 bundles remain unchanged.
2. Inspect process/port ownership. Do not stop or repoint production or unrelated
   services. If the intended development window is unavailable or startup remains
   denied, retain PENDING and the exact reason.
3. Start the existing saved-data backend from this worktree using the supported
   approved terminal procedure; no persistent application DB or live provider:

~~~powershell
uv run python -m scripts.serve_personal_financials .local/free-data-v3-final
~~~

4. Supply an approved core development backend on 8431 if the surrounding app
   shell needs it. Do not assume an old service is running. From `frontend`, after
   building, use the existing supported private custom server:

~~~powershell
$env:APP_ENV='development'
$env:BACKEND_URL='http://127.0.0.1:8431'
$env:WOOFI_PERSONAL_RESEARCH='1'
$env:WOOFI_PERSONAL_BACKEND='http://127.0.0.1:8432'
npm run start:personal
~~~

5. In the approved integrated browser at `http://127.0.0.1:3431`, open
   `/stocks/TCB#stock-fundamentals`. Check financial highlights, overview revenue/
   bank-income charts, and dedicated balance, cash-flow, profitability and health
   destinations. Annual preferred uses the two-year original report; provider
   selection restores the original eight-year history without source splicing.
6. In TCB health, check demand deposits, classified-loan subtotal, NPL and matching
   allowance coverage against original PDF pages 167/168/174. Confirm the margin-
   lending exclusion and accounting CASA-style definition; no vendor CASA/NIM/CAR
   is claimed. Test tooltips, series toggles and percent formatting above 100%.
7. Open the company-specific industry link. It must select category 8355, inherit
   the requested FY2025 period, show two of 22 members, and show correct ranks,
   percentiles and covered medians/ranges for the 15 common metrics. Missing 20
   companies stay listed. Specialist TCB-only ratios must have no rank/median.
   No historical membership date or sector total is offered for the snapshot.
8. Inspect VCB annual balance, EPS VND/share, all three cash flows and 2025 ROE/ROA.
   Compare selected source cells and units with pinned PDF pages 8/9/11–14/18.
   Switch provider/quarterly/TTM: unqualified flow sums/ratios remain withheld.
9. Inspect HPG 2024–25 margins/FCF and 2025 liquidity; its earlier opening balance
   must not become a fabricated prior closing balance. Inspect FPT existing amount
   history and VHM's four annual periods, missing net revenue and partial metadata.
   Missing profitability/valuation groups must not create empty chart dashboards.
10. Use the dividend shortcut on FPT. Confirm three source-linked cash notices,
    record/payment/notice dates and absent inferred ex-dates/yield. Another issuer
    must show incomplete coverage rather than a conclusion of no dividends.
11. Check both languages/themes; desktop, narrow pane and phone-width layouts;
    navigation wrapping/scroll, sticky table labels, horizontal period scroll,
    metric definitions, chart units/tooltips, true zero/small/negative values and
    distinct loading/error/empty states. Record screenshots and source/period
    evidence, then verify default/public mode cannot read private responses.
12. Mark runtime/browser/mobile PASS only after these actual checks. Do not use
    static HTML/ASGI/build success as visual acceptance or bypass a new denial.

## Reproduce completed offline checks

From the worktree root, with the existing ignored private bundle:

~~~powershell
uv run pytest -q
uv run python -m scripts.validate_free_data --captures .local/free-data-v3-final --report research/validation/free-data-v3 --private .local/free-data-v3-api --probe-directory .local/free-source-probes
uv run python -m scripts.recover_financial_evidence --baseline .local/activation-captures --bundle .local/free-data-v3-final --output research/validation/free-data-v3
uv run python -m scripts.validate_financial_v3 --bundle .local/free-data-v3-final --private .local/free-data-v3-api --report research/validation/free-data-v3
Set-Location frontend
npm test
npm run typecheck
npm run build -- --webpack
node scripts/validate-financial-activation.mjs ../.local/free-data-v3-api/preferred ../research/validation/free-data-v3/preferred/REAL_DATA_FRONTEND_VALIDATION.json
node scripts/validate-financial-activation.mjs ../.local/free-data-v3-api/provider ../research/validation/free-data-v3/provider/REAL_DATA_FRONTEND_VALIDATION.json
node scripts/validate-free-financial-data.mjs ../.local/free-data-v3-api ../research/validation/free-data-v3/FREE_DATA_FRONTEND_VALIDATION.json
~~~

Source documents, body values and private API responses stay ignored. Committed
reports contain counts, evidence hashes and outcomes. The financial view rendering
matrix includes intentional unavailable-section fallbacks; it is not proof that
every issuer supports every financial module.
