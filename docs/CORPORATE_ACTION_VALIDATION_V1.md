# Corporate-action validation V1

Reviewed 2026-10-18 against development base
`eaac5cbfe99e050a0a1aab80bd7ab34927f0bf88`. This is a bounded historical
source comparison and presentation correction, not current-session or live-data
acceptance. No production database was opened or imported.

## Existing evidence and scope

Reused all six components in `data/corporate_actions/verified_v1.json`, the source
table in `docs/CORPORATE_ACTION_CONTEXT_V1.md`, the existing provenance study's
notice references, and the read-only API/model/tests. No original corporate-action
documents were cached with this curated set. The saved `verified` flag is
record-level: some records explicitly rely on secondary reports for ex-dates.
It does not encode independent, original-publication verification per field.

Only missing original references were retrieved manually. No SSI request,
acquisition job, credentials, ingestion, polling or scheduler was used. Original
VSD links timed out; the same notice IDs were readable on VSDC's canonical domain.
Publication/update dates below belong to those sources; they do not replace
the saved secondary publication timestamps or historical Woofi receipt times.

## Field-by-field results

**Verified** means a fact is expressly present in the reviewed official notice.
**Corroborated text** is weaker: issuer-authored material read through a mirror's
PDF text extraction, without successful visual inspection of its scanned pages.
**Original-unverified** means a populated saved fact was not established by the
reviewed original; it is not a contradiction. **Missing** means no supported value
in this record/original, not proof that no such date exists elsewhere.

| Saved component | Type and amount / ratio | Ex-rights date | Record date | Payment date |
| --- | --- | --- | --- | --- |
| VNM-2020-cash | Corroborated text: cash, 2,000 VND/share | Original-unverified: saved 2020-09-29 relies on Dan Tri | Corroborated text: 2020-09-30 | Corroborated text: 2020-10-15 |
| VNM-2020-bonus | Corroborated text: capital-from-equity bonus, 5 old : 1 new (saved 0.2 new/old) | Original-unverified: same saved date / secondary reference | Corroborated text: 2020-09-30 | Missing; cash-component payment must not transfer here |
| HDB-2021-stock-dividend | Verified: stock dividend, 100 old : 25 new (0.25 new/old) | Original-unverified: saved 2022-09-27 relies on secondary report | Verified: 2022-09-28 | Missing |
| GAS-2023-equity-bonus | Verified: capital-from-equity bonus, 10 old : 2 new (0.2 new/old) | Original-unverified: saved 2023-09-22 relies on SHS | Verified: 2023-09-25 | Missing |
| SSI-2022-rights | Verified: rights offering, 2 rights : 1 new, 1 right per old share (0.5 new/old), subscription 15,000 VND/share | Original-unverified: saved 2022-06-22 relies on KIS | Verified: 2022-06-23 | Missing for rights component; sibling cash dividend is separate |
| HFC-2023-additional-registration | Verified as additional registration; entitlement ratio and subscription price missing | Missing | Missing | Missing |

No conflicting value was found among the facts compared. This does not establish
completeness or check later amendments. None of the six components passes full
original-evidence verification of all displayed event fields. There are no pending
or withdrawn records in this small saved set; their display behavior is tested
with explicitly constructed fixtures, not claimed as actual provider events.

## Original references and evidence boundaries

