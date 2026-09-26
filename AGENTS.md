# AGENTS.md

## Project operating rules

Read `CONTEXT.md` before making product or backend changes. When touching the frontend, also read `frontend/DESIGN.md`.

### Architecture invariants

- Keep exactly one root `main.py` and one `app = FastAPI()`.
- Reuse existing schemas, analytics, providers, and services before adding parallel abstractions.
- Deterministic Python is the numerical ground truth. AI may explain computed outputs but must not silently recalculate or rewrite them.
- Keep ticker support dynamic. Seed tickers are fixtures, not the supported universe.
- Never add ticker-specific business logic such as `if ticker == "FPT"`.
- Missing data stays missing. Do not replace unavailable values with zero or fabricated fallbacks.
- Preserve source/provenance fields and explicit fixture flags.
- Do not use holdout historical cases for calibration, review queues, or development summaries.
- No BUY/SELL/HOLD recommendation logic.

### Product invariants

- North Star: help the user know what deserves attention, not give them more data.
- Materiality is attention-worthiness, not bullishness, future-return prediction, or investment advice.
- Raw evidence must remain inspectable behind insights.
- Preferences may change ranking, not factual reality.
- The UI is English-only.

### Working style

Prefer small vertical slices and existing test seams.

For meaningful feature work:
1. align on the spec and domain terms;
2. write or confirm tests at the highest useful public seam;
3. implement the smallest coherent slice;
4. run focused tests during the change;
5. run the full relevant regression suite at the end;
6. review the diff against both the spec and repository standards.

Do not perform opportunistic architecture refactors unless the current task is blocked by real architectural friction.

### Agent skills

Repo-local Codex skills may be installed under the Agent Skills convention. The recommended set and install commands are documented in `docs/AGENT_SKILLS_SETUP.md`.

Use skills only when the task matches:
- `grill-with-docs`: resolve a substantial design decision before implementation.
- `to-spec`: convert an already-resolved discussion into an implementation spec.
- `tdd`: implement behavior through a red/green feedback loop.
- `diagnosing-bugs`: reproduce and isolate a real bug before fixing it.
- `code-review`: review a completed diff against standards and its originating spec.
- `setup-matt-pocock-skills`: reconfigure skill metadata only when tracker/domain-doc setup changes.

### Project knowledge

- Domain vocabulary: `CONTEXT.md`
- Frontend design contract: `frontend/DESIGN.md`
- Issue tracker rules: `docs/agents/issue-tracker.md`
- Domain-doc layout: `docs/agents/domain.md`
- Existing implementation reports: `docs/`
