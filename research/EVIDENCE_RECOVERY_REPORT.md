# Financial evidence recovery V2

21 October 2026. Recovery starts from the original eight immutable captures,
not a new UI or a provider ratio import. The original 2,816 eligible observations
are traced individually in
[FIELD_LEVEL_EVIDENCE_MATRIX.csv](validation/free-data-v2/FIELD_LEVEL_EVIDENCE_MATRIX.csv).
The preferred nine-issuer views have a separate
[ACTIVATED_VIEW_EVIDENCE_MATRIX.csv](validation/free-data-v2/ACTIVATED_VIEW_EVIDENCE_MATRIX.csv).
Both contain lineage/metadata/statuses, not the private financial value dump.
They include actual per-input original units/currency and normalization
multiplier, fiscal start/end, original date strings, document/page digests and
review references. Unknown fields are explicit. Per-field EPS units override
the monetary statement heading.

## Field-level outcome

| Field | Original 2,816 presentations | Additional original-report evidence |
|---|---|---|
| Provider identity | Source, recorded version, source code/label, capture/receipt/record digests retained | Issuer URL, original binary digest, page text/image digests, review reference and row/column locators |
| Original value | Original capture bytes unchanged; canonical TCB/SSI line values/codes retained | Original numeric tokens, signs and selected source column retained before one explicit unit conversion |
| Unit | 2,816 inferred adapter transport conventions, no recovered original units | HPG VND ×1; TCB million VND ×1,000,000; TCB EPS VND/share ×1 |
| Currency | Original currency unknown throughout baseline | Explicit original VND wording |
| Scope | Unknown throughout baseline; not inferred from provider endpoint/company | Explicit consolidated titles for both reports |
| Fiscal boundaries | Year/quarter tags exist, explicit boundaries unknown | Explicit calendar fiscal year and original statement column dates |
| Flow basis | Adapter convention, not original disclosure | Original annual income/cash statement headings |
| Publication | Reported naive date strings, unqualified | Unknown qualified publication time. Document approval, URL date and current download time are not substitutes |
| Revision | Capture/record identities; full original transport absent for canonical TCB/SSI | Separate document/extraction revision identity; never replaces an original capture or historical journal row |

2,320 original presentations replay exact saved raw REST responses; 496 have
canonical source-line evidence only. There are 2,352 distinct source-metric
identities: quarter/TTM period-end balances account for repeated presentations.
No baseline unit/scope/date was repaired by copying another source's metadata.
Installed vnstock version 4.0.2 is not retroactively assigned to older captures
whose recorded version was unknown.

## Original documents recovered

HPG's official Q4/2025 consolidated PDF returned 200, 7,135,524 bytes, 33 pages,
SHA-256 `e6689e18fc46f8eac61ee76e24d582923cecd66654c0d7b4324d7325ac5684e3`.
Source pages 2–9 and 11 were visually inspected, including the rotated income
page. Selected transcriptions retain exact row/column quotes and page-image
hashes. The 2025 opening balance header says **01/01/2025**; it is preserved and
is not relabelled 31/12/2024. Only the qualified 2025 closing balance enters the
engine. Annual income/cash comparatives support 2024–25. Two explicitly reported
FX reconciliation cells complete the cash endpoint equations. The filing is a
Q4 pre-audit vintage; later audited provider figures remain separate.

TCB's official annual report returned 200, 31,023,262 bytes, 197 PDF spread pages,
SHA-256 `4369e240b46d42c99c2541f9c25a7497ed22e60e17dd9fb9158429596bf01d39`.
Native text and visually reviewed pages 149–153 support selected 2024–25
consolidated statement rows, units and annual boundaries. Gross customer loans
are distinguished from loans net of provisions. Reported EPS keeps its separate
per-share scale. Report approval on 16 March 2026 is not a publication timestamp.

Original PDFs, PNGs, HTML bodies, exact financial values and manifests stay in
ignored private folders. The committed matrices retain reviewable hashes and
metadata, not redistributed documents. The strict loader validates pinned
binary/page/text hashes, selected numeric cells, issuer model, units and periods.
It does not claim automatic OCR or an audit of issuer disclosures.

## Independent verification dimensions

| Category | Rule | Baseline | Preferred views |
|---|---|---:|---:|
| SOURCE_VERIFIED | Nonfixture actual input identities/hashes plus reviewed original PDF/page extraction and original currency/unit | 0 | 100 |
| ACCOUNTING_VERIFIED | Source-qualified inputs; one source, compatible known scope and fiscal boundaries; applicable balance/cash consistency | 0 | 100 |
| POINT_IN_TIME_VERIFIED | Accounting-qualified inputs plus qualified original publication time for every input | 0 | 0 |
| PUBLICATION_RIGHTS_APPROVED | Applicable evidenced public-display permission for every input, independently of accounting | 0 | 0 |
| FULLY_VERIFIED | All four dimensions | 0 | 0 |

SOURCE_VERIFIED authenticates this selected extraction, not the accuracy of the
issuer's entire accounts. ACCOUNTING_VERIFIED is a deterministic consistency and
basis decision, not an audit opinion. A statement contradiction blocks affected
accounting/derived metrics while retaining the reported source fact and unrelated
statements. Cash beginning/ending require the FX-aware endpoint check. Permission
and point-in-time grades never grant private access by themselves.

The 100 observations consist of 63 reported canonical cells and 37 supported
derivations. Two extra FX cells are reconciliation evidence, not extra headline
metrics. Preferred views contain 2,660 observations (2,623 reported, 37 derived),
2,196 distinct source-metric identities. All-selectable presentation union is
2,948 = original 2,816 + report 100 + new CafeF 32. The original provider histories
remain selectable; shorter reviewed annual views do not erase them.

[VERIFIED_METRIC_COVERAGE.csv](validation/free-data-v2/VERIFIED_METRIC_COVERAGE.csv)
counts each ticker/source/frequency/metric separately.
[Machine-readable counts](validation/free-data-v2/EVIDENCE_RECOVERY_COUNTS.json)
include lineage and reported/inferred/unknown origins. The legacy
VERIFIED/PARTIALLY_VERIFIED/UNAVAILABLE grade remains compatible; a missing
publication timestamp can keep its broad grade partial even when SOURCE and
ACCOUNTING dimensions are true. The UI discloses these separately.

## Reproduction

From the financial-data worktree, with the existing private inputs:

~~~powershell
uv run python -m scripts.recover_financial_evidence --baseline .local/activation-captures --bundle .local/free-data-v2-final --output research/validation/free-data-v2
~~~

This performs zero provider requests and source mutations. It neither rewrites
the 23,040-version existing journal nor certifies point-in-time/public reuse.
