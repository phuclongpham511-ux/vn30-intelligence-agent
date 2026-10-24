# Woofi native financial tools — offline pilot

24 October 2026. Branch `feature/financial-data-intelligence`.
Baseline and pushed prerequisite: `47dc8b1abcbd11e7e6e0adae129f6ec1f5786c1b`.
The corporate-actions pilot was verified at origin before this work.

## Scope and architecture

Three bounded Python tools retrieve one explicitly selected immutable capture.
`NativeFinancialTools(request).invoke(name, arguments)` is the tool seam, and
`answer_questions(tools, plans)` is the deterministic scripted planner seam.
No LLM, framework, new provider dependency, route, storage model or calculator
was introduced. Production access controls/configuration and the UI are unchanged.
No provider request, data acquisition, journal migration or V5.14 work occurred.

The implementation reuses `configured_research_packet`/`sqlite_research_packet`,
read-only `MetricJournal`, `financial_engine`, `personal_projection`, the existing
verification assessment, `metric_unit` and `saved_financial_insights`.
The V5.8–V5.13 reports, AGENTS/CONTEXT/README, existing source/serving contracts,
and `VNSTOCK_ECOSYSTEM_INTEGRATION_RESEARCH.md` informed this scope. Historical
README descriptions do not override current private-serving and domain rules.

## Contracts and limits

Request/output models live in `src/schemas/financial_tools.py`.
`tool_schemas()` returns the three request JSON Schemas; the response schema is
`ToolResponse.model_json_schema()`. Requests are strict, reject unknown fields,
and accept JSON objects only. Tool names form a closed dispatch vocabulary.

| Tool | Required input | Result |
|---|---|---|
| `get_financial_statements` | ticker, capture ID, annual/quarterly, income/balance/cash | Saved source lines, exact periods, units, scope/basis, semantic status, receipt/record/document lineage, missing fields |
| `get_financial_metrics` | ticker, capture ID, frequency, distinct canonical metric IDs | Existing engine values permitted by the private projection, formula, safe input references, verification dimensions, eligibility and missing prerequisites |
| `get_financial_insights` | ticker, capture ID, frequency, supported metric IDs, YoY/QoQ | Existing insight values, exact comparisons, attention policy/reasons, evidence and insufficient-comparison cases |

All tools accept an optional list of periods. Without one they return up to the
last four observed periods of the selected family (statements) or whole packet
(metrics/insights). This is capture-local availability, not current/live coverage.
Explicit missing periods remain missing; there is no nearest-period fallback.
The original engine's 40-period processing limit remains in place.

Bounds per invocation: one ticker/capture, eight distinct metrics, four distinct
periods, 8,192 UTF-8 request bytes, 400 lines per statement observation and 524,288
UTF-8 serialized response bytes. Oversized output fails explicitly without
partial/truncated evidence; reduce the selection. A session allows ten tool
attempts, including authenticated failed attempts, hence at most ten distinct
tickers. Scripted planning accepts one to ten questions, with one tool call each.
Host code owns the session lifetime; these are local bounds, not global quotas.
TTM and annual QoQ are outside this pilot. Unknown metric names are rejected;
supported metrics with insufficient evidence return null and explicit reasons.

## Evidence and numerical truth

Each response carries ticker/source/source version, capture ID, original capture
SHA256 and packet SHA256. Each metric input carries the same capture references,
statement/field/code, source value when permitted, unit, original unit/multiplier,
known scope/basis/dates, receipt/record/document hashes and page when present.
Statement values are direct saved lines, not newly calculated financial facts.
Statement evidence is also attached per line through the saved field-code map,
retaining original units/multipliers/pages even within mixed-unit filings. Raw
amounts without interpretable original units are withheld explicitly; normalized
saved amounts retain their own line units. An observation-wide first-field unit
is never presented as the original unit for all lines. Existing verification
grades are retained independently of a tool value's display eligibility.
Metrics use canonical formulas and private display decisions; insights preserve
the existing comparison values, attention criteria, historical evidence links,
verification dimensions and missing-information reasons.

