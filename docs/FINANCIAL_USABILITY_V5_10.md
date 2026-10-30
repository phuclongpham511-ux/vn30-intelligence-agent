# VN30 financial usability and qualification V5.10

Assessment: 23 October 2026; baseline `33b5490`, branch
`feature/financial-data-intelligence`. Universe remains the saved HOSE VN30
snapshot effective 3 August 2026. All six statement families remain present for
30/30 issuers. No VN100 expansion, production activation or source refresh.

## Actual blockers

The audit selects the exact V5.9 metric additions by immutable identity difference
against its pre-run SQLite backup, then selects `UNQUALIFIED` reported/derived
records. This reproduces **2,142 records: 1,200 reported and 942 derived**.
These have null normalized metric values; source numbers remain inspectable in
input references. Unavailable/blocked metric kinds are excluded from this cohort.

| Evidence category | Records affected |
|---|---:|
| Original unit/currency/scale evidence absent | 2,142 |
| Reporting scope absent | 2,142 |
| Explicit fiscal boundaries absent | 2,142 |
| Original-document extraction evidence absent | 2,142 |
| Public display rights unreviewed | 2,142 |
| Qualified publication time absent | 2,142 |
| Missing mapped source code | 0 |
| Missing required inputs for the already computed reported/derived values | 0 |

Categories overlap. Normalized VND units and adapter scale are present; missing
original-unit evidence is not a claim that every numeric amount has unknown
normalized units. Mapped codes/formulas are present, but independent confirmation
of their original accounting definitions remains part of the document gap.
Rights and publication vintage are separate dimensions: unknown public rights
do not alone prevent private research; unknown publication time prevents
point-in-time certification, not an ordinary same-basis comparison.

All **81** original V5.9 comparisons were reproduced through
`saved_financial_insights`, with metric/period/evidence/reason results retained
privately. **27 quarterly YoY cases lack an exact comparison period**; the four
returned quarters cannot supply the same quarter one year earlier. The remaining
54 annual YoY/quarterly QoQ cases explicitly fail scope, original-unit evidence
and fiscal-boundary guards. Those metadata gaps also remain on the current
endpoints of the 27 missing-period cases; the comparison routine returns early
for a missing exact pair. Publication vintage, public rights, lack of causal
evidence and insufficient anomaly history appear in `missing_information`, but
are separate limitations, not all prerequisites for private pair comparison.

## Bounded evidence improvement

Audited issuers include the five V5.9 banks, securities issuer TCX and three
ordinary issuers. Their missing original scope/boundaries cannot be supplied
from SDK captures alone. A repair was selected in VJC, a VN30 ordinary issuer
whose existing original PDF already establishes scope, units and first-quarter
semantics, with a missing prior period as its actionable blocker. This yields
measurable improvement without another acquisition campaign.

The preserved original separate Q1/2025 PDF has explicit `Quarter I / This year /
Previous year` columns on PDF pages 7–9. Visual review of these archived images
supports ten Q1/2024 comparative source amounts: three income amounts and seven
cash-flow/reconciliation amounts. The source's calendar-year evidence plus the
dated first-quarter title establishes January–March 2024. No opening balance is
relabeled as a prior first-quarter balance. The original source URL is retained
in the existing manifest and every new evidence reference.

The existing `reviewed-report-v2` adapter gains optional
`relative_year='previous_year'`. This narrow rule requires a standalone Q1 flow,
ordered current/prior quarter columns, explicit column wording and a matching
dated report title. Balance sheets, YTD labeling, absent wording, reversed
columns and unsupported quarter/date mappings fail validation. The field is
omitted from hashed metadata when absent, preserving existing packet identities.
All existing file hashes, quote, source-cell, fiscal-calendar and unit checks
remain active. No numerical calculation is added to the adapter.

Visual review also corrects a previously unused gross-profit comparative token
in the new manifest. The old transcription, capture and selected current-period
observations remain unchanged. Both years' cash-flow and FX endpoint identities
pass. All 27 selected source amounts in the revised packet remain linked to the
same original PDF and the exact rendered page hashes.

