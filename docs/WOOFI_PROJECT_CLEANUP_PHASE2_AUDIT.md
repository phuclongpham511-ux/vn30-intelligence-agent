# Woofi project cleanup - Phase 2 audit

Audit date: 25 October 2026. Repository/worktree baseline: `884f28b02a7ece1d061eac928e3423c93f5cf592`, branch `feature/financial-data-intelligence`. This is an inventory and proposal; no destructive cleanup, source refactor, worktree pruning, account operation or provider request was performed.

## Decisions and measured totals

| Output | Finding |
| --- | --- |
| WORKTREE_INVENTORY | 15 linked checkouts, one shared Git object store; full paths, branches, HEADs and WIP below |
| WORKTREES_SAFE_TO_REVIEW_FOR_REMOVAL | 9 clean checkouts have their exact committed history contained elsewhere. 3 have no detected protected ignored files; 6 require private-file retention first. None is approved for removal |
| DOCUMENTS_REVIEWED | 313/313 previously metadata-only documents classified at content level; 9 untracked notes/templates reviewed, one overlapping that 313-file set |
| DOCUMENTS_TO_KEEP | All 313 protected/operational/fixture documents, all 9 untracked notes/templates, active contracts and decision lineage |
| DOCUMENTS_TO_ARCHIVE | 14 historical candidates for navigation or a later reviewed move; no move in this phase |
| DELETE_CANDIDATES | No authored document or protected export has sufficient deletion evidence; generated caches only are conditional future candidates |
| REGENERABLE_CACHE_CANDIDATES | 298 eligible directory groups / 3,004 files; protected data/evidence cache paths excluded |
| ESTIMATED_SPACE_SAVINGS | Current pass: 0 bytes. Future cache ceiling 2.048 GB; optional 3-checkout review ceiling 1.334 GB, with overlap described below |
| PROTECTED_FILES_CHANGED | 0 |
| FILES_DELETED | 0 |
| PUSH_STATUS | Existing commit 884f28b pushed by normal fast-forward; audit-report commit remains local |

## Push verification

- Verified local branch and HEAD exactly match the requested baseline. Remote feature HEAD before push was `f0ec2635080f5d8e33c7f93027b907005670f5ef`.
- The linear push necessarily included predecessor `157088d0d8f73f0f98129b9815c9bab98e77ea1e` (PowerShell/TLS operator setup) plus `884f28b`. Both committed trees were checked for private runtime/database/PDF/key material; no uncommitted source or owner document was staged or uploaded.
- Normal Git push used the exact source SHA and feature destination; no force, rebase or merge. Remote feature HEAD afterward: `884f28b02a7ece1d061eac928e3423c93f5cf592`.
- Remote main before/after: `1d7706a90f9270fa91e245c671ccb7ed9ce98777`; local main: `79a477fc9703d99abf9c0c352b6cb3df18506e07`. Neither was modified.
- Only the explicitly requested Git remote operations used the network. No provider, browser, financial API or real LLM request was made during the audit.

## How to read the worktree inventory

- HEADs and WIP are the pre-report snapshot. Committing this report adds one documentation commit only to W13 afterward.
- T/U counts mean modified tracked paths / individual untracked files (`--untracked-files=all`), not collapsed directory entries. Staged paths are included in T.
- Local main is older/divergent, so report both exact graph differences from local `main` and from the locally verified `origin/main` SHA. A commit being absent from main does not mean it is absent from all other worktrees.
- Exclusive counts are commits absent from origin/main and from every other checkout HEAD. Exact ancestry is used for containment; dirty working files are never assumed to be copied by ancestry.
- Sizes are logical file lengths, excluding shared `.git` storage and reparse targets. Compression, hard links, sparse allocation and filesystem overhead were not measured; totals are upper-bound estimates, not guaranteed reclaimed disk space.

