# V4 product acceptance

The supported private API and Next custom server start normally on literal
loopback 8432/3431. Real HTTP proxy/boundary checks pass. Actual Codex Integrated
Browser desktop checks pass for the bounded flows below. **Mobile visual
acceptance remains PENDING**: the exposed tab capabilities provide page assets
and WebMCP, with no viewport-resize/device-emulation control. No external browser
or alternative automation framework was used.

The historic exact error was `CreateProcess rejected: blocked by policy`, before
an earlier preview startup. V4's ordinary supported launches were accepted;
there was no new policy denial or policy override. The absent core market backend
8431 is a separate environment limitation. Stock identity, follow and quote facts
remain unavailable; authorized saved financials/dividends now work independently.

## Actual desktop checks

| Flow | Result / observed evidence |
|---|---|
| Stock Detail financial deep link | PASS — TCB/FPT/VNM load despite absent market identity; no fabricated company/quote fallback |
| Financial highlights | PASS — period, money units and separate accounting/source counts; FPT latest has 48 available/source/accounting-qualified metrics |
| Revenue, profit and growth | PASS — FPT dedicated destination, backend amounts/YoY and exact-prior-year table; source period labels preserved |
| Balance sheet | PASS — TCB destination and three-year component/table history; FPT original statement switching |
| Cash flow | PASS — TCB three-year signed operating/investing/financing chart and table; negative values retained |
| Profitability | PASS — TCB current ROE/ROA, earlier unqualified returns shown as dashes |
| Bank financial health | PASS — funding and credit charts, >100% coverage axis, 2023 note gaps and accounting definitions |
| Historical controls | PASS — two-period selection changes 2023–25 to 2024–25; quarterly switch restores original VCI source and partial-metadata disclosure |
| EPS / book value | PASS — FPT 2022–24 EPS and 2023–24 dated BVPS, ordinary capital/reserves, unscaled shares and unavailable P/E/P/B |
| Original source links | PASS — FPT 2022 links to 2023 report; 2023/2024 link to 2024 report; collection receipt uses issuer disclosure index |
| Dividends | PASS — financial shortcut selects existing action tab; three source-linked FPT notices, cash/share, record/payment dates and incomplete details |
| Company-to-peer navigation | PASS — TCB selects bank category 8355 and FY2025; two-company label, 2/22 coverage, median/range, 20 missing banks, no rank/percentile columns |
| Single-company specialist note | PASS — NPL metric shows TCB only, 1/22 coverage, zero comparable companies, no sample distribution |
| Partial and missing states | PASS for exercised cases — VNM four annual periods, source/accounting counts zero, unsupported quarterly/TTM disabled; missing peer members explicit; unknown saved ticker has a distinct coverage message and retry control |
| Loading | Observed — loading financial/industry states before real data; company-peer link absent until ticker/period load |
| Localization and theme | PASS for exercised VNM desktop view — Vietnamese/light and English/dark; original CafeF/SSI/issuer names preserved |
| Chart hover tooltips, exhaustive retries, interrupted requests | PENDING — not claimed from static rendering or ordinary chart display |
| Mobile / tablet visual layout and touch interactions | PENDING — no exposed viewport control; desktop screenshots are not mobile acceptance |
| Full Stock Detail market/identity/follow experience | PENDING — approved core backend 8431 absent |

Private screenshots are in `.local/v4-browser`; only their hashes and dimensions
are included in `validation/free-data-v4/V4_ACCEPTANCE.json`. No financial screenshot
or original statement table is committed. Actual browser checks are distinct from
the 144 EN/VI static view renders, which also include unavailable-section fallbacks.

## Reproduce the permitted runtime

Use the existing financial-data worktree and branch. Check port/process ownership
before starting anything; do not stop production or another worktree's service.
If normal startup is rejected, preserve the exact error, stop restart attempts,
and leave affected acceptance PENDING.

From the worktree root, with the pinned private bundle present:

~~~powershell
uv run python -m scripts.serve_personal_financials .local/free-data-v4-ready
~~~

From `frontend`, in a separate approved terminal after a successful build:

~~~powershell
$env:APP_ENV='development'
$env:BACKEND_URL='http://127.0.0.1:8431'
$env:WOOFI_PERSONAL_RESEARCH='1'
$env:WOOFI_PERSONAL_BACKEND='http://127.0.0.1:8432'
npm run start:personal
~~~

These are the existing launchers. They enforce loopback socket/Host boundaries,
private/no-store/noindex, the one canonical backend app and saved-source reads.
The private backend uses transient SQLite and blank SSI credentials. No collector,
provider subscription or production migration is needed. Supply an independently
approved core development backend on 8431 only if market/company context is wanted.

## Exact remaining manual acceptance

1. In the Codex Integrated Browser open
   `http://127.0.0.1:3431/stocks/FPT#stock-fundamentals`. Confirm three reviewed
   annual periods; source/accounting counts are separate from publication rights.
   Switch provider history and restore preferred original reports.
2. Open Revenue/Balance/Cash/Profitability/Health/Valuation/Statements/Sources.
   Hover each financial series: tooltip period/value/unit must match its observation
   table; hide/re-enable series; verify missing values do not connect to zero.
3. Check FPT book value and its ordinary-share inputs against original note pages
   190/191 in the 2024 PDF. Reported EPS can use different corporate-action bases.
   P/E/P/B/earnings yield and historical market valuations must remain absent.
4. Open TCB health and its industry link: FY2025 pair sample 2/22, missing 20,
   no all-industry rank/percentile. Select a TCB-only credit metric, then an empty
   metric. Verify coverage and that fewer than two compatible observations have
   no distribution. Confirm historical sector totals remain disabled.
5. Check HPG, MWG, VCB and SSI. MWG's pre-audit 2024 opening column must not become
   a fabricated prior closing balance; source dashes must not become invented zero.
   VNM is a partial four-year summary, with no fabricated net revenue or cash flow.
6. Check dividends for FPT and a ticker without saved notices; the latter means
   incomplete coverage, not proof that no dividend occurred.
7. Using only approved integrated-browser controls available to the operator,
   resize the pane to phone (~360/390 px) and tablet (~768 px) widths. Verify all
   stock tabs remain reachable, financial navigation wraps/scrolls, chart labels
   remain legible, tables scroll inside their region with sticky labels/periods,
   numeric columns remain aligned, and no body-level horizontal overflow appears.
   Record actual dimensions/screenshots; do not substitute desktop screenshots.
8. Repeat core flows in EN/VI and light/dark. Inspect actual keyboard focus,
   loading, unavailable frequency, missing company, service failure and retry
   completion. Do not disable source/Host/privacy guards to force an error test.
9. Verify default/public mode rejects private payloads; foreign Host requests to
   both running services must fail. Mark additional acceptance PASS only when
   the actual interaction has been observed.

## Completed static/contract reproduction

~~~powershell
uv run pytest -q
uv run python -m scripts.validate_free_data --captures .local/free-data-v4-ready --report research/validation/free-data-v4 --private .local/free-data-v4-api --probe-directory .local/free-source-probes
uv run python -m scripts.recover_financial_evidence --baseline .local/activation-captures --bundle .local/free-data-v4-ready --output research/validation/free-data-v4
uv run python -m scripts.validate_financial_v3 --bundle .local/free-data-v4-ready --private .local/free-data-v4-api --report research/validation/free-data-v4
Set-Location frontend
npm test
npm run typecheck
npm run build -- --webpack
node scripts/validate-financial-activation.mjs ../.local/free-data-v4-api/preferred ../research/validation/free-data-v4/preferred/REAL_DATA_FRONTEND_VALIDATION.json
node scripts/validate-financial-activation.mjs ../.local/free-data-v4-api/provider ../research/validation/free-data-v4/provider/REAL_DATA_FRONTEND_VALIDATION.json
node scripts/validate-free-financial-data.mjs ../.local/free-data-v4-api ../research/validation/free-data-v4/FREE_DATA_FRONTEND_VALIDATION.json
~~~

The existing V3 validator is reused against V4 inputs; its legacy output filename
does not turn its in-process checks into browser acceptance. Evidence recovery
regenerates the unchanged baseline CSV; `BASELINE_REFERENCE.json` pins the already
committed V3 copy to avoid committing a duplicate.
