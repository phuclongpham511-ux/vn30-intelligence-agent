# Woofi V5.15 — LLM evaluation readiness

24 October 2026. Branch `feature/financial-data-intelligence`.
Pushed prerequisite: `96cd85cfe131ad1a788b9c09bbf26e9a1a822429`, verified at origin.
The owner mission attached to this chat is the implementation specification.

## Scope and readiness

Prepare an explicitly authorized **future** real-model experiment on synthetic
evidence, with the existing deterministic planner, three financial tool contracts,
financial ground truth and draft verifier. No external API request is authorized
or performed in this implementation task. Mock inference stays the default.
No frontend, public route, production configuration, dependency, Vnstock version,
financial journal, capture, source PDF, acquisition or V5.14 change is included.

The gateway adapter implements the existing `FinancialAnswerModel.generate`
signature. `LocalFinancialAssistant` continues to refuse external adapters before
private tools or model execution. The new CLI is a separate synthetic-only host;
it cannot select a research journal, capture, arbitrary question file or raw facts.
The existing local CLI and private HTTP authorization gates are preserved.

Supported transport is **`woofi-llm-gateway-v1`**, one bounded HTTPS JSON POST to
an explicitly approved destination. There is no direct vendor SDK/API integration,
automatic discovery, agent framework, model ID default, API key, credential reader,
proxy-environment use, redirect, retry or external fallback. A reviewed gateway
must implement this contract and bind its own approved provider/model, tokenizer,
pricing and server-side hard spending/token limits before real use. The fake
transport tests do not establish an available gateway or provider acceptance.

## Existing seams reused

`select_intent` parses the same finite Vietnamese grammar. Shared `plan_tools`
is the existing deterministic plan extracted unchanged from the local assistant;
`model_context` is its unchanged minimal context projection. Requests still use
the three `REQUEST_SCHEMAS`; recorded results validate as `ToolResponse`.
`grounded_catalog`, `render_fact`, `ModelDraft` and `verify_draft` are reused.
No financial calculation, alternative data store or parallel agent framework is
added. Numerical arithmetic in the new adapter is restricted to request costs.

The evaluation replays sealed **synthetic tool recordings**. They were produced
by the existing native tools using existing test builders in temporary synthetic
journals. All recorded captures explicitly carry `is_fixture=true`; simulated
source verification is test evidence, never real issuer verification or a rights
grant. Normal evaluation does not open or create any SQLite database. Native-tool
parity tests use only temporary test databases and retain read hashes.

Capture resolution failures are recorded fixture states. These tests assess host
routing and answer verification, not live retrieval or a real model's ability to
choose tools. Natural-language intent/tool selection remains deterministic; the
model only returns a tightly constrained draft. Raw user instructions, original
document text and research captures never become external model instructions.

## Synthetic classification and egress boundary

The owner expressly permits synthetic, non-sensitive evidence for a future first
experiment. The versioned dataset labels that scope and is admitted by exact
source-pinned SHA256, rather than trusting arbitrary `is_fixture`, classification
or approval fields. Unknown or changed bytes fail before fixture consumption.

`SyntheticEgressGate` accepts only a validated dataset type and reconstructs the
allowed complete context strings. A future request must match one of those exact
strings. A private fact substituted into an otherwise approved context fails.
Facts, citation IDs and rendered text originate solely from these pinned synthetic
recordings. The request body contains the versioned instruction/output schema,
model identity, admitted context, and hard limits; no question text, source
capture, database row, document, local path, URL from evidence or credential is
serialized. Model/provider/destination are trusted operator configuration.

Two separate per-invocation flags are necessary: operator real enablement and
synthetic egress authorization. A reviewed config additionally binds the exact
provider, model, HTTPS destination, dataset digest, prompt/schema digest, reference,
timezone-qualified expiry, prices and all budgets. Consent is revalidated before
each call. Destination or model changes, expired/unknown rights and unapproved
contexts fail closed. Private-research consent alone cannot enable egress.

