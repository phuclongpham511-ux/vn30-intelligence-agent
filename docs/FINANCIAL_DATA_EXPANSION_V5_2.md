# Financial Data Expansion V5.2

**Branch:** `feature/financial-data-intelligence`
**Base:** `0dbaf10`
**Scope:** repeatable private multi-ticker acquisition through the installed VCI/vnstock SDK; no provider upgrade, paid feed, dashboard redesign, or new financial engine.

## Acquisition boundary

The pinned environment uses `vnstock==4.0.2`. New collection calls use its `Finance` statement methods and their four-period result limit for each annual or quarterly frequency. The workflow does not call vnstock's underlying financial-statement REST endpoint. Requests run serially with a six-second minimum delay between SDK reads, matching the installed guest-tier limit observed during the provider audit. Data remains in the ignored, private `.local` capture directory; this personal research workflow does not grant redistribution rights. See the [vnstock financial statement guide](https://www.vnstocks.com/docs/vnstock/co-ban-fundamental) and [data-source access guide](https://www.vnstocks.com/docs/vnstock/tham-khao/data-sources).

The adapter preserves source field codes, English and Vietnamese labels, parent relationships, reported numeric values, statement kind, annual or quarterly periods, source identity, package version, and local observation time. Currency, units, consolidation scope, exact fiscal boundaries, and publication timestamps are retained as unknown where the installed SDK response does not establish them. A missing frequency is recorded as a diagnostic without discarding successful statement periods.

## Repeatable workflow

`scripts/acquire_financial_batch.py` calls the existing normalized packet adapter and writes into the existing hash-pinned private capture format. `src/services/financial_batch.py` accepts 1–15 validated symbols, skips verified existing packets by default, refreshes only when requested, isolates issuer failures, checkpoints the index per successful issuer, and keeps immutable prior revisions. A shorter four-period response cannot replace a longer saved history. The existing API continues reading the same capture index and financial projection contracts.

PowerShell example (from the repository root):

```powershell
$env:PYTHONIOENCODING = 'utf-8'
uv run python -m scripts.acquire_financial_batch `
  --captures .local/free-data-v4-ready `
  --tickers ACB BID CTG MBB VPB VCI VIC VRE GVR SAB MCH GAS BSR
```

The command is resumable: rerun it after interruption and completed valid captures are skipped. Use `--refresh` for a bounded current-period update; the longer-history guard still applies.

## Pilot coverage

The pilot was selected from the available SSI FastConnect universe response (last sync 2026-10-19, marked stale) and sampled across categories represented in Woofi's saved observed HOSE membership snapshot (source receipt 2026-10-17). The symbols appear in the repeatable command below, not as an embedded restriction in the acquisition workflow.

| Ticker | Sector sample | Status | Quarterly periods | Annual periods | Income / balance / cash field codes |
|---|---|---|---:|---:|---|
| ACB | Banking | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 26 / 86 / 52 |
| BID | Banking | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 26 / 86 / 52 |
| CTG | Banking | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 26 / 86 / 52 |
| MBB | Banking | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 26 / 86 / 52 |
| VPB | Banking | Added | 2025-Q4–2026-Q3 (4) | 2022–2025 (4) | 26 / 86 / 52 |
| VCI | Securities | Added | 2025-Q4–2026-Q3 (4) | 2022–2025 (4) | 79 / 208 / 148 |
| VIC | Real estate | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 25 / 122 / 41 |
| VRE | Real estate | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 25 / 122 / 41 |
| GVR | SSI observed: plastics, rubber and fibers | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 25 / 122 / 41 |
| SAB | SSI observed: food | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 25 / 122 / 41 |
| MCH | SSI observed: food | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 25 / 122 / 41 |
| GAS | SSI observed: oil and gas distribution | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 25 / 122 / 41 |
| BSR | No row in saved HOSE membership snapshot | Added | 2025-Q3–2026-Q2 (4) | 2022–2025 (4) | 25 / 122 / 41 |

Field columns are income / balance / cash field-code counts across the acquired annual and quarterly observations. ACB, BID, CTG and MBB each returned 208, 672 and 408 non-null statement values, with 0, 16 and 8 missing values respectively. VPB matched these bank line counts. VCI returned 624, 1,648 and 1,176 non-null values with 8, 16 and 8 missing. Each of the other seven issuers returned 200, 968 and 328 non-null values with 0, 8 and 0 missing. The reported gaps remain null.

The packets retain 15,744 source parent links across the 13 issuers' statement lines. A second invocation skipped all 13 valid captures without calling the fetch function, confirming resumability and no duplicate acquisition.

The five added bank packets expand the saved coverage of the 22 observed banks from two to seven, while the securities sample expands to two of 21, and the real-estate sample to three of 56. The SSI mapping snapshot remains observed and not taxonomy-verified; peer ranks, sector totals, and historical sector analytics remain disabled. The food group has two of 11 saved members, the plastics/rubber/fibers group one of 15, and the oil/gas distribution group one of nine. BSR has financial statements but is outside the saved HOSE membership snapshot, so it is not placed in an industry group.

Financial ratios are not added: the existing VCI ratio endpoint in this pinned version is not a dependable source of ratios. The pilot therefore expands statement-line coverage only; existing supported calculations remain governed by their prior field and metadata rules.

## V5.1 comparison and validation

V5.1's ten saved financial tickers remain present; V5.2 raises this to 23 by adding 13 of the 13 requested issuers. Existing FPT, HPG, MWG, TCB, VCB and SSI keep their 34-period quarterly histories, and VNM keeps its original four annual summaries. Each new capture has four annual observations (2022–2025) and four quarterly observations. Eleven new issuers' quarterly histories cover 2025-Q3–2026-Q2; the provider currently returns 2025-Q4–2026-Q3 for VPB and VCI. These are the source's labels as returned by the SDK; their exact fiscal boundaries and publication dates remain unknown in this capture format.

All 13 results were added with no ticker-level errors. A read-only in-process TestClient check returned HTTP 200 for all 13 new issuers, each with four quarterly rows and all three statement families. It also returned the existing 34-quarter responses for FPT, TCB and VCB. It did not open a listener or restart the preview. The responses are private and no-store.

The V5.1 versus V5.2 comparison is 10 versus 23 saved issuers; 13 new issuers each have four returned annual periods, four returned quarterly periods and source-coded income, balance and cash-flow lines. Backend regression passed **1,618 tests and 32 subtests** with one existing Starlette/httpx deprecation warning. Frontend tests passed **336** with one existing skip; TypeScript typecheck and optimized production build passed. Visual/browser acceptance remains pending; the API check used an in-process TestClient without starting or restarting a listener.

## Limits

New free-tier acquisitions expose at most four periods per frequency in the installed SDK. They do not backfill old history beyond what the source returns. The saved SSI snapshot may not be current, provider responses may omit statements or fields by issuer, and data-use rights remain limited to the documented personal/research access conditions. Public activation and current historical industry aggregation are not implied.
