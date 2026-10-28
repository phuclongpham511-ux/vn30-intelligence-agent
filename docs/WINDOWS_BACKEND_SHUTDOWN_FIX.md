# Windows Backend peer-reset shutdown correction — 2026-10-15

Scope: source-only Backend correction on base
`4c507655be908e12b63ca1a0d98d575d6c917ae1`. No canonical installation,
orphan signalling, database writes, Supervisor activation or startup registration.
The production runtime remains pinned to `df05ccd` and launch-blocked.

## Confirmed cause

The production Backend log contains an exception in
`_ProactorBasePipeTransport._call_connection_lost(None)` at CPython 3.12.10's
`proactor_events.py:165`: `socket.shutdown(SHUT_RDWR)` raises
`ConnectionResetError [WinError 10054]`. This interrupts the original callback
before `socket.close()`, `server._detach()` and the completed-callback flag.

A fresh identity-qualified, nonblocking Python stack read found native Uvicorn
16976 inside the event loop. A bounded read-only symbolic coroutine walk,
validated against a local CPython coroutine first, resolved its pending task as:

`Server.serve -> _serve -> shutdown -> wait_for -> _wait_tasks_to_complete -> asyncio.Server.wait_closed`.

The event-loop wait has no timer. These findings match a leaked server attachment,
not a current Python logging-lock or SQLite query deadlock. The listener is already
closed, but Uvicorn cannot reach ASGI lifespan shutdown; pooled SQLite resources
remain live. Changing the supervisor wait from 45 seconds would not repair this.

Historical/current ownership remains observer 29184, venv redirector 9764 and
native Backend 16976, with original creation identities. Credential-helper
parents exited during the earlier control event. The redirector waits on native
Python; the observer cannot safely forget those members. No additional signal,
suspension, process-memory write or handle closure was performed on them.

## Minimal correction

`main.py` installs an idempotent process-local hook from
`src/services/windows_socket_cleanup.py` before Backend startup completes.
Only Windows `_ProactorSocketTransport._call_connection_lost` is wrapped.
The original CPython callback still owns ordering, close, detach and duplicate-call
handling. A temporary socket facade tolerates `ConnectionResetError` **only from
its shutdown operation**, allowing the original cleanup to continue.

Protocol errors, socket-close errors and unrelated shutdown errors propagate.
On an interrupted callback the original socket reference is restored. Pipe
transports, event-loop choice, signals, deadlines, worker ownership, generation
fencing, stopped intent and collector mutex are unchanged. No installed Python
or third-party library file is modified. Non-Windows imports do nothing.

This is a compatibility hook into a private CPython transport API. Validate it
again before changing Python/asyncio versions. Evidence here covers Windows
CPython 3.12.10 and existing Uvicorn 0.53.0. It is not permission to patch running
processes, ignore unknown teardown failures or claim arbitrary shutdown hangs fixed.

## Reproduction and validation

- Unmodified WMI -> actual PowerShell observer/rolling pipeline -> synthetic
  credential-free helper -> real venv redirector/Uvicorn/temporary SQLite shut
  down correctly in the simple control. An isolated real application control,
  with external sockets blocked and provider reads stubbed, also exited. The
  process hierarchy or logging pipeline alone did not reproduce the hang.
- Two bounded natural TCP-RST controls did not reproduce this OS error. They
  are not claimed as positive reproductions of the production failure.
- Deterministic injection of the exact recorded shutdown exception into an
  actual native CPython transport/server reproduced `wait_closed` timeout with
  leaked attachment before the fix. The same gate passed after the fix.
- Nine new regression cases cover reset cleanup, idempotence, unchanged pipes,
  non-Windows behavior, error propagation and real native process lifecycles.
  Three lifecycle scenarios run twice each: normal HTTP close, recorded-reset
  injection, and reset plus explicitly delayed lifespan shutdown. All five owned
  processes must exit, with one qualified control request, no fixture rescue,
  a committed in-flight SQLite row, integrity/FK checks and native exit codes.
  The delayed scenario also proves graceful completion after helper parents exit.
- Existing relevant coverage includes supervisor Start/Stop serialization,
  generations, ownership/unknown-owner rejection, collector singleton/mutex,
  lock inventory, JSON sharing, PATHEXT bootstrap, live-market and health APIs.
  No frontend or full application suite is required by this localized change.

The first expanded run was 205 PASS / 3 FAIL. Two failures were deterministic
Windows MAX_PATH errors under an overlong test root (265-character ordinary open
failed; the same new temporary file with an extended path succeeded). The third
fixture expects a venv `sys.prefix`, whereas the initial runner used base Python
with development packages on PYTHONPATH, creating a nonexistent Scripts/python.exe
fixture path. No assertion/timeout was changed; only those three cases were
revalidated with a short temporary root and the existing development venv.
That targeted run passed all three cases in 17.69 seconds. Current passing
evidence covers all 208 unique relevant cases, including all nine new cases,
with zero skips or unresolved failures. This is split-run evidence, not a claim
that the first 208-case invocation was clean (it took 95.57 seconds).

The separate test collection error was a third-party `tests` package shadowing
the repository's namespace. The external runner explicitly binds the real
repository tests directory; no test or application code is substituted.

## Safety review and operational handoff

Review covered hook scope, callback restoration on exceptions, unchanged pipe
transport, single detach, no hidden protocol errors, startup installation,
finite fixture rescue (asserted unused), and preservation of all supervisor
ownership/control code. The fix does not issue signals or manage processes.

Evidence is saved under
`C:\Users\PC\.codex\tmp\woofi-backend-shutdown-20261015`:
production stack/await-chain, red/green gate, new/native and final regressions,
validation-environment diagnostics and before/after runtime snapshots.
Only symbolic stack/wait metadata is retained; no environment, credential values,
application frame locals or full process-memory dump is stored.

The old three processes and DB holder remain unresolved. Production recovery
requires a separate explicit operational decision; source integration does not
release those handles or authorize a launch. Preserve journals, stopped intent,
the newest live database and the blocked launch gate. No Technical/FPT changes.

References:
[CPython Proactor cleanup](https://github.com/python/cpython/blob/v3.12.10/Lib/asyncio/proactor_events.py),
[Server wait_closed](https://github.com/python/cpython/blob/v3.12.10/Lib/asyncio/base_events.py),
[read-only profiler mechanism](https://github.com/benfred/py-spy#how-does-py-spy-work).
