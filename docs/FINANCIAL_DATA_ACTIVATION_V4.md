# Financial Data Activation V4 — PARTIAL

Date: 2026-10-20. Base: `3663b54f3c456e1abb58a70209847ee92a8061a5`.
Development only. **New real financial fields activated: 0.** This is not a
successful live-data activation. No provider financial request, SDK upgrade,
worker, database change, server restart, push, deployment or browser operation.

## Concrete source findings

Installed SDK metadata: vnstock 4.0.2. Saved receipts record SDK `unknown`;
do not retroactively assign the installed version to them. Current online
documentation describes newer interfaces and is not proof of the 4.0.2 contract.

Inspected existing raw `FPT.json`, `PNJ.json`, `VCB.json` in
`C:/Users/PC/.codex/tmp/woofi-fundamental-engine-v1-20261013/`.
Each has income, balance and cash statements, with 8 annual and 34 quarterly
observations per statement: **378 observations total**. Every saved observation
lacks `consolidation` and original `unit`. Source catalogs contain no
consolidated/standalone/separate basis labels. Parent-attributable profit is a
line-item definition, not proof of the entire packet's basis.

Capture hashes:

| Issuer | SHA-256 |
| --- | --- |
| FPT | fdcf9bc60642157ce6a9fced8e405ea3b2a4637a7d2a72cdc0ae30c778ccdb0f |
| PNJ | 18e0642234faf1c5d10f855506bc081869094f9f80b44d98ab7af7fb2748c0a6 |
| VCB | 9c608fea54f2d744dc416cef420be4ccd3d0c8331cfd69682f00fe39e608cb00 |

`yearReport` and `lengthReport` identify provider year/quarter; they do not
establish fiscal start/end dates. `publicDate`, `createDate`, `updateDate`
are retained as original strings, separately from retrieval. No publication
timezone, audited/revised status or point-in-time availability is inferred.
Existing VND x1 adapter normalization remains an audited engineering contract;
missing original units are still recorded as missing. EPS remains VND/share.
Quarterly flow, annual and period-end balance semantics are unchanged.

The latest annual and quarterly saved periods remain 2025 and 2026-Q2. The
normalizer's original hashes, code/label checks and bank exclusions remain.
Nine saved annual/quarterly/TTM projections still have 0 QUALIFIED and 0 DEMO
metrics. This is saved evidence, not current provider freshness.

## Owner authorization and source rights

The owner stated in this task: “tôi cam kết các dữ liệu trên đều được sử dụng
hợp pháp”. Record this as **owner-attested lawful use**, not provider-issued
certification. It authorizes the requested development investigation; do not ask
the owner to repeat the same attestation. No provider account, credentials,
source-specific agreement, public redistribution scope or entitlement was supplied.
No credentials were searched or requested.

Technical basis remains unresolved independently of rights. No blanket
`display_rights=permitted` flag is inserted into all provider observations.
Any eventual rights application must reference the owner's applicable scope
and source family; a provider payload cannot grant itself permission.
Public redistribution eligibility is not independently established here.

