# Financial Analysis V2 — evidence-preserving foundation

Base: `dc00ec174ef94f75cbbb71563f13b74f54a8cded`. Development only.
No provider requests, credentials, production database access, acquisition changes,
server operations, push or deployment. This increment uses the task's explicit
fallback when no real field passes the applicable qualification requirements.
**Real-data display vertical slice: PARTIAL, not completed or live accepted.**

## Existing path reused

`src/providers/vnstock/financial_packet.py` (one shared bounded issuer packet/cache)
→ `financial_statements.py` (VCI metadata/code normalization)
→ `src/schemas/financials.py` → `src/analytics/financial_engine.py`
→ `src/services/financial_presentation.py`
→ `GET /stocks/{symbol}/financials?projection=display`
→ `frontend/lib/financial-engine-data.ts`
→ existing Stock Detail `FundamentalTrends`, charts and statement table.

The three existing VCI REST sections are INCOME_STATEMENT, BALANCE_SHEET and
CASH_FLOW, plus their `/metrics` catalog. The statement endpoint supplies `years`
and `quarters`. No new endpoint, page, database model, worker or request loop.
The separate statement-evidence API and legacy financial APIs are unchanged.
This is a presentation activation guard, not a redesign of legacy raw-evidence
access controls or a grant to redistribute raw VCI content.

## Evidence reviewed and source contract

Original captures: `C:/Users/PC/.codex/tmp/woofi-fundamental-engine-v1-20261013/`
(`FPT.json`, `PNJ.json`, `VCB.json`). Each has three statement reads, 8 annual and
34 quarterly observations per statement, latest annual 2025 and quarter 2026-Q2.
Source is `vnstock:VCI`. Previously audited installed SDK version is 4.0.2; these
particular raw captures record `sdk_version=unknown`, which replay preserves.
No SDK version is filled into an old receipt by inference.

The new offline script replays actual saved REST envelopes, not the historical
DataFrame-derived metadata `items` array (which includes non-JSON NaN grouping
values). It uses the same `metadata_rows()` mapper as the current transport.
It verifies statement hashes and every individual source-record hash. A first
diagnostic attempt rejected the legacy NaN metadata; no financial value was
repaired. The completed replay uses the preserved original REST metadata.

Each observation now carries additive `FinancialSourceContext`:

- Provider-reported year/quarter, without inventing issuer fiscal boundaries.
  `period_start` and `period_end` remain null; raw boundary strings, if supplied,
  stay in original metadata until their semantics are qualified.
- Original currency and amount unit, **null when omitted**. Normalized amounts
  retain the existing audited VCI VND ×1 adapter contract. This is not new issuer
  confirmation. Other currencies/multipliers remain unsupported and rejected.
  Reported EPS retains its existing VND/share line unit; it is not a money total.
- Original record SHA-256, with statement content hash/source URL/acquisition time
  retained in the existing receipt. Original labels and canonical field codes stay
  inspectable. A different record produces a different hash, not an inferred
  restatement classification.
- Raw publication/update/create strings remain separate from acquisition and
  response-construction time. Publication timezone/precision, audit status and
  restatement status remain UNKNOWN. Raw audit/revision flags are retained as
  uninterpreted evidence, not promoted to verified flags.
- Display-rights state defaults to `unreviewed`, with no reference. Provider raw
  fields cannot assert permission. Nonfixture display requires a reviewed
  `permitted` state **and** a nonempty evidence reference; missing legacy context
  fails closed too. There is no enabled configuration/automatic enrichment path
  to grant VCI rights in this increment. Test permission references are explicitly
  synthetic, never source/license evidence.

## Qualification matrix (the saved three-company sample only)

| Family / original codes | Availability and technical contract | Remaining evidence / display decision |
| --- | --- | --- |
| Ordinary revenue/gross profit `isa3/isa5`; total PAT/parent PAT `isa20/isa22` | Known metadata mappings in FPT/PNJ, annual and audited standalone-quarter convention; VND ×1 | Consolidation unknown; publication context and VCI rights unresolved. UNQUALIFIED, display null. Parent and group profit never substituted. |
| Basic EPS `isa23` | Reported VND/share; annual or standalone quarter; never sum/difference into TTM | Reporting basis and rights unresolved. No P/E denominator qualification inferred. |
| Assets/liabilities/equity `bsa53/bsa54/bsa78`; ordinary cash/current assets/liabilities/inventory/borrowings | Original period-end balances retained, not summed TTM flows | Same basis/rights gaps; no invented period-end calendar dates. |
| CFO/CFI/CFF `cfa18/cfa26/cfa34`; capex `cfa19` | Original signs/labels retained. CFO minus nonpositive purchase outflow supports existing ordinary-company FCF definition | Same gaps. Bank cash-flow metadata anomalies remain withheld; no generic banking FCF activation. |
| Bank operating income `isb38`, net interest income/customer loan/deposit fields | VCB metadata selects bank profile; padded corporate revenue is not a bank fact | Consolidation/rights unresolved. No NIM, NPL or CASA inferred. |
| Margins, ROE/ROA, growth, leverage and FCF | Existing deterministic engine/formulas reused; technical synthetic cases pass | Every actual input must pass basis/provenance/rights gates. Mathematical correctness is not financial-source certification. |
| P/E, P/B, market cap, BVPS | No compatible qualified price/share/book/parent-earnings set | UNAVAILABLE. No stale price join, proxies or new valuation calculations. |

