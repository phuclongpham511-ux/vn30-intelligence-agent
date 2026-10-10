# Operational EOD V1 isolated checkpoint

Base: `84cb2ef5141010b6e6230f3146f5e1e34216adc8`.
Branch: `codex/woofi-technical-stock-detail`.

Only these 22 approved backend, regression and evidence documentation files were
transferred byte for byte from the original worktree. SHA-256 values below
describe source bytes before Git line-ending normalization. This manifest is
the sole additional checkpoint file. Original worktree files were not edited.

Excluded: .env and credentials, runtime databases, raw SSI history, generated
market-data snapshots, and unrelated Dividend/calibration/research WIP.
The historical evidence report remains an unedited record; later policy and
owner-reported SSI authorization are documented in the persistence report.

| File | Source SHA-256 |
| --- | --- |
| `CONTEXT.md` | `c4ee3d91dd2a1a50320f0058c9f824092968b1be8ebf48c3795096c4510def5d` |
| `routers/technical.py` | `ac79cd69f81445cd4b2fb285765446ab2fd57a3bc2b5fa544b68b55effdc087e` |
| `scripts/ingest_data.py` | `af4a2aa91f0bcf0929c11a5f5127b7487cb1f105861670c9b437941bf3771fa2` |
| `src/db/session.py` | `ce52530d63991f87ae6812ccd4e1a88679913fd7af43b4937d9b3cafb3ba52c9` |
| `src/providers/ssi/__init__.py` | `adfab6cb04fdc5e2d4849f7227c0805370023c06a2cee0eea9c8f4210da374c7` |
| `src/services/technical_api.py` | `973f501da0cb038a64798dd5d975a3277e9a00cebc831d025b86030e9b4556b5` |
| `src/services/technical_eod.py` | `181f71bc06fbdb7ac218e744b26c7ff088e1f76d9860acfaa6a66f4b449b1a45` |
| `tests/test_data_reliability.py` | `97ced93907351a6b764d0ea9934f87314269b29a8868232bded2b700d2784eee` |
| `tests/test_ssi_provider.py` | `ceafcbb5e312aa768613885faf0b25ca57e832a825fcaaecaa04fe26c4a0baee` |
| `docs/TECHNICAL_EOD_PERSISTENCE_V1.md` | `7d93de8c6f9e5eee808e7a0cd04927b7c8dcb498f15f5f3dd21b1ceefeddb198` |
| `docs/TECHNICAL_V1_FPT_FIRST_RECEIPT_2026-10-09.json` | `4c7672c46a1ab929a271e27587d2fe8305b08b178ae1a1dc52cea87485390499` |
| `docs/TECHNICAL_V1_FPT_SECURITY_RECEIPT_2026-10-09.json` | `6446ad20e1ab1ff692ae8b3a7799f213d5a46c85fb33bfc3ddf1cd87ccc4f20d` |
| `docs/TECHNICAL_V1_HOSE_PUBLICATION_2026-10-08.json` | `416f1fbc0e4cb0f95c2db1174858997b0bfe485480b706fca45d235f4413ad8e` |
| `docs/TECHNICAL_V1_HOSE_SESSION_INDEX_2026-07-01_2026-10-08.tsv` | `88b288afa760f13e09522624f17b9fa6dce481047bf2bbfee839d13ebec9bd49` |
| `docs/TECHNICAL_V1_OPERATIONAL_EVIDENCE_2026-10-09.md` | `4df88de412685f58de33aff41ac268cc261ff9d8d831a2a90bd4bebb8d28a259` |
| `docs/TECHNICAL_V1_PROVISIONAL_OPERATIONAL_EOD_V1.md` | `a741757a21ebb86706ca0bc0f7ed9611c9fd58d8bb54b020ff92f0f1fb60e179` |
| `scripts/produce_technical_eod.py` | `12b73209ffdfc5c6f73f3d4a7fa440f116dc0c532060f01cd297ff38cc1b33bd` |
| `src/models/technical_eod.py` | `799edb5eeb72af29425add9649b0e25c501607d5825dc112177b8af09e972e07` |
| `src/services/provisional_eod.py` | `93bb703dfaed4047c0101cc8394670fa2a93da982bf50990c60c3bd93e0ca694` |
| `src/services/technical_eod_store.py` | `663424de033044b2d0f3baf2205c0be6ec9c49ad64da43d7c5afb46f577f476f` |
| `tests/test_provisional_eod.py` | `09a40c464384ae6fb97650db0d5e50654ff68c150cdcce2fc087005c22af3620` |
| `tests/test_technical_eod_persistence.py` | `a1f41dbdced2f92b814c553daaae558f9c84d3ba0474de7da09a74bc5eaa12ec` |

Validation before the authorized local commit: 849 backend tests passed,
Technical identity guard passed (9 files), transfer hashes matched, and
staged paths and Git blobs matched this allowlist. No push or deployment.
