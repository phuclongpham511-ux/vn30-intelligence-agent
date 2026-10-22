# V5.7 follow-up: finish the cached VJC quarterly review

Date: 22 October 2026. Source baseline: `8ffb36f`. This is a bounded
continuation of the V5.7 pilot, following the owner's direction to improve
available free evidence without pursuing exhaustive coverage or paid data.
The original [pilot report](FINANCIAL_COLLECTOR_V5_7.md) remains its dated baseline.

## Completed slice

The previously downloaded [VietJet separate Q1 2025 financial statements](https://ir.vietjetair.com/File_Upload/financial-information/financial-reports/2025/Separate%20Q1.2025.pdf)
now have a reviewed private capture. No additional source requests were made.
The scan has no usable extracted text, so the selected rows were visually
transcribed from rendered pages and pinned to the original PDF and page hashes.
This is a selected-row review, not a review of every line or an audit opinion.

Seventeen reported amounts were retained: seven balance-sheet amounts on PDF
pages 4-6, three income amounts on page 7, and seven cash-flow/reconciliation
amounts on pages 8-9. Page 10 establishes issuer identity, calendar year and VND.
The balance identity, sum of operating/investing/financing cash flows and the
cash endpoint equation including the reported FX effect all have zero residual.

The evidence is **separate/standalone**, exclusively **2025-Q1**. Comparative
tokens stay inspectable but are not additional imported periods. The balance
opening column dated 1 January 2025 is not relabeled as an annual 2024 statement.
Provider and issuer histories remain independent; their periods are not spliced
to calculate growth or TTM. Missing capex, prior comparables and unsupported
metrics remain missing. Publication time and redistribution rights remain unknown.

## Small adapter extension

The existing `reviewed-report-v2` adapter now accepts optional `quarter`,
`flow_basis` and `period_quote` evidence on amounts. Quarterly flows must declare
`standalone` or `ytd`, with matching calendar boundaries and source date quotes.
A calendar-year first-quarter title plus its end date establishes the Q1 start;
other quarters require both start and end dates. Balances remain point-in-time.
Mixed flow bases within one statement/period are rejected.

No source-specific business branch, new numerical engine, HTTP route, financial
schema migration or frontend contract was introduced. Existing annual packet
identities are preserved by excluding absent new optional fields from metadata
hashes. A synthetic pre-change packet golden hash and the actual previously
reviewed HDB packet both retain their exact identities. YTD evidence remains
inspectable without being silently promoted to standalone-quarter calculations.

## Measured result

| Measure | Before follow-up | After follow-up |
|---|---:|---:|
| Immutable capture revisions | 32 | 33 |
| Statement-period observations | 1,446 | 1,449 |
| Selected statement-period observations | 1,446 | 1,449 |
| Metric revisions, including blocked/unavailable records | 84,487 | 84,564 |
| VJC observed quarters in each statement family | 4 | 5 |
| VN100 issuers with saved values | 26/100 | 26/100 |
| VN30 issuers with saved values | 23/30 | 23/30 |

The new capture contributes 17 source amounts and 77 normalized metric records;
these are different measures. Sixteen records are unqualified reported metrics;
the FX line is reconciliation evidence. Zero records are promoted to public
display qualification. VJC history now starts at 2025-Q1 and explicitly exposes
the missing 2025-Q2 interval. The union-of-sources coverage count does not certify
a continuous comparable history. Backlog priority totals remain unchanged.

A fresh consistent backup was created before the append. Every prior row in
all four journal tables remains byte-for-byte present, all 99 baseline source
file hashes match, SQLite integrity is `ok`, and there are no foreign-key errors.
A second offline run reuses all five cached sources and inserts zero captures,
observations or metric records. The restricted MSN source is not retried.

## Evidence and validation

Private artifacts are under `.local/financial-collector-v57/`:

- `vjc-quarter-review.json`, `vjc-quarter-packet.json`, `vjc-pages/`
- `before-vjc-quarter-review.sqlite`
- `coverage-before-vjc-review.json`, `coverage-after-vjc-review.json`
- `coverage-after-vjc-review-matrix.csv` (100 issuer rows)
- `vjc-quarter-review-audit.json`, immutable `runs/<run_id>/` records

Import run: `20261022T160737-d3752d8b`; repeat: `20261022T160804-11afcce6`.
PDF SHA-256: `26f340d97c97dc29eef66335772a4cd2bcce49d497b6c2e3f30a9f4aa3492f7b`.
The database, backups, raw documents and review manifests remain Git-ignored.
The two existing tooltip edits, generated frontend declaration, feasibility note
and owner-direction context changes were preserved unchanged during this slice.

Focused adapter/source/collector suite: **67 passed**. The actual imported packet
also passes annual, quarterly and TTM engine execution, private quarterly
projection, and existing public-display withholding checks.

Full backend regression: **1,674 tests and 32 subtests passed** in 311.46 seconds.
The only warning is the existing Starlette/httpx deprecation. Manual review of
the adapter, synthetic tests and this report against the bounded scope and
repository invariants found no outstanding issues. `git diff --check` passes.

The installed Woofi runtime has not been changed; it does not yet serve this
research journal. The validated follow-up is committed separately before V5.8;
nothing was pushed or merged into main.

## Next product boundary

This finishes the pending selected-row review without expanding acquisition.
The next useful slice is to inspect Woofi's existing attention and evidence
services, then choose one financial signal that can explain what changed, why it
deserves attention, its supporting evidence and the limits caused by missing
data. Numerical outputs must stay deterministic. Any later ML experiment needs
explicit comparable history and publication-vintage limits; an agent should
orchestrate existing tools rather than invent missing financial values.
