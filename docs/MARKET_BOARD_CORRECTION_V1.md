# Market board correction V1 — local checkpoint

STATUS: IMPLEMENTED / RELEASE BLOCKED BY BROWSER ACCEPTANCE

## Product finding and direct research

The earlier tall-card Price map over10 alphabetical records failed the user's
market-comparison task. Passing tests did not establish a useful product.

Opened https://sstock.vn/bang-dien interactively: Nhóm ngành, Bản đồ nhiệt,
back to Nhóm ngành, group selector All→Group1. Captured desktop1440x900 and
mobile390x844. SStock uses narrow grouped panels with aligned ticker/SM/price/%/
volume, plus a separate industry heatmap. No authentication boundary was bypassed,
source code copied or proprietary artwork reused. SM, sector weighting and volume
semantics cannot be established merely by viewing its UI.

Compared the actual canonical Woofi1d7706a at the same desktop size. Its oversized
cards repeat explanation and metadata, losing scanning density. Three normal
ten-record VN30 pages were inspected. The reference pattern adopted is compact
columns, financial alignment and separate board/heatmap, with Woofi styling.

## Empty quote root cause and actual coverage

- Security metadata does not establish an observed price. Visible-only leases
  expire after75seconds; cached quotes retain their original age afterward.
- The previous UI also rendered a null pending client batch as Unavailable. New
  code distinguishes loading from a completed missing response.
- The old all-equities page observed now had7 current closing observations,
  3 stale and0 confirmed missing after completion. This does not reconstruct an
  earlier screenshot's exact state or prove an SSI defect.
- VN30:30/30 source-backed identities and30/30 priced,0 stale,0 missing under
  the existing closed-session policy. API observation22:52:43 ICT October16.
  All source timestamps14:45:00 ICT October16; SSI:FastConnect:ohlc:1m.
  These are cached closing observations, not LIVE or a fresh-provider certificate.
- Membership synced22:44:43 ICT October16 from SSI:FastConnect. Latest cached
  universe read1519 active equities; dynamic membership remains authoritative.
- Qualified Security fields contain no issuer sector. All30 total_volume fields
  are null. No ticker mismatch/unsupported-symbol defect in this VN30 sample.
  Broader universe, VN100 and HNX30 quote coverage was not measured.
- Metadata GETs and one ordinary cached quote read captured already observed
  symbols for replay. No force flag, full-market subscription, provider reset or
  ingestion command. Evidence retains source values, timestamps and sessions.

## Implemented correction

DEFAULT_SCOPE: existing SSI VN30 membership; one bounded30-symbol page.

- Compact36px rows in up to3 contiguous columns; ticker/research link,
  right-aligned VND price/change%, per-symbol source-time button.
- Separate compact3/5/6-column equal-area heatmap, with no capitalization claim.
- Inline source disclosure: company, exchange, original full timestamp, session,
  source, reference price and absolute change. Touch/keyboard controls.
- Sort by percentage descending/ascending, price descending or ticker.
  Current valid observations precede stale/missing metrics; null never becomes0.
- Current/stale/missing coverage and current-direction counts describe this
  selection only. No market breadth, aggregate return, sentiment, flow or SM.
- All-equity search/filters and pagination remain available. Typing search clears
  the initial index restriction visibly in the selector. No hardcoded issuer list.
- One existing LivePrices context/lease. View/sort/source controls do not fetch.
  Watchlist reuses the compact heatmap with its existing symbols/review state.
- VI/EN chrome, existing theme tokens, neutral stale/missing backgrounds.
- No provider, API, formula, database, Supervisor, collector or Technical change.

Operational bounds: one selected page<=30 versus existing API max50 and global
cache/demand cap256. Existing30s quote cadence,75s lease, hidden-page release,
cancellation, focus recovery and bounded closed-session checks remain unchanged.
No all-market stream. Warm coverage does not certify cold30-symbol bootstrap
latency; cold/read timeout behavior is still a pre-release qualification gate.

