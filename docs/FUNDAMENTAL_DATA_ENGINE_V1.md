# Fundamental Data Engine V1

Local implementation on `codex/woofi-fundamental-analysis-v1`, continuing from
`2ca3f74f42917cd3cf6bd4d18b3e76e3d98651c2` in the existing checkout.
No runtime cutover, push, deployment or preview execution.

## Product result

The existing Fundamental Analysis workspace now reads a structured Python engine
instead of the four-column annual income summary. Its financial overview, business
performance, financial statements and ratios sections remain within the unchanged
five Stock Detail tabs. The existing unit/period controls, responsive tables,
Recharts series selection, themes and VI/EN product chrome are reused.

Annual, quarterly and trailing twelve-month views expose actual source coverage.
Income, balance-sheet and cash-flow tables retain source field codes, EN/VI labels,
period basis and real zeros. Conflicted fields show unavailable values with an
inspectable, explicitly unqualified raw amount and original source labels.
Overview shows ordinary revenue or qualified bank operating income, total PAT,
equity, ROE and ROA. Performance retains parent-shareholder PAT separately. Ratios
and cash-flow tables render calculated backend results; the frontend only formats
units, selects already-loaded periods/series and validates ownership.

Source disclosures include actual acquisition timestamps, source URLs, content
hashes, source publication strings, missing-input reasons, calculation formulas
and input evidence. Annual/quarterly reconciliation differences remain visible;
neither source series overwrites the other and no cause is inferred.

## VCI audit and normalized boundary

Installed vnstock **4.0.2** was inspected directly. Its VCI Finance adapter supplies
the public session/headers and issuer company type. The existing SDK transport is
reused for these exact endpoints, preserving normal TLS verification:

- `/v1/company/{ticker}/financial-statement/metrics`
- `/v1/company/{ticker}/financial-statement?section=INCOME_STATEMENT`
- the same endpoint with `BALANCE_SHEET` and `CASH_FLOW`

The raw report envelope contains both `years` and `quarters`, sorted oldest first.
The SDK's legacy DataFrame path takes four periods before projection and can fill
missing values with zero. The new reader retains the raw envelope, filters fields
against applicable metadata, sorts normalized periods, and only then selects the
requested latest periods. Existing legacy financial APIs are unchanged.

One process packet cache is shared across frequencies and statement endpoints
(hour buckets, maximum 128 issuer entries). Cache misses are serialized to prevent
duplicate packet reads. Each miss makes one metadata GET and at most three report
GETs, with at most three concurrent report reads and 15-second transport timeouts.
There is no immediate report retry loop. Partial report failures are isolated and
cached; all-report failure returns HTTP 502 rather than a successful empty archive.
The existing SDK constructor additionally performs its bounded public handshake
and issuer-listing lookup. No financial collector, database persistence or scheduler
was added. Cold reads can exceed the frontend's 20-second deadline when the source
is slow; the user may retry against the completed process cache. No background
automatic polling or forced-refresh endpoint was introduced.

Metadata qualification is required, because bank raw envelopes contain padded zeros
for generic company fields. Positive bank company type plus its operating-income
metadata selects bank treatment. The SDK's CT fallback alone is insufficient:
ordinary treatment also requires qualified net-sales/gross-profit metadata.
Securities/insurance and unknown profiles withhold generic revenue/liquidity metrics.
No ticker-specific rules or invented sector master were added.

Observed source anomalies:

- VCB has metadata grouping headers without numerical codes. These are not values.
- VCB repeats `bsb158` with two incompatible labels. Both labels and the raw amount
  remain inspectable; the qualified value is withheld.
- VCB `cfa34` is labelled net cash increase/decrease but grouped under financing.
  It is withheld from cash-financing calculations. `cfa35` is absent from applicable
  bank metadata; raw padding does not qualify it.
- Quarterly income and cash-flow amounts are standalone in the audited contract.
  For 2024–2025, annual comparisons and cash roll-forward confirmed this convention.
  Some earlier source annual/quarter versions differ. No inferred restatement cause
  or silent annual replacement is introduced.

Owner, period collection, duplicates, currency, amount units, finite values and
consolidation values are validated. Non-VND/unit changes fail closed. Report limits
are bounded to 160 annual and 160 quarterly source records and 20 response periods.
VND monetary amounts remain VND; basic/diluted EPS statement rows remain VND/share.
Unknown source publication timezones and consolidation remain unknown. Current
source revisions are not historical point-in-time vintages.

## Python calculation contract

All rates are fractions, formatted as percentages by the UI. Multiples remain
dimensionless and are shown with ×. Missing inputs remain null; zero is preserved.
Every derived output carries its formula, original codes/periods/values, statement
content hash and a reason when withheld.