| ID | Absolute path | Branch | HEAD at audit | T/U | Logical size |
| --- | --- | --- | --- | ---: | ---: |
| W1 | `C:/Users/PC/Downloads/vn30-intelligence-agent` | `main` | `79a477fc9703d99abf9c0c352b6cb3df18506e07` | 11/88 | 1.555 GB |
| W2 | `C:/Users/PC/.codex/worktrees/adaptive-news-integration/vn30-intelligence-agent` | `codex/adaptive-news-integration-v1` | `e64986e0cb011d8af40a122e14d5bb47f540ba22` | 0/0 | 0.536 GB |
| W3 | `C:/Users/PC/.codex/worktrees/technical-development-reconciled/vn30-intelligence-agent` | `codex/technical-development-reconciled` | `e64986e0cb011d8af40a122e14d5bb47f540ba22` | 17/65 | 0.745 GB |
| W4 | `C:/Users/PC/.codex/worktrees/technical-signal-v1-checkpoint/vn30-intelligence-agent` | `codex/technical-signal-v1-checkpoint` | `84cb2ef5141010b6e6230f3146f5e1e34216adc8` | 9/13 | 0.225 GB |
| W5 | `C:/Users/PC/.codex/worktrees/woofi-explore-refresh/vn30-intelligence-agent` | `codex/woofi-explore-refresh` | `3d56bf1fa23eeab6ede48bf3989dcf783c6ddc39` | 0/0 | 0.757 GB |
| W6 | `C:/Users/PC/.codex/worktrees/woofi-integration-readiness/vn30-intelligence-agent` | `codex/woofi-integration-readiness` | `2ea10490de0c2120d2b9ddcc44a509868a88079b` | 0/0 | 0.766 GB |
| W7 | `C:/Users/PC/.codex/worktrees/woofi-news-relevance-v2` | `codex/woofi-news-relevance-v2` | `4f17d99d65413f26b896d9b98ee56a1ebc588fb8` | 0/0 | 0.996 GB |
| W8 | `C:/Users/PC/.codex/worktrees/woofi-runtime-compatibility-v1/vn30-intelligence-agent` | `codex/runtime-compatibility-ingestion-v1` | `135a31fa88f4e275015701024dd40bb585cfcb4f` | 0/0 | 0.533 GB |
| W9 | `C:/Users/PC/.codex/worktrees/woofi-technical-operational-v1/vn30-intelligence-agent` | `codex/woofi-technical-operational-v1` | `30fdff2175dc7709b3e5aa02f1c52213b2ca254a` | 0/0 | 0.741 GB |
| W10 | `C:/Users/PC/.codex/worktrees/woofi-technical-stock-detail/vn30-intelligence-agent` | `codex/woofi-technical-stock-detail` | `df5a4569fac70dd9df5cc155aaf6027316d27c4f` | 0/0 | 0.821 GB |
| W11 | `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/supervisor-listener-fix` | `codex/woofi-supervisor-pid-reuse-v1` | `75deb9b55a57bee30ed5f42403f26d655ab6209d` | 0/0 | 0.010 GB |
| W12 | `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/vn30-intelligence-agent` | `codex/woofi-market-board-correction` | `548e10d855b3d470b4eb2019ae027118a0505b14` | 0/0 | 1.497 GB |
| W13 | `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/woofi-financial-data` | `feature/financial-data-intelligence` | `884f28b02a7ece1d061eac928e3423c93f5cf592` | 6/10 | 9.482 GB |
| W14 | `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/woofi-latest-app-integration-v1` | `codex/woofi-latest-app-integration-v1` | `b88f6f00250ea1a3ddc2a87ce7aabb95653d6573` | 0/0 | 0.265 GB |
| W15 | `C:/Users/PC/.codex/worktrees/woofi-watchlist-intelligence-v1/vn30-intelligence-agent` | `codex/woofi-product-acceptance-v1` | `ed9862cb35e82279c2c6c143a535907a9839371e` | 0/0 | 0.583 GB |

### Commit containment and removal review

| Worktree | Not local main | Not origin/main | Patch-unique vs origin/main | Exclusive across checkouts | Same committed work retained in | Removal proposal |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| W1 | 0 | 1 | 1 | 1 | No other checkout contains this HEAD | KEEP primary/current development |
| W2 | 3 | 0 | 0 | 0 | W3 (same HEAD), W13, W4 and 10 more | Conditional review; verify owner/runtime pin before any future proposal |
| W3 | 3 | 0 | 0 | 0 | W2 (same HEAD), W13, W4 and 10 more | NO: uncommitted work |
| W4 | 4 | 0 | 0 | 0 | W13, W5, W6 and 8 more | NO: uncommitted work |
| W5 | 9 | 0 | 0 | 0 | W13, W6, W7 and 6 more | Review only; protected ignored files must remain recoverable |
| W6 | 10 | 0 | 0 | 0 | W13, W7, W8 and 5 more | Review only; protected ignored files must remain recoverable |
| W7 | 17 | 0 | 0 | 0 | W13, W9, W11 and 2 more | Review only; protected ignored files must remain recoverable |
| W8 | 14 | 0 | 0 | 0 | W13, W7, W9 and 3 more | Conditional review; verify owner/runtime pin before any future proposal |
| W9 | 23 | 1 | 1 | 1 | No other checkout contains this HEAD | NO: exclusive committed work |
| W10 | 8 | 0 | 0 | 0 | W13, W5, W6 and 7 more | Review only; protected ignored files must remain recoverable |
| W11 | 45 | 5 | 5 | 5 | No other checkout contains this HEAD | NO: exclusive committed work |
| W12 | 68 | 28 | 28 | 0 | W13, W14 | Review only; protected ignored files must remain recoverable |
| W13 | 108 | 68 | 68 | 28 | No other checkout contains this HEAD | KEEP primary/current development |
| W14 | 80 | 40 | 40 | 0 | W13 | Conditional review; verify owner/runtime pin before any future proposal |
| W15 | 13 | 0 | 0 | 0 | W13, W7, W8 and 4 more | Review only; protected ignored files must remain recoverable |

W2 and W3 have identical committed HEADs, but W3 has extensive WIP; they are not interchangeable working directories. W9 retains one uncontained commit, and W11 retains five. W1 has its own unshared main commit plus WIP. W13 is active financial/AI development with WIP. These are retention blockers, regardless of directory age.

A process-path check found two other project Node processes referring to W1; no candidate worktree matched an observed app/collector command path. No listener was observed on 3000/3001/8000/8001/8765. These limited checks do not establish installed Supervisor source pins, dormant tasks, backups, or user ownership. Runtime/owner verification remains required for every future removal decision.

### Protected ignored files and cache totals

| Worktree | Protected ignored files | Protected logical size | Eligible cache logical size |
| --- | ---: | ---: | ---: |
| W1 | 422 | 265.27 MB | 216.51 MB |
| W2 | 0 | 0.00 MB | 72.08 MB |
| W3 | 35 | 0.26 MB | 66.95 MB |
| W4 | 3 | 0.77 MB | 2.99 MB |
| W5 | 347 | 4.44 MB | 72.55 MB |
| W6 | 994 | 17.82 MB | 68.38 MB |
| W7 | 1 | 0.00 MB | 72.05 MB |
| W8 | 0 | 0.00 MB | 65.62 MB |
| W9 | 5 | 1.29 MB | 65.58 MB |
| W10 | 7 | 0.95 MB | 139.59 MB |
| W11 | 0 | 0.00 MB | 1.76 MB |
| W12 | 8 | 45.29 MB | 441.43 MB |
| W13 | 1964 | 8079.78 MB | 416.34 MB |
| W14 | 0 | 0.00 MB | 250.84 MB |
| W15 | 24 | 20.84 MB | 95.13 MB |