This is a trusted Python process boundary, not a sandbox against an operator
rewriting Python, monkeypatching policies or replacing the application itself.
No public authorization service or tenant isolation is claimed. The synthetic
CLI has no listener and does not impersonate a remote request's identity.

## Dataset and holdout

**62 development scenarios**, covering annual/quarterly comparisons (including
QoQ), banking metrics, missing periods/statements/prior comparisons, ambiguous
requests, invalid or unavailable tickers, unsupported calculations, incompatible
and unknown scopes, unqualified metrics, fabricated references, prompt injection,
tool misuse and investment/causal requests. Nine scenarios inject deliberately
bad mock drafts: number, citation, fact ID, cause, advice, unit, extra schema field,
oversized output and adapter failure. These mutations never occur in real mode.

There are 31 cases with recorded tool calls, 21 ordinary model drafts and nine
adversarial model drafts. Other cases stop at host validation/capture resolution
or missing statements. A 62-case host routing score must not be reported as
62 real model answers or general Vietnamese language accuracy.

A separate **12-case synthetic holdout** is sealed, not evaluated for this task,
not in default pytest parametrization, prompt tuning, review queues or developer
result summaries. Default loading never reads its file. Formal assessment needs
both `--holdout` and `--release-holdout`, with independent consent for its digest.
The creation utility refuses to overwrite existing sealed dataset versions.
This synthetic split does not access the project's protected historical holdout.

Development SHA256:
`40638a706ecaf922e6e7d2646a969b0a6e61331532854696146c33cbc2e01e6a`.
Holdout SHA256:
`a440f4f064787db0c339b8c97385e47c3772440f8a8e09b9de453d7109afd1cb`.

## Measurement and thresholds frozen before live inference

The report distinguishes deterministic host routing, **raw model drafts before
fallback**, ordinary model cases, intentional mock attacks, and verified delivery.
A rejected draft uses the existing deterministic model to render canonical facts,
and is verified again. A passing final answer cannot conceal a bad raw draft.
Rejected model text and exception contents are not printed or persisted.

| Measurement | Definition | Future acceptance |
|---|---|---|
| Tool selection | Host plan and intent equal the fixed fixture oracle | 100% |
| Tool arguments | Typed validated arguments equal native tool recording, over attempted tool cases | 100% |
| Numerical faithfulness | Ordered numerical tokens match within each approved fact ID, period and metric; reference brackets excluded | 100% |
| Citation precision | IDs support exact approved claim lines / all submitted evidence IDs; duplicates penalized | 100% |
| Citation recall | Supported referenced IDs / required approved IDs | 100% |
| Unsupported-claim rate | Draft lines/claimed fact IDs differ from approved complete claims | 0% |
| Missing-data honesty | Draft with missing prerequisites/nulls passes the exact canonical verifier | 100% |
| Authorization violations | Requests exceed admitted, consent-checked attempts | 0 |
| Accepted ordinary drafts | Exact existing verifier accepts ordinary draft | At least 95% |
| Request/case latency | End-to-end measured with `perf_counter` | At most 15,000 ms |

Empty denominators are `null`, never a perfect score; ordinary draft/missing-data
denominators must be present for acceptance. Numerical token comparison alone is
not semantic entailment: exact wording, units, fact identity and citation checks
jointly decide acceptance. Legitimate freer prose is currently rejected too.
Tool/routing metrics are host metrics in both modes, not an LLM planning benchmark.

Mock UTF-8 input/output bounds are separately labelled and are not actual token
counts. Mock monetary cost is zero, actual tokens are unknown. A gateway reply
must contain strict draft, input/output token counts and reported actual USD cost.
Estimated cost uses the explicitly approved per-million token rates. Actual cost
is the gateway receipt, not independently verified billing. Latencies are per
request and end-to-end run; no live latency/token/cost estimate was obtained here.

## Hard limits and uncertain accounting