Vnstock explicitly separates software rights from source-data rights:
[tool scope](https://vnstocks.com/onboard/pham-vi-cong-cu).
Its newer [financial interface](https://vnstocks.com/docs/vnstock/co-ban-fundamental)
describes statement access and optional filing discovery. Neither establishes a
record-level join between our old saved VCI observations and issuer filings.
No paid route or access restriction was bypassed.

## Provider comparison — documentation, not account validation

| Source | Coverage/history and statements | Basis, units and provenance | Access/reliability/rights |
| --- | --- | --- | --- |
| Existing vnstock/VCI | Actual three-issuer sample above; three statements, annual/quarterly. Do not extrapolate exact coverage to all listed stocks. | Existing normalized VND contract; raw basis absent. Original URLs/hashes/dates available, no filing identity join. | Existing adapter/cache reusable. No new requests or reliability claim. Owner attestation recorded; specific public scope not established. |
| FiinGroup Datafeed | Documented corporate/bank and other issuer statement families, annual/quarter definitions; exact entitled ticker coverage/history requires account sample. | Explicit consolidated/separate endpoint families; documented source name, period boundaries, public date and audit flag. Currency/multiplier still needs the applicable feed contract. | Structured API is the strongest documented candidate for a future scoped adapter. No account/paid subscription assumed; SLA, revision delivery and display scope require the applicable agreement. |
| WiGroup WiFeed | Provider advertises listed-company financial statements across three exchanges and broad historical coverage; not verified ticker-level completeness. | Public product page does not establish each statement's basis/unit/publication schema. | Official API product intended for applications. Schema, sample entitlement, revisions/SLA and display terms still required; no scraping or subscription attempted. |
| Original issuer disclosures | FPT/PNJ published consolidated annual statements; VCB investor/disclosure pages offer source references. Not a verified complete structured universe. | Filing titles can establish that document's basis, but not which filing produced a VCI row. Document units/page/period and exact version need review before a join. | Useful authoritative cross-check, not a scalable licensed API substitute. No automated extraction/acquisition introduced. |

Sources:

- [FiinGroup financial statement catalog](https://datafeed.fiingroup.vn/api-doanh-nghiep/bao-cao-tai-chinh-bctc)
- [FiinGroup consolidated balance-sheet contract](https://datafeed.fiingroup.vn/api-doanh-nghiep/bao-cao-tai-chinh-bctc/bctc-hop-nhat/bang-can-doi-ke-toan-hop-nhat)
- [WiFeed official product](https://www.wigroup.vn/san-pham/wifeed)
- [FPT original disclosure index](https://fpt.com/en/ir/information-disclosures)
- [PNJ original financial reports](https://www.pnj.com.vn/quan-he-co-dong/bao-cao-tai-chinh/)
- [VCB investor sources](https://www.vietcombank.com.vn/Nha-dau-tu)

These are public documentation reads only. Do not transfer FiinGroup's contract
to VCI just because field codes look similar. No numerical match alone qualifies
reporting basis, units or filing version.

## Small reusable source increment

The existing display projection now reports all independent input blockers per
metric, with its original primary `reason` retained for compatibility. Unknown
basis no longer hides a second rights gate. This does not change numerical
calculations, qualification decisions or permitted values.

The existing UI validates this optional additive list and exposes it inside each
metric's disclosure. Missing old payloads remain supported. Empty asset/funding,
growth/quarterly or valuation chart pairs share one expandable disclosure.
Available historical charts remain rendered independently, including real zero.
Period selection, source navigation, EN/VI and all source evidence are preserved.
No new dashboard or provider abstraction. News, Board colors, Watchlist,
Corporate Actions and market adapters are unchanged.

## Selected strategy and exact next activation slice

Retain VCI and the canonical model. First resolve a source-contract or
record-linked filing statement proving basis for the exact source/version,
statement and period. Do not mark a whole ticker/history consolidated.
If VCI cannot provide that evidence, evaluate an entitled FiinGroup sample
through its explicitly separate statement families before writing a new adapter.
WiFeed remains an alternative pending its schema.

Start with reported revenue/operating income, profit, assets, liabilities and
equity for compatible annual periods, and only then supported historical series.
Each observation must retain its source, period/frequency, currency/multiplier,
basis and reviewed rights reference. Mixed-source ratios and incompatible periods
stay blocked. VCB uses bank definitions; no generic industrial revenue or liquidity
fallback. P/E/P/B still need separately compatible price/share/earnings inputs.

The immediate technical request is an applicable VCI basis contract or
filing identifier mapping; for another provider, an authorized sample with
documented basis, units, periods and source references. No paid purchase,
new credentials or recurring acquisition is authorized by this report.

## Validation

Focused backend: 51 PASS, including six new activation boundary cases; existing
Starlette/httpx deprecation warning. Full frontend: 315 PASS, 1 pre-existing SKIP.
Typecheck PASS. Final webpack build PASS in the separate artifact folder.
The first build caught a newly inserted separator encoded as Windows-1252;
it was corrected to UTF-8, then the same webpack build passed.
Synthetic tests exercise dynamic symbols and are not real qualification evidence.
Nine saved-source replays preserve receipt hashes and activate zero metrics.

Artifacts:
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/financial-activation-v4-20261020/`
contains `saved-replay/` and a separate `frontend-build/`, so running build files
are not overwritten. Browser acceptance remains PENDING; no browser was operated.
