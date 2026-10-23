# V5.8 financial insight foundation

Scope: the owner's V5.8 mission supplied 22 October 2026. Implementation baseline
is the separate V5.7 follow-up commit `5a88e5d`. No acquisition, training, LLM,
HTTP contract, Stock Detail, dashboard or runtime activation is included.

## Contract and agreed test seams

`financial_insights(packet, ..., authorization_reference=...)` produces a typed,
private structured response from the existing engine and personal projection.
`saved_financial_insights(journal_path, capture_id, ...)` in the existing personal
financial service reads an explicit immutable whole capture, read-only. These are
the public Python seams under test; no HTTP endpoint is added. Capture revisions
are selected explicitly, never combined or selected by lexicographic hash.

Each result carries ticker, metric, current/comparison periods and values,
absolute/percentage change, direction, attention criteria, input evidence,
missing information and comparison qualification. `percentage_change` is a
fraction, ratios are fractions, and absolute ratio changes are fraction differences
(0.05 means five percentage points). Original units/tokens remain in references.
No cause or recommendation is generated. A supported current fact remains visible
when a change cannot be established.

Only exact annual YoY, quarterly YoY and quarterly QoQ are supported. TTM insight
comparison is deferred. Same canonical definition/formula, source, known scope,
normalized unit/currency, reported line mapping, explicit calendar boundaries
and period basis are required. Quarterly flow comparisons require standalone
flows; raw YTD is rejected. Existing engine cross-document compatibility guards
remain in force. An incomplete, withheld, contradictory or incompatible pair
returns `INSUFFICIENT_COMPARABLE_DATA`, with null change values and explicit reasons.
Unknown scope never matches another unknown scope as evidence of comparability.

Source-publication timing and public rights remain independent missing evidence;
a private comparable result is not point-in-time certified or publicly licensed.
Original statement lines, dates, URLs, page/row references, document hashes,
receipt/record hashes and exact capture identity are preserved when available.

## Supported metrics and attention policy

Reuse engine amounts for revenue, operating income, net profit, operating cash,
assets, liabilities, equity, total debt, customer loans and deposits; engine
ratios for gross/net margin, debt/equity, liabilities/assets, accounting loan/
deposit ratio, accounting demand-deposit share, classified NPL and allowance
coverage. Ratio movements cover composition and specialist bank changes without
a new composition engine or guessed NIM definition.

Versioned policy `financial-attention-v1` is fixed before pilot evaluation:
absolute relative movement >=20% for amounts, >=0.05 fraction for ratios, >=0.25
for multiples, plus explicit sign reversals and movements away from zero.
Percentage changes require a strictly positive prior value; zero and negative
bases still permit compatible absolute changes, with the percentage limitation
disclosed. A threshold indicates attention-worthiness, not direction of value.

An unusual movement requires at least five earlier compatible exact-period
changes. Its absolute change must exceed the historical median absolute change
and be at least three times that median. Historical inputs and their references
are exposed; absent history gives a separate insufficient-history status.
Only periods earlier than the requested current period can enter that baseline.
No holdout cases or real-pilot fitting is permitted.

## Acceptance

Synthetic integration tests cover exact periods, gaps, definitions, scope, units,
basis, revisions, zero/negative bases, provenance, contradictory inputs, optional
unsupported claims, repeatability, historical anomaly criteria and unchanged
engine output. Real private SQLite pilots use FPT, TCB and the 17-line VJC capture;
provider captures explicitly demonstrate rejection of unknown reporting scope.
Private files/data and unrelated working changes must retain their hashes.
The full relevant backend regression and separate standards/spec diff reviews
precede the V5.8 commit. Nothing is pushed or merged. Visual acceptance remains
pending because this slice supplies no UI activation.