Existing statement tables retain additional original labels; that does not make
every raw code a supported canonical metric. Operating margin, EPS growth,
borrowings/assets and expanded operating-profit/PBT/receivable canonical mappings
are not newly implemented by this bounded foundation increment. No FPT/PNJ/VCB
number is labeled VERIFIED or enabled as a newly qualified public fact.

## Field-level qualification correction

Previously `calculate()` used coherence of all three statements, even for a ratio
using only income inputs. Unknown or separate cash/balance basis could suppress
an otherwise coherent income margin. Qualification now follows the calculation's
actual input receipts. ROE/ROA, cash conversion and other mixed-statement ratios
still reject differing bases. Growth still requires the exact comparable period
and compatible input bases. Missing/zero/negative denominators remain guarded.

Each overview metric owns its consolidation; overall mixed/unknown response basis
remains unknown. Frontend validation and metric definitions use the metric basis,
with the old summary basis only for old payloads lacking the new field. This does
not promote any currently unqualified source. Unknown rights/basis still suppress
affected metrics, chart values, comparisons and statement presentation amounts.

Existing annual/quarterly/YTD/TTM rules remain: YTD differences need comparable
consecutive same-year observations; TTM requires four contiguous compatible flows;
balance snapshots are not summed; EPS is not additive. Audit/revision chronology
cannot be reconstructed from a current provider envelope or its update strings.

## Stock Detail integration and result

Same sections, charts, period/unit controls, error states and statement table.
An expandable EN/VI Statement provenance disclosure exposes original metadata and
hashes in the existing source area. No change to Market Board, Heatmap, News,
Watchlist, Community, browser storage or public market-data qualifications.

Replay results (no DEMO or QUALIFIED metrics in any packet):

| Issuer | Annual | Quarterly | TTM |
| --- | --- | --- | --- |
| FPT | 15 UNQUALIFIED / 4 UNAVAILABLE | 15 / 4 | 14 / 5 |
| PNJ | 15 / 4 | 15 / 4 | 14 / 5 |
| VCB | 11 / 8 | 11 / 8 | 10 / 9 |

Rights are evaluated separately from technical normalization. Existing owner-
reported SSI permissions are preserved; they do not establish VCI financial-content
rights. Review an applicable existing VCI/vnstock agreement or source-specific
permission, rather than assume a new license is always necessary. An SDK license
alone is insufficient. No legal/provider confirmation was fabricated or requested.

## Validation and next step

Evidence root:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/financial-foundation-v2-20261019/`.
Saved replay JSON stays outside Git; no raw financial dataset is newly published.
The qualification JSON contains input hashes, source URLs/times and status counts.
The separate frontend build is a copied source artifact with existing dependencies;
no running preview/production files are changed.

Focused tests cover per-input consolidation/rights, legacy missing context, raw
self-asserted permission, YTD/TTM gaps and provenance, invalid units, cache-copy
isolation, source revisions, bank exclusions, calculations and SELECT-only APIs.
Existing financial regression includes denominator, reporting period, issuer,
DEMO/live and stale-ticker/loading isolation. EN/VI render/contract tests verify
the added disclosure and per-metric basis. Build and typecheck validate compilation;
they are not actual browser acceptance. Cloud Browser unavailable in this session;
visual acceptance PENDING, no local browser fallback.

Final results: **62 backend tests PASS** (16 new cases), **35 relevant frontend
tests PASS** (2 new cases), all **9 saved-real response contracts PASS**, isolated
optimized webpack production build PASS and separate typecheck PASS. The existing
Starlette/httpx deprecation warning remains. No tests were skipped or assertions
weakened; the former assertion expecting an income margin to be blocked by an
unrelated balance basis was replaced by the correct input-scoped expectation.
Original mixed-basis ROE and cross-year income basis guards remain asserted.
The final source hashes match the tested build copy. Final saved evidence is in
`saved-replay-final/`; `VALIDATION.json` records the build ID and source hashes.

Next bounded slice: choose FPT first; attach evidence establishing the exact
income-statement reporting basis and applicable VCI display scope, preserving its
hash/period/unit and publication limitations. If adequate evidence exists, enrich
only the affected original observations through a reviewed source mapping and
enable that period's direct revenue/PAT first. Do not require unrelated cash-flow,
bank, valuation or SSI gates. No quarterly-to-TTM expansion until all required
periods and accounting bases qualify. If original issuer filings supply the
missing metadata, match their exact issuer, statement, period and fields; do not
infer consolidation from similar amounts or company identity.

Production application pin `a98793a`, installed P1 `67aab035`, product SQLite,
Collector, cooldowns, Technical Pilot OFF and FPT PAUSED are not changed or
recertified by this source-only task. No push, merge or deployment.
