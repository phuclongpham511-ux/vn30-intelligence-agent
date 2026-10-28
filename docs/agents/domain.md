# Domain Documentation Layout

This repository uses a **single-context** domain documentation layout.

Primary domain glossary:
- `/CONTEXT.md`

Architecture / implementation decisions:
- existing reports and plans under `/docs/`;
- future durable architecture decisions may be recorded under `/docs/adr/` when the decision is genuinely load-bearing.

Agent operating rules:
- `/AGENTS.md`

Frontend design contract:
- `/frontend/DESIGN.md`

Consumers should read `CONTEXT.md` before introducing or renaming domain concepts. Frontend work should additionally read `frontend/DESIGN.md`.
