# Financial SQLite storage foundation V5.5

Branch: `feature/financial-data-intelligence`. Base: `e2e42f6`.

V5.5 extends the existing dedicated `MetricJournal` with an explicit, versioned
SQLite mirror of saved financial packets. It does not activate SQLite in HTTP
reads, change financial formulas, acquire data, or modify the product database.
The existing saved-capture APIs, private controls, source adapters and frontend
remain the serving path. The two pre-existing tooltip edits remain uncommitted.

## Storage contract

SQLite `user_version=1`, four tables total:

| Table | Contents |
|---|---|
| `financial_metric` | Existing immutable `MetricObservation` identities/payloads and period/frequency index; retained compatibly |
| `financial_capture` | Immutable source capture revision, original SHA-256, normalized packet digest, ticker/source, packet/receipt header and import provenance |
| `financial_statement` | Every annual/quarterly `StatementObservation`, including mapped financial fields, source field codes, full line hierarchy/labels, raw values, nulls, scope/basis, metadata and document references |
| `financial_selection` | Explicit selected revision per ticker/source/statement/period/frequency/scope/basis |

Company type/profile, source version, fixture flags and receipt statuses/URLs/hashes
remain in the existing packet header. Source documents and original captures stay
in their private archive; the database retains their references, not new copies of
PDF binaries. No company/source/industry master-data platform or new schema for
financial calculations was added.

`initialize()` only upgrades an empty database or the recognized dedicated legacy
journal. It rejects application tables, unexpected columns and unknown versions.
A legacy upgrade takes an exclusive new-path SQLite backup before transactional
DDL. Re-running initialization is a no-op. Existing metric identities/payloads are
not rewritten. `backup()` never overwrites a destination and supports restoring a
snapshot into another new path. Readers use `mode=ro` and `query_only=ON`.

Each packet import is one transaction. Re-importing the same source capture and
normalized packet inserts nothing. Changing a packet under an existing source
capture hash is rejected; a changed source capture must have its own hash/revision.
This intentionally does not provide automatic parser-version remapping under the
same raw hash; such a future migration needs an explicit normalization-version
contract. Unrecognized/corrupt evidence fails visibly; completed earlier packet
transactions remain resumable.

Short candidates append new periods without removing old ones. Overlapping
revisions are retained, with the first accepted period remaining selected.
`select_revision(capture_id, statement=..., period=...)` is the explicit library
operation to change selection; it never deletes the older capture. Scope, basis
and source variants have separate keys and are not reconciled or merged.

`read_packet(capture_id)` returns one exact source revision, including receipt and
statement ordering. `selected_statements(ticker, source, ...)` inspects accumulated
periods with their individual capture and receipt provenance. It deliberately does
not synthesize a mixed-vintage `FinancialPacket` or claim cross-period
comparability/PIT certification. There is no new web endpoint or production toggle.

## Limits and incremental updates

- **Source persistence:** no period-count limit in the new statement store. Tests
  preserve 34 and 60 quarters, as well as future new quarters.
- **Legacy normalized importer:** its hardcoded 20-period request is now 40, the
  existing Financial Engine maximum. It also persists the entire base packet
  before materializing metrics. Histories beyond 40 remain complete in base
  storage; their older derived projections are not yet materialized by this CLI.
- **Financial Engine:** unchanged, accepts up to 40 response periods.
- **Private financial route:** unchanged, up to 40; defaults to 34.
- **Other stock financial routes/frontend display limits:** unchanged.

The tested incremental example starts with 2018-Q1–2026-Q2, then imports a candidate
covering 2025-Q4–2026-Q3. The selected quarterly store reaches 35 quarters; revised
overlapping amounts remain separate and require explicit selection. No eligible
new period is rejected because the candidate is shorter. A separate test exercises
`--mirror --packet` and indexed `capture_history` through the real saved validators.

The existing acquisition batch still protects its legacy file/index history with
the shorter-history guard. V5.5's offline SQLite import is independent of that
guard: pass an already saved canonical candidate using `--mirror --packet` to
accumulate it. Live acquisition-to-database integration and scheduled refresh are
future work; this release neither changes acquisition behavior nor calls providers.