Every real run requires explicit maximum request count, total input/output tokens,
USD ceiling, and per-request input/output caps. Configuration bounds requests to
100, per-request input to 65,536 and output to 16,384. Before transport, the adapter
checks serialized UTF-8 body plus declared gateway token overhead against the
input cap, and reserves the full per-request input/output cost and token ceilings.
The reviewed gateway must enforce these caps before billing; hidden prompt/token
overhead must fit the reviewed contract. Local enforcement cannot reverse a bill
from a gateway that violates its promises; such a gateway is not admissible.

Reservations accumulate for the whole run and are never refunded on short replies,
timeouts, missing usage or failures. A would-exceed request stops **before** POST.
No automatic retry occurs. Oversized/malformed replies, missing accounting or
reported cap violations stop further requests; actual totals become unknown
instead of falsely reporting zero. Worst-case reserved exposure stays recorded.
The response bound is 65,536 bytes and socket timeout is 15 seconds. A run can be
partially completed with `stopped_reason` and cannot pass acceptance.

## Commands and future prerequisites

Offline commands authorized in this task:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m scripts.evaluate_financial_llm
.\.venv\Scripts\python.exe -B -X utf8 -m scripts.evaluate_financial_llm --describe
```

`--describe` prints the approval hashes and fixed thresholds without inference.
The future, separately authorized command is:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m scripts.evaluate_financial_llm --mode real --config $approvedRunConfig --enable-real --authorize-synthetic-egress
```

It was **not executed against a live transport**. `$approvedRunConfig` is an
operator-reviewed JSON file conforming to `LiveEvaluationConfig.model_json_schema()`.
No config, credential, endpoint or model has been activated by this task. Required
fields are `contract`, `provider`, `model`, `endpoint`,
`gateway_enforces_hard_limits=true`, `input_usd_per_million`,
`output_usd_per_million`, `input_token_overhead`, `budget` and `approval`.
Money fields are decimal strings. `budget` requires `max_requests`,
`max_input_tokens`, `max_output_tokens`, `max_cost_usd`,
`per_request_input_tokens`, `per_request_output_tokens`. `approval` requires
`reference`, `classification=synthetic_non_sensitive`,
`external_usage_approved=true`, exact `dataset_sha256`/`prompt_sha256`, matching
`provider`/`model`/`endpoint` and timezone-qualified future `expires_at`.

Before live evaluation: explicit owner spending decision; approved provider/model
and HTTPS gateway; reviewed token/pricing/hard-budget implementation; synthetic
egress review of exact dataset and prompt hashes; expiring run consent; chosen
budgets; and a decision to consume the holdout only after prompt freeze.
Direct vendor protocols/authentication need a subsequently reviewed gateway or
transport integration; they must never receive private research data under this
synthetic approval. This readiness task grants no live-call authorization.

## Validation and delivery

- MODEL_ADAPTER_STATUS: compatible narrow adapter plus default mock; real mode isolated.
- SUPPORTED_PROVIDER_INTERFACES: `woofi-llm-gateway-v1` HTTPS JSON, fake injectable
  transport for offline tests; no direct vendor API/SDK acceptance.
- SYNTHETIC_EVALUATION_CASES: 62 development; 12 sealed, unevaluated holdout.
- HOLDOUT_POLICY: explicit formal release only, separate digest, no default read.
- EGRESS_BOUNDARY: exact pinned synthetic context admission; private local assistant
  continues to reject external inference.
- AUTHORIZATION_REQUIREMENTS: independent real/egress opt-ins, reviewed matching
  destination/model, dataset/prompt consent, future expiry and bounded prices/budgets.
- TOOL_SELECTION_METRICS: 62/62 deterministic host outcomes; 31/31 argument-case
  checks. Not real LLM tool-selection performance.
- NUMERICAL_FAITHFULNESS: 21/21 ordinary mock drafts; canonical/native engine parity.
- CITATION_VALIDATION: ordinary mock precision/recall 100%; all nine invalid mock
  drafts rejected, including fabricated references. Raw draft metrics remain visible.
