# Provider metadata and free-source audit

Current V3 results supersede the checkpoint below: **175 verified observations,
64 supported definitions, and 15 qualified TCB/VCB peer metrics**. See
[V3 delivery](FINANCIAL_INTELLIGENCE_V3_DELIVERY.md),
[current comparison](SSTOCK_FEATURE_COMPARISON_V3.md), and
[current manual acceptance](DASHBOARD_VERIFICATION_V3.md). Runtime remains PENDING.

## Prior bdc70ad checkpoint record

21 October 2026. No dependency upgrade, paid subscription or WiData dependency.
Existing SSI and VCI integrations remain primary. New sources are explicit,
bounded offline saved-evidence adapters, never automatic fallback requests.

## Installed schemas first

`pyproject.toml`, `uv.lock` and installed package metadata agree on vnstock
**4.0.2**. Inspected installed `explorer/vci/financial.py`,
`explorer/kbs/financial.py` and their constants before comparing current docs.
The VCI dataframe path limits reports (`head(4)`), drops/transposes metadata and
fills null cells with zero. Woofi's existing raw-response path preserves original
records and does not adopt those lossy transformations. No package was changed.
The saved raw REST records do not contain recoverable original unit/currency,
consolidation or qualified fiscal/publication fields. Their complete field names
and recorded metadata remain in private captures. Canonical TCB/SSI packets
cannot reconstruct absent original transport fields.

Current [official free financial docs](https://vnstocks.com/docs/vnstock/free/co-ban-fundamental)
and the [official financial API guide](https://github.com/vnstock-hq/vnstock-agent-guide/blob/main/docs/vnstock/advanced-usage/07-financial-api.md)
describe current APIs, not proof of fields in installed 4.0.2 or historical
responses. No guessed modern schema was injected into old records.

The installed KBS code advertises `Audit`, `Unit`, `Head`, `United`,
`YearPeriod` and `ReportDate`; potential metadata is not recovered metadata.
One normal direct request is recorded below. Its failure yielded no usable rows.

## Actual source responses

All receipts preserve requested query, response status, byte count, SHA-256 and
actual UTC observation time privately under `.local/free-source-probes`.
No credentials, cookie reuse, user-agent impersonation, proxy or access bypass.
[Committed response metadata](validation/free-data-v2/SOURCE_RESPONSE_AUDIT.json)
contains the bounded queries/statuses/hashes without response bodies.

| Source / endpoint | Actual response | Decision |
|---|---|---|
| KBS `kbbuddywts.kbsec.com.vn/iis-server/investment/stock/finance-info/FPT` | One GET, page 1/pageSize 4/type KQKD/unit 1000/termtype 1/languageid 1: 400, HTML 154 bytes | No mapping from nonexistent payload; no retry/header tricks. HTTP 400 alone does not prove a licensing denial |
| KBS `/robots.txt` | 400, same 154-byte body | No successful robots policy document recovered |
| VNDirect `api-finfo.vndirect.com.vn/v4/financial_statements` | One GET, FPT annual model 2, size 100: 403, 13 bytes | Stopped, no workaround or integration |
| CafeF `cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx` | Six 200 responses: FPT income/balance, TCB income, SSI income, VHM income/balance | Added strict saved annual adapter; VHM four periods enter private research |
| HPG official Q4/2025 PDF | 200, 7,135,524 bytes | Original-report adapter with reviewed rows/pages; annual 2024–25 and 2025 closing balance |
| TCB official 2025 annual report PDF | 200, 31,023,262 bytes | Same original-report adapter, selected 2024–25 bank rows |
| VSDC `/vi/ad/183589`, `/189195`, `/195957` | Three 200 HTML pages, 71,740 / 71,772 / 72,240 bytes | Existing corporate-action model, exact official cash-dividend notice fields |
| Two candidate FPT PDF URLs | 404 | No binary/page qualification from indexed text or filename |

KBS failure body:
`61232743a1a887eee2d4d2ff8df6f2477097a7ed3b6df5ffa7bef01a062a4d65`.
VNDirect failure body:
`d134ca025a6c63b2555200885d71cb6e61f8097cdfd7ecf13675b3df0c721797`.
Original report hashes/pages are in [the evidence report](EVIDENCE_RECOVERY_REPORT.md).

## Free schemas evaluated, without installing packages

The public vnfin tree was inspected at
`338558bb984e31fb0ec66ea5f61698a72959c110` (default branch master), including
[CafeF field documentation](https://github.com/hungson175/vnfin/blob/338558bb984e31fb0ec66ea5f61698a72959c110/docs/sources/fundamentals-cafef.md)
and [VNDirect schema](https://github.com/hungson175/vnfin/blob/338558bb984e31fb0ec66ea5f61698a72959c110/docs/sources/fundamentals-vndirect.md).
Independent parsing was implemented against the actual saved CafeF responses;
no provider module was copied. VNDirect model IDs (corporate 1/2/3, bank
101/102/103) are documented possibilities, not actual financial rows in this
mission. The repository code licence does not grant all upstream data rights.

VietFin's public tree
`8e55130dcbced62c152eb2d4401b873b4e59737d` and
[financial docs](https://vietfin.readthedocs.io/en/v0.1.0/usage/financial.html)
were inspected. Its legacy `fiin-fundamental.ssi.com.vn` download service is not
the existing SSI FastConnect integration. No authentication, identity spoofing,
new subscription or legacy endpoint request was attempted.

Existing [SSI FastConnect documentation](https://developers.ssi.com.vn/docs/sdk/nodejs/utilities)
identifies the classification field family as ICB. The existing ordinary-HOSE
archive supplies exact code/label pairs; it supplies no vendor taxonomy version,
level, effective membership dates or historical classification revisions.

## CafeF

The saved adapter is deliberately limited to individually supported reported
amounts, with the scale reference below retained in each source context.

## Field mapping decisions

- CafeF Type 1/2 annual responses use `Data.Value` with four annual headings.
  Saved owner/query/hash/period/label validation bounds the reader. The reviewed
  ×1,000 transport convention is **inferred**, never original-unit evidence.
  All 32 FPT cross-source cells match VCI within 1,000 VND; maximum difference
  499 VND. This comparison transfers neither scope nor currency metadata.
- `DTTBHCCDV` is labelled gross sales: it is not canonical net revenue. It stays
  unmapped. `TotalDebt` is labelled total liabilities: it maps only to liabilities,
  never interest-bearing debt. Bank “Lợi nhuận ròng(**)” is not silently mapped
  to parent profit. Each unsupported field stays unavailable independently.
- HPG closing/opening dates are kept literally; the opening 01/01/2025 balance
  is not used as a 31/12/2024 closing observation. Q4 annual figures remain a
  distinct pre-audit filing vintage. TCB monetary and EPS scales are separate.
- VSDC article extraction excludes surrounding related articles. Publication
  local date is `announced_on`; missing time/zone stays absent. Record/payment
  dates do not supply an ex-rights date or confirm payment.

## Access and deployment

Successful public HTTP retrieval establishes accessibility, not a blanket
redistribution grant. Existing owner-authorized private research is preserved;
no applicable new public source-family grant was recovered. Original reports and
HTML stay ignored/private; generated coverage contains hashes/statuses. Public
consumers reject the private contracts. The adapters read saved evidence only;
an ordinary dashboard visit never triggers a provider call or authentication.
Rights, accounting correctness and publication timing are independently graded.
