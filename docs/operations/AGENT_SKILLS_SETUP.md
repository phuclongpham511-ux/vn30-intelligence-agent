# Codex Agent Skills Setup

This project uses a small curated subset of Matt Pocock's engineering skills.

Source:
- https://github.com/mattpocock/skills

The goal is to improve engineering discipline without turning the repository into a workflow framework.

## Recommended skills

Install only:

```text
setup-matt-pocock-skills
grill-with-docs
to-spec
tdd
diagnosing-bugs
code-review
```

Do not install the full set unless there is a concrete need.

## Installation

From the repository root, use the universal Agent Skills installer:

```powershell
npx skills@latest add mattpocock/skills
```

In the interactive picker:

1. select Codex as the target agent;
2. select the six skills listed above;
3. make sure `setup-matt-pocock-skills` is included;
4. install them as editable project skills rather than relying on a global hidden workflow.

The upstream project currently uses `skills.sh` as the supported installation path for Codex. A native Codex plugin is not required.

After installation, run the setup skill once.

Recommended answers for this repository:

```text
Issue tracker: GitHub
Triage workflow: skip unless the triage skill is later installed
Domain docs: single-context
Domain glossary: CONTEXT.md
Architecture decisions: docs/adr/ when needed
Agent instruction file: AGENTS.md
```

This repository already contains the intended setup files, so the setup skill should preserve them rather than create duplicates.

## Invocation

Use skills deliberately.

Examples:

```text
$grill-with-docs
```

Use for a substantial unresolved product or architecture decision.

```text
$to-spec
```

Use after the decision is already resolved and the conversation should become an implementation spec.

```text
$tdd
```

Use for behavior changes where a stable public seam exists.

```text
$diagnosing-bugs
```

Use when a real bug must first be reproduced and isolated.

```text
$code-review
```

Use after implementation, with an explicit fixed point such as the pre-feature commit.

## Do not over-orchestrate

Avoid chaining skills just because they exist.

Normal flow:

```text
decision needed?
→ grill-with-docs

decision already made?
→ to-spec

implementation
→ tdd where useful

unexpected failure
→ diagnosing-bugs

completed diff
→ code-review
```

Do not use architecture-improvement, ticket decomposition, wayfinding, or deep research skills unless the project actually develops a problem that requires them.

## OpenDesign

OpenDesign is a separate design-assistance layer.

Source:
- https://github.com/nexu-io/open-design

Do not copy the OpenDesign repository into this project and do not add it as a runtime dependency.

The project's production design authority is:

```text
frontend/DESIGN.md
```

OpenDesign may be used externally to prototype or critique frontend changes. If the local OpenDesign CLI is installed, it supports Codex through its MCP integration.

The intended mechanism is:

```text
OpenDesign references/templates
→ design exploration
→ approved VN30-specific design decisions
→ frontend/DESIGN.md
→ Codex modifies the existing Next.js components
```

The production frontend remains Next.js + Tailwind + shadcn/ui + Lightweight Charts + Recharts.
