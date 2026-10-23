# V5.8 evidence-based financial insight foundation

Delivery date: 23 October 2026. Branch: `feature/financial-data-intelligence`.
Implementation scope: [V5.8 spec](FINANCIAL_INSIGHTS_V5_8_SPEC.md).
The validated [17-line VJC follow-up](FINANCIAL_COLLECTOR_V5_7_VJC_FOLLOWUP.md)
is preserved in the separate commit `5a88e5d`.

## Delivered behavior

The private Python service answers what changed, why the movement meets an
explicit attention criterion, which input evidence supports it, and what remains
missing. It reuses `financial_engine`, `personal_projection`, `metric_unit`,
source compatibility and verification helpers. It adds no provider, financial
ratio engine, paid dependency, acquisition, scheduler or model.

`financial_insights` returns `FinancialInsightsResponse` (`financial-insights-v58`).
Each insight has ticker, metric/unit/formula, current/comparison period and value,
absolute and fractional percentage change, a bounded direction enum,
`attention_reason`, `evidence_references`, `missing_information`, comparison
qualification and independent verification dimensions. `causal_explanation` is
always null; arbitrary explanation/recommendation fields are rejected by the
strict result schema. No LLM narration adapter was justified for this foundation:
the structured facts, reasons and evidence already provide an inspectable result.

Exact annual YoY, quarterly YoY and quarterly QoQ comparisons require the same
canonical definition and source-line mapping, known matching scope, verified
normalized monetary units, explicit matching calendar basis and source revision.
Unknown scope does not match unknown scope. Original document compatibility
follows the existing engine guard; independently reviewed document vintages are
not automatically reconciled. A raw YTD flow is never compared as a standalone
quarter. No nearest-period fallback, filling gaps, source splicing or inferred
publication dates are used.

An incompatible/incomplete pair returns `INSUFFICIENT_COMPARABLE_DATA`, null
changes and explicit reasons. Each supported endpoint can remain visible as its
own private fact. Zero/negative comparison values allow absolute changes but
leave percentage changes null. Reported values and derived engine ratios keep
their formulas and original input references. Comparison qualification does not
upgrade publication rights, point-in-time certification or source verification.

## Attention method

`financial-attention-v1` uses fixed, inspectable criteria chosen before the pilot:

- Amounts: absolute relative change at least 20%, with a positive prior base.
- Fraction ratios: absolute change at least 0.05 (five percentage points).
- Multiples: absolute change at least 0.25.
- Sign reversals and nonzero movement away from a zero base are explicit cases.
- Historical unusualness: at least five earlier compatible exact-period changes;
  current absolute change exceeds their median absolute change and reaches three
  times that median. The baseline periods, changes and evidence links are exposed.

Inclusive thresholds tolerate only floating-point roundoff (`rel_tol=1e-12`,
zero absolute tolerance); engine values and reported changes are not rewritten.
Historical samples exclude the current and all later periods. Missing history
returns a separate insufficient-history status. These are attention heuristics,
not audited materiality standards, causal explanations or return predictions.
There is no real-pilot fitting or use of holdout cases.

Eighteen existing metrics are supported: revenue, operating income, net profit,
operating cash flow, total assets, liabilities, equity, total debt, gross margin,
net margin, debt/equity, liabilities/assets, customer loans, customer deposits,
accounting loan/deposit ratio, accounting demand-deposit share, classified NPL
ratio and classified-loan allowance coverage. The two deposit ratios retain their
existing accounting definitions, rather than claiming regulatory LDR/vendor CASA.
Unqualified NIM definitions and valuations are outside this slice.

## Private SQLite pilot

| Case | Results | Comparable | Insufficient |
|---|---:|---:|---:|
| FPT original history, FY2024 vs FY2023 | 6 | 6 | 0 |
| TCB original history, FY2025 vs FY2024 | 8 | 8 | 0 |
| VJC separate original, Q1/2025 vs Q1/2024 | 5 | 0 | 5 |
| FPT VCI quarterly YoY and QoQ, metadata incomplete | 2 | 0 | 2 |
| TCB VCI annual customer loans, metadata incomplete | 1 | 0 | 1 |
| Total | 22 | 14 | 8 |

