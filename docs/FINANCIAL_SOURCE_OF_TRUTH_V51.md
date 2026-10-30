# PNJ Financial Source-of-Truth V5.1

Base: `c787fd169ce8dad4a1b2a0a48e7546afa6aaa0e6`. Review: 2026-10-20.
Decision: **C — EVIDENCE_INCOMPLETE**. Public activation remains disabled.
Application implementation and qualification rules are unchanged.

## Original PDF verification

The [issuer annual-report index](https://www.pnj.com.vn/quan-he-co-dong/bao-cao-thuong-nien/)
still links the [Vietnamese PNJ 2024 annual report](https://cdn.pnj.io/images/quan-he-co-dong/2025/20250416-PNJ-Bao-cao-thuong-nien-2024-vi.pdf),
published 16 April 2025. The public document reader identifies 117 PDF pages.
This establishes the selected publication reference, not binary identity.

A normal, unauthenticated retrieval of that exact URL at
`2026-10-20T12:29:07.268010+00:00` returned **HTTP 403 Forbidden**.
No alternate headers, credentials, proxies or denial bypass were attempted.
The supported document reader could read text. Its screenshot operation on
zero-based PDF pages 96 and 97 returned text markers but **no image content**.
Those markers are not visual evidence. No local or personal browser was used.

Consequently, the original PDF binary, its SHA-256 and page images remain
unavailable to this review. `document_sha256` stays null. The saved extraction
SHA-256 remains `98d6983373312c188465fe9a4ecf2a9fbdc31e902e10e4944a437f599e81829f`;
it identifies the saved reader text, not the PDF. No value has been independently
verified against original page pixels in V5.1. A or B would overstate the evidence.

## Field-level evidence retained, without promotion

These are the existing source-text observations replayed in V5.1, **not newly
visually verified facts**. Original dot-grouped tokens and normalized integers
remain in the manifest and canonical receipts. Unit: VND, multiplier 1, based on
the saved statement headers; consolidated calendar-year periods, based on the
saved headings and note 2.2. These qualifications retain V5's text-only confidence.

| Field/code | 2024 VND | 2023 comparative VND | One-based PDF / printed page | V5.1 original-page verification |
| --- | ---: | ---: | --- | --- |
| Net revenue / 10 | 37,822,837,171,385 | 33,136,929,196,429 | 98 / 195 | UNVERIFIED |
| Total profit after tax / 60 | 2,112,916,282,946 | 1,971,099,177,135 | 98 / 195 | UNVERIFIED |
| Total assets / 270 | 17,207,730,777,685 | 14,427,558,015,356 | 97 / 193 | UNVERIFIED |
| Total liabilities / 300 | 5,952,424,147,163 | 4,621,377,351,380 | 98 / 194 | UNVERIFIED |
| Equity / 400 | 11,255,306,630,522 | 9,806,180,663,976 | 98 / 194 | UNVERIFIED |

Remaining page checks: company/ticker/exchange PDF 35 (printed 69), audit and
consolidated statement context PDF 96 (printed 190–191), statement spreads
PDF 97–98 (printed 192–195), fiscal-year note PDF 100 (printed 198–199).
The 2023 figures are comparative columns in the 2024 filing; no original 2023
publication-vintage claim. Approval/audit date 24 March 2025 is separate from
issuer index publication and local receipt time. No value was repaired or
filled using VCI; no VCI comparison or provider request was repeated.

## Display-rights review

Reviewed the official annual-report index/footer, the report reader's searchable
text, the linked [PNJ policy collection](https://www.pnj.com.vn/chinh-sach-bao-hanh-va-thu-doi.html),
the [issuer IR contact page](https://www.pnj.com.vn/quan-he-co-dong/lien-he/), and
existing Woofi V4/V5 rights records. The policy collection covers customer service,
warranty, delivery and personal-data processing. No applicable grant for financial
statement extraction/public reuse was established in this bounded review. This
does not establish that no such permission exists elsewhere. PDF download links,
the site's copyright footer and the owner's lawful-use attestation are not a
financial-data redistribution license. No blanket prohibition is inferred either.

| Use | Evidence and decision |
| --- | --- |
| Internal validation | This task authorizes bounded offline research. Source-issued permission not established; no broader entitlement claimed. |
| Local development display | Explicitly scoped offline EN/VI artifacts only. No general application activation or external sharing license established. |
| Public website display | Applicable permission/legal basis unresolved; existing guard remains enabled. |
| Commercial redistribution | No applicable license established; disabled. |
| Attribution | Retain issuer, title, original URL, page/code, fiscal period and comparative vintage. These are existing provenance controls, not confirmed licensor-prescribed wording; exact required wording remains unresolved. |

Exact question for PNJ IR or the applicable rights holder (not sent automatically):

> May Woofi extract, normalize, retain and display these ten PNJ 2023–2024
> numerical statement facts and derived metrics from the 2024 annual report:
> internally, on a local development application, and on a public/commercial
> website? Please identify the applicable permission or legal basis, whether a
> separate agreement is required, required attribution/link wording, permitted
> caching and updates, and whether redistribution of PDF/page images differs
> from display of extracted facts. Identify the authority granting that scope.

This question separates facts/metrics from reproduction of the report itself.
Neither absence of a discovered grant nor internal task authorization resolves
the public-use question. No email/message was sent and no legal conclusion about
statutory reuse exceptions is asserted.

## Internal pipeline validation

Reused the exact V5 manifest/extraction through `scripts.validate_financial_filing`
without `--saved-vci`. Ten original field observations normalize once at VND ×1
with issuer/document/page/code/raw-token provenance and exact annual periods.
Both `assets - liabilities - equity` identities equal **0 VND**. Existing scoped
engine output contains the five reported fields and existing derived metrics;
derived metrics are not labelled issuer-reported values. Default public summary
values remain null; source rights remain `unreviewed`.

The existing offline renderer uses the actual financial components and compiled
V5 CSS: EN and VI each render all ten original values. This is static HTML/source
verification, not browser or running-app acceptance. The normal public parser
rejects internal payloads, and no HTTP query can select internal scope.

Fresh focused validation: **41 backend PASS**, **2 frontend PASS**. Existing
Starlette/httpx deprecation warning only. No implementation changes; typecheck
and build were not repeated (V5 evidence remains applicable to unchanged code).
No tests or assertions were weakened. No new synthetic case proves source facts.

## Receipts and next action

Evidence directory outside Git:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/financial-source-truth-v51-20261020/`

Contains the 403 retrieval receipt, raw reader/screenshot responses, bounded
official policy review response, `replay/` canonical/internal/public projections,
`internal-ui/` EN/VI HTML, and `DECISION.json` with artifact hashes. No PDF or image
digest is invented. These local artifacts are not for public hosting.

Next: obtain an authorized copy of this exact official PDF (for example a
user-supplied original download). Hash it, inspect the listed complete page images
and compare all ten tokens, column years and units before upgrading evidence.
Separately obtain the applicable rights terms or scoped confirmation above.
Do not activate public fields until both gates are resolved. No additional
dashboard, company expansion or provider comparison is needed.

Production, Supervisor, Collector, SQLite, application pin, News V3, Market Board
colors and running development instances were untouched. No push/merge/deployment.
