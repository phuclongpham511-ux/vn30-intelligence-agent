# Home session polling recovery

A visible Home tab that received a closed-market response previously stopped
polling until a visibility change or reload. It could retain Friday's snapshot
through Monday opening. Existing documents also retain their loaded JavaScript
across a release update: the observed V1 Evidence links were resolved by document
reload, not by changing the approved V2 server build.

The shared presentation scheduler now checks the next weekday 09:00 Vietnam
opening, coalesces visibility/focus/pageshow revalidation, and deadlines each
request after 20 seconds. A hung request cannot stop recovery, and cancelled or
late responses cannot replace current data. Only one non-aborted request runs;
focus events reuse a pending request rather than restart it. Hidden/unmounted
clients cancel requests/timers and release their demand leases.

Recovery uses Asia/Ho_Chi_Minh independently of the browser timezone:

- Active visible index responses retain the existing 15-second cadence.
- Closed replies during weekday presentation hours permit at most three automatic
  slow rechecks per Vietnam date (1, 2, 4 minutes), then sleep until next opening.
  Foreground checks do not reset this budget.
- Unknown replies retain at most three startup checks at the caller interval,
  capped at 15 seconds. Unknown/error recovery then backs off at 1, 2, 4, 8 and
  15 minutes, with a 15-minute standby cap rather than endless minute retries.
- Recovery checks respect lunch, closing and weekends. A delayed timer after
  closing does not start a burst. Break replies during lunch wake at 13:00.
- Clock windows permit bounded checks; they are not exchange calendar evidence.
  Holidays/exceptional closures never become active from a timer. Provider labels,
  source timestamps, unavailable values and the existing freshness expiry remain
  authoritative. Failed reads still mark retained UI data stale.

Deterministic tests cover Friday/Monday, overnight/preopen/weekend boundaries,
delayed timers, focus/pageshow coalescing, sleep recovery, opening failure then
active recovery, hung/late reads, hide/show cancellation, holiday closed budgets,
unconfirmed evidence/backoff, lunch recovery and cleanup. These are synthetic
lifecycle tests, not fresh SSI acquisitions or certification of a holiday calendar.

This change does not update an already executing obsolete V1 document. Those
tabs still need navigation/reload. No runtime/ingestion/Technical EOD policy,
credential or production database change is required by this frontend fix.
