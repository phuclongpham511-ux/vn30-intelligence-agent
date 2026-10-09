# D5-B1 EOD runtime consumer V1

Readiness: **PARTIAL**. The consumer and fixture-backed real-adapter integration
are implemented. The existing repository does not provide a verified exchange
session calendar, immutable market receipt archive or episode checkpoint. Calendar
absence returns a typed diagnostic with actual normalized observations; it does
not generate a fake valid packet. No live-source verification was performed.

## Public service and developer invocation

`src.services.technical_eod.evaluate_technical_eod_packet(ticker, trading_session,
evaluation_as_of=..., generated_at=..., db_session=..., provider=None,
history_read=None, calendar=None, history_start=None, corporate_actions=None)`
returns the existing `TechnicalDailySignalPacket` or a `TechnicalEODDiagnostic`.
Both are typed frozen Pydantic models. `summarize_eod_result(result)` exposes packet
state, event/selection/overflow counts, unresolved checks and bounded provenance,
or diagnostic status/reasons/available-observation count. It never prints exception
details, credentials or configuration.

The smallest developer entry point is this service invocation, not a new route:

```python
from datetime import datetime, timezone
from src.services.stocks import get_market_provider
from src.services.technical_eod import (
    read_eod_history, evaluate_technical_eod_packet, summarize_eod_result,
)

# db_session: existing application Session; ticker/session/history_start: caller
# request. calendar: VerifiedSessionCalendar from independently verified venue
# evidence, or None to inspect the honest unavailable-calendar diagnostic.
read = read_eod_history(ticker, get_market_provider(), history_start, session_date)
as_of = datetime.now(timezone.utc)  # Explicit cutoff AFTER actual acquisition.
result = evaluate_technical_eod_packet(
    ticker, session_date, db_session=db_session, history_read=read,
    calendar=calendar, history_start=history_start,
    evaluation_as_of=as_of, generated_at=as_of,
)
print(summarize_eod_result(result))
```

A caller asking for an earlier cutoff cannot acquire data now and backdate it.
If the consumer's optional convenience acquisition observes data after the
requested as-of, it returns `history_observed_after_cutoff`. For current
reconstruction, acquire first and supply a subsequent explicit timestamp as above.
For an earlier operational cutoff, only an actually preserved receipt can support
the request. `EODHistoryRead` is a receipt sidecar over existing normalized
`HistoricalObservation`/`MarketBar`, not a new vendor client or archive loader.
The consumer never auto-loads research datasets, manifests or protected cases.

## Actual source contracts

Acquisition reuses `src.services.data.history` and the configured
`SsiMarketDataProvider.get_history`. SSI's existing adapter provides:

- Dynamic ticker requests; daily OHLC transport/pagination and numerical/range
  validation; qualified adjusted prices VND ×1 and shares volume ×1.
- Dated bars before the actual Vietnam today, bounded ordered ranges ≤730 days,
  at most 16 upstream pages and a five-minute bounded process cache.
- Rejection of conflicting duplicates and safe provider error text; identical
  repeated upstream records are already deduplicated by the provider.

It does **not** return bar venue, exchange-calendar completeness, vendor revision
IDs, record publication/receipt times or historical vendor vintages. A MarketBar
cannot prove an absent bar means holiday, suspension or provider loss. SSI provider
normalization rejects malformed required numeric fields for the whole request;
the consumer does not recover these as invented partial prices/volumes.

The consumer reads exactly one active ordinary equity from the existing `Security`
cache, checking SSI source, venue, instrument type and `last_synced_at <= as_of`.
It does not seed stocks, update the universe or fetch every security. The cache is
current metadata, not certified historical ticker/venue identity; that limitation
stays visible. Unknown cached identity is incomplete evidence, not proven invalid
listing. Syntax-invalid ticker/session/timestamps are INVALID_REQUEST.

## Dates, evidence and missingness

The target must be before the Vietnam evaluation day; today's bar is rejected
even after close, preserving existing SSI completed-daily policy. No latest-bar
substitution, live quote ingestion, future-date use or raw/adjusted mixing occurs.
Wrong identity, currency, basis, volume units, duplicates, malformed normalized
records or calendar coverage fail explicitly. Missing current rows with a valid
calendar flow to the unchanged D1/D4 unresolved checks.

`observed_at` records actual operational reader receipt, including a cache read;
it is never fabricated from the evaluation cutoff. `fetched_at` stays null when
the existing cache does not expose its upstream fetch timestamp. A content digest
is a logical read fingerprint, not a SSI vendor-vintage ID. Optional preserved
operational snapshots remain distinct from current reconstruction and are not
promoted to certified historical PIT evidence.

Finalized daily availability uses the approved labelled EOD assumption. Existing
HistoricalObservation stores the assumed timestamp; the adapter preserves its
assumed basis instead of copying that timestamp into D1's audited `available_at`.
Published availability keeps its actual field and cannot be overridden by an EOD
assumption. Unknown/late availability stays unresolved. Price/volume comparability
can be explicitly withheld by session; zero shares remain genuine observations.
There is no guessed invalid-row repair or missing-as-zero fallback.

## Calendar and bounded history

`VerifiedSessionCalendar` carries venue, declared sessions, covered interval,
source reference/version and actual knowledge time. The caller is responsible for
the verification behind that source reference; a self-assigned label alone does
not certify it. It must match metadata venue and cover the requested bounded
interval, with unique target-inclusive sessions and knowledge no later than as-of.
No weekdays/holidays or adjacency are inferred from returned bars.