Protected ignored entries include private runtime/data paths, databases, PDFs, environment/secret files and operational evidence. Their contents were not enumerated as credentials or copied into this report. A clean `git status` does not protect these files from checkout removal.

## Content-level review of the remaining 313 documents

- The Phase 1 manifest had inspected these through metadata. This phase read all local TXT/Markdown/HTML content and examined every distinct PDF payload without contacting a provider.
- Corpus: 246 TXT, 56 files named PDF, 7 Markdown and 4 HTML. There are 19 unique byte payloads among the 56 PDF-named files.
- 287 files were reviewed through complete text reads/extraction; 20 scanned-PDF copies correspond to four unique originals visually classified from rendered cover and page 3; six PDF-named files were read as non-PDF response bodies.
- Scanned originals were confirmed as financial statements, not disposable exports. Visual sampling establishes their document role, not a new financial/numerical qualification of every page.
- All 263 text/response payloads decoded as UTF-8 without replacement characters. No holdout-named case file was included; the sealed evaluation datasets were not opened.
- Extracted financial values, original tables, raw document text, API keys, account evidence and rendered source pages are not included in this commit. Original files are read-only and retained.

| Content role | Files | Decision |
| --- | ---: | --- |
| saved acquisition/research or validation evidence | 15 | KEEP; protected evidence, operations or fixture dependency |
| scanned original financial statement source; protected | 20 | KEEP; protected evidence, operations or fixture dependency |
| original financial/source/provenance PDF; protected even when duplicated | 30 | KEEP; protected evidence, operations or fixture dependency |
| statement text extraction or validation log supporting the financial evidence chain | 233 | KEEP; protected evidence, operations or fixture dependency |
| saved plain-text HTTP/error response mislabeled as PDF | 3 | KEEP; protected evidence, operations or fixture dependency |
| saved HTML response mislabeled as PDF | 3 | KEEP; protected evidence, operations or fixture dependency |
| saved source/access response evidence | 3 | KEEP; protected evidence, operations or fixture dependency |
| current local credential-storage operating documentation; untracked owner work | 1 | KEEP; protected evidence, operations or fixture dependency |
| dated data inventory or missing-metric evidence | 2 | KEEP; protected evidence, operations or fixture dependency |
| source-rights/provenance decision record | 2 | KEEP; protected evidence, operations or fixture dependency |
| synthetic/community parser fixture, not a temporary export | 1 | KEEP; protected evidence, operations or fixture dependency |

### PDF extension mismatches

These are captured access/error/application responses rather than financial PDFs. They do not establish statement coverage. They remain protected source-access evidence; any future relabeling needs an owner-reviewed path/reference manifest, not deletion or a new acquisition.

| Exact relative path under W13 | Actual content | Bytes | Decision |
| --- | --- | ---: | --- |
| `.local/free-data-v3-research/fpt-annual-2025.pdf` | text response | 17 | KEEP original failure evidence |
| `.local/free-data-v3-research/hpg-audited-2025.pdf` | text response | 17 | KEEP original failure evidence |
| `.local/free-data-v4-research/hpg-annual-2024.pdf` | text response | 17 | KEEP original failure evidence |
| `.local/free-data-v4-research/ssi-annual-2025.pdf` | HTML response | 25727 | KEEP original failure evidence |
| `.local/free-data-v4-research/vnm-annual-2023.pdf` | HTML response | 562553 | KEEP original failure evidence |
| `.local/free-source-research/fpt-annual-2025.pdf` | HTML response | 7342 | KEEP original failure evidence |

### Duplicate and derived export findings

- Found **12 exact byte-duplicate groups**, representing **115 files / 103 extra copies** within this protected corpus. Extra logical bytes: **577,567,824 (577.57 MB)**.
- These are run-specific source/derived-evidence copies, predominantly inside separate `.local/` acquisition/review bundles. Identical bytes do not make their provenance paths, pinned hashes or audit references interchangeable.
- All duplicate groups remain KEEP and are excluded from savings estimates. No hardlink deduplication, consolidation, source deletion or journal migration is proposed.
- The 233 statement extraction/validation TXT files are derived outputs supporting the financial evidence chain. Reproducing them can require exact source bytes, extraction/OCR versions and operator review; their presence in `.local/` independently makes them protected in this task.
- Other saved acquisition/validation reports remain audit evidence. No private export was established as independently disposable. Full per-file hashes, role classifications and duplicate membership are retained only in the local audit workspace.

## Untracked documentation review

All nine owner notes/templates were content-reviewed. They are kept byte-identical and are not moved, deleted or included in this audit commit.

