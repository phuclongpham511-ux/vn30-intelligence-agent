# Woofi AI Financial Assistant — controlled local prototype

24 October 2026; branch `feature/financial-data-intelligence`.
Baseline/prerequisite `6a01a50b9ddae56f1e88672e527e4f550a1328ad` was verified at
origin before work. This is mock inference over saved evidence, not real-LLM
performance, live source acceptance or a production chatbot.

## Orchestration and contracts

`LocalFinancialAssistant(request).ask(payload)` is the application seam. The
strict input contains `question`, optional immutable `capture_id`, and an optional
bounded `budget`. The returned `AssistantAnswer` contains `answer`, `used_tools`,
`facts`, `evidence_references`, `missing_information`, `limitations`, status,
explicit `QuestionIntent` and measured mock usage. No HTTP route is registered.

The flow is a finite Vietnamese grammar → typed intent/ticker/period validation
→ the existing whole-capture selection → approved native tool calls → canonical
fact/citation catalog → narrow mock model → output verification → Vietnamese
answer. A failure yields a safe reason code and no speculative financial result.

`get_financial_statements`, `get_financial_metrics` and `get_financial_insights`
are reused unchanged. The existing Financial Engine, Insight Engine, private
projection and immutable read-only journal remain the financial ground truth.
The orchestrator performs no financial arithmetic, aggregation, unit conversion,
rounding, source reconciliation or source acquisition.

## Supported Vietnamese questions

| Initial intent | Example | Tool selection |
|---|---|---|
| Financial performance | `Kết quả tài chính FPT năm 2024` | Metrics plus insights for revenue and net profit |
| Annual growth/change | `So sánh tăng trưởng doanh thu FPT năm 2024` | Exact existing YoY insights |
| Available bank metrics | `Các chỉ tiêu ngân hàng sẵn có cho TCB năm 2025` | Operating income, PAT, customer loans/deposits |
| Cash-flow availability | `Dữ liệu dòng tiền quý mới nhất của NT2 còn thiếu gì?` | Saved cash statement at the latest whole-capture period |
| Qualified quarterly comparison | `So sánh quý đủ điều kiện của VJC quý 1/2025` | Quarterly YoY insights; explicit reviewed capture when needed |

The metric aliases and Vietnamese labels form an explicit small vocabulary in
`financial_assistant_intent.py`. Generic profit is labelled PAT in the answer;
distinct unsupported definitions such as pre-tax profit, unqualified NIM/CASA,
ambiguous margins, TTM/YTD and causal/investment requests are rejected.
Accents are normalized for parsing. A ticker is uppercase, or follows explicit
`mã`/`cổ phiếu`; support comes dynamically from saved captures, not seed branches.
This grammar is intentionally incomplete. It is not an NLU benchmark or general
semantic understanding of arbitrary Vietnamese.

Annual/quarterly periods are kept separate. Up to two explicit periods are
accepted; each insight uses the existing engine's exact YoY or quarterly QoQ
counterpart. An omitted period uses the latest saved period across the selected
whole packet, including a newer period whose cash statement may be absent. It
does not claim the latest live filing. Missing values and unknown scopes stay
missing/unqualified. Unsupported requests and mixed period labels fail closed.

## Capture identity and private authorization

Each question rechecks the existing `require_personal_request` development,
personal opt-in, numeric-loopback bind, socket peer and Host restrictions.
SQLite mode is required. The journal location comes only from trusted operator
environment; question text and model output cannot supply a path, SQL or URL.
The existing serving selector resolves one whole immutable capture; a selected
capture must match ticker/frequency. Its digest is matched to one journal ID.
Ambiguous revisions require `capture_id`; no source or revision splicing occurs.

The serving selector's existing quarterly default favors the saved provider
packet. It does not silently upgrade VJC to an independently reviewed revision.
For reviewed VJC Q1/2025 comparisons, select the reviewed capture explicitly.
The provider may lack that exact quarter, which remains insufficient rather than
being filled from the original filing. Synthetic evaluation tests genuine
ambiguous annual revisions and explicit old/new selections separately.

The trusted terminal process has no remote socket. It constructs a local request
context only after retaining all existing private environment opt-ins; it creates
no listener or authentication system. This context must never be used to
authenticate remote requests. A future network host must supply its actual
request and preserve the existing no-forwarded-header deployment boundary.

## Model, grounding and egress policy

`FinancialAnswerModel.generate(context_json, max_output_tokens=...)` is a narrow
vendor-neutral interface. The only wired implementation is
`DeterministicFinancialModel`, with `external_io=False`. External adapter kinds
are rejected before tool/model execution; no SDK, credentials, provider factory,
real-model mode, environment-selected model or egress path was installed.

