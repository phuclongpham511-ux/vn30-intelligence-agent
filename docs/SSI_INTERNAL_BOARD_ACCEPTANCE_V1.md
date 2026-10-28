# Internal SSI Board acceptance V1

Result: **PASS for saved-evidence/internal UI acceptance only**. No live-session
acceptance, SSI certification or public display/redistribution qualification.

Reviewed base: `7d40b38aa8074538475732236b690c688fbfe82b`.
Evidence date: 18 October 2026. Artifact directory:

`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/internal-ssi-acceptance-v1-08xbNl/`

## Environment and confirmed correction

Port 3410 had no listener at preflight. A new external offline frontend snapshot
was prepared with the existing acceptance preparer; all API handlers use its
closed fixture allowlist, with no backend fallback. One development process was
started on loopback 3410. No existing preview was stopped or replaced. Port 3400
and production were untouched. Development hot reload served the correction;
no preview handoff was needed.

The first actual browser request returned 404 despite explicit development opt-in.
Next 16.3.8 `base-server.js` populates `x-forwarded-host` from Host and
`x-forwarded-for` from the connection even on direct loopback requests. A temporary
snapshot-only diagnostic confirmed those exact headers. The old gate rejected
every such request. That diagnostic was removed.

The correction permits only a matching local Host and one exact loopback address;
foreign hosts/peers, mismatched Hosts, proxy chains and invalid ports fail closed.
The development/replay/opt-in gates are unchanged. Host headers are not an
authentication boundary; loopback binding remains a required precondition.
The permanent regression reproduced the failure before correction and passes now.

The previously dedicated Chrome profile was reused through Playwright, with
separate user-data-dir, remote-debugging pipe, sandbox enabled, synchronization
and extensions disabled. Process identity was verified before navigation; no
personal Chrome attachment occurred. Physical Escape closes the owned context.
The isolated browser connection closed once without a recorded Escape; the same
profile was resumed and its new process identity verified. Browser requests were
restricted to the local preview origin.

## Observed product evidence

- Saved ACB: floor **19,200**, reference **20,600**, ceiling **22,000 VND/share**;
  volume **5,160,300 shares**, value **106,488,260,000 VND**. The desktop table
  uses compact 5.16 M / 106.49 B (localized in VI); the evidence card preserves
  exact values and units. Multiplier remains 1, without deriving traded value.
- Trading date **2026-10-16**, explicitly stale. Source observation timestamp is
  unavailable; Summary fetched time is separately **2026-10-17T13:26:48.812223Z**.
  The raw JSON inspected through the browser exactly equals the saved source packet.
- Live last price and change remain missing and neutral, with no fabricated
  reference/current price or provisional ceiling/floor color promotion.
- Eight desktop/mobile × EN/VI × light/dark combinations rendered. Mobile client
  and document scroll widths both 375 at a 390 viewport (15px native scrollbar),
  with no horizontal page overflow. Exact KL/GT remain available in the evidence
  card on mobile; source dialog and raw receipts were opened through real controls.
- No page errors, internal API requests or external browser requests were observed.
  Internal ticker interaction opens evidence instead of mounting research acquisition.

`browser-matrix.json`, `browser-runtime-evidence.json` and actual PNG captures under
`screenshots/` record the browser observations. Representative captures:
`board-desktop-en-light.png`, `board-desktop-vi-dark.png`,
`board-mobile-en-light-evidence.png`, `board-mobile-vi-dark-evidence.png`,
`source-dialog-desktop-en-dark.png`, `raw-saved-source-receipts.png`.

## Invalid and time-state fixtures

An external snapshot-only harness reused the actual InternalBoard and Python
normalizer. It was visibly labelled **SIMULATED MUTATIONS / CLOCK, NOT LIVE SSI**;
it is not part of application source. The original route was restored afterward.
No synthetic record was promoted to an original observation.

All eleven cases passed: unchanged saved ACB; date-only/source-time-unverified;
known source time; two successive valid cumulative snapshots; contradictory bands;
conflicting venue; different trading dates; implausible totals; missing totals;
unqualified transport packet. Invalid normalization returned no packet and the
actual UI showed its rejection state without financial values. The unqualified
packet was rejected by the frontend transport gate. Stale saved evidence, missing
live quotes and rejected qualification remained distinct states.

The two simulated snapshots displayed 1,000,000 then 2,000,000 shares, never
3,000,000. These cases prove replacement/presentation behavior, not live SSI
increment/reset/finality semantics. `scenarios.py`, `scenarios.json`,
`scenario-browser-results.json` and `simulated-*.png` retain the labelled evidence.

## Server access control

Actual development HTTP requests verified:

- Removing opt-in returned HTML 404; URL parameters could not enable it.
- Foreign Host, foreign forwarded Host/peer, and chained forwarding returned 404.
- Explicit local opt-in returned the saved Board.
- Public home/replay routes exposed no provisional contract or ACB payload;
  the guessed saved-JSON URL returned 404. Public ACB API remains unavailable under
  the offline fixture allowlist, and exposed no provisional data.

Environment changes were tested after Next's reload; a request while reload was
in progress still used the previous enabled configuration. No default-off claim
is based on that transitional request.

A separate optimized production build had explicit flag=1 and replay configured.
Its **real Next production request handler** was exercised with in-memory Node
IncomingMessage/ServerResponse streams, without opening a listening socket or
starting a second preview. HTML returned 404. RSC used HTTP 200 with the framework's
`NEXT_HTTP_ERROR_FALLBACK;404` payload; neither response exposed provisional data.
The same RSC denial behavior was checked over the running default-off dev server.
No network/provider calls occurred. This is server enforcement, not client hiding.

`server-access-results.json` and `production-gate-build/production-gate.cjs` retain
the distinction between wire status and route denial. No production service was
used for these tests.

## Validation and scope

- Frontend: **259 passed, 1 existing optional skip, 0 failed** (260 total).
- Provisional Python contract: **37 passed**.
- Legacy unqualified Summary regression: **20 passed**, separate run.
- Typecheck: PASS. Separate optimized production webpack build: PASS.
- Correction scope: local-header gate, route call, permanent focused regression,
  and documentation. Existing product data contracts and qualification guards
  were not weakened. No Watchlist membership/review consumer was mounted.

Public release still requires the endpoint-specific semantic, timing, rights,
normal-session and controlled integration gates in the provisional contract.
No new provider requests, acquisition worker, production change, deployment,
Supervisor/Collector/SQLite operation or cooldown reset occurred. Technical Pilot
and FPT automation settings were not changed.