Unknown scope is retained on an individual reported observation. A derived
metric with unknown scope is withheld even if two unknown scopes appear equal.
The Insight Engine already rejects such comparisons. No source/revision filling
is performed. Zero remains zero, null remains null, and missing dates stay null.
Prohibited source values are withheld in statement lines and evidence references.
Unqualified detailed securities lines remain inspectable source evidence; they
do not become specialist KPIs. Fixture flags are preserved; the existing private
serving selector rejects actual fixture packets as real source evidence.

Qualification, permission to read privately, publication rights and PIT vintage
are separate. A private comparable result does not grant public redistribution
or support causal claims, return predictions or investment recommendations.

## Authorization and leakage boundary

Every invocation calls the existing `require_personal_request`: development
environment, personal-research opt-in, configured numeric-loopback bind, actual
ASGI peer and Host must all pass. SQLite mode is additionally mandatory, and
the serving reader rechecks its existing configuration gates. The configured
journal path comes from trusted host environment, never from tool arguments.
Ticker/capture/frequency mismatches fail closed, with no alternate revision read.

No router is registered. Request/response models are private Python contracts,
not a capability token or a SaaS authentication system. A future host must supply
the genuine incoming request and maintain the existing no-proxy-header deployment
boundary; it must not construct a loopback identity from untrusted tool input.
The offline harness constructs its own local request only for authorized tests.

Output evidence uses an allowlist: raw document/page/row text, original metadata,
filesystem paths and source URLs are excluded. Hash/page references allow the
authorized researcher to inspect the original evidence through existing records.
Tool errors contain stable safe codes, not rejected payloads or database paths.
No SQL, Python execution, arbitrary path or URL input is accepted. There is no
tool-output integration into public responses or frontend components.

## Saved-capture acceptance

Ten explicit questions were run twice against existing saved captures of five
issuers. Full answers, selected revision IDs and audit hashes remain private under
`.local/native-ai-tools-pilot/`; no financial amounts or private captures are
included in this commit. These are real **saved-capture** tests, not live source
or LLM acceptance. Named issuers are test cases, never business-logic branches.

| Issuer and period | Tested result |
|---|---|
| FPT, FY2024 reviewed history | Four numeric requested metrics; four comparable annual YoY insights |
| TCB, FY2025 reviewed history | Eight numeric requested banking metrics; four comparable annual YoY insights, with accounting definitions retained |
| VJC, Q1/2025 reviewed revision | Five numeric metrics and five comparable Q1/2024 YoY comparisons |
| NT2, Q3/2026 provider capture | Cash-flow statement absent; both requested cash metrics null; available earlier cash periods remain visible |
| SSI, Q2/2026 provider history | 79 detailed income lines; one of four canonical metrics numeric, three withheld/unavailable; no invented specialist KPI |

The ten plans execute exactly ten invocations per session. A separate repeat
session returns equal typed answers. Metric/formula parity is checked against
the canonical engine; deliberate private/unknown-scope withholding remains
explicit. Insight parity compares every non-evidence field, and every retained
evidence field equals the original insight output. Capture/source ownership and
input references are checked. No displayed values are recomputed by the planner.
Sockets are blocked during acceptance and the external `vnstock` SDK is absent
from imported modules. There is no LLM package/call in the execution path.

Financial SQLite SHA256 before and after:
`fc6bf966397c845409af8b03dfcd1d3300fec6697e5bebb66206cbc26f074656`.

## Validation and delivery report

- TOOLS_IMPLEMENTED: the three read-only native tools and scripted planner.
- TOOL_SCHEMAS: strict Pydantic requests and typed `ToolResponse`/`ScriptedAnswer`.
- REAL_CAPTURE_TEST_CASES: ten plans, five issuers, repeated identically.
- SYNTHETIC_TEST_CASES: isolated temporary journals reuse existing reviewed-report
  and provider fixture builders; these simulate provenance for tests only and
  do not establish source acceptance or source rights.