The model sees only the typed intent and approved fact renderings with generated
fact/citation IDs. Original question instructions, raw captures, document text,
paths and credentials are not model instructions or tool arguments. All facts
and citations are copied from actual tool outputs and hash-bound to their content.
The model cannot return new financial values. The draft must include every
approved fact, exactly the associated citations, and exact permitted Vietnamese
wording. Changed numbers/units, causal claims, advice, arbitrary prose, invented
references, invalid schema, oversized output and adapter failures are rejected.
The application safely renders the same canonical facts instead, marking
`SAFE_FALLBACK`; rejected draft text never appears in the result.

This deliberately constrains prose as well as tool selection. A future real LLM
could select/organize approved claims, but freer narration requires a separately
reviewed verification design. Source evidence is data, never an authority to
override the host policy. This in-process interface is not a sandbox for arbitrary
operator-injected Python adapters; the CLI always constructs the built-in mock.

Model cost is zero USD and a nonzero budget is rejected. Public publication
rights, PIT qualification, source verification and private permission remain
independent. `COMPARABLE` is not a claim of full verification or redistribution
rights. The assistant does not promote unqualified specialist definitions.

## Resource bounds and terminal use

Per question: one ticker/capture, four metrics, two requested periods, eight facts,
two approved tool calls, one model call, zero USD cost, 500 characters/2,048 UTF-8
question bytes, 32,768 input-token upper-bound units, 16,384 output-token
upper-bound units and 65,536 final serialized response bytes. Existing native tool
limits also remain active. In mock mode token limits are conservatively charged
using UTF-8 bytes; these are not measured tokens or prices from a real provider.
The output limit is passed to the adapter and checked again before accepting its
draft. There is no retry loop, alternate tool search or external fallback.

In the existing explicitly configured private research development environment:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m scripts.ask_financial_assistant --question "Kết quả tài chính FPT năm 2024"
.\.venv\Scripts\python.exe -B -X utf8 -m scripts.ask_financial_assistant --question "So sánh quý đủ điều kiện của VJC quý 1/2025" --capture-id $selectedCaptureId --json
.\.venv\Scripts\python.exe -B -X utf8 -m scripts.ask_financial_assistant
```

Required existing flags are `APP_ENV=development`, `WOOFI_PERSONAL_RESEARCH=1`,
`WOOFI_PERSONAL_BIND=127.0.0.1`, `WOOFI_PERSONAL_FINANCIAL_READS=sqlite` and the
operator's preconfigured `WOOFI_PERSONAL_SQLITE`. The CLI does not set them or
print the journal path. Plain output is Vietnamese with citation IDs and missing
reason codes; `--json` exposes the full structured proof for local inspection.
Set `$selectedCaptureId` from the existing private review/audit before the second
example; an arbitrary or mismatched ID fails closed.
Interactive sessions stop after ten questions or `:quit`. No history file is
saved, no process listens for remote traffic and no frontend is changed.

## Evaluation and delivery report

- ORCHESTRATION_DESIGN: finite Vietnamese intent → existing private capture
  selection → approved tools → canonical catalog → mock draft → strict verifier.
- SUPPORTED_QUESTION_TYPES: performance, selected metrics/bank availability,
  annual/quarterly exact changes and cash-flow availability, within the grammar.
- TOOLS_REUSED: all three existing read-only native financial tools, unchanged.
- MODEL_ADAPTER: narrow vendor-neutral protocol, deterministic mock only.
- MOCK_TEST_RESULTS: the tracked corpus contains **46 Vietnamese questions**,
  including missing data, wrong/dynamic tickers, unsupported definitions, mixed
  periods, unqualified data, revision conflict, injection, paths/SQL/URLs and advice.
  Separate adversarial mock tests cover nine invalid draft/failure modes.
- REAL_LLM_TEST_STATUS: **NOT RUN / DISABLED**. Saved-data checks still use mock
  inference and do not establish real LLM accuracy, latency, costs or robustness.
- TOOL_SELECTION_ACCURACY: **46/46 expected intent/routing/rejection outcomes**
  in this fixed deterministic corpus; not a general-language accuracy estimate.
- NUMERICAL_PARITY: tool/engine values and formulas are copied; known synthetic
  amounts and comparisons match independently specified expectations. Mock text
  cannot override a value with an instruction or an invented figure.
- CITATION_VALIDATION: every returned citation/fact matches the actual tool
  catalog; invented citations/IDs and omitted facts fail verification.
- DATA_EGRESS_POLICY: zero external model/source calls; no credential access,
  raw-document upload or dynamic plugin/model loading. External model adoption
  requires a separate explicit operator decision and source-permission review.
- AUTHORIZATION_CHECKS: private environment/socket/Host gates, explicit revision
  ownership, read-only storage and sanitized CLI/database errors are exercised.
- PROMPT_INJECTION_RESULTS: unsafe requests rejected; unused numeric instructions
  do not enter model context. All nine adversarial drafts safely degrade to the
  canonical template; no invalid claim or private exception text is displayed.
- KNOWN_LIMITATIONS: small hand-written grammar and controlled wording; no
  arbitrary financial question answering, causal inference, investment advice,
  source reconciliation, hosted authentication, global quotas, UI or real LLM.
  Existing missing statement/period/scope/rights/PIT limits remain visible.
- LIVE_LLM_PREREQUISITES: explicit source-data egress permission; reviewed minimal
  disclosure projection; model/vendor and cost decision; bounded tokenizer/usage
  and request budgets; citation/numerical/injection evaluation on permitted data;
  real host identity binding and a separate decision on any freer answer prose.
- TEST_RESULTS: final focused suite **141 passed**, including **70 prototype
  cases**. Full backend: **1,847 passed + 32 subtests, 1 existing Windows timing
  failure**, 407.50 seconds; the unchanged Windows file passed **8/8** on an
  isolated retry. See the failure record below. One existing Starlette/httpx
  deprecation warning. No frontend source/build/browser acceptance is involved.
- COMMIT_HASH: final delivery response; obtainable with `git log -1 --format=%H -- docs/WOOFI_AI_ASSISTANT_LOCAL_PROTOTYPE.md`.
- PUSH_STATUS: **NOT PUSHED**; no merge or V5.14 activation.

Private acceptance artifacts under `.local/ai-assistant-local/` contain eight
saved-capture questions over FPT/TCB/NT2/VJC/SSI, repeated typed answers and an
actual terminal-entrypoint check. Socket guards deny network access. Reviewed
FPT and VJC support valid changes; TCB keeps banking definitions, NT2 reports
missing Q3/2026 cash flow, SSI withholds an inapplicable generic margin, and the
default VJC provider keeps its missing exact-quarter result. No expectation is
relaxed to manufacture a comparable result.

A separate Python `-m scripts.ask_financial_assistant` process also passed a
saved FPT question with JSON output: exit code 0, one fact, one actual citation,
zero USD model cost. Its full private response remains in the ignored pilot
folder rather than this report.

The existing financial SQLite hash before/after acceptance is
`fc6bf966397c845409af8b03dfcd1d3300fec6697e5bebb66206cbc26f074656`.
Captures, PDFs, answers/audit artifacts and unrelated worktree changes remain
outside the commit. No application/financial schema or financial data changed.

## Reproduction and independent review

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_financial_assistant.py tests/test_native_financial_tools.py tests/test_financial_insights.py tests/test_financial_sqlite_serving.py
```

