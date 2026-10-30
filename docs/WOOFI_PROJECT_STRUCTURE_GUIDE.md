# Woofi local project structure guide

Verified 25 October 2026. This guide describes the local filesystem and documentation layout. It does not change application architecture or authorize runtime/data operations.

## Which checkout to use

- Current financial/AI development: `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/woofi-financial-data`, branch `feature/financial-data-intelligence`.
- Main Git checkout: `C:/Users/PC/Downloads/vn30-intelligence-agent`. Its `main` branch and existing WIP are separate from this worktree.
- All 15 registered checkouts share `C:/Users/PC/Downloads/vn30-intelligence-agent/.git`. A worktree is a separate checkout, not an independent clone or a backup to delete.
- The financial worktree contains the newest registered commit and uncommitted credential/operator work. It descends from the latest-app integration checkout; a newer source checkout does not by itself mean it has been deployed.
- Always run `git rev-parse --show-toplevel`, `git branch --show-current` and `git status --short` before editing. Use the intended absolute working directory; do not reorganize a similarly named checkout by assumption.

| Registered checkout | Branch | HEAD at inventory |
| --- | --- | --- |
| `C:/Users/PC/Downloads/vn30-intelligence-agent` | `main` | `79a477fc9703` |
| `C:/Users/PC/.codex/worktrees/adaptive-news-integration/vn30-intelligence-agent` | `codex/adaptive-news-integration-v1` | `e64986e0cb01` |
| `C:/Users/PC/.codex/worktrees/technical-development-reconciled/vn30-intelligence-agent` | `codex/technical-development-reconciled` | `e64986e0cb01` |
| `C:/Users/PC/.codex/worktrees/technical-signal-v1-checkpoint/vn30-intelligence-agent` | `codex/technical-signal-v1-checkpoint` | `84cb2ef51410` |
| `C:/Users/PC/.codex/worktrees/woofi-explore-refresh/vn30-intelligence-agent` | `codex/woofi-explore-refresh` | `3d56bf1fa23e` |
| `C:/Users/PC/.codex/worktrees/woofi-integration-readiness/vn30-intelligence-agent` | `codex/woofi-integration-readiness` | `2ea10490de0c` |
| `C:/Users/PC/.codex/worktrees/woofi-news-relevance-v2` | `codex/woofi-news-relevance-v2` | `4f17d99d6541` |
| `C:/Users/PC/.codex/worktrees/woofi-runtime-compatibility-v1/vn30-intelligence-agent` | `codex/runtime-compatibility-ingestion-v1` | `135a31fa88f4` |
| `C:/Users/PC/.codex/worktrees/woofi-technical-operational-v1/vn30-intelligence-agent` | `codex/woofi-technical-operational-v1` | `30fdff2175dc` |
| `C:/Users/PC/.codex/worktrees/woofi-technical-stock-detail/vn30-intelligence-agent` | `codex/woofi-technical-stock-detail` | `df5a4569fac7` |
| `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/supervisor-listener-fix` | `codex/woofi-supervisor-pid-reuse-v1` | `75deb9b55a57` |
| `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/vn30-intelligence-agent` | `codex/woofi-market-board-correction` | `548e10d855b3` |
| `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/woofi-financial-data` | `feature/financial-data-intelligence` | `157088d0d8f7` |
| `C:/Users/PC/.codex/worktrees/woofi-visual-news-v1/woofi-latest-app-integration-v1` | `codex/woofi-latest-app-integration-v1` | `b88f6f00250e` |
| `C:/Users/PC/.codex/worktrees/woofi-watchlist-intelligence-v1/vn30-intelligence-agent` | `codex/woofi-product-acceptance-v1` | `ed9862cb35e8` |

## Application source stays stable

```text
main.py                 # single FastAPI entry point
routers/                # existing HTTP routes
src/                    # schemas, providers, analytics, services and persistence
scripts/                # existing CLI/operator tools
tests/                  # tests and sealed/synthetic fixtures
frontend/               # existing Next.js app, proxies, assets and frontend tests
evaluation/             # existing evaluation configuration
research/               # reusable research and protected evidence
docs/                   # documentation navigation and contracts
```

Run commands from the repository root unless the existing command explicitly says `cd frontend`. A document move does not change the working directory for its code examples. No Python package or TypeScript import was reorganized.

## Documentation locations

- Start at [`docs/README.md`](README.md) for current contract and operations links.
- Read [`CONTEXT.md`](../CONTEXT.md) for current domain decisions and [`AGENTS.md`](../AGENTS.md) for operating rules. Their authority is unchanged.
- `docs/product/` holds the original product brief. It expresses the North Star; its initial MVP/provider/stack proposals are historical context, not a replacement for current contracts.
- `docs/operations/` holds the skill setup instructions and browser policy. Existing runtime manuals remain at their stable paths and are linked by the index.
- [`docs/archive/README.md`](archive/README.md) catalogs historical milestones. Physical reports are retained at their current paths because they contain audit history or have preserved references.
- Existing V5.x financial, AI evaluation and gateway reports stay at root `docs/` when moving them would break dirty/untracked notes or disturb evidence/operational references.
- Keep future integration contracts with related current integration documents and link them from the index. Create `docs/integrations/`, `docs/ai/` or another category only when a reviewed set of documents can actually move there; do not pre-create empty trees.
- Keep reusable source/product research in `research/` with its existing subfolders. Source-rights, original provenance, recorded data and screenshots stay with their evidence bundles, rather than being moved into a generic archive.
- Local untracked feasibility/Vnstock/meeting/Groq notes stay where the owner created them until separately approved. They are not silently committed or moved.

## Private runtime and generated files

- `.local/` is ignored and holds private financial SQLite journals, captures, source PDFs, backups and local pilot results. Existing exact paths are dependencies for scripts and reproducibility; this cleanup did not open their contents or move them.
- `%LOCALAPPDATA%/Woofi/GroqTrial-*` contains private operator configs, account evidence, approvals, TLS material, reports and immutable failed-run ledgers. Its contents and Windows Credential Manager were not inspected or changed by this task.
- `.env`/local secret files are never documentation input or commit candidates. The tracked `.env.example` is an example, not a secret store.
- `data/` is broadly ignored, but tracked `data/corporate_actions/verified_v1.json` is an intentional fixture exception. Check Git status instead of assuming all similarly named folders are disposable.
- `.venv/`, `frontend/node_modules/`, `.next/`, pytest caches and bytecode are generated tooling/build state. They were inventoried but not deleted/reset. Rebuildability is not permission to remove a running application's files.
- Git metadata and every worktree are retained. Do not merge copies, remove a checkout or relocate a runtime through a documentation cleanup.

## Naming and avoiding new clutter

1. Use a descriptive topic name and preserve meaningful version/date suffixes. Keep current established basenames unless a reviewed rename has a concrete benefit.
2. Give each new report its scope, date, source/evidence boundary, result, limitations and owner/consumer. Separate a proposal from observed results.
3. Add a short entry to the documentation index. Link current contracts and historical evidence separately; do not duplicate their conclusions into another competing canonical context file.
4. Use document-relative Markdown links. For a move, check structured/executable references as well as Markdown links and preserve any dirty/untracked referring document.
5. Classify before archiving: active contract, useful reference, historical candidate, overlap candidate, generated output or protected evidence. Similar names and older versions are not duplicate evidence.
6. Preserve audit trails, legal/source-rights records and original sources. Keep candidate deletions as proposals until specifically authorized; never clear runtime ledgers to obtain another attempt.
7. A documentation-only commit should contain only reviewed moves, navigation and reports. Do not stage unrelated source changes, owner notes, private data, caches or credentials.
