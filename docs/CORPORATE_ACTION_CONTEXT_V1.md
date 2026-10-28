# Corporate-action-aware Technical context V1 — 2026-10-08

## Scope and result

The approved V1 enriches existing Technical observations with verified exact-session
corporate-action evidence. It does not assert causation, suppress events or change
SSI adjusted prices, analytics, thresholds, Significance, Novelty, Base Materiality,
volume logic or calibration exclusions. Watchlist and frontend are untouched.
There is currently no live user-facing scored Technical-event consumer; this
checkpoint supplies backend service, persistence and replay seams without creating
one. No new network feed, scraper, worker or monitoring infrastructure is added.

Initial Git base: `77fe34a0be1ba4c907761c487e820be95add1968`, branch `main`.
Initial remote tracking `origin/main`: `b5f3c89fab02c42623cacacfb3dbb0ab07cca2d3`.
Pre-existing tracked frontend/main.py changes, the separate web-ingestion CONTEXT
line and unrelated untracked research/ingestion files must remain outside this commit.
No push is authorized for this checkpoint.

## Model, dates and evidence

`CorporateActionNotice` stores `symbol`, `action_type`, nullable `effective_date`,
`record_date`, `payment_date`, `announced_at` or date-precision `announced_on`,
`source`, `source_url` or stable `source_id`, `supporting_urls`, `component_id`,
`source_revision`, nullable `terms`, `verified`, `withdrawn`, `is_fixture`, and
`verification_note`. `CorporateActionObservation` adds immutable `observation_id`,
`action_id` and actual UTC `observed_at`.

Normalized types: `cash_dividend`, `stock_dividend`, `bonus_shares`,
`rights_offering`, `additional_issuance`, `other`. Ordinary meetings/filings are
not price-affecting actions; `other` does not match. Terms, when known, hold
`cash_vnd_per_share`, `new_shares_per_old` and `subscription_price_vnd` (VND, not
SSI chart price units). No adjustment factor or reconstructed price is produced.

Effective/ex-date means the verified trading session affecting the security price
basis. Record and payment dates are separate facts; neither registration, custody,
listing nor announcement dates substitute for an unresolved ex-date. Source
publication timestamps require an explicit timezone; date-only publication is
retained at source-local date precision rather than invented midnight. Receipt
time reflects when Woofi ingested the notice, never when the document claims to
have been published. Missing optional values remain `null`.

Every context includes `status`, `as_of`, individual observations, `coverage` and
`reason`. Verified active dated notices may yield `KNOWN_MATCH`. Otherwise V1
returns `UNKNOWN` with `not_configured`, `not_observed` or `source_unavailable`;
coverage is always `INCOMPLETE`. No certified `KNOWN_NO_MATCH` state is offered.

## Knowledge time, identity and updates

`get_known_actions_as_of` first selects the latest revision of each source component
whose receipt is <= the supplied aware cutoff. Symbol/date filtering happens only
after revision selection, so corrected dates and symbols cannot leave obsolete
matches active. `get_actions_for_symbol` also exposes unresolved metadata;
`get_actions_effective_on` matches only verified, active, recognized actions with
exactly equal effective dates. Known upcoming notices never enrich an earlier
Technical session. No proximity window or price/news causal inference is used.

Identity hashes source + stable notice ID (or exact source URL) + component ID.
Without an explicit component ID, symbol + action type identifies the component
within that notice. Adapters must supply distinct document-scoped component IDs
for multiple components of the same type in a document, and retain them across
corrections. Canonical normalized payload equality deduplicates against the
latest version and preserves first receipt. Changed versions append records;
A→B→A preserves all three versions. Conflicting same-time or backdated source
revisions are rejected. Cross-source reports remain distinct corroborating
observations; there is no speculative cross-source merger or coverage count.
The curated command is a single-writer import seam, not a concurrent ingestion
scheduler.

