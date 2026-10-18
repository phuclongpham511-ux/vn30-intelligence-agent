# Product Acceptance V1 — isolated browser results

18 October 2026. Base checkpoint: 8220af0617f98a811ddb1287cd1be978458adf0c.

BROWSER_ISOLATION: VERIFIED
PRODUCT_ACCEPTANCE: PARTIAL

## Browser ownership and boundaries

Used installed Playwright 1.62.1 with the installed Chrome executable, a newly created empty profile under the acceptance artifact folder, synchronization/extensions disabled, and debugging through a private pipe. No connection or attachment to a personal browser was made. The original context contained only about:blank and zero cookies. Before navigating, the root executable, profile command line, creation time and parent PID were checked. Roots were PID 5192 and, after a tool-timeout recovery, PID 5136 sequentially in the same dedicated profile. The tool timeout closed the first browser; no forced termination or host-policy workaround was used.

All page requests were restricted to http://127.0.0.1:3410. No off-origin page requests occurred. A trusted Escape key handler was installed to stop/close the test context; no physical Escape interruption was received in this run. The test browser was closed using its context.close() operation and a final process census found zero matching test-browser roots. Personal windows/tabs/profiles were not targeted. Test storage used only the four woofi.acceptance.* keys.

## Actual flows exercised

| Flow | Observed result |
| --- | --- |
| Served Heatmap correction | PASS: actual EN text reads “Read left → right across each row, then top → bottom.” and VI reads “Đọc từng hàng từ trái → phải, rồi trên → dưới.” |
| Stock Detail / Overview | PASS for DEMO identity, ticker/exchange/name, source metadata, cross-ticker navigation and explicit missing business/classification/history states. Original unknown data was not fabricated. |
| Company News | PASS: one primary story with two source articles; publication and observation times separate; weaker stored ticker relevance disclosed; expanding evidence and switching tabs did not review the story. |
| Community | PASS: one DEMO/unverified discussion, original link attribution, publication/observation times, missing replies versus real zero views, no invented sentiment. |
| Watchlist add/remove | PASS using actual header Follow, ticker search/selection and Follow BBB controls. Removing BBB preserved AAA review receipts. |
| Explicit review / persistence | PASS: AAA story 1→0 unread while Community stayed 1; Community review then persisted to zero unread after reload. Adding BBB produced two unread items independently of AAA's receipts. Mobile story review reduced BBB 2→1; navigation/reload and Refresh updates preserved it, with AAA still reviewed. |
| Saved FPT financial guards | PASS: annual and quarterly navigation; all unsupported/unqualified metrics, comparisons, charts and statement amounts remain withheld; source/read time and unknown reporting basis disclosed. No compatible valuation inputs were inferred. |
| Corporate Action states | PASS for four supplied DEMO states: fixture, pending, unresolved correction and withdrawn. Dates/terms remain unavailable; filters and source disclosure work; fixture documents are not invented. Original-source confirmed/incomplete fact rendering was not browser-tested because no authentic observation receipt was supplied to this replay. |
| ABC DEMO Financial Analysis, unmodified replay | FAIL: client page error “Cannot read properties of undefined (reading 'includes')”. Payload lacked available_period_types, but the client parser accepted it; the frequency toolbar dereferenced it. |
| ABC after diagnostic metadata repair | PASS only as a labelled browser-local diagnostic: added missing fixture metadata without changing any financial amount, source observation or qualification. DEMO EPS/revenue/zero profit/ROE and unavailable P/E/cash flow rendered; unsupported quarterly/TTM controls disabled; amount-unit switching worked. This does not certify the unmodified server or the new client guard. |

Desktop 1440×1000 and mobile 390×844 were exercised, with EN/VI and light/dark views across the covered research flows. This is not an exhaustive Cartesian matrix for every component. Financial screenshots cover saved FPT EN/dark desktop and VI/dark desktop/mobile. News/Community and actions include VI/light mobile; Watchlist includes EN/dark desktop/mobile and VI/light mobile. Previously completed Market Board acceptance was not repeated beyond the Heatmap wording check.

Layout measurements found no horizontal document overflow in checked mobile source/action, news and Watchlist states. Initial apparent clipping of the Follow control was not reproduced after layout/font settling: both action children fit inside the measured header. No CSS change was made based on that suspicion. Full-page screenshots may place sticky headers at their captured scroll position.

## Confirmed defect and local correction

The full Financial Analysis view requires reporting-frequency metadata, whereas the prior shared fixture tested only its overview snapshot and omitted that field. Two narrow changes address the demonstrated failure:

1. Complete the shared synthetic fixture's transport metadata, without adding financial facts or upgrading DEMO qualification.
2. Reject missing, non-array or unknown frequency metadata in financialEngineData before the response reaches the view. The existing request catch path then presents the scoped financial load error instead of crashing the page.

New regressions cover malformed frequency metadata rejection, the actual loading hook's error path, and rendering the complete replay financial view in EN/VI. Existing financial bases, units, valuation restrictions, corporate-action verification and Watchlist semantics remain unchanged.

Validation: 34 focused tests PASS; source typecheck PASS; isolated snapshot typecheck and optimized Next.js webpack build PASS; git diff --check PASS. No backend code changed, no provider probes or unrelated test campaign. The compiled correction is prepared in verified-fix-build, but it has NOT been started. The running ready-build on 3410 was neither modified nor restarted and its offline health endpoint remained HTTP 200.

## Evidence

24 new real-browser PNGs, isolated storage receipt evidence and process ownership records are under:

C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/product-acceptance-v1/isolated-browser/

Key captures:

- 02-heatmap-corrected-en.png / 03-heatmap-corrected-vi.png
- 04-aaa-overview-desktop-en-dark.png
- 05-aaa-news-community-unread.png / 06-aaa-story-reviewed.png
- 07-watchlist-unread-discussion.png / 08-watchlist-reviewed-after-reload.png
- 09-watchlist-cross-ticker.png
- 10-abc-financial-client-error.png — unmodified served replay failure
- 11-fpt-unqualified-financials-en-dark.png / 12-fpt-quarterly-source-guard.png
- 13-actions-all-states-desktop.png / 14-actions-mobile-vi-light.png
- 15-news-community-mobile-vi-light.png
- 18-abc-demo-BROWSER-ONLY-fixture-metadata-repair.png / 19-abc-demo-units-BROWSER-ONLY.png — explicitly diagnostic, not an installed fix
- 20-fpt-guards-mobile-vi-dark.png / 21-fpt-guards-desktop-vi-dark.png
- 22-watchlist-mobile-unread-en-dark.png / 23-watchlist-mobile-reviewed-persistence-en-dark.png
- 24-watchlist-mobile-vi-light.png / 25-company-overview-mobile-vi-light.png

ISOLATION.json and BROWSER_RUN.json contain the owned profile/process details, scoped storage receipts and screenshot inventory. The profile contains only this test's synthetic/local replay state; the user's Watchlist was not read or changed.

## Release/acceptance gate

Do not mark Product PASS from the diagnostic response override. The corrected fixture and client guard need a separately authorized handoff of 3410 to verified-fix-build followed by an unmodified ABC Financial Analysis browser check and a malformed-response error-state check. No additional architecture or redesign is required for this defect.

Live SSI/financial-source acceptance and authentic original-publication action verification remain separate. No production ports, Supervisor, Collector, SQLite, acquisition state, Technical Pilot or FPT automation were changed. No server restart, push or deployment was performed in this run.