The new canonical packet is archived and hashed as its own source capture,
with the original PDF digest retained separately in provenance. It is not
imported under the old PDF capture identity. SQLite appends one capture and five
statement observations; only the two previously absent 2024-Q1 income/cash
observations become new selected rows. The prior three selected observations
remain unchanged. The full reviewed revision is requested explicitly by capture
ID through the existing private service; no sources are spliced together.

## Measured usability

| Category | Before → after / improvement |
|---|---|
| A: stored original source amounts in VJC reviewed revision | 17 → 27 |
| B: numeric metric-period outputs in authorized private projection | +16 (12 prior-period outputs, 4 current-period change outputs) |
| C: compatible VJC quarterly YoY headline comparisons | 0 → 5 |
| D: newly public-display-eligible observations | 0 |
| Original V5.9 unqualified metric cohort | 2,142 → 2,142 |
| Original V5.9 comparisons enabled / still insufficient | 0 / 81 |

The five additional comparisons are revenue, net profit, operating cash flow,
gross margin and net margin, Q1/2025 versus Q1/2024. Nine newly reviewed canonical
reported amounts support the prior-period outputs; the tenth FX amount is
reconciliation evidence. The 16 outputs also include existing-engine ratios and
changes; they are not 16 new reported source amounts. Calculations, source
references and public withholding reuse the existing engine/private path.
No causal explanation, recommendations, public licence or publication vintage
is inferred. Private-research usability does not rewrite public qualification.

For completeness, the entire journal's `UNQUALIFIED` revision count is
**64,364→64,429**, including unavailable records; its reported/derived subset is
**30,557→30,597**. These are immutable revision counts across all saved issuers,
not unique current observations. Appending the reviewed packet adds new revisions
without relabeling old ones. The normalized public-facing quality classification
still withholds these values, while the authorized original-report projection
can expose qualified private calculations. The measured private improvement is
the 16 newly available metric-period outputs above, not the revision-count delta.

## Storage, validation and reproducibility

Private artifacts under `.local/financial-usability-v510/` include `blockers.json`
(all 2,142 records), `81-comparisons.json` (each original attempted comparison),
`review.json`, `packet.json`, `insights.json`, `audit.json`, tests and a consistent
`before.sqlite` backup. `run.py` reproduces the bounded offline evidence review,
canonical append, private engine checks and repeat-ingestion assertions. The
existing `.local/financial-collector-v57/` PDF/page images are reused unchanged.
No network request, new PDF download or new database schema was needed.

SQLite integrity is `ok`; foreign-key errors zero. Exact comparison against the
backup found zero prior rows missing/changed in all four tables, including
selection. All **1,619** pre-existing private/unrelated file hashes match.
Storage: captures **42→43**, statements **1,665→1,670**, selected observations
**1,665→1,667**, metric revisions **90,108→90,262** (154 appended revision
records, including unavailable records; not a count of newly usable metrics).
Repeating packet import and metric append inserts zero rows.

The packet passes annual/quarterly/TTM Financial Engine processing and saved
private Insight Engine processing. Focused regression initially passed **173**
tests; the final reviewed-quarter suite passes **19**, including a new end-to-end
SQLite/private-insight/public-withholding test. Full backend regression passed
**1,711 tests and 32 subtests** in 327.30 seconds, exit code 0, with one existing
Starlette/httpx deprecation warning. The final 19-test seam run additionally
covers the new end-to-end case added after full-suite collection. Existing
HTTP/dashboard contracts, production config and public rights
remain unchanged; no UI activation or visual acceptance is claimed.

Independent code-review skill reviews: Standards **0 actionable findings / 0
smells**; Spec **0 actionable findings**. The reporting caveat about independent
rights/publication/causal/history limits is reflected above. Private financial
files, both tooltip edits, CONTEXT.md, next-env.d.ts and the feasibility note
remain outside the commit. No push or merge is authorized by this delivery.