`TechnicalContextHistory.record(event_id, result, generated_at=...)` stores the
original serialized scored output with a stable caller-owned event ID. It
re-queries context at generation time, rejecting replacement of an existing
event with different content. `append_update(..., enriched_at=...)` stores only
changed context in a separate timestamped update row; repeated unchanged reads
do not append rows. Late notices add evidence without rescoring. Corrected or
withdrawn matches can append UNKNOWN context without removing the earlier
match from history. Original scores/evidence/timestamp remain intact;
`get(..., as_of=...)` shows only original events and updates available then.
Append chronology is strictly increasing. These are application-level immutable
records, not a claim of database administrator tamper protection.

Imports stamp actual receipt time with no CLI backdating option. The repository's
explicit receipt injection exists for controlled simulations; fixture tests label
synthetic knowledge times and do not assert historical Woofi awareness. This
practical knowledge-time constraint is not SSI historical vendor-vintage/PIT
certification. No protected historical OHLC cohort or calibration run was opened.

## Source and verified examples

`data/corporate_actions/verified_v1.json` contains six manually verified components
across five issuers. It has source links, normalization notes and explicit
limitations, but no claimed historical receipt times. Production import does not
mark these verified real notice facts as synthetic; behavior simulations explicitly
set `is_fixture=True` for injected receipts and synthetic prices.