The final focused suite passes **141 tests**, including **70 prototype cases**.
The tracked question corpus supplies **46** of those cases; the remainder check
canonical parity, draft tampering, budget/auth boundaries, exact revisions,
terminal behavior, dynamic tickers and safe errors. Model output is deliberately
constrained; these outcomes do not predict real-LLM performance.

The full regression command was
`.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider`.
Its one failure was
`tests/test_runtime_supervisor_windows.py::test_wmi_child_survives_termination_of_its_own_starter_job`.
The existing `wait_file` helper polls file existence and immediately decodes
JSON. In this run it observed an empty file between creation and completion of
the child writer, producing `JSONDecodeError`. The completed synthetic artifact
then contained valid JSON, SQLite integrity `ok` and preserved fixture provenance.
Neither the test nor runtime supervisor is part of this diff. The unchanged
Windows file was rerun separately and passed **8 tests** in 22.56 seconds.
No assertion was skipped/weakened and no unrelated lifecycle code was changed.
This retry does not erase the recorded full-run failure or claim that every
full-suite invocation was green.

### Standards

Independent review of the initial diff and subsequent source deltas: **0
actionable findings, 0 smells requiring change**. Existing ground-truth, dynamic
ticker, missing-data, provenance and private-serving contracts are reused.
Worst remaining Standards issue: none.

### Spec

Review identified incorrect generic-profit aliases and lost banking comparison
intent. The final grammar rejects unsupported qualified profit definitions and
routes explicit banking comparisons to the insight tool. Boundary follow-ups
also found invalid years/numbered quarters could silently select latest. Years
and complete quarter/year forms are now validated across supported Vietnamese
and ISO syntax; incomplete numbered quarters fail, while unnumbered latest-quarter
questions remain supported. Positive and negative regression cases cover these
corrections. Final re-review: **0 remaining actionable findings**, no scope creep.
Worst remaining Spec issue: none.

Summary: Standards **0**, Spec **0 unresolved**. Source and tests are frozen after
the final review; subsequent documentation updates record verification only.