- FINANCIAL_ENGINE_PARITY: PASS for returned values and formulas; null gating
  is preserved and unknown-scope derived results are additionally withheld.
- INSIGHT_ENGINE_PARITY: PASS, including attention and insufficient cases;
  evidence is a documented safe projection of the original output.
- EVIDENCE_REFERENCE_VALIDATION: PASS for selected ownership, capture and packet
  hashes, original receipt lineage, record/document references and units.
- AUTHORIZATION_BOUNDARIES: existing private development/socket/Host gate reused
  for every invocation; SQLite mode required, no new auth system or route.
- DATA_LEAKAGE_TESTS: prohibited amounts/metadata/paths withheld, arbitrary
  SQL/path/URL rejected, public display gates and endpoint contract retained.
- NO_PROVIDER_CALLS: PASS; socket guards and no external provider SDK import.
- NO_LLM_CALLS: PASS; deterministic calls only, no LLM SDK or framework.
- DATABASE_HASH_PRESERVATION: PASS; existing SQLite hash unchanged. Tests also
  enforce mode=ro, deny SQL writes/attach and check repeat-read hashes.
- TEST_RESULTS: final full backend regression **1,778 passed + 32 subtests**,
  zero failures, 376.64 seconds. Focused regression **108 passed**, including
  **30 new tool cases**. One existing Starlette/httpx deprecation warning.
  Command: `.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider`.
  No frontend source changed; no frontend build/browser acceptance is claimed.
- KNOWN_LIMITATIONS: saved evidence only; existing source, scope, period, metric,
  private permission, publication-rights and PIT limitations remain. No natural
  language planner, tenant authorization, persistent/global quotas, model-facing
  transport, runtime deployment, public AI endpoint or UI acceptance is claimed.
- NEXT_LLM_INTEGRATION_PREREQUISITES: explicit model/cost decision, genuine host
  request binding, session/tenant budgets, evaluation of citation correctness,
  handling source text as untrusted data, safe structured answer generation and
  independent public/private publication policy. Any live/hosted integration
  needs a subsequent scoped decision.
- COMMIT_HASH: obtain with `git log -1 --format=%H -- docs/WOOFI_NATIVE_AI_TOOLS_PILOT.md`;
  the delivery response reports the final commit without a circular self-hash.
- PUSH_STATUS: NOT PUSHED; no merge.

## Reproduction and review

Focused offline regression (no services or provider credentials required):

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_native_financial_tools.py tests/test_financial_sqlite_serving.py tests/test_financial_insights.py tests/test_personal_financials.py
```

This passed **108 tests**, including **30 new native-tool cases**. Synthetic
journals/PDF-like evidence live only in temporary test directories. The private
saved-data acceptance plans are intentionally not copied into tracked source.
To repeat that acceptance locally in this checkout, the ignored artifact is
`.local/native-ai-tools-pilot/run.py`; it only reads the already selected journal
revisions and writes new pilot audit/answer artifacts in its own ignored folder.

### Standards

Independent review of the four-file diff and final source delta: **0 actionable
findings, 0 smells requiring change**. Existing engine, journal, permission,
missing-data and dynamic-ticker contracts are reused. Worst issue: none.

### Spec

Initial review found one P2: observation-level original-unit metadata could
misrepresent later lines in a mixed-unit filing. The final adapter preserves
safe per-line original units/multipliers/pages, withholds uninterpretable raw
amounts and includes a reviewed-report mixed-unit regression case. Re-review:
**0 remaining actionable findings**, no scope creep. Worst remaining issue: none.

Summary: Standards **0**, Spec **0 unresolved**. No source/test changes followed
the final review; subsequent report updates only record validation results.