The FPT profit/operating-cash movements and TCB customer-loan, accounting loan/
deposit and allowance-coverage movements meet the declared criteria. The private
JSON outputs preserve the actual values, arithmetic, document URLs, pages, source
rows, original tokens and statement codes. All **39/39 returned numerical
endpoints** link to their source observations through capture/packet/receipt/
record identities and URLs. This is link coverage, not a count of fully verified
or publicly licensed facts.

VJC retains the full original 17 lines in SQLite. Its five requested observations
are supported facts, with page references, but no compatible prior is present.
All five return `OBSERVATION_ONLY` and `INSUFFICIENT_COMPARABLE_DATA`. None is
assigned a trend or a materiality flag; the VCI packet is not used to fabricate a
comparison. Neither FPT nor TCB original history supplies five compatible earlier
changes, so historical unusualness remains unassessed in this real pilot. Its
positive/negative behavior is covered by synthetic tests.

## Integration and reproducibility

`saved_financial_insights` lives in the existing personal financial service.
The caller provides an explicit capture ID and nonempty private authorization
reference. It opens `MetricJournal(..., readonly=True)`, reads one immutable whole
packet, and annotates every reference with the exact capture and packet hashes.
It does not change selected revisions or synthesize a multi-capture history.
The authorization reference records caller intent at the existing internal seam;
it is not a new authentication system or public endpoint.

Example from the repo root with the existing virtual environment:

```python
from src.services.personal_financials import saved_financial_insights

result = saved_financial_insights(
    '.local/financial-research-v55/financial.sqlite',
    '2e00e4fefe6c73ffca6d608cb1bd626348d66e60f337df06d95667d91ad97e18',
    metrics=['revenue', 'net_profit'],
    authorization_reference='owner:private-financial-research',
)
print(result.model_dump_json(indent=2))
```

Private pilot outputs and `pilot-report.json` are under
`.local/financial-insights-v58/`. No private artifacts are committed.
All **389** pre-existing captured/private/protected files retain their hashes,
including SQLite, source PDFs, VJC page manifests and unrelated tooltip edits.
Storage remains schema 1, 33 captures, 1,449 selected statement observations and
84,564 metric revisions. No data was imported or migrated during V5.8.

## Validation and limits

Focused suite: **135 passed**, covering private insight seams, original reports,
quarterly evidence, collector and personal projections. Tests exercise exact
periods/gaps, scope/definition/unit/basis conflicts, revisions, nonpositive bases,
original provenance, independent accounting gates, access withholding, no causal
claims, repeatability, historical look-ahead exclusion and engine compatibility.

Full backend regression: **1,705 tests and 32 subtests passed** in 278.71 seconds.
The only warning is the existing Starlette/httpx deprecation. Full output and the
zero exit status are retained privately in `full-regression.log` and
`full-regression-exit.txt`. Both final review axes have zero outstanding findings.
HTTP routes, public API contracts, Stock Detail and frontend are unchanged.
No runtime was restarted or upgraded. Visual acceptance remains **PENDING**:
this service foundation has no activated UI flow. Quarterly comparisons are
demonstrated synthetically; the current real provider histories lack the metadata
needed for qualified comparisons. TTM comparisons, cross-vintage reconciliation,
learned thresholds, causal evidence linking and agent orchestration remain future
work. No investment recommendations are generated. No push or merge is performed.
Projection uses the existing engine's maximum window of 40 periods per frequency;
storage retains the full capture independently of that response window.

## Standards

One provenance finding was corrected: direct and SQLite-backed responses now use
the journal's canonical UTF-8 packet digest. A Vietnamese-text parity regression
was observed failing before the fix and passing afterward. Final independent
standards review: **0 remaining documented-standard findings; 0 smell findings**.

## Spec

Independent scope/spec review: **0 actionable findings**. It confirmed the exact
comparison guards, immutable revision choice, VJC observation-only behavior,
private integration and documented conservative limits. Final total: Standards
0 outstanding (one corrected provenance issue); Spec 0 outstanding.