| Issuer / type | Effective date | Evidence and limitations |
| --- | --- | --- |
| VNM cash / bonus | 2020-09-29 | [Issuer notice mirrored by Vietstock](https://static2.vietstock.vn/vietstock/2020/8/6/20200806_20200806%20-%20VNM%20-%20CBTT%20ngay%20DKCC%20chot%20danh%20sach%20tra%20co%20tuc.pdf) supplies record 09-30, cash 2,000 VND, payment 10-15 and 5:1 bonus; [Dan Tri contemporaneous report](https://fica.dantri.com.vn/chung-khoan/co-dong-vinamilk-huong-loc-co-tuc-gia-co-phieu-bat-tang-manh-20200929010525937.htm) explicitly confirms the ex-session for both. |
| HDB stock dividend | 2022-09-27 | [Vietstock report via 24HMoney](https://24hmoney.vn/news/hdbank-chot-quyen-chia-co-tuc-2021-ty-le-25-c4a1629620.html) explicitly confirms ex-date, record 09-28 and 25% dividend from undistributed profits. Secondary-backed. |
| GAS bonus | 2023-09-22 | [SHS Market Lens p5](https://archive.shs.com.vn/Sites/QuoteVN/SiteRoot/reportattach/20230912_172533_Market%20Lens%20Final%20New%2012-09-2023.pdf) explicitly confirms ex-date, record 09-25 and 20% capital-from-equity bonus. [VSD reference](https://www.vsd.vn/vi/ad/161638) retained; retrieval intermittent. |
| SSI rights | 2022-06-22 | [KIS calendar p3](https://kisvn.vn/wp-content/uploads/2022/06/Bai-Daily-ngay_Vi_20220622.pdf) explicitly supplies ex-date; [ACBS rights notice](https://acbs.com.vn/tin-tuc/chi-tiet/thong-bao-thuc-hien-quyen-mua-phat-hanh-them-ssi-1015000270-nc7204e5a) supplies record 06-23, MIRSSI221, 2:1 rights and 15,000 VND subscription. Source date is not claimed first issuer announcement. |
| HFC additional issuance | unresolved | [VSDC notice 161939](https://vsdc.vn/vi/ad/161939) verifies additional registration of 2,000,000 shares and custody dates. It does not verify a price-effective/ex-date: retained as unresolved and **must not match**. Synthetic dated additional-issuance behavior is tested separately. |

This sample is not broad market coverage, latency certification or an automatic
official source. Historical documents published after the simulated cutoff are
not presented as actual historical receipt evidence. Real metadata is exercised
through the repository and existing market-event service with synthetic prices;
no issuer-specific detector logic exists.

## Runtime use

Run from repository root, with the existing configured database:

```powershell
uv run python -m scripts.ingest_corporate_actions data/corporate_actions/verified_v1.json --append-updates
```

The command validates the dataset, creates additive tables through existing
`create_tables`, imports with actual receipts, reports inserted/duplicate/revision
counts and optionally appends changed context to recorded events. It does not
rewrite `.env`, stage files or trigger a market-data acquisition. It is explicit
curated import, not part of the News/Community worker or web startup trigger.

Existing `detect_and_score_market_events` accepts optional `corporate_actions`
repository and an explicit `generated_at`. Indicators/detectors/scoring run
normally; enrichment is a separate result field, not candidate evidence used by
Significance/Novelty or case identity. Callers can record returned results with
`TechnicalContextHistory` and append later updates after import.
`replay(..., corporate_actions=repository)` queries context at each observation's
`available_at` and emits the same candidate, scores, memory and case IDs. The
replay CLI's default remains unchanged; no calibration or output archive is
rewritten. The existing evidence-only AST research adapter remains compatible
without editing pre-existing untracked research files.

No renderer is added. Future presentation should say only that Technical movement
coincided with a verified action's effective session, and expose source/receipt
and original-versus-later context. It must not assert that the action caused the
entire movement. Existing default results expose UNKNOWN/not_configured.

Persisted observations and event updates permit inspecting announcement-to-receipt
latency when an actual timestamp exists, exact matches, late updates and revisions.
Import counters are diagnostics, not manufactured source coverage percentages.

## Verification and acceptance

Focused tests cover normalization, all five known types, missing dates/terms/source
URL, incomplete and failed sources, explicit timezone validation, multiple issuers
and components, stable source duplicates, separate corroborating sources,
corrections/withdrawal eligibility, exact matching, no pre-observation leakage,
late append history, idempotent imports, immutable events and CLI integration.
Real examples above run through the service; HFC proves conservative unresolved
date handling. Synthetic cases compare price/volume/MA/RSI/lower-and-upper BB event
candidates, component scores, exclusions and reason codes before/after enrichment.
Replay prefix equivalence and existing case IDs remain unchanged.

Verification completed:

```powershell
uv run --no-sync python -B -m pytest -q -p no:cacheprovider tests/test_corporate_action_context.py tests/test_corporate_action_edges.py tests/test_corporate_action_history.py tests/test_corporate_action_curated.py tests/test_corporate_action_replay.py
# 29 passed before the CLI integration test was added; final new-suite total: 30.
uv run --no-sync python -B -m pytest -q -p no:cacheprovider tests/test_corporate_action_curated.py
# 7 passed, including actual-receipt CLI import + late-update persistence.
uv run --no-sync python -B -m pytest -q -p no:cacheprovider tests/test_development_v3.py tests/test_validation_v2.py tests/test_corporate_action_replay.py
# 19 passed: evidence-only adapter compatibility and replay gating.
uv run --no-sync python -B -m pytest -q -p no:cacheprovider
# 655 passed, 1 existing Starlette/httpx deprecation warning, 58.58 seconds.
```

Full backend regression passes; no frontend suite is needed because this task
does not edit frontend. Official Materiality calibration,
historical benchmark certification, Watchlist work, vendor price reconstruction
and next milestone work are not performed.

## Files in this checkpoint

- `CONTEXT.md` — only the new corporate-action policy section.
- `research/provenance/technical_data_readiness_v1/CORPORATE_ACTION_REASSESSMENT.md` — appended decision, previous study intact.
- `docs/CORPORATE_ACTION_CONTEXT_V1.md`.
- `data/corporate_actions/verified_v1.json`.
- `src/corporate_actions/__init__.py`.
- `src/corporate_actions/models.py`.
- `src/corporate_actions/storage.py`.
- `src/corporate_actions/repository.py`.
- `src/corporate_actions/context.py`.
- `src/corporate_actions/history.py`.
- `src/corporate_actions/curated.py`.
- `src/db/session.py`.
- `src/materiality/models.py`.
- `src/materiality/service.py`.
- `src/evaluation/models.py`.
- `src/evaluation/replay.py`.
- `scripts/ingest_corporate_actions.py`.
- `scripts/preview_materiality.py` — JSON serialization of the new nested context.
- `tests/test_corporate_action_context.py`.
- `tests/test_corporate_action_edges.py`.
- `tests/test_corporate_action_history.py`.
- `tests/test_corporate_action_curated.py`.
- `tests/test_corporate_action_replay.py`.
