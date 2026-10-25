# Woofi Browser Automation Policy

## Preferred browser

Use the **Codex Integrated Browser**, the browser pane inside Codex Desktop, for Woofi development, public web research, localhost UI testing, screenshots, and visual acceptance when the current session exposes a supported tool that controls it.

Before interacting with a page, inspect the available tools and confirm that the selected tool controls the Codex Integrated Browser and supports the requested operation. The pane being visible does not by itself mean the agent can control it. Do not invent browser APIs or claim visual acceptance from HTTP checks or rendered source files.

A genuine **Codex Cloud Browser**, hosted in a separate execution environment, may be used if it is actually available. It is an alternative capability, not a requirement when the integrated browser is available and supported.

## Personal browser boundary

The user's **Personal External Browser** means Chrome, Edge, Firefox, or another browser outside Codex. Never launch or control it, attach to its profile or debugging session, inspect its tabs, or access its history, cookies, passwords, extensions, authentication sessions, or unrelated sites.

Do not launch external local browser automation frameworks, hidden browser processes, or alternate launchers to bypass a restriction or host execution policy. Use of a different browser environment requires explicit authorization for that task.

## When browser control is unavailable

If this session has no supported Codex browser-control tool, or the supported browser cannot reach a target such as localhost, stop browser operations and report the exact limitation. Keep visual acceptance pending until real browser evidence is available. Do not silently substitute a personal/local browser, screenshots generated from source, or HTTP-only checks.

This policy is also summarized in the repository's `AGENTS.md` and applies to all Woofi work until the user changes it.