| Exact path | Evidence and usefulness | Action / risk / recovery |
| --- | --- | --- |
| `docs/FINANCIAL_DATA_INFRASTRUCTURE_FEASIBILITY_2026_10_22.md` | Budget, acquisition and storage tradeoffs; retain its dated feasibility assumptions, rather than treating them as current coverage counts. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/operator-readiness/groq-first-trial/free-plan-review.json.template` | Intentionally unfilled account review. Null account assertions are safeguards, not broken or obsolete private configuration. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/operator-readiness/groq-first-trial/gateway-config.json.template` | Intentionally unapproved synthetic-run configuration; null consent is not authorization. Retain the placeholder template. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/operator-readiness/groq-first-trial/README.md` | Dated pre-live audit and manual operations procedure. Keep its historical claims; later add navigation to the persistent credential procedure after a separately reviewed documentation decision. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/VNSTOCK_ECOSYSTEM_INTEGRATION_RESEARCH.md` | Reusable ecosystem mapping and source/entitlement constraints; useful integration reference. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/VNSTOCK_FOUNDER_MEETING_AUDIT_2026_10_24.md` | Meeting evidence, source qualification and unresolved provider questions; protected technical audit. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/VNSTOCK_FOUNDER_TECHNICAL_QUESTIONS.md` | Actionable provider/rights questions; retain until the owner resolves or records answers. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/WOOFI_GROQ_CREDENTIAL_STORAGE.md` | Current Windows Credential Manager procedure matching the uncommitted operator implementation; important operations documentation. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |
| `docs/WOOFI_GROQ_GATEWAY_INTEGRATION.md` | Groq mapping, contract parity, budget accounting and security gates; dated research/implementation record. | KEEP_UNTRACKED; owner review before any checkpoint/move; retain original bytes |

The credential-storage note and operator source/tests form uncommitted work that should be reviewed together in a separately scoped checkpoint. This audit does not open Windows Credential Manager, replace a key, create an approval, read the private Groq account files, or reset the stopped ledger.

## Obsolete instructions, superseded plans and historical reports

| Exact path / section | Content evidence | Recommendation | Risk / recovery |
| --- | --- | --- | --- |
| `README.md` / Interface and language | Says the interface is permanently English-only; `AGENTS.md` requires EN/VI and existing localization documentation/implementation describes both | Later align the current setup summary; keep the root README and its dated feature context | Documentation-only review against current contracts; reversible patch |
| `README.md` / MVP roadmap and boundaries | Broadly lists AI/LLM as unimplemented while tracked local assistant/evaluation/gateway pilots exist | Clarify prototype vs production capability in a separate docs update; do not infer public inference readiness | Preserve gated inference boundaries; reversible patch |
| `research/NEXT_PHASE_ROADMAP.md` | Explicitly separates a V4 checkpoint from a superseded historical record | KEEP dated reference; take present priorities from CONTEXT/current contracts | Older qualification/rights limitations may remain important; no whole-file deletion |
| `research/REMAINING_DATA_GAPS.md` | Contains V4 qualified-data scope and a historical gap section | KEEP; current acquisition counts do not supersede qualification/provenance gaps | Do not relabel prior reported quality metrics as current coverage |
| `docs/TECHNICAL_D2_DATA_FRAME_PIT_DECISION.md` and `_V2.md` | V2 explicitly revises V1; V3 records the succeeding approved authority and preserved lineage | Prior normative versions are superseded for future generation but remain required governance history | KEEP original bytes and review-chain references |
| `docs/WOOFI_UI_UX_PROGRESS.md` | Interim checkpoint overlaps the final `WOOFI_UI_UX_REDESIGN_V1.md` delivery record | Historical navigation/archive candidate; retain factual/audit differences | Later move only after reference and owner review |

No whole authored document is certified unnecessary for deletion. Archive candidates below retain important audit/research conclusions. Three newly confirmed V3 records explicitly label themselves historical and link their V4 successor; this is content evidence of supersession, not an inference from filename age.

| Historical/archive candidate | Evidence | Proposed action | Space saving |
| --- | --- | --- | ---: |
| `docs/ADAPTIVE_NEWS_INTEGRATION_V1.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/DAY0_REPORT.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/SECTION1_REPORT.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/SECTION1_6_REPORT.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/UI_REFRESH_REPORT.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/SECTION2_PHASE1_REPORT.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/SECTION2_PHASE2_REPORT.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/WOOFI_UI_UX_PROGRESS.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/WOOFI_UI_UX_REDESIGN_V1.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/PRODUCT_ACCEPTANCE_V1_2026-10-10.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `docs/WOOFI_INTEGRATION_READINESS_2026-10-10.md` | Completed milestone scope already separated by the Phase 1 historical catalog | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `research/SSTOCK_FEATURE_COMPARISON_V3.md` | Explicit Historical checkpoint notice with V4 successor links | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `research/DASHBOARD_VERIFICATION_V3.md` | Explicit Historical checkpoint notice with V4 successor links | Archive navigation first; physical move deferred; keep audit content | 0 bytes |
| `research/FINANCIAL_INTELLIGENCE_V3_DELIVERY.md` | Explicit Historical checkpoint notice with V4 successor links | Archive navigation first; physical move deferred; keep audit content | 0 bytes |

Current financial SQLite/storage/coverage/qualification/serving, AI evaluation/gateway, source-rights records, provenance, governance approvals and original provider evidence require retention. The V5.x reusable infrastructure is not obsolete because a later version or pilot exists.

## Prioritized cleanup proposals and savings

No proposal below is permission to execute. Every future deletion needs an exact reviewed manifest, resolved runtime ownership and the owner's explicit destructive-cleanup decision.

