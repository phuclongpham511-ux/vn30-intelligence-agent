# Financial Source-of-Truth V5

Base: `3c0eac43b5aea4412d405d973990555e3041e487`. Development only, 2026-10-20.
**Independent official-source pipeline: PASS within saved-text/internal scope.**
**Public activation: DISABLED. Browser acceptance: PENDING.** No production,
server, database, acquisition worker, SSI/VCI API, push, merge or deployment change.
This is a concrete real-data increment, not another VCI qualification audit.

## Official source and verified fields

Selected source: PNJ Annual Report 2024, containing its consolidated financial
statements and 2023 comparative columns. Official issuer
[annual-report index](https://www.pnj.com.vn/quan-he-co-dong/bao-cao-thuong-nien/)
lists publication on **16 April 2025** and links the
[original document](https://cdn.pnj.io/images/quan-he-co-dong/2025/20250416-PNJ-Bao-cao-thuong-nien-2024-vi.pdf).
This is PNJ, not FPT, and not a third-party financial aggregator.

| Canonical field | Original statement code | 2024 raw / normalized VND | 2023 comparative VND | PDF page / printed page |
| --- | --- | ---: | ---: | --- |
| Net revenue | 10 | 37,822,837,171,385 | 33,136,929,196,429 | 98 / 195 |
| Profit after tax, total | 60 | 2,112,916,282,946 | 1,971,099,177,135 | 98 / 195 |
| Total assets | 270 | 17,207,730,777,685 | 14,427,558,015,356 | 97 / 193 |
| Total liabilities | 300 | 5,952,424,147,163 | 4,621,377,351,380 | 98 / 194 |
| Total equity | 400 | 11,255,306,630,522 | 9,806,180,663,976 | 98 / 194 |

Original monetary tokens use dot grouping; normalized VND uses **multiplier 1**.
The capture preserves original Vietnamese labels, codes, exact grouped tokens,
page numbers, headers, source/discovery URLs and extraction receipt hashes.
Company/ticker/exchange: original PDF page 35. Basis and audited statement context:
page 96. Calendar fiscal year (1 January–31 December): note 2.2, PDF page 100.
Both annual statement columns explicitly state VND. Approval/audit date 24 March
2025 is distinct from index publication 16 April 2025 and receipt assembly time.
The 2023 column is a comparative in the 2024 filing, not the originally published
2023 vintage. No latest-quarter or current-freshness claim.

Two exact identities PASS:

- 2024 assets − liabilities − equity = **0 VND**.
- 2023 assets − liabilities − equity = **0 VND**.

**Evidence limitation:** the web reader extracted the official PDF page text;
the original binary was not downloaded or hash-verified. Its `document_sha256`
is explicitly null. The extraction digest authenticates the saved tool response,
not the PDF. No pixel-level/visual PDF verification or OCR confidence is invented.
Confidence is `text_and_arithmetic_verified_not_visual`. Earlier FPT/PNJ PDF
attempts encountered 403/404/size/reader limitations; none was bypassed. The selected
PNJ annual report was independently readable through the normal public web reader.

## Reusable canonical path

`FilingEvidence` / `FilingField` in `src/providers/financial_filings.py` accept an
explicitly reviewed manifest and saved extraction, without network access.
The provider-independent input describes issuer, source, source document,
currency/scale, fiscal boundaries, basis, source columns and original field rows.
It feeds the existing `FinancialPacket`, `StatementObservation`,
`FinancialSourceContext`, `FinancialLine` and `StatementReceipt` models.
No parallel calculation engine or database schema.

The boundary validates HTTPS evidence URLs, timezone-bearing receipt time,
extraction hash, original issuer/exchange/basis/header/period quotes, exact year
column order and whole monetary tokens. Original values must occupy the source
row's trailing columns; substrings and note/code numbers cannot substitute.
Only reviewed currency/scales are supported. Amounts outside safe numeric range,
unqualified generic bank revenue and contradictory balance identities fail closed.
An exact duplicate is recorded once, never summed; conflicting duplicate mappings
or values reject the import. Missing fields remain missing.

Initial supported slice: annual calendar-year reports and five explicitly
reviewed monetary fields. Unsupported fiscal calendars, quarterly/YTD flows,
unreviewed extraction layouts and other fields need their own contracts; they
are not guessed. The sample ticker appears only in external evidence, not in
application branching. Synthetic tests exercise several ticker names.

The existing Python financial engine then calculates its supported projections.
Latest internal summary has five reported fields plus five existing derived
metrics (two YoY rates, net margin, ROE and ROA). Derived values retain original
inputs and formulas; they are not extra issuer-reported observations. P/E/P/B,
EPS, debt/equity, cash flow and unsupported items remain unavailable. Nothing is
filled from VCI or a different filing.

## Reconciliation with saved VCI

The existing saved PNJ VCI packet was normalized without provider calls. All
**10 same-label/year values MATCH exactly**. No numeric conflict observed.
VCI's original unit metadata and reporting basis remain unknown. Matching year
labels do not qualify missing fiscal boundaries: the comparator records
`LABEL_MATCH_BOUNDARIES_UNVERIFIED`. Normalized VND compatibility is separate
from original-unit evidence. No basis, provenance, publication date or rights are
transferred to VCI.

`reconcile_filing` preserves both packets and reports missing periods/values,
known basis conflicts, original-unit differences, numeric conflicts, distinct
receipt vintages and possible version differences. Same receipt hashes with
different values are an evidence contradiction. A changed number alone does not
establish a restatement. Import/CLI never overwrites previous evidence folders.

## Rights and public boundary

| Use | Decision |
| --- | --- |
| Internal research | Authorized by this task for the bounded saved-evidence investigation. This is not a provider license. |
| Local development display | Offline, explicitly scoped verification artifact only; not a user-facing live feed. |
| Public user display | No applicable source permission established; disabled. |
| Commercial redistribution | No applicable permission established; disabled. |

The issuer index has copyright notices and provides reports, but no financial-data
redistribution grant was established. Availability of the PDF and the owner's
lawful-use attestation are not converted into provider permission. Source contexts
retain `display_rights=unreviewed`, with no fabricated permission reference.
There is no new public/internal HTTP endpoint or runtime provider selection.

An explicit offline Python call may request `internal_research` scope with an
authorization reference, only for original-filing contexts verified by this
boundary. It cannot enable unreviewed VCI data or override `prohibited` rights.
The default display path retains public qualification requirements. An internal
response cannot be passed back through the public display projection without
error. The frontend's normal parser rejects internal responses; only the offline
renderer opts in. HTTP query parameters cannot select this scope. Existing
legacy raw-evidence contracts are unchanged; generated evidence JSON is local
research material and is not for public hosting.

## Concrete internal UI result

`scripts/validate_financial_filing.py` reads the manifest/extraction, produces
canonical, internal and default-public projections and a reconciliation JSON.
`frontend/scripts/render-reviewed-financial.mjs` uses the actual existing
`FundamentalOverview` and `FinancialStatementTable` components. There are no
financial calculations, fabricated facts, request hooks or state overrides in
the renderer. EN/VI each render all 10 original monetary observations; tables
show full VND amounts and consolidated annual column labels. The overview uses
the existing unit presentation, with an INTERNAL RESEARCH/public-disabled label.
Original field/page/provenance details remain expandable.

The artifacts reuse compiled application CSS. They are static HTML source
renders, not browser screenshots, an interactive route or deployment to 3431.
No Cloud Browser capability is available; no local browser was opened.

Evidence root (outside Git, not publicly served):
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/financial-source-truth-v5-20261020/`.
It retains the source reader receipts, reviewed manifest/extraction,
`acceptance/RESULTS.json`, canonical/scoped display JSON,
`acceptance-ui/reviewed-financial-en.html`, its VI counterpart and render
results, plus an isolated `frontend-build/`.

Reproduction (no network/DB; destination must be new):

```text
python -m scripts.validate_financial_filing MANIFEST EXTRACTION NEW_OUTPUT --saved-vci SAVED_PNJ_CAPTURE
node frontend/scripts/render-reviewed-financial.mjs NEW_OUTPUT/internal-display.json NEW_HTML_OUTPUT COMPILED_STATIC_STYLES
```

## Validation and scale feasibility

Final focused financial backend regression: **105 PASS**, including 41 filing
boundary cases. This is one final run, not a sum of earlier runs. Existing
Starlette/httpx warning remains.
Full frontend run: **317 PASS, 1 existing SKIP**. Typecheck PASS. Webpack production
build PASS in a separate artifact directory. Actual PNJ source-to-engine-to-UI
replay passes independently of synthetic tests, with two balance identities,
10 numeric VCI matches and EN/VI renders of 10 facts each.

Scale requires issuer/exchange filing discovery receipts, a document-version
registry and controlled review. This implementation does not add a crawler,
polling loop or automatic filing selector. Structured disclosures can map directly
to the same reviewed schema; PDFs need layout/column verification, and scanned
PDFs additionally need OCR/manual review. Changed documents retain new hashes
and vintages; compare and review rather than overwrite. Ambiguous basis, units,
periods, codes or arithmetic go to an exception queue, not a guessed repair.

No provider price quote, cost per company, update SLA or full-universe coverage
was established. Current work unit is one manually reviewed document, five fields
across two annual columns. Human review/rights effort dominates expansion; the
in-memory numerical projection is not an estimate of that effort. Banking and
other financial issuers need applicable line definitions, not industrial revenue.

Exact remaining gates: obtain applicable public display/redistribution terms;
retain/verify the binary and page images for stronger document assurance; add
reviewed manifests before increasing issuer/period/field scope; perform actual
Cloud Browser acceptance before claiming visual PASS. No further VCI investigation
is necessary to demonstrate this independent internal path.