## Verified local import

Database:

```text
C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/woofi-financial-data/.local/financial-research-v55/financial.sqlite
```

It began as a SQLite Backup API copy of `.local/financial-metrics.sqlite`, preserving
all **23,040** existing metric revision rows. The source journal and delivery journal
were not migrated in place. The copied legacy database was upgraded with a further
`financial.pre-v55.sqlite` rollback snapshot.

The FPT/TCB/VCI pilot passed before the full import: **five capture revisions**
(including FPT/TCB reviewed alternatives), **294 statement observations**, and
annual/quarterly/TTM projection parity. All 23 saved issuers were then imported.

| Coverage | Verified result |
|---|---:|
| Issuers | 23 |
| Provider/summary captures | 23: 21 VCI, two CafeF |
| Reviewed original-report alternatives | 5 |
| Total capture revisions | 28 |
| Statement-period observations | 1,368 |
| Source-line slots, including nulls | 92,380 |
| Non-null source-line values | 91,528 |
| Repeated full mirror insertions | 0 captures / 0 observations |
| Saved/mirrored packet and public/private projection comparison | 28/28 pass across annual, quarterly and TTM |
| Preserved original private files/journals | 101/101 hashes unchanged |

Issuer inventory: ACB, BID, BSR, CTG, FPT, GAS, GVR, HPG, MBB, MCH, MWG, PNJ, REE,
SAB, SSI, TCB, VCB, VCI, VHM, VIC, VNM, VPB, VRE. This is a saved-data sample, not a
hardcoded supported universe or certified dated VN100 membership list.

FPT, HPG, MWG, PNJ, REE, SSI, TCB and VCB each retain **eight annual and 34 quarterly
periods**, 2018-Q1–2026-Q2 for quarterly observations. The other 13 VCI issuers have
four annual/four quarterly periods. VHM/VNM have four CafeF annual summaries and
no saved quarters. Five reviewed alternatives remain independent of provider data.

The extended legacy importer additionally materialized all 34 quarterly periods for
the eight long histories and recent metric projections for the other saved issuers.
It appended **59,444** revisions, bringing the journal to **82,484** metric revisions
including the 23,040 preserved legacy rows. These counts include blocked/unavailable
metrics and legitimate revision alternatives; they do not claim that every metric
has a usable value. Public verification/rights gates remain unchanged.

Reports and snapshots remain ignored/private under `.local/financial-research-v55/`:
`pilot/`, `all/`, `reimport/`, `metrics/`, `metrics-reimport/`, `backups/`, `restored/`,
`SOURCE_HASHES_BEFORE.json`, and `PRESERVATION_REPORT.json`. None is committed.

## Exact Windows commands

Run in PowerShell. Use the existing virtual environment; no installation, database
service, dependency synchronization or server restart is necessary.

```powershell
Set-Location 'C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-financial-data'
```

For a new empty private store, initialize explicitly. Repeating this command is
safe; do not use a product database path:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --initialize --journal .local/financial-research-v55/financial.sqlite
```

Alternatively, start a **new generation** from the original legacy journal as was
done for this delivery. The destination must not already exist. Do not run this
against the already delivered database:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --journal .local/financial-metrics.sqlite --backup .local/financial-research-next/financial.sqlite
```

Pilot, compare, import all, then compare again. These commands use the existing
delivered generation and are rerunnable; use `financial-research-next` instead
when validating a new generation:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --mirror --captures .local/free-data-v4-ready --journal .local/financial-research-v55/financial.sqlite --tickers FPT TCB VCI --report .local/financial-research-v55/pilot
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --compare --captures .local/free-data-v4-ready --journal .local/financial-research-v55/financial.sqlite --tickers FPT TCB VCI --report .local/financial-research-v55/pilot
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --mirror --captures .local/free-data-v4-ready --journal .local/financial-research-v55/financial.sqlite --report .local/financial-research-v55/all
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --compare --captures .local/free-data-v4-ready --journal .local/financial-research-v55/financial.sqlite --report .local/financial-research-v55/all
```

`--compare` opens only a read-only DB connection; it writes its comparison report
to the specified private report directory. A financial mismatch returns exit code
1; missing/corrupt inputs fail with an error. It compares exact packets and all
financial output fields, excluding only the volatile top-level `read_at` timestamp.

Optional canonical metric materialization through the existing CLI, without
changing serving configuration:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --captures .local/free-data-v4-ready --journal .local/financial-research-v55/financial.sqlite --report .local/financial-research-v55/metrics
```