## Data dependencies deliberately not invented

Sector columns require authoritative issuer classification with source/version/
timestamp, coverage and a defined Python aggregate over aligned observations.
News sector tags cannot substitute. Session-volume display/sort needs qualified
cumulative/window semantics and units; minute volume is not session volume.
Capitalization area needs shares/freefloat methodology. SStock SM, sentiment and
institutional flow need reproducible qualified inputs, not inferred volume scores.

## Validation and unmet visual gate

TEST_RESULTS:171 frontend cases;170 PASS,0 FAIL,1 pre-existing optional Stock
Detail replay SKIP. Focused24/24 PASS. Typecheck PASS. Production webpack build
PASS. New pure/SSR tests cover bounds/default, identity/values, sort/columns,
stale/missing/invalid/zero, loading versus missing, language and both views.
Fixtures are synthetic; captured SSI values are replay, not a live session test.
The captured30-symbol source replay also passed all4 sort modes: all identities,
exact snapshot object/value/time preservation, no mutation and3 balanced columns.
That check executes presentation helpers only and does not certify visual layout.

The legacy Explore SSR fixture discarded QuoteMap and asserted the old ten-row
default. It now renders the real board over30 fixtures and checks the qualified
default, links and result boundary. No failing product assertion was hidden.

REAL_BROWSER_ACCEPTANCE: NOT_VERIFIED for new code.
DESKTOP_MOBILE: NOT_VERIFIED for new code.
EN_VI: automated PASS; browser NOT_VERIFIED.
LIGHT_DARK: existing tokens used; visual contrast NOT_VERIFIED.

Automatic approval review rejected the frontend preview launch: blocked by policy.
No frontend preview started. No retry, changed port/launcher, static-file browser
workaround or canonical deployment was attempted. The earlier isolated replay
HTTP fixture had no DB, credentials or forwarding, received no frontend requests,
and was closed gracefully afterward. Preview ports verified closed. A subsequent
shell request to save the report was also rejected; the report was saved through
the source-file patch tool without executing a preview.

Evidence directory: C:/Users/PC/.codex/tmp/woofi-market-board-20261016/.
BEFORE_SCREENSHOT: woofi-before.png, actual canonical UI1440x900.
This matched-size screenshot shows the old VN30 page3; original all-equities
capture is separately retained as woofi-before-original1280.png. Client widths
and scrollbars are recorded in comparison-dimensions.json.
REFERENCE_SCREENSHOT: sstock-group-board.png; sstock-heatmap.png; sstock-mobile.png.
AFTER_SCREENSHOT: NOT_AVAILABLE — preview execution denied.
Postimplementation side-by-side critique remains a mandatory unmet gate. No old
runtime or source rendering is presented as acceptance of the new UI.

## Release decision and safety

MAIN_SHA:1d7706a90f9270fa91e245c671ccb7ed9ce98777.
RUNTIME_SHA:1d7706a90f9270fa91e245c671ccb7ed9ce98777.
DEPLOYMENT_STATUS: NOT_PUSHED / NOT_DEPLOYED.

Supported read-only Status: Supervisor alive, desired_running=true; Backend,
Frontend and Collector alive. Two worker command rows are one Collector execution
root. Technical Pilot OFF. No lifecycle, configuration, journal, product DB,
credential or cooldown modification. FPT automation unchanged. The two unrelated
untracked frontend instruction files remain untouched. No new worktree.

REMAINING_PRODUCT_GAPS: actual browser density, contrast, responsiveness,
sorting/navigation/source/Watchlist interactions and cold30-symbol lifecycle.
Data-dependent features above remain explicitly deferred.

NEXT_SAFE_ACTION: separately permitted/manual preview of this exact checkpoint;
complete real desktop/mobile VI/EN/themes, cold-cache acceptance and side-by-side
critique before integration or controlled release. Do not use canonical cutover
to bypass preview policy. No automatic retry scheduled.
