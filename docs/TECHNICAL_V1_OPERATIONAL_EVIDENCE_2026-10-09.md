# Technical V1 operational evidence and decision request — 2026-10-09

Status: **NEED_USER — operational EOD acceptance policy is unresolved.** This is
an operational FPT smoke investigation, not benchmark generation, calibration,
holdout review, or permission to publish a verified Technical Daily Packet.

## Completed work and evidence

| Check | Observed result | Limit |
| --- | --- | --- |
| Repository | Clean checkout at `84cb2ef5141010b6e6230f3146f5e1e34216adc8`; `.env` ignored | No code or production state changed |
| SSI settings and authentication | Both secrets resolved through `Settings`; one bounded SDK authentication succeeded; FPT metadata and history endpoints accessible | Credential values and tokens were never displayed |
| FPT identity | SSI securities response identified `FPT` as `Stock` on `HOSE` | Current metadata is not a historical listing vintage |
| Bounded history | `2026-04-01` through `2026-10-08`: 131 nonfixture daily observations, 130 before target, no duplicate dates | Returned dates do not establish venue-calendar continuity or bar finality; 252 prior observations are not present in this window |
| Units and basis | Existing qualified adapter uses VND prices ×1, shares volume ×1, currently adjusted SSI history | Adjustment factors and historical SSI vintages are unavailable |
| Raw target schema | October 8 OHLC row keys: `symbol`, `tradingDate`, `open`, `high`, `low`, `close`, `volume`, `value`; envelope keys: `code`, `data`, `msg`, `pageIndex`, `pageSize` | No final flag, publication timestamp, record revision ID, or correction notice in this response |
| Read receipt | `EODHistoryRead` has an actual operational `observed_at`, a content fingerprint, `fetched_at=None`, and zero completion attestations | Its `end_of_day_assumption` at 23:59:59 Vietnam time is not an audited SSI publication time |
| Existing consumer | Real 131-row read returned `INCOMPLETE_EVIDENCE`, `verified_session_calendar_unavailable`, with 131 available observations | No D1/D4/D5 packet or verified API snapshot was produced |
| Regression | Focused SSI provider, EOD, D1, D4, D5, and Technical API suite: 290 passed, one existing Starlette/httpx deprecation warning | This proves code paths, not live evidence readiness |

The operational smoke uses October 2026 only to check current product plumbing.
It does not enter protected historical cases, a review queue, a development
summary of event outcomes, calibration, or the official PIT-sensitive benchmark.

## Calendar investigation

The [HOSE 2026 trading-holiday notice](https://staticfile.hsx.vn/Uploads/UploadDocuments/2428610/20251209%20-%20HOSE%20-%20Notice%20of%20trading%20holiday%20schedule%20for%202026%20-%20PV.pdf)
and [New Year amendment](https://staticfile.hsx.vn/Uploads/UploadDocuments/2437411/20251225_Thong%20bao%20%20ve%20%20viec%20cap%20nhat%20lich%20nghi%20giao%20dich%20Tet%20Duong%20lich%202026%20toan%20thi%20truong.pdf)
are official schedule candidates. A schedule can establish planned closures; it
cannot prove that every other day actually traded or that an emergency closure
did not occur. Direct retrieval of the annual PDF through the web reader failed,
so its full coverage and amendments remain unverified here.

An October 8 HOSE trading bulletin appears in [a republication attributed to
HOSE](https://cafef.vn/du-lieu/hose-2993991/hose-diem-tin-giao-dich-ngay-08102026.chn),
dated 16:34 Vietnam time. It is a lead for a directly sourced exchange record,
not an authenticated HOSE artifact in this investigation. It covers one venue
day, not all dates in the 190-day history range, and does not bind SSI's adjusted
FPT bar hash. No complete verified HOSE session ledger was found in this
repository or acquired for this smoke test.

## SSI completion and revision investigation

SSI's [daily OHLC documentation](https://developers.ssi.com.vn/docs/tutorials/ohlc),
[Python market-data services](https://developers.ssi.com.vn/docs/sdk/python/service-classes),
and [OHLCData model](https://developers.ssi.com.vn/docs/sdk/python/utilities)
describe historical daily rows and their fields but do not document a final-bar
attestation, publication timestamp, or revision identifier. SSI says REST market
data updates periodically in its [Market Data FAQ](https://developers.ssi.com.vn/docs/faq/market-data);
[operating hours](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
describe the trading session, not the final publication time of adjusted OHLC.
The source decision already records SSI's direct answer: a historical query
returns its currently stored version, with no earlier vintage, revision lineage,
or correction notifications. A later stable read or a market-close clock cannot
prove immutable finality.

Other candidates need qualification: an SSI daily CSV/download could have a
publication receipt but is still the same provider and has no documented
finality guarantee; an exchange daily bulletin may establish venue occurrence
but not the exact adjusted SSI bar. Neither was promoted to proof. SSI historical
storage/retention rights remain unresolved in the source decision.

## Decision options

1. **Keep the current VERIFIED gate.** Require independently verified complete
   HOSE session evidence and a source-bound completion attestation matching the
   exact SSI bar/version. This preserves current semantics but leaves live
   packets blocked until those sources exist.
2. **Approve a distinct operational acceptance tier (recommended for product
   exploration).** A post-session SSI bar could become *operationally accepted,
   correction possible* only after a qualified official venue occurrence/closure
   ledger covers every date; an official session bulletin is published for the
   target; and two fresh, separately acquired SSI reads of the exact target bar
   match in price, volume, identity and adjusted basis. The first read occurs
   after bulletin publication. Proposed conservative
   timing: the second read occurs at least 24 hours after the bulletin's
   publication and at least six hours after the first read. Both receipts and
   hashes are retained if storage rights permit. Missing source evidence,
   mismatches or later revisions withhold/retract the provisional output.
   These timings are proposed operating rules, not source-certified finality.
   The tier must not set `completion_assurance=VERIFIED`,
   `safe_to_display_as_verified=true`, or enter the official benchmark. It needs
   separately versioned API/product semantics and explicit limitations. A
   persisted producer additionally needs confirmed storage rights.
3. **Seek a source-certified finalization mechanism from SSI or HOSE.** This
   could support the existing verified path if it binds ticker/session, adjusted
   bar content, venue, and an actual publication/knowledge time. No such
   mechanism has been established by the currently qualified interfaces.

**Recommended policy request:** authorize design of option 2 as a separate,
clearly provisional operational tier, while keeping the existing verified
consumer and API gate unchanged, with the two-read/24-hour/six-hour criteria
above. Implementation still depends on qualifying a direct official calendar
and bulletin source and confirming storage rights. If only verified output is
acceptable, choose option 1 and request a source-certified SSI/HOSE attestation.
No producer or snapshot should be built under an implicit relaxation.

## Remaining tasks and next action

- Qualify a direct official HOSE venue-day/closure source for complete bounded
  coverage, including amendments and outages; unresolved dates stay unknown.
- Obtain SSI's written answer about historical OHLC publication/finalization,
  corrections and snapshot retention rights, or qualify another authoritative
  bar-bound source.
- After the policy decision, implement only the approved evidence acquisition
  and acceptance path; keep D1/D4/D5 numerical and readiness contracts intact.
- Re-run the real FPT consumer, local snapshot boundary and read-only API only
  when the required independent evidence can actually be supplied.

No source code, credentials, production snapshots, commits, pushes, or deployments
were created in this investigation.
