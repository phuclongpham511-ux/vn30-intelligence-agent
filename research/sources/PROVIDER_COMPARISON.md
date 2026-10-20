# Source decisions

| Source | Evidence inspected | Decision |
|---|---|---|
| SSI FastConnect | Official registration/key documentation and existing adapter/tests | Preserve verified pricing; no new pricing/auth requests |
| VCI / vnstock 4.0.2 | Existing adapter, six saved captures, bounded new TCB/SSI packets | Retain pinned provider; private research only for unqualified sample |
| vnstock-java-kbs | Apache-2.0 repository and FinanceService/KbsConfig at pinned tree SHA in KBS_CODE_RECEIPT.json | No Java dependency or runtime provider change |
| vnfin | Apache-2.0 code; documented VNDirect/CafeF fundamentals, explicit units and personal/internal data boundary | Candidate only; no silent failover |
| vietfin | Apache-2.0 code; personal/research/education intent; financial/event APIs documented | Candidate only; no integration grant inferred |
| Official issuer/HOSE/HNX/VSDC | Existing filing and corporate-action boundaries; saved official PNJ page text | Replay independently; no licensing or binary-verification promotion |
| Annual-report repository | Public README/index description; LICENSE retrieval 404 | Metadata lead only; underlying document rights unresolved |
| TiniX OCR dataset | Public dataset card specifies CC BY-NC 4.0 | Excluded from commercial runtime and redistribution |

KBS source requests financial page size four, two pages, annual/quarter terms and unit=1,000,000,000. That differs from Woofi's raw VND convention; code parameters do not prove response units. Its pagination merge assumes row alignment, another reason to validate field identities before any adapter. The host robots.txt returned 400; automated collection was not continued. No cross-provider numerical agreement is claimed for FPT/HPG/TCB/SSI.

Primary links: https://guide.ssi.com.vn/ssi-products/general-information ; https://github.com/anhtri04/vnstock-java-kbs ; https://github.com/hungson175/vnfin ; https://github.com/vietfin/vietfin ; https://github.com/thanhnp-uel/vietnam-listed-companies-annual-reports ; https://huggingface.co/datasets/tinixai/ocr_annual_financials .