For an already saved, validated canonical VCI update (example file must exist),
append it alongside the index without rewriting the capture index:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --mirror --captures .local/free-data-v4-ready --packet .local/approved-candidates/new-packet.json --journal .local/financial-research-v55/financial.sqlite --report .local/financial-research-v55/update
```

Backup and restore to new, unused destinations; choose different names on reruns:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --journal .local/financial-research-v55/financial.sqlite --backup .local/financial-research-v55/backups/operator-snapshot.sqlite
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --journal .local/financial-research-v55/backups/operator-snapshot.sqlite --backup .local/financial-research-v55/restored/operator-financial.sqlite
.\.venv\Scripts\python.exe -B -m scripts.ingest_financial_intelligence --compare --captures .local/free-data-v4-ready --journal .local/financial-research-v55/restored/operator-financial.sqlite --report .local/financial-research-v55/restored/operator-parity
```

Rollback today requires no serving switch: APIs still read original captures.
For a storage rollback, retain the failed generation, restore a snapshot to a new
private path and verify it before using that path in subsequent offline commands.
The pre-V5.5 backup restores legacy metrics only; a post-import snapshot also
restores capture/statement/selection tables. Source archive files need their own
backup; a database backup contains references, not the original PDF binaries.

## Validation and boundaries

Focused storage tests cover migration/backup, idempotency, 34/60-quarter retention,
short updates, explicit revisions, scope/basis/source isolation, nulls/hierarchy,
exact packet and HTTP contract parity, indexed history/offline candidates,
failed upgrades, unknown/application schemas, read-only guards and restore.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q tests/test_financial_storage.py tests/test_financial_intelligence.py tests/test_personal_financials.py tests/test_financial_batch_acquisition.py
.\.venv\Scripts\python.exe -B -m pytest -q
Set-Location frontend
npm test
```

Validation: full backend regression **1,636 passed + 32 subtests**; the complete
storage module passed **13 tests**, including an additional indexed-history/offline-
candidate case added after the full suite had collected. Frontend regression:
**338 passed, one existing skip**. The full real normalized importer rerun added
**zero** metric revisions. A final post-metric backup/restore retained all **82,484**
metric revisions and passed the same 28-capture projection comparison.

Final database integrity/foreign-key checks pass; all 23,040 original metric
identities/payloads remain byte-exact. The final database occupies approximately
382.2 MB. Its raw source store includes 324 issuer-quarter pairs and 124
issuer-annual-period pairs from the 23 provider/summary packets, plus the separate
reviewed-source alternatives.

## Standards

Independent review against repository rules found **0 actionable findings**.
Existing schemas, journal and deterministic projections are reused; provenance,
nulls and private/source boundaries remain intact.

## Spec

Independent review against the V5.5 mission found **0 actionable findings**.
Offline incremental storage, backup/restore and parity are implemented; live
acquisition/default serving remain explicitly deferred. Reviews used the change
since `e2e42f6`, excluding the pre-existing tooltip edits and assessment report.

Review totals: Standards **0**, Spec **0**; no worst issue in either axis.

No frontend source
or dependency was changed, so no preview/build/restart or visual acceptance was
needed for this backend storage foundation. Actual production/browser acceptance
and automatic database serving are not claimed.

Remaining work: dated VN30/VN100 coverage policy, live acquisition integration,
scheduled refresh, explicit normalization remapping/version migrations, historical
derived projections beyond 40 periods, and eventual opt-in accumulated-history
serving with compatibility review. Unknown scope, units, publication timing and
data-use rights remain unknown. No new data rights, source reconciliation platform,
financial engine, PostgreSQL, Docker, or production configuration was introduced.
