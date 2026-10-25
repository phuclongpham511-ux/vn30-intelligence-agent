# AGENTS.md

## Project operating rules

Read `CONTEXT.md` before making product or backend changes. When touching the frontend, also read `frontend/DESIGN.md`.

### Browser isolation and authorization

- Prefer the Codex Integrated Browser: the browser pane inside Codex Desktop. It may be used for Woofi development, public research, localhost access, UI inspection, screenshots, and acceptance when a browser-control tool is actually exposed and supports the requested operation.
- Before browser work, inspect the current session's available tools and verify that the selected tool controls the Codex Integrated Browser and supports the intended action. A visible browser pane alone does not prove that an agent-control capability exists. Do not invent or assume unsupported browser tools.
- A genuine Codex Cloud Browser may be used when it is actually available, including in another execution environment. It is not required when the Codex Integrated Browser is available and supported.
- Never launch, control, attach to, or interact with the user's Personal External Browser, including Chrome, Edge, Firefox, existing profiles or sessions, tabs, debugging ports, or desktop computer-control tools. Do not access personal history, cookies, passwords, extensions, authentication sessions, or unrelated websites.
- Do not launch external local browser automation frameworks or use hidden processes, alternate launchers, or other methods to bypass an integrated-browser restriction or host execution policy. A different browser environment requires explicit authorization for that task.
- If no supported Codex browser-control capability is available, or the supported browser cannot reach the target (including localhost), stop browser work, report the precise capability or connectivity limitation, and keep visual acceptance pending. Do not substitute HTTP checks or generated HTML for visual evidence.
- This policy remains in force until the user explicitly changes or revokes it.

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
- The UI supports English and Vietnamese. Translate product chrome only; preserve original source evidence.

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

Repo-local Codex skills may be installed under the Agent Skills convention. The recommended set and install commands are documented in `docs/operations/AGENT_SKILLS_SETUP.md`.

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