- [VNM issuer-authored notice, mirrored PDF](https://static2.vietstock.vn/vietstock/2020/8/6/20200806_20200806%20-%20VNM%20-%20CBTT%20ngay%20DKCC%20chot%20danh%20sach%20tra%20co%20tuc.pdf):
  dated 2020-08-03; page 1 has record/cash/payment facts, page 2 the separate bonus
  component, page 3 issuer signature text. Text extraction succeeded; PDF screenshot
  requests timed out. No visual authenticity/signature verification is claimed.
  No ex-rights date was established from this document.
- [HDB, VSD notice 153334](https://vsdc.vn/vi/ad/153334): published
  2022-09-19 15:35:57; record-date and stock-dividend sections support the matrix.
  The notice does not supply the ex-rights or payment dates.
- [GAS, VSDC notice 161638](https://vsdc.vn/vi/ad/161638): published
  2023-09-14 11:11:39; record-date and capital-from-equity distribution sections
  support the matrix. Ex-rights and payment dates remain unverified/missing.
- [SSI, VSD notice 151355](https://vsdc.vn/vi/ad/151355): published
  2022-06-13 16:09:36; rights section supports the matrix. Its separate cash
  distribution specifies 1,000 VND/share and 2022-07-20 payment; those facts are
  **not** rights terms. Rights-code validity and subscription periods are also
  not ex-rights, record or payment dates.
- [HFC, VSDC notice 161939](https://vsdc.vn/vi/ad/161939): published
  2023-09-22 17:34:13; additional registration starts 2023-09-22, custody starts
  2023-09-26. Neither is an ex-date. Aggregate registered shares and par value
  do not establish an entitlement ratio or subscription price.

These are depository publications and a mirrored issuer document, not a claim
that exchange-hosted originals were obtained. No ex-date is inferred by subtracting
a working day from record date. No payment, entitlement or price adjustment is
calculated. Sources remain inspectable; no secondary fact was silently promoted.

## Corrections and regression scope

- Label source hyperlinks as recorded references, not automatically original
  documents. Label the stored date as announcement / publication, since KIS/SHS
  dates are report dates, not certified first issuer announcements.
- Label the flag as **Source-marked verified** and explicitly explain its scope.
  Missing displayed dates or applicable terms get **Incomplete event details**.
  Complete field presence never gets a fully-confirmed badge.
- Reuse the existing explicit `Unresolved correction` note prefix as a display
  veto even if a stale verified flag remains true. Retain the note and evidence;
  withhold all event terms/dates. No arbitrary conflict detection from prose.
- Preserve stored values, identities, revisions and source URLs byte-for-byte.
  No new schema, importer behavior or production data mutation.

Tests exercise actual React rendering in EN/VI, secondary-source labels, incomplete
dates/terms, contradictory verification flags, separate VNM cash/bonus components,
SSI sibling cash versus rights, and HFC's missing entitlement facts. Saved notice
facts use simulated API receipts only; synthetic cases are never live evidence.
Browser acceptance remains blocked by the previously recorded execution policy;
no browser/process/port attempt is part of this validation.

## Remaining gate

Obtain authoritative ex-rights disclosures for the dated components, retrieve a
visually inspectable VNM original, and seek missing component-specific dates only
through an authorized source review. Later corrections and display permissions
are not certified here. The current API lacks structured per-field original-source
qualification, so this report's audit results are not advertised as new live API
certifications. Any future field-level activation needs its own bounded contract
change and review. No full corporate-action or Market Workspace completion claim.

## Executed validation

- 62 frontend tests PASS in one focused run: stock actions, action presentation,
  Stock Detail, stock tabs, fundamentals, community, company overview, localization
  and financial loading. Eight permanent regression cases were added to the two
  action test files; existing assertions were retained with the new status wording.
- Three existing read-only corporate-action API tests PASS in a separate run using
  test-mode, in-memory SQLite. They verify SELECT-only reads, latest corrections,
  missing facts and pagination. One existing Starlette/httpx deprecation warning.
- `npm run build -- --webpack` PASS and subsequent `npm run typecheck` PASS in a
  hash-matched artifact copy. No shared `.next`, runtime `.env` or server process
  was used. Backend build target was an inert loopback endpoint.
- `git diff --check` PASS. No changes under `data`, `src`, `scripts` or `main.py`.
  Curated JSON SHA256 remains
  `85a97915f7aae8f9f53c54230b55d2efeeb96775228446676da1615668a96ee9`.
- Browser: NOT RUN; previous policy blocker preserved. Renderer tests are not
  browser acceptance or live provider validation. No push or deployment.

Logs and build source hashes are saved locally at
`C:/Users/PC/.codex/visualizations/2026/10/17/01a14811-87da-7ee2-8499-7835dd010da3/corporate-action-validation-v1/`.
Production Supervisor, Collector, SQLite, runtime pin, SSI/News cooldowns,
Technical Pilot and FPT automation were not changed or re-certified.
