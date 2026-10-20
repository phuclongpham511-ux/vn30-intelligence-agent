# Financial Data Intelligence V1

## Real-data activation continuation — 21 October 2026

From 591f665, the existing saved-data reader now supports its original raw captures
and canonical-financial-packet-v1 entries in the same hash-pinned index. Canonical
files are bounded to 32 MB and checked for mapped source amounts, labels, units,
ownership, original dates, flow basis, model, duplicates and prohibited provenance
promotion. Missing statements can remain missing without erasing other evidence.
Strict JSON validation rejects booleans and numeric strings as financial numbers.
Original canonical transport reconstruction is not claimed.

The additive financial-verification-v1 response field separates VERIFIED,
PARTIALLY_VERIFIED and UNAVAILABLE from display/public eligibility. Its per-metric
missing-evidence list is visible in Financial Analysis. It grants no data rights
and does not populate withheld values. Default/public behavior is unchanged.

Prepare a new private bundle without modifying the original capture directory:

~~~powershell
uv run python -m scripts.prepare_financial_activation --captures C:\private\original-captures --destination .local\activation-captures --packet .local\provider-validation\TCB-packet.json --packet .local\provider-validation\SSI-packet.json
uv run python -m scripts.validate_financial_activation --captures .local\activation-captures --report-dir research\validation --private-responses .local\activation-api
node frontend/scripts/validate-financial-activation.mjs .local/activation-api research/validation/REAL_DATA_FRONTEND_VALIDATION.json
~~~

The first command reuses captures already present; it does not fetch TCB or SSI.
An existing different bundle is rejected; use a new revision folder. Existing
normalized journal ingestion also accepts the new index through the shared reader.
Canonical/source bytes, original timestamps and hashes are retained; private
responses and source archives remain outside Git and static hosting.

scripts.review_industry_memberships rechecks a caller-pinned SSI archive, keeps
the full observed pair dataset privately, and emits a counts/provenance report.
Its distinct review contract cannot be loaded as IndustryTaxonomy. No effective
dates, classification version, hierarchy or financial model are inferred.

The measured private path has 25 distinct reported fields, 24 API/frontend
projections and 2,816 eligible observations. It has zero fully verified/public
metrics and no activated real industry cohort. Current-branch runtime/browser
validation remains PENDING; offline API transport is not a server restart.
See [activation report](../research/REAL_DATA_ACTIVATION_REPORT.md),
[dashboard/operator procedure](../research/DASHBOARD_VERIFICATION.md) and
[remaining blockers](../research/REMAINING_BLOCKERS.md).

## Original V1 implementation

This isolated increment adds normalized financial facts, an explicit offline
revision journal, compatible industry arithmetic and four additional financial
chart projections. It reuses the existing FinancialPacket and deterministic
engine. SSI prices and the pinned vnstock provider remain unchanged.

## Source and calculation boundaries

MetricObservation preserves ticker, metric, finite value, VND currency/unit,
fiscal labels and optional boundaries, report scope, source, publication/fetch
times, revision hash, formula version, metric kind and quality reasons/input
references. Unknown original dates and scope remain unknown. Source-reported,
derived, estimated and unavailable have distinct kinds; estimates require the
ESTIMATED status. No estimates are produced by this version.

The engine has 60 outputs (49 baseline plus 11 additions). Additions are net
working capital; average equity/assets/inventory; asset and inventory turnover;
accounting customer loan/deposit ratio; and YoY/QoQ loans/deposits growth. Turnover
is a period measure. Inventory COGS is independently defined as revenue minus
gross profit, with nonnegative COGS and positive average inventory required.
Bank loan/deposit comparison is not regulatory LDR. Existing YTD differencing,
contiguous TTM, source/scope compatibility, averaged balances and share-count
guards still apply. An additional normalized-fact gate rejects balance-dependent
values when assets minus liabilities minus equity exceeds
max(1 VND, abs(assets) * 1e-6). Original source evidence remains inspectable.

Public normalized values use the existing reviewed-evidence display gates.
The measured VCI sample produces zero qualified public financial metrics.
No original metadata, public permission or publication date is inferred from a
transport convention or successful provider response.

## Explicit offline ingestion

Run from the repository root, with an existing hash-pinned saved-capture index:

~~~powershell
uv sync --frozen
uv run python -m scripts.ingest_financial_intelligence --captures C:\private\approved-captures --journal .local\financial-metrics.sqlite --report .local\coverage-report
~~~

The capture folder must satisfy the existing personal-saved-captures-v1
index/hash contract. Optional repeatable --packet C:\private\canonical-packet.json
arguments accept canonical FinancialPacket captures, each at most 32 MB.
Inputs are validated before use; duplicate issuers in a run fail. There are no
live requests, credentials, scheduled worker or implicit application DB migration.
The CLI reports field-level raw coverage and most recent 20 periods per
annual/quarterly/TTM projection; eight annual periods exist in this measured sample.

