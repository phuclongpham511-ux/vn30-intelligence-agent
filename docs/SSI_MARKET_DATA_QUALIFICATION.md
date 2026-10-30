# SSI qualification and remaining Market Workspace work

Reconciled 2026-10-18 from existing source and saved evidence only. No new provider
requests, application changes, test campaign, production inspection or deployment.
This records unfinished gates; it does not certify Market Board completion.

## Continue the existing implementation

Worktree: `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/vn30-intelligence-agent`.
Branch: `codex/woofi-market-board-correction`.
Latest Market Workspace commit: `cb5979fa5e1717d4b634a98490cc391f6da50aa5`.
Its ancestors include Unified V2.1 `79cbe4661c4139609017f582de0b55a93a0f5682` and
Market Board V1 `b5af18c30f722406f884a0d2ef07c4bc1d87e9e9`.

Already implemented: Overview's comparable sample and persisted News; ordinary
three-panel Board and movement groups; Compact/Detailed equal-area Heatmap; stock
research navigation; EN/VI and light/dark. Newer uncommitted work adds KL/GT columns,
numeric sorting with unknowns last, shared activity source inspection, raw trade
evidence, interval rejection and qualified-limit color guards. Retain those changes.
See [activity acceptance](MARKET_BOARD_ACTIVITY_QUALIFICATION.md),
[refinement acceptance](MARKET_WORKSPACE_V21_REFINEMENT.md) and
[Unified V2.1](UNIFIED_MARKET_WORKSPACE_V21.md).

Prior isolated activity evidence reports frontend **182 passed / 1 skipped**,
focused backend **84 passed**, typecheck and webpack build PASS. Desktop 1440×900
and mobile 390×844, EN/VI, light/dark, sorting and missing/stale/simulated activity
were exercised. These are prior results, not a new run or live SSI certification.
No completed UI or research needs rebuilding to resolve the gates below.

## Reuse the five completed source reads

Installed SDK inspected previously: **ssi-sdk 3.2.1**, matching the project pin.
Five sequential GETs on **2026-10-17, 20:26:42–20:26:48 ICT**: SecuritiesInfo VN30,
VN100, HOSE; MasterData October 16 page 1; SecuritiesSummary ACB October 16.
Successful responses establish observed access to these requests only. They do not
prove broad account entitlement or display/redistribution permission. No new read
is needed to establish these already observed fields or sample counts.

| Family | Actual saved evidence | Acceptance and remaining gate |
| --- | --- | --- |
| Matched KL/GT pair | ACB `tradingDate="2026/10/16"`, `totalMatch="5160300"`, `totalMatchValue="106488260000"`; same record. `totalDeal`/`totalDealValue` null, not zero. | **PARTIAL.** Explicit quantity/monetary units and multipliers, regular-board/odd-lot scope, correction/reset/finality semantics, original observation time or date-only policy, rights and normal-session acceptance remain unqualified. One symbol/day is not VN30 coverage. |
| Trade quantity | SDK maps daily trade `v` to cumulative total and `q` to individual matched quantity; interval `v` is separate. No new stream opened. | **PARTIAL.** Raw `v` stays unverified; no unit multiplier or negotiated-scope assumption. Current trade path has no qualified GT field. |
| ICB | Paired nonempty code/name on VN30 **30/30**, VN100 **100/100**, HOSE explicitly ordinary Stock **406/406**. Across all 785 HOSE instruments, **431/785** paired. | Availability **PARTIAL**, activation **BLOCKED**. Version, hierarchy/parents, classification effective dates and intended display rights absent. Four-character codes do not establish a hierarchy. No HNX/UPCOM or all-equity claim. |
| MasterData limits/reference | ACB October 16 `ceiling="22000"`, `floor="19200"`, `refPrice="20600"`; raw `board` field. Page 1: **1000/1979** records, **15/30** VN30 members, all 15 positive ordered limits. | **PARTIAL.** Explicit price units and day-effective metadata contract needed. Page 1 omissions do not prove unavailable data. No second-page request was made. No original intraday time supplied. |

ICB examples retained verbatim: ACB `8355` / `Ngân hàng`; GVR `1353` /
`Nhựa, cao su & sợi`. Distinct observed codes: VN30 13, VN100 28, HOSE ordinary
Stock 61. No shared-symbol mapping conflicts were found across the three responses.
Listing dates are not classification effective dates.

ACB summary close 20600/change 0 agrees with same-date MasterData refPrice 20600
and saved October 16 14:45 ICT OHLC close 20600. This supports one historical
comparison only. Numerical consistency does not establish units, finality or current
freshness. Retrieval time is never source observation time.

## Smallest unfinished integration, gated by evidence

1. **KL/GT:** obtain authoritative units/multipliers, detailed scope and temporal
   semantics plus applicable rights. Preserve the paired daily summary separately
   from tick-time activity. A new bounded shared summary acquisition/cache requires
   explicit acquisition-scope authorization; no per-row requests, new worker or
   fabricated source timestamp. Do not substitute last price × volume.
2. **Ceiling/floor:** after price-unit qualification, extend the existing MasterData
   cache and DTO to retain day-effective original limits/reference distinctly from
   tick observation time. Existing `_references()` currently discards ceiling/floor.
   No new endpoint or SQLite schema is inherently needed for this narrow path.
   Do not stamp limits with a tick time to pass `priceLimitTone`'s current guard.
3. **Industry:** confirm intended display rights and taxonomy/effective-date policy.
   Reuse original SecuritiesInfo mappings; durable integration needs a reviewed
   metadata/schema contract, since current Security persistence has no ICB fields.
   Keep grouping inactive; no code-prefix hierarchy or alternate acquisition path.
4. **Live acceptance:** in a normal Vietnamese session, use the existing authorized
   canonical path to verify actual VN30 coverage, source age/session, cold load and
   partial failures. The closed-market five-read sample cannot pass this gate.

Until those inputs are available, no additional field is fully qualified for safe
activation. Keep unavailable KL/GT as em dashes, stale/missing neutral, industry
grouping inactive, and real SSI limit colors gated. Synthetic fixtures remain
explicitly simulated. User product approval and live data acceptance remain pending.

## Preserved evidence receipts

Existing evidence directory (not copied or modified):
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/ssi-qualification/`.
The report's production process observations are historical and are not a current
health diagnosis. No production process or database was accessed in this continuation.

SHA-256 receipts read on 2026-10-18:

| File | SHA-256 |
| --- | --- |
| `FINAL_REPORT.md` | `266d2b2d406d02648952251a5be225ed1a4a3c669be3ff5ee2fc5093fcd477bf` |
| `evidence.json` | `7daa4ee90df0e8241749e3004326ccd4d6035d1df2725789d67ee6a40d62202b` |
| `analysis.json` | `e880006deb48e3d6465ff0327590885f84e7eef8b7bc30ae429d1c3d474710b5` |
| `alignment-checks.json` | `9bc67bae274745a6c59c52b7a6be94204112fc95541d38c92dc2969404281341` |

The raw market-only evidence includes original responses and request/retrieval times;
no credential/token evidence is needed or reproduced. Prior UI evidence is in the
sibling `market-activity/` and `market-refinement/` directories. Preserve all files.
No new source request is justified simply by resuming this work.

Production/Supervisor, Collector, SQLite, cooldowns and runtime pin are outside this
task. Technical Pilot must remain OFF and FPT PAUSED. No push or deployment.