Queries span at most 730 calendar days; at most 512 session records are processed.
Default start is the verified calendar's covered start clipped to that bound,
or target minus 730 days when calendar evidence is absent. These are resource
bounds, not factual quantile windows or arbitrary episode gap rules.

D1 itself selects up to 252 valid comparable strictly prior observations, minimum
60. A full 252-return reference needs 254 closing prices including current; the
consumer does not truncate to 252 raw bars. Missing/invalid comparability may leave
less usable history inside the bound, which remains unresolved. No expanding
whole-history fetch or checkpoint invention is introduced.

The bounded read explicitly declares an unknown episode left boundary. D4 then
uses the existing helper's conservative mode: initial warm-up cannot invent an
old price/volume anchor. A verified normal observation followed by re-entry or a
verified new transition can establish a new anchor. Known calendar closures allow
adjacency; missing expected rows leave relationships unresolved. The original D4
default and all previously emitted identities for callers without this marker
remain unchanged. There is no second episode algorithm.

## Scoring and runtime pipeline

Contiguous valid native prefixes reuse `technical_history`; exact adjacent price
pairs reuse `market_snapshot`. Existing `build_context` supplies empirical-v0.1
own-history midranks over its last 252 declared feature records (minimum 60 valid
values). That V0 population remains separate from D1's last-valid-observation
population. Current is appended only after its scoring context is built.
Market-relative and sector channels are null because a verified aligned reader
is unavailable; no unrelated benchmark security is fetched. Factual recurrence
history is likewise unavailable and explicitly labelled; no legacy permissive V0
detector is run to manufacture recurrence or reset a delivery ledger.

One compatibility guard in `build_context` now leaves relative volume null when
current volume is missing. For present volume its formula is unchanged. The
existing z-score helper already handles missing current values.

Pipeline: normalized reader + explicit calendar → native scoring context → one
`evaluate_d4_market_events` call (its actual D1 factual runtime) → existing V0
scoring and CA enrichment → one `build_technical_daily_packet` call. No duplicated
factual predicate, ranking, threshold or indicator implementation is added.

Consumer limitations enter upstream provenance before D5 hashing. D5's additive
pass-through preserves them in packet limitations without changing ranking or
delivery. Event/episode IDs, all current events, Top 3, overflow and the three
packet states remain intact. New source/context payloads can correctly change
packet evaluation identity without rewriting semantic event identity.

The existing CA repository is read with the evaluation cutoff. Incomplete coverage
remains UNKNOWN. Optional CA source failure yields UNKNOWN/source_unavailable
and a limitation; it does not remove otherwise valid events or alter scores.
No CA notice, context history or Dividend source is written.

## Diagnostics, resource usage and readiness

Diagnostics distinguish INVALID_REQUEST, INCOMPLETE_EVIDENCE, SOURCE_UNAVAILABLE
and INFRASTRUCTURE_FAILURE. They do not masquerade as a successfully evaluated
no-change packet. Existing provider sanitization does not distinguish every
upstream timeout from malformed payload; that remains a source-contract limitation.

Work is one cached equity lookup, one bounded history request if needed, linear
native/context preparation and bounded D4 prefix reconstruction. D4's existing
prefix replay is quadratic within the ≤512-record cap; this is an on-demand
single-ticker seam, not a full-universe startup computation or production worker.
There is no new persistent cache, database table, packet archive or route.

The reconciled worktree has neither a local `.env` nor `vn30.db` at verification.
No credentials/database were copied from Downloads. Tests use in-memory SQLite,
normalized synthetic observations and SSI SDK + MockTransport with realistic
OHLC envelopes. They prove the adapter chain and guards, not live SSI freshness,
calendar certification or production readiness.

## Validation and Git preservation

Commands run from the reconciled worktree:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_technical_eod_consumer.py -q
.venv/Scripts/python.exe -m pytest tests/test_technical_eod_consumer.py tests/test_d1_runtime.py tests/test_d4_runtime.py tests/test_d5_packet.py -q
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m scripts.check_technical_identity
git diff --check
```

Focused consumer suite: **36 passed**. Combined runtime chain: **156 passed**
(before the final developer-summary test was added). Final full backend:
**851 passed**, including every D1/D4/D5-A, benchmark, Materiality, Bollinger,
historical evaluation and corporate-action regression. One existing Starlette/httpx
deprecation warning remains. Identity guard passed across nine files; full diff
and six milestone-file whitespace checks passed. Initial red runs confirmed the
missing service and exposed the relative-volume missing-value compatibility defect;
assertions were retained while that guard was fixed.

Branch and HEAD remain `codex/technical-development-reconciled` /
`e64986e0cb011d8af40a122e14d5bb47f540ba22`. Initial status: 15 modified tracked,
55 untracked, index empty. Final: 16 modified tracked, 58 untracked, index empty.
Of 70 pre-existing dirty files, 68 kept exact byte hashes. Only existing
`src/materiality/episodes.py` and `src/materiality/delivery.py` gained the narrow
compatibility hooks described above. `src/evaluation/context.py` adds the one-line
null guard; the service, tests and this report are new. The original Downloads
repository, credentials, Dividend/frontend/calibration WIP, branch pointer and
index were untouched. No commit, push, stash, reset, rebase or cleanup occurred.

Next prerequisite is verified venue/session evidence with an operational receipt
contract. D5-B2 may then expose a narrowly scoped read-only packet/diagnostic API
or explicitly versioned persistence; neither is implemented by this task.