| Priority | Exact target or inventory IDs | Evidence | Maximum logical saving | Risk | Recovery / prerequisite |
| --- | --- | --- | ---: | --- | --- |
| P1 | Eligible compiler/cache paths listed below | Ignored, generated cache files; excludes all protected data/provenance paths | 2.048 GB across 298 groups | Low/medium: rebuild cost, live compiler ownership | Verify consumers stopped; recreate with existing pinned build/test tooling |
| P2 | W2, W8, W14 absolute roots in the worktree table | Clean; exact commits contained elsewhere; no detected protected ignored files | 1.334 GB whole-checkout upper bound | Medium: unknown source pins/tasks, generated environment cost | Confirm owner/runtime pin; retain branch refs; a future git worktree add from the preserved branch recovers tracked content, not ignored custom data |
| P2 blocked | W5, W6, W7, W10, W12, W15 | Clean and commit-covered, but protected ignored data/evidence exists | Not counted | High until private files are retained | Explicit private-data retention and verified owner backup; keep every branch/history |
| P0 retention | W1, W3, W4, W9, W11, W13 | Primary/active, WIP or uncontained commits | Not counted | Losing source, research or local work | Keep; separately review/checkpoint WIP or exclusive history |
| P3 | Historical document table and untracked review table | Navigation/status clarity; small text files with audit value | 0 bytes for moves | Broken refs or lost historical decisions | Keep bytes; reviewed link-aware moves only |
| Excluded | All `.local/`, private data/config, source PDFs, SQLite, Groq artifacts/credentials/ledgers and source rights/audits | Explicit retention boundary | 0 eligible bytes | Irrecoverable provenance/authorization loss | Preserve original files and immutable revisions |

The three optional whole-checkout candidates overlap **388,536,757 bytes (388.54 MB)** of eligible caches. Do not add both totals. Cache cleanup plus those three checkouts has a combined non-overlapping upper bound of **2,993,056,371 bytes (2.993 GB)**, subject to all future approvals and runtime checks. Current reclaimed space is **0**.
Protected cache-shaped paths: **77 groups / 2,243,288 bytes** under data/provenance/validation paths were explicitly excluded. Likewise the 577.57 MB of protected duplicate payloads is not a saving candidate.

### Highest-value exact cache paths

These compiler-cache directories account for most of the eligible cache bytes. The remaining eligible bytecode/pytest cache leaves are inventoried per worktree in the local audit data; no wildcard delete or full `.next`/environment reset is proposed.

| Exact absolute path | Files | Logical size | Risk / recovery |
| --- | ---: | ---: | --- |
| `C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\vn30-intelligence-agent\frontend\.next\cache` | 186 | 440.47 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-financial-data\frontend\.next\cache` | 84 | 410.88 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-visual-news-v1\woofi-latest-app-integration-v1\frontend\.next\cache` | 33 | 249.51 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\Downloads\vn30-intelligence-agent\frontend\.next\cache` | 253 | 213.84 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-technical-stock-detail\vn30-intelligence-agent\frontend\.next\cache` | 49 | 136.52 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-watchlist-intelligence-v1\vn30-intelligence-agent\frontend\.next\cache` | 70 | 91.82 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\adaptive-news-integration\vn30-intelligence-agent\frontend\.next\cache` | 24 | 70.10 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-explore-refresh\vn30-intelligence-agent\frontend\.next\cache` | 48 | 69.46 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-news-relevance-v2\frontend\.next\cache` | 30 | 68.70 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-runtime-compatibility-v1\vn30-intelligence-agent\frontend\.next\cache` | 22 | 65.62 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-technical-operational-v1\vn30-intelligence-agent\frontend\.next\cache` | 16 | 65.39 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\woofi-integration-readiness\vn30-intelligence-agent\frontend\.next\cache` | 22 | 65.16 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |
| `C:\Users\PC\.codex\worktrees\technical-development-reconciled\vn30-intelligence-agent\frontend\.next\cache` | 16 | 63.77 MB | Confirm compiler/runtime idle; existing Next build regenerates cache |

Installed `.venv/` and `node_modules/` are dependencies rather than the first cleanup target. They remain intact. Reinstalling them can need network/package availability and is outside this audit. Git objects, branches and checkout metadata are not space-reclamation candidates here.

## Minimal final structure

Keep the existing application directories and the small Phase 1 documentation layout. Do not introduce empty category trees or a second research hierarchy.

```text
main.py
frontend/
routers/
src/
scripts/
tests/
evaluation/
research/
  data/                 # retained source/research records
  provenance/           # protected originals and decisions
  sources/              # rights and provider reference
  validation/           # preserved acceptance/audit records
docs/
  README.md             # active navigation
  product/              # original product brief
  operations/           # current setup/policy
  archive/README.md     # historical catalog; original report paths stable
  ...existing contracts/reports at stable paths