| Metric | Inputs / rule |
| --- | --- |
| Revenue / total PAT / parent PAT | Qualified `isa3` / `isa20` / `isa22`; never interchangeable |
| Bank operating income | Qualified bank `isb38`, never relabelled ordinary revenue |
| Gross / net margin | Gross profit or total PAT / positive net revenue; ordinary issuers only |
| ROE / ROA | Total PAT / mean current and prior total equity/assets; group numerator and denominator |
| Annual ROE / ROA | Prior year-end and current year-end balances |
| Quarterly ROE / ROA | Previous quarter-end and current quarter-end; not annualized |
| TTM ROE / ROA | Four contiguous qualified quarterly PATs / mean current and year-earlier balances |
| YoY / QoQ | Exact comparable year/quarter; percentage requires a positive prior value |
| Absolute changes | Exact comparable prior-year subtraction; negative/zero prior values remain valid |
| Total debt / debt-equity | Nonnegative short + long borrowings; positive equity; ordinary issuers only |
| Liabilities/assets | Reported total liabilities / positive assets; not bank borrowings |
| Current / quick ratios | Current assets / positive current liabilities; quick excludes inventories; ordinary only |
| Cash conversion | Operating cash flow / positive total PAT; ordinary only |
| Capex / free cash flow | Verified nonpositive purchase outflow; FCF = CFO minus positive capex outflow; ordinary only |
| Balance residual | Assets minus liabilities minus total equity; inspectable diagnostic |

Explicit YTD flows are differenced only against a compatible previous same-year
YTD report; Q1 needs no subtraction. Unknown basis or missing prior YTD withholds
the flow. EPS is never summed or differenced. TTM sums only four contiguous,
compatible, qualified quarter flows; balances remain period-end values. TTM statement
tables show original quarterly reports with a clear label, not invented TTM filings.
Incompatible consolidation/source/currency cannot create a ratio or growth result.
Matching unknown consolidation is disclosed and does not certify reporting basis.

P/E, P/B, valuation, NIM, NPL, CASA and causal/forecast/recommendation narratives are
not estimated from unavailable inputs.

## HTTP contracts

Both read existing cached Security/Stock identity using SELECT only. They do not
onboard stocks, initialize the product DB, acquire SSI or run ingestion.

- `GET /stocks/{ticker}/financials?frequency=annual|quarterly|ttm&limit=8` returns
  observations, chart gap placeholders, deterministic changes/calculations,
  original statement rows, receipts, capabilities and limitations.
- `GET /stocks/{ticker}/financials/statements/{income|balance|cash}` accepts
  `frequency=annual|quarterly` and `limit=1..20`, returning the original qualified
  statement and receipt from the same cached packet. It does not manufacture TTM
  statements.

Unknown/inactive cached equities return 404; unsupported parameters return 422;
unconfigured structured providers return 503; invalid/all-failed source packets
return a safe 502 without exposing headers, cookies or raw exceptions.

## Acceptance evidence — 2026-10-13

LIVE_VCI_FINANCIAL_READ: the completed new provider path was read once for FPT,
PNJ and VCB. All nine issuer/statement reads were healthy; each statement returned
8 annual and 34 quarterly observations. Latest annual was **2025**, latest quarter
**2026-Q2** for all three. Acquisition timestamps were approximately
16:37:40–16:37:45 UTC (23:37:40–23:37:45 Vietnam). These are statement-read times,
not publication times or market-quote freshness.

Artifacts remain outside Git in
`C:/Users/PC/.codex/tmp/woofi-fundamental-engine-v1-20261013/`:
original FPT/PNJ/VCB raw audit captures, nine `*-engine.json` responses and
`engine-live-validation.json`. Public financial evidence only; no credentials.
REPLAY_OF_LIVE_VCI_RESPONSE: all nine annual/quarterly/TTM saved responses passed
the frontend ownership/value/statement/chart contract. API TestClient replay uses
isolated in-memory SQLite identity only and is separately labelled from live reads.
No existing product database was copied or changed for this engine task.

AUTOMATED_VALIDATION: full backend regression passed **1,008 tests** before the
last narrow API/finite-result corrections. Final relevant backend regression passed
**61 tests**, covering all changed backend seams and existing history/analytics/
stock/provider contracts. Final frontend suite passed **140 tests**; typecheck and
optimized Next.js production build passed. API replay passed all nine research
and nine statement requests using 36 SELECTs and no mutations; all nine replay
responses also passed the frontend engine contract. Backend
fixtures cover formulas, group-vs-parent ownership, YTD/TTM, gaps, negative/zero
bases, incompatible consolidation, metadata conflict isolation, receipt/cache
failure and SELECT-only HTTP reads. Frontend tests cover source-unit tables,
fixture labels, bank exclusions, EN/VI, four retained sections, frequency controls,
missing states and chart ownership. Full backend regression, frontend suite,
typecheck and optimized production build passed; final targeted regression covers
the subsequent narrow correctness adjustments, including nonfinite-result guards.

REVIEW: one focused review of the normalization → calculation → HTTP → UI path.
Conflicting metadata, bank padding, per-share units, unknown publication basis,
TTM eligibility, comparable period ownership, empty vs source failure, bounded
reads, existing API compatibility and five-tab preservation were checked.

BROWSER_ACCEPTANCE: **NOT_VERIFIED**.
BLOCKER: **PREVIEW_EXECUTION_DENIED_BY_POLICY**, carried from the prior checkpoint.
No denied command was retried and no alternate preview port/launcher/server was
started. SSR and build evidence do not establish rendered-browser acceptance.
No new screenshot, tooltip, mobile interaction or physical theme-switch claim.

CHECKPOINT: one local commit containing this report; exact SHA in the handoff.
NEXT_SAFE_ACTION: separately authorized browser verification in a permitted
environment, then review for integration. Do not push/deploy automatically.

Canonical runtime, product DB, credentials, collectors, source cooldowns, FPT
automation, Technical EOD policy and Downloads WIP remain untouched.
The pre-existing untracked frontend AGENTS.md/CLAUDE.md files are preserved outside
the implementation commit; tracked/index cleanliness does not claim their removal.