Use a dedicated private SQLite file. The writer rejects unrelated database
tables. Identical refetches preserve the earliest capture and insert no duplicate
revision. An existing revision cannot be silently rewritten or backdated.
The revision digest includes quality, lineage and fiscal-boundary metadata as well
as calculation inputs. A gate change therefore creates a new normalized version.
Blocked values retain reported/derived lineage while their display value is null.
Different revisions with the same receipt time become CONFLICT on reads. Reads
with as_of require a timezone and exclude unknown publication times and any
publication/fetch after the cutoff. This conservatism does not establish
historical membership vintages or full point-in-time accuracy.

## Industry configuration and APIs

Industry reads are opt-in. Set these only for the isolated backend intended to
serve the explicitly reviewed evidence:

~~~powershell
$env:WOOFI_FINANCIAL_JOURNAL='C:\private\financial-metrics.sqlite'
$env:WOOFI_FINANCIAL_TAXONOMY='C:\private\reviewed-taxonomy.json'
~~~

The taxonomy is an IndustryTaxonomy JSON document with:

- contract "woofi-industry-taxonomy-v1", nonempty name, version and source reference;
- industry definitions: id, English/Vietnamese names, and one model from
  non_financial, bank, securities, insurance, real_estate;
- memberships: ticker, industry_id, inclusive effective_from/effective_to and
  source_reference. Duplicate definitions, unknown ids and overlapping membership
  periods for a ticker are rejected.

No real taxonomy is bundled or enabled. Do not turn the synthetic test/preview
classification into a production membership file. An empty unconfigured directory
is a deliberate unavailable state.

Read-only endpoints:

~~~text
GET /stocks/FPT/financials/metrics?frequency=annual&limit=8
GET /financial-intelligence/industries
GET /financial-intelligence/industries/manufacturing?period=2025&frequency=annual&membership_on=2025-12-31
GET /financial-intelligence/industries/banks?period=2025-Q4&frequency=quarterly&membership_on=2025-12-31&as_of=2026-03-01T00%3A00%3A00Z
~~~

The stock endpoint follows the existing packet/cache acquisition path. Industry
endpoints only read the selected taxonomy/journal and never fetch providers.
The frontend /industries page uses a read-only same-origin proxy, a 15-second
timeout and private/no-store responses.

Industry calculations require qualified, nonfixture facts with compatible issuer
model, VND unit, known fiscal boundaries and report scope. Each ratio uses the same
companies in numerator and denominator, with compatible per-issuer sources.
Multiple provider observations for one issuer/metric are excluded. Amounts sum;
ROE/ROA and margins divide matched sums, never average issuer ratios. Coverage and
excluded tickers are per metric. Different cohort fiscal intervals are rejected.

Rank 1 is the largest numerical value; ties use competition ranks. Percentile is
(number below + 0.5 * ties) / included company count. This is a sample position,
not investment merit. Contributions use observed additive totals only when
positive and finite. Nonfinite aggregates and derived results stay unavailable.
Industry P/E/P/B require a future matched capitalization/earnings or equity
cohort and remain unavailable. Securities/insurance have common-model guards;
unverified margin, trading, underwriting and actuarial fields are not fabricated.
Real estate uses the nonfinancial base, without project forecasts.

## Frontend and validation

Four new projections reuse FinancialAnalysisPanel: cash flow, profitability,
liquidity/leverage and bank funding. Multiple axes display ×, fractions display
percentages and amount units remain selectable. The industry page shows coverage,
peer rank/percentile/contributions, taxonomy version/date and method/source
disclosures. VI/EN and existing stock navigation remain intact.

For synthetic local UI validation, build/run with
NEXT_PUBLIC_WOOFI_VALIDATION=replay and direct BACKEND_URL at an unused isolated
port. /demo/financial-intelligence uses the actual components and visibly labelled
synthetic fixtures. Normal builds generate a not-found page for this route.
The standard app shell may attempt its existing refresh requests; never point a
fixture preview at a production backend.

~~~powershell
uv run pytest -q
Set-Location frontend
npm ci --no-audit --no-fund
npm test
npm run typecheck
npm run build -- --webpack
~~~

See [the delivery report](../research/FINAL_RESEARCH_REPORT.md), measured
[coverage](../research/DATA_COVERAGE_REPORT.md), and actual
[browser acceptance](../research/validation/BROWSER_ACCEPTANCE.md). Source tests,
synthetic rendering and saved PNJ text reconciliation do not establish complete
financial correctness, commercial data rights or public activation readiness.