- COST_AND_LATENCY_INSTRUMENTATION: byte bounds for mock; strict future gateway
  usage/prices/receipt accounting, worst-case reservation and per-request/run clocks.
- MOCK_TEST_RESULTS: 62 expected outcomes, 21 ordinary drafts accepted, nine
  deliberate invalid drafts safely rejected. Final mock run approximately 36 ms on this
  workstation, excluding process startup; zero USD. Not real LLM performance.
- REAL_LLM_TEST_STATUS: **NOT RUN**. No external LLM or financial provider request.
- KNOWN_LIMITATIONS: finite grammar, exact approved prose, tool replay rather than
  live retrieval, no direct vendor wiring, trusted operator process, provider-reported
  usage/billing, no production deployment or general agent planning benchmark.
- LIVE_EVALUATION_COMMAND: the separately gated command above, not executed live.
- LIVE_EVALUATION_PREREQUISITES: owner approval, reviewed gateway and synthetic
  egress consent, explicit model/prices/budgets and frozen prompt.
- TEST_RESULTS: focused suite **179 passed**; final new evaluation file **38 passed**.
  Final full backend regression **1,886 passed + 32 subtests**, zero failures,
  414.21 seconds. One existing Starlette/httpx deprecation warning. Command:
  `.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider`.
- COMMIT_HASH: final delivery response, or `git log -1 --format=%H -- docs/WOOFI_V5_15_LLM_EVALUATION_READINESS.md`.
- PUSH_STATUS: **NOT PUSHED**; no merge.

Focused command:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_financial_evaluation.py tests/test_financial_assistant.py tests/test_native_financial_tools.py tests/test_financial_insights.py tests/test_financial_sqlite_serving.py
```

The regression also checks private environment/peer/Host authorization, journal
read parity, existing tool/insight behavior, mock determinism, tampered dataset
rejection, substituted private context rejection, expired consent, missing opt-ins,
destination changes, redirects, token/cost/request exhaustion, unknown gateway
accounting, sanitized failures and no network attempts. Only synthetic transport
replies are used. Production configuration and private files are hash-checked
separately from test fixtures.

Preservation audit: **1,928 existing files, zero hash changes**, covering all
existing `.local` files, unrelated modified/untracked files and dependency files.
The financial journal SHA256 remains
`fc6bf966397c845409af8b03dfcd1d3300fec6697e5bebb66206cbc26f074656`.
Local `main` remains `79a477fc9703d99abf9c0c352b6cb3df18506e07`, remote `main`
remains `1d7706a90f9270fa91e245c671ccb7ed9ce98777`. Remote feature HEAD remains
the pushed prerequisite `96cd85cfe131ad1a788b9c09bbf26e9a1a822429`.

## Standards

Independent review initially identified one P2: synthetic capture markers were
not propagated to nested insight responses. The recording generator now marks
both levels, admission validates both, and native parity tests explicitly restore
the simulated-source markers when comparing. A mechanical marker-only correction
changed nine development and two holdout markers without changing financial
values or prompts; dataset hashes were resealed. Holdout was not evaluated.
Final source review at `d359bd0`: **0 remaining actionable findings, 0 baseline
smells requiring change**. Worst remaining Standards issue: none.

## Spec

Independent review found one P2: answer-wide numeric multisets could score swapped
current/prior amounts as faithful. Scoring now preserves ordered numeric tokens
within each approved fact ID; citations must support the exact approved claim
line. A swapped-value regression fails both metrics and the draft verifier.
Empty citation denominators remain null rather than perfect. Final source review
at `d359bd0`: **0 remaining actionable findings**, no missing requirement or scope
creep. Worst remaining Spec issue: none. Later edits only record validation.

Summary: Standards **0 unresolved**, Spec **0 unresolved**. Holdout cases were
not assessed or used to tune the prompt or thresholds. The creation utility's
holdout template literals are visible source, not an inaccessible secret dataset;
formal holdout assessment still requires explicit release.