.local/                 # protected, ignored private runtime/evidence
```

Future: review and checkpoint owner WIP separately; correct current README status wording; enrich historical navigation with the three explicit V3 records. Only after all dirty/untracked references are resolved should a populated set move to a new docs category. Archive moves reclaim no bytes and must not erase audit meaning.

## Complete WIP inventory by worktree

Each path below is relative to its exact absolute root in the worktree table. Untracked does not mean redundant. No file here is staged, moved or deleted by this audit.

### W1 - main

Tracked modifications:

- `CONTEXT.md`
- `frontend/app/components/Explore.tsx`
- `frontend/lib/translations.ts`
- `frontend/next-env.d.ts`
- `routers/stocks.py`
- `scripts/ingest_data.py`
- `src/corporate_actions/models.py`
- `src/corporate_actions/repository.py`
- `src/corporate_actions/storage.py`
- `src/db/session.py`
- `tests/test_data_reliability.py`

Untracked files:

- `.agents/skills/code-review/SKILL.md`
- `.agents/skills/code-review/agents/openai.yaml`
- `.agents/skills/diagnosing-bugs/SKILL.md`
- `.agents/skills/diagnosing-bugs/agents/openai.yaml`
- `.agents/skills/diagnosing-bugs/scripts/hitl-loop.template.sh`
- `.agents/skills/grill-with-docs/SKILL.md`
- `.agents/skills/grill-with-docs/agents/openai.yaml`
- `.agents/skills/setup-matt-pocock-skills/SKILL.md`
- `.agents/skills/setup-matt-pocock-skills/agents/openai.yaml`
- `.agents/skills/setup-matt-pocock-skills/domain.md`
- `.agents/skills/setup-matt-pocock-skills/issue-tracker-github.md`
- `.agents/skills/setup-matt-pocock-skills/issue-tracker-gitlab.md`
- `.agents/skills/setup-matt-pocock-skills/issue-tracker-local.md`
- `.agents/skills/setup-matt-pocock-skills/triage-labels.md`
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/tdd/agents/openai.yaml`
- `.agents/skills/tdd/mocking.md`
- `.agents/skills/tdd/tests.md`
- `.agents/skills/to-spec/SKILL.md`
- `.agents/skills/to-spec/agents/openai.yaml`
- `VN30_Intelligence_Wolf_Mascot_Assets/MASCOT_USAGE_GUIDE.md`
- `VN30_Intelligence_Wolf_Mascot_Assets/README.txt`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/01_curiosity.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/02_analyzing.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/03_opportunity.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/04_scanning.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/05_idle.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/06_value.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/07_watching.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/08_bullish.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/09_bearish.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/10_uncertain.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/11_neutral.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/12_insight.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/png_512_transparent/13_identity.png`
- `VN30_Intelligence_Wolf_Mascot_Assets/preview_all_mascots.png`
- `docs/DIVIDENDS_AUTO_V1.md`
- `docs/SECTION1_5_UI_REFRESH_V2.md`
- `docs/SECTION1_6_FINANCIAL_VISUALIZATION.md`
- `docs/SECTION1_DATA_ANALYTICS_FOUNDATION.md`
- `docs/TECHNICAL_CALIBRATION_EXPERIMENT.md`
- `docs/TECHNICAL_CALIBRATION_V2.md`
- `docs/TECHNICAL_V3_FINALIZATION_PHASE1.md`
- `docs/VALIDATION_PRELABEL_PROTOCOL.md`
- `docs/VALIDATION_V2_PRELABEL_PROTOCOL.md`
- `docs/VN30_Intelligence_Agent_DAY0_PLAN_EN.md`
- `docs/VN30_Intelligence_Agent_README.md`
- `frontend/AGENTS.md`
- `frontend/CLAUDE.md`
- `frontend/app/components/stock/StockDividends.tsx`
- `frontend/lib/dividends.ts`
- `frontend/tests/dividends.test.mjs`
- `research/provenance/technical_data_readiness_v1/DECISION_INVARIANCE_AUDIT.md`
- `research/provenance/technical_data_readiness_v1/decision_invariance_audit.py`
- `scripts/compare_materiality_calibration.py`
- `scripts/evaluate_development_v3.py`
- `scripts/evaluate_frozen_validation.py`
- `scripts/evaluate_validation_v2.py`
- `scripts/ingest_dividends.py`
- `scripts/prepare_development_v3.py`
- `scripts/prepare_validation.py`
- `scripts/prepare_validation_v2.py`
- `scripts/report_frozen_validation.py`
- `scripts/resume_calibration_v2.py`
- `scripts/run_calibration_v2.py`
- `skills-lock.json`
- `src/corporate_actions/ingestion.py`
- `src/corporate_actions/read.py`
- `src/corporate_actions/source.json`
- `src/corporate_actions/vsdc.py`
- `src/evaluation/calibration.py`
- `src/evaluation/calibration_v2.py`
- `src/evaluation/development_v3.py`
- `src/evaluation/development_v3_evaluation.py`
- `src/evaluation/review_artifacts.py`
- `src/evaluation/review_v2.py`
- `src/evaluation/validation_sampling.py`
- `src/evaluation/validation_v2.py`
- `tests/test_calibration_comparison.py`
- `tests/test_calibration_v2.py`
- `tests/test_decision_invariance_audit.py`
- `tests/test_development_v3.py`
- `tests/test_development_v3_evaluation.py`
- `tests/test_dividend_ingestion.py`
- `tests/test_frozen_validation.py`
- `tests/test_validation_sampling.py`
- `tests/test_validation_v2.py`
- `tests/test_validation_v2_evaluation.py`

### W2 - codex/adaptive-news-integration-v1

Tracked modifications: none. Untracked files: none.

### W3 - codex/technical-development-reconciled

Tracked modifications:

- `CONTEXT.md`
- `frontend/app/components/Explore.tsx`
- `frontend/lib/translations.ts`
- `main.py`
- `routers/stocks.py`
- `scripts/ingest_data.py`
- `src/corporate_actions/models.py`
- `src/corporate_actions/repository.py`
- `src/corporate_actions/storage.py`
- `src/db/session.py`
- `src/evaluation/benchmark/episodes.py`
- `src/evaluation/benchmark/facts.py`
- `src/evaluation/context.py`
- `src/materiality/__init__.py`
- `src/materiality/detectors.py`
- `src/materiality/service.py`
- `tests/test_data_reliability.py`

Untracked files:

- `docs/D1_FACTUAL_RUNTIME_V1.md`
- `docs/D4_RUNTIME_EPISODES_V1.md`
- `docs/D5_A_RANKING_PACKET_V1.md`
- `docs/D5_B1_EOD_RUNTIME_CONSUMER_V1.md`
- `docs/D5_B2_GATED_READ_ONLY_API_V1.md`
- `docs/DIVIDENDS_AUTO_V1.md`
- `docs/EOD_READINESS_CALENDAR_EVIDENCE_V1.md`
- `docs/TECHNICAL_CALIBRATION_EXPERIMENT.md`
- `docs/TECHNICAL_CALIBRATION_V2.md`
- `docs/TECHNICAL_V3_FINALIZATION_PHASE1.md`
- `docs/VALIDATION_PRELABEL_PROTOCOL.md`
- `docs/VALIDATION_V2_PRELABEL_PROTOCOL.md`
- `frontend/app/components/stock/StockDividends.tsx`
- `frontend/lib/dividends.ts`
- `frontend/tests/dividends.test.mjs`
- `research/provenance/technical_data_readiness_v1/DECISION_INVARIANCE_AUDIT.md`
- `research/provenance/technical_data_readiness_v1/decision_invariance_audit.py`
- `routers/technical.py`
- `scripts/compare_materiality_calibration.py`
- `scripts/evaluate_development_v3.py`
- `scripts/evaluate_frozen_validation.py`
- `scripts/evaluate_validation_v2.py`
- `scripts/ingest_dividends.py`
- `scripts/prepare_development_v3.py`
- `scripts/prepare_validation.py`
- `scripts/prepare_validation_v2.py`
- `scripts/report_frozen_validation.py`
- `scripts/resume_calibration_v2.py`
- `scripts/run_calibration_v2.py`
- `src/analytics/episodes.py`
- `src/analytics/factual.py`
- `src/corporate_actions/ingestion.py`
- `src/corporate_actions/read.py`
- `src/corporate_actions/source.json`
- `src/corporate_actions/vsdc.py`
- `src/evaluation/calibration.py`
- `src/evaluation/calibration_v2.py`
- `src/evaluation/development_v3.py`
- `src/evaluation/development_v3_evaluation.py`
- `src/evaluation/review_artifacts.py`
- `src/evaluation/review_v2.py`
- `src/evaluation/validation_sampling.py`
- `src/evaluation/validation_v2.py`
- `src/materiality/delivery.py`
- `src/materiality/episodes.py`
- `src/materiality/factual.py`
- `src/services/session_evidence.py`
- `src/services/technical_api.py`
- `src/services/technical_eod.py`
- `tests/test_calibration_comparison.py`
- `tests/test_calibration_v2.py`
- `tests/test_d1_runtime.py`
- `tests/test_d4_runtime.py`
- `tests/test_d5_packet.py`
- `tests/test_decision_invariance_audit.py`
- `tests/test_development_v3.py`
- `tests/test_development_v3_evaluation.py`
- `tests/test_dividend_ingestion.py`
- `tests/test_eod_readiness.py`
- `tests/test_frozen_validation.py`
- `tests/test_technical_daily_api.py`
- `tests/test_technical_eod_consumer.py`
- `tests/test_validation_sampling.py`
- `tests/test_validation_v2.py`
- `tests/test_validation_v2_evaluation.py`

### W4 - codex/technical-signal-v1-checkpoint

Tracked modifications:

- `CONTEXT.md`
- `routers/technical.py`
- `scripts/ingest_data.py`
- `src/db/session.py`
- `src/providers/ssi/__init__.py`
- `src/services/technical_api.py`
- `src/services/technical_eod.py`
- `tests/test_data_reliability.py`
- `tests/test_ssi_provider.py`

Untracked files:

- `docs/TECHNICAL_EOD_PERSISTENCE_V1.md`
- `docs/TECHNICAL_V1_FPT_FIRST_RECEIPT_2026-10-09.json`
- `docs/TECHNICAL_V1_FPT_SECURITY_RECEIPT_2026-10-09.json`
- `docs/TECHNICAL_V1_HOSE_PUBLICATION_2026-10-08.json`
- `docs/TECHNICAL_V1_HOSE_SESSION_INDEX_2026-07-01_2026-10-08.tsv`
- `docs/TECHNICAL_V1_OPERATIONAL_EVIDENCE_2026-10-09.md`
- `docs/TECHNICAL_V1_PROVISIONAL_OPERATIONAL_EOD_V1.md`
- `scripts/produce_technical_eod.py`
- `src/models/technical_eod.py`
- `src/services/provisional_eod.py`
- `src/services/technical_eod_store.py`
- `tests/test_provisional_eod.py`
- `tests/test_technical_eod_persistence.py`

### W5 - codex/woofi-explore-refresh

Tracked modifications: none. Untracked files: none.

### W6 - codex/woofi-integration-readiness

Tracked modifications: none. Untracked files: none.

### W7 - codex/woofi-news-relevance-v2

Tracked modifications: none. Untracked files: none.

### W8 - codex/runtime-compatibility-ingestion-v1

Tracked modifications: none. Untracked files: none.

### W9 - codex/woofi-technical-operational-v1

Tracked modifications: none. Untracked files: none.

### W10 - codex/woofi-technical-stock-detail

Tracked modifications: none. Untracked files: none.

### W11 - codex/woofi-supervisor-pid-reuse-v1

Tracked modifications: none. Untracked files: none.

### W12 - codex/woofi-market-board-correction

Tracked modifications: none. Untracked files: none.

### W13 - feature/financial-data-intelligence

Tracked modifications:

- `CONTEXT.md`
- `frontend/app/components/stock/FinancialAnalysisPanel.tsx`
- `frontend/app/components/stock/FinancialResearchCharts.tsx`
- `frontend/next-env.d.ts`
- `scripts/groq_trial_operator.py`
- `tests/test_groq_operator_setup.py`

Untracked files:

- `docs/FINANCIAL_DATA_INFRASTRUCTURE_FEASIBILITY_2026_10_22.md`
- `docs/VNSTOCK_ECOSYSTEM_INTEGRATION_RESEARCH.md`
- `docs/VNSTOCK_FOUNDER_MEETING_AUDIT_2026_10_24.md`
- `docs/VNSTOCK_FOUNDER_TECHNICAL_QUESTIONS.md`
- `docs/WOOFI_GROQ_CREDENTIAL_STORAGE.md`
- `docs/WOOFI_GROQ_GATEWAY_INTEGRATION.md`
- `docs/operator-readiness/groq-first-trial/README.md`
- `docs/operator-readiness/groq-first-trial/free-plan-review.json.template`
- `docs/operator-readiness/groq-first-trial/gateway-config.json.template`
- `scripts/groq_windows_credentials.py`

### W14 - codex/woofi-latest-app-integration-v1

Tracked modifications: none. Untracked files: none.

### W15 - codex/woofi-product-acceptance-v1

Tracked modifications: none. Untracked files: none.

## Exclusive commit retention evidence

The following commits are absent from origin/main and from every other checkout HEAD in this snapshot. Shared non-main history is counted in the table, without duplicating the full log for every ancestor checkout. These commit IDs are retention evidence; no branch or commit is removed.

### W1 - 1 exclusive commits

- `79a477fc9703d99abf9c0c352b6cb3df18506e07`

### W9 - 1 exclusive commits

- `30fdff2175dc7709b3e5aa02f1c52213b2ca254a`

### W11 - 5 exclusive commits

- `67aab03500b7ad4fe8c63e5d9c883a65f80b4364`
- `75deb9b55a57bee30ed5f42403f26d655ab6209d`
- `89d80318a3effa9b74df86517b877ee59ececf26`
- `b44aca1fbd9af7e99c9678bae6bf850119d85ebd`
- `e3b75bd2ae6e6d7a5b6f577296606d1fed59c574`

### W13 - 28 exclusive commits

- `0dbaf10399cb3124eb0a8b852a7009da61b8ec45`
- `157088d0d8f73f0f98129b9815c9bab98e77ea1e`
- `33b54908574c557b6844b56c087d4d1cb6f5da16`
- `3ba50faa12e15f493580aabe0157dd9a7945cd10`
- `47dc8b1abcbd11e7e6e0adae129f6ec1f5786c1b`
- `4c4b0c4fdb11b2e654fee7f86b52565414d7cc56`
- `591f665782f373132de6d6f06c631e1b8383b530`
- `5a88e5d7b5fc5ec2b38a4d40540a4997080a85a6`
- `6a01a50b9ddae56f1e88672e527e4f550a1328ad`
- `6f757cd7f9a645f154bb7337e7cdc6c772df855c`
- `74e576bb7951248ee7e7bd09260288e5e1b3cb37`
- `76afaea734f22874f1999f0c19c64439707cca8d`
- `829cfbe9627ce2a254fee26fca9ff65b478da676`
- `86000d34c96f7b27c8c68ca99cbb58a7f82eeaba`
- `884f28b02a7ece1d061eac928e3423c93f5cf592`
- `8ffb36f023e466cf2eb45e694ecc6965a624456c`
- `94baed824fc180140b98c9a73b6a4439d4bfdf26`
- `96cd85cfe131ad1a788b9c09bbf26e9a1a822429`
- `b11843f027ae3dc13553e0fe51da2e53240372a0`
- `b72d64d0511a3bec70afb9d92d27b920d415e1a0`
- `bdc70adeecad74b67cc1704074036eeefffce9fc`
- `cd194595c3fba3a5ca811464f07843daf9acf4cd`
- `d452f8e5f0dbddd50ff2061713f75660f053e5a2`
- `dd4425504e6ec98ae80ac5a4eaed5fd8dde350ae`
- `e2e42f610e83bfd8a4f17e43e1bdc6528835a836`
- `e65284bc6672310cf439253921b6ac0da8929652`
- `f0ec2635080f5d8e33c7f93027b907005670f5ef`
- `fdb531adcf02dd30df5f757fe9521926b0b20d0f`

Reproduce the exact graph counts without networking: `git rev-list --count main..<HEAD>`, `git rev-list --count origin/main..<HEAD>`, and `git merge-base --is-ancestor <HEAD> <keeper-HEAD>`. Patch-unique counts use `git rev-list --cherry-pick --right-only --no-merges origin/main...<HEAD>`.

## Preservation and delivery checks

- All original source documents, their hashes and the 15 checkout snapshots were recorded locally before inspection; content reads and PDF rendering wrote only new audit artifacts outside the repositories.
- No original/private file, SQLite database, source capture, credential, ledger, security approval, cache or worktree was moved, deleted, reset or modified. No branch/history was deleted or rewritten; the feature branch advances only through the authorized push and report commit.
- Original WIP hashes/statuses, checkout HEADs/branches and protected document hashes are checked before the report commit. Only this new Markdown audit report is staged.
- Main and origin/main refs remain pinned to the values above; the failed Groq ledger is checked against its existing immutable hash without resetting it.
- Markdown links and staged scope are checked. No application regression or live smoke is run because the audit changes no executable file.
- The audit commit is local only; the separately requested Phase 1 commit is already pushed. No new live approval is created.

### Measured final checks

- Verified all **15** worktree branches, HEADs and original statuses; **219** WIP file hashes remain identical.
- Verified **384,878** original file size/mtime entries, including **378,043** ignored entries, with no deletion or mutation.
- Rehashed all **313** reviewed protected documents: all unchanged. The failed Groq ledger hash and main refs are unchanged.
- Report uses literal exact paths; there are no new relative-link targets to break. Archive candidate paths and eligible cache directories all exist. Secret-pattern and staged-scope checks pass.
- Original/unrelated changes: **0**. Protected files changed: **0**. Files deleted: **0**. Worktrees removed/pruned: **0**. Application/provider API calls: **0**.
- Documentation/spec review: the report states content-review limits, conditional removal gates, source/evidence retention and non-overlapping savings estimates. No application regression was needed for this single Markdown addition.
