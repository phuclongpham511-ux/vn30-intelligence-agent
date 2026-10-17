# Stock Detail V1 — company overview and recorded distributions

Development base: `e01066c47dddbddf9bf3bae980c502c263df0902` in the existing
Market Workspace checkout. No V2.2 reset, new worktree or Stock Detail redesign.

## Implemented increment

StockHeader preserves the full ticker, source-provided company name and exchange,
with wrapping for long identities and explicit missing-name text. EN uses the
provided English name when available, otherwise the original name; no translation
or invented issuer name. Existing LivePrice and FollowStock remain in place.

CompanyOverview replaces the existing inline identity panel. It reuses the same
cached Security record and synchronization receipt, distinguishes cache time from
issuer publication, and exposes original metadata source. No profile or financial
request is added. Business description is unavailable in the existing identity
contract. Industry/sector remains unqualified for display; saved SSI ICB availability
does not activate classifications or rights. An explicit link opens the existing
lazy financial-analysis tab, whose actual statements, ratios, publication dates and
missing-data behavior remain authoritative. Existing daily analytics are retained.

The existing Dividends & corporate actions tab now presents one compact responsive
record per stored source observation, rather than an eight-column table plus a
duplicate evidence timeline. A local filter selects all records, dividends/bonus
shares, or rights/other actions without a new request. Counts refer to returned
observations, never unique paid dividends or complete market coverage. Source order
is preserved; the API still returns the latest50 observations with has_more and
INCOMPLETE coverage. It is not an execution-date calendar.

Each record retains the existing original text, source title, verification note,
revision, announcement precision, source update/receipt times and safe source links.
Receipt timestamps are labeled ICT; date-only event fields remain dates. Verified
source observations, pending verification, withdrawals and DEMO fixtures remain
distinct. A reported payment date never proves payment has occurred.

## Supported facts and safety gates

The existing CorporateActionNotice/Observation and ActionTerms contracts support:

- cash_dividend: original cash_vnd_per_share in VND;
- stock_dividend / bonus_shares: original new_shares_per_old, not a computed percent;
- rights_offering / additional_issuance: original new_shares_per_old and
  subscription_price_vnd where provided;
- effective/ex-rights date, record date and payment date independently;
- original announcement date/timestamp and observation provenance.

Other types never inherit unrelated monetary/share terms. No yield, historical
return, adjustment factor, ex-date-from-record-date, payment confirmation or amount
aggregation is calculated. Missing is unavailable; a genuinely reported zero stays
zero. Tiny ratios never round into a fake zero. Invalid/nonfinite/negative/unsafe
numeric values and malformed calendar dates are withheld.

Trust requires explicit verified=true, withdrawn=false, is_fixture=false and a
nonempty source. Missing flags do not confer trust. DEMO, withdrawn and pending
records retain original evidence but cannot publish confirmed event dates/terms.
A page containing a different instrument fails closed before displaying records.
Status text and the display gate use the same qualification decision.

## Reused services and validation

Routes remain `/stocks/[symbol]` and the existing
`/stocks/{symbol}/corporate-actions?limit=50` read. Company identity comes from the
existing cached universe read. The corporate-action repository's latest-revision,
as-of, read-only behavior is unchanged. No backend, provider, scheduler, acquisition,
schema or product-database code was changed. No new polling or price lease.

Focused frontend validation covers company/header rendering in EN/VI, missing and
unqualified profile fields, source timestamps, all supported action types, zero,
small ratios, invalid values/dates, category filters, provenance, mixed identities,
deferred financial reads and existing financial/research behavior. Existing API
integration tests use an in-memory SQLite test database and verify SELECT-only
reads, revisions, withdrawals, future-receipt exclusion and pagination. No product
SQLite is opened by these tests.

Validation result: **53 frontend tests PASS**, **3 read-only API integration tests
PASS**, typecheck PASS and supported webpack build PASS. The API run reports one
existing Starlette/httpx deprecation warning. Exact evidence is recorded in the
sibling visualization artifact directory `stock-detail-v1/FINAL_REPORT.md`.
The build uses a separate
frontend snapshot and separate .next output; it does not update running preview
assets. Responsive desktop/mobile rules and shared light/dark tokens are implemented,
but browser acceptance is **BLOCKED** by the existing execution policy and was not
attempted again. Automated rendering is not browser or live-data acceptance.

No live dividend coverage or provider display rights were newly certified. No SSI
probe, production process operation, Supervisor/Collector/SQLite change, cooldown
reset, production-pin change, push or deployment. Technical Pilot OFF / FPT PAUSED
remain required and were not modified.
