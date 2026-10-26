# Watchlist financial changes — private experiment

26 October 2026. Default off; no production activation, provider or LLM calls.

## Existing capability and scope

Targeted inspection, including WIP, found no Financial integration in the existing
Watchlist. Reuse `saved_financial_insights`, immutable MetricJournal packets,
`FinancialInsightsResponse`, `financial-attention-v1`, and existing browser-local
Watchlist receipt/revision identity. No financial formula or verification rule changes.

This first slice checks **annual revenue YoY**, one latest selected period pair,
for at most the **first five followed symbols in membership order**. It is not
complete financial monitoring or an issuer-independent definition of bank income.
Other symbols explicitly show NOT_CHECKED. No fallback to another source, nearest
period, arbitrary revision or live provider. All existing index/source selection
ambiguities fail closed until an operator updates the existing pinned index.

Updates require COMPARABLE, the existing noteworthy rule and non-fixture saved
evidence. READY with no items means no eligible noteworthy annual revenue change;
MISSING_DATA, INSUFFICIENT_COMPARISON, UNAVAILABLE and NOT_CHECKED remain distinct.
Every item includes exact periods, current/prior/delta, optional fractional change,
the existing attention criteria/threshold, missing information and source references.
The private grant does not upgrade public rights or certify publication vintage.

## Authorization and integration

The **existing supported personal-research servers** remain the only intended
host. No launch or permission-policy workaround is part of this change.

- Both existing private runtimes must explicitly set
  `WOOFI_WATCHLIST_FINANCIALS=1`; omission keeps the feature off.
- Backend also requires its unchanged personal router's development, opt-in,
  numeric-loopback socket peer and numeric-loopback hostname gates, plus explicit
  `WOOFI_PERSONAL_FINANCIAL_READS=sqlite` and existing journal/capture configuration.
- Frontend requires development mode and the existing server-established
  personal runtime/boundary flags. Literal 127.0.0.1:3431 Host/URL, same origin and
  fetch-site checks apply; forwarded Host/Forwarded headers are rejected.
- New private POST `/personal-research/watchlist-financials` accepts at most five
  normalized symbols. It never reads News/Community/Technical or modifies SQLite.
- The existing Next Watchlist proxy attaches the private result after the normal
  core response. Default/public responses remain unchanged. Stock Detail's optional
  `community_groups=true` shared read is not augmented.
- Private failures become only a financial UNAVAILABLE state, preserving original
  News/Community/Technical values. Private responses use private/no-store and
  noindex headers. Existing FastAPI public Watchlist routes never read financials.
- The frontend retains the existing browser-local receipt storage. No financial
  amount/document is written to browser storage; only existing ID/revision receipts.

The new Watchlist section is deliberately separate from **Read First**. Saved
financial periods and read time do not become new publisher timestamps or a new
importance ranking. The existing unreviewed-item count may include financial
items; it remains a count, not a score. No financial observation is marked reviewed
by navigation, refresh or source inspection.

## Identity and revision

`financial:<digest>` identifies source + ticker + frequency + metric + exact period
pair, independently of current receipt time. Revision hashes include the exact
capture/packet identity, insight, evidence and limitations. Same content has the
same revision; an explicitly selected revised source reopens the same item through
`isUnread`/`reviewUpdates`. New period pairs are new items. Missing/withdrawn/ambiguous
selection withholds an item without deleting old review receipts or claiming
cancellation. Existing News/Community/Technical and legacy review behavior remains.

## Validation and limits

Synthetic HTTP tests cover qualified revenue 800 → 1000 (+200, +25%), insufficient
scope, absent values, no coverage, duplicate imports, explicit revision selection,
ambiguous revisions, request bounds, peer/Host spoofing, production/default denial,
public-route exclusion and unchanged SQLite hash. Network sockets are forbidden
for external destinations in the new backend tests; Windows asyncio's internal
loopback socketpair remains available.

Frontend tests cover the actual Next proxy's public/private behavior, source
parity, bounded reads, malformed/private-failed responses, existing receipt reload
and correction semantics, and EN/VI rendered numbers/periods/criteria/limitations.
Read First logic is unchanged. The existing News SSR harness was updated only to
recognize the new child component; its assertions are retained.

Saved read-only smoke: FPT READY with no noteworthy annual revenue item;
TCB/SSI/VHM MISSING_DATA for this metric/pair selection. No new real-company
financial alert is claimed. Synthetic eligible cases demonstrate the update path;
they are not claims about those issuers.

Relevant backend regression: 241 tests passed. Full frontend regression: 347
passed, one pre-existing optional persisted Technical replay skipped. Typecheck and
isolated production webpack build pass. Evidence is local under
`C:/Users/PC/AppData/Local/Woofi/WatchlistFinancial-20261026T145916Z` and named
Watchlist financial test logs in the local temporary directory.

Browser acceptance is pending. No denied preview startup was retried, production
configuration changed, or private data committed. Further metrics/frequencies,
Read First inclusion, full-watchlist paging and live monitoring need separate scope.
