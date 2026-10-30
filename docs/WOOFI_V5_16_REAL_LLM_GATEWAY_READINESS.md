# Woofi V5.16 — real LLM gateway readiness

**Status:** implementation and offline tests only. No provider call, real evaluation,
holdout release, financial-data access, or spending approval occurred. The gateway
is not connected to `LocalFinancialAssistant` and is not a public chatbot endpoint.

## Provider comparison (official pages reviewed 2026-10-24)

Prices below are standard text rates per 1 million input/output tokens in USD.
Recheck pricing, model availability, retention controls, and account terms before
any approved run; config is rejected unless the selected OpenAI model and rates
match the gateway's explicit reviewed allowlist.

| Provider/model | Input / output | Structured JSON and future tools | Latency / Vietnamese | Data controls |
| --- | ---: | --- | --- | --- |
| OpenAI `gpt-6-luna` | $0.10 / $0.50 | Responses API, Structured Outputs and function calling supported | Described as efficient for focused/high-volume tasks; no Woofi latency or Vietnamese benchmark exists | API content is not used for training by default. Responses application state can be retained 30 days by default, so this adapter sets `store:false`. Abuse-monitoring logs can retain content up to 30 days by default; ZDR requires separate account eligibility/approval. |
| OpenAI `gpt-6.1-sol` | $1.00 / $5.00 | Responses API, Structured Outputs and function calling supported | Stronger-cost comparison; no Woofi latency or Vietnamese benchmark exists | Same API data-control considerations as above. |
| Google Gemini `gemini-3.1-flash-lite` | $0.25 / $1.50 paid Standard | Structured output and function calling supported; different API wire contract | Officially described as low-latency; no Woofi latency or Vietnamese benchmark exists | Free-tier prompts/responses may be used to improve products and can be reviewed. Paid service does not use prompts/responses for product improvement, but logs them for a limited period for abuse monitoring. This gateway does not implement Gemini. |

**Recommendation:** first evaluate OpenAI GPT-6 Luna on the paid API path, with
GPT-6.1 Sol as the stronger comparison. The lower-priced Gemini alternative is
not implemented here. No official source located provides a Woofi-relevant
Vietnamese financial-answer accuracy result. Measure Vietnamese quality,
latency, raw verifier metrics, and actual invoices on an owner-approved synthetic
run before deciding whether the price-quality trade-off is useful.

Sources: [GPT-6 Luna model and pricing](https://developers.openai.com/api/docs/models/gpt-6-luna),
[GPT-6.1 Sol pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data),
[Gemini 3.1 Flash-Lite capabilities](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite),
[Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing),
[Gemini API terms and data use](https://ai.google.dev/gemini-api/terms).

## Gateway and security boundaries

- `src/services/financial_llm_gateway.py` implements the existing
  `woofi-llm-gateway-v1` request and receipt contract. It accepts only OpenAI
  Responses API models explicitly listed in `OPENAI_MODELS`; no model/provider
  fallback exists.
- `scripts/serve_financial_llm_gateway.py` is a separate standard-library HTTPS
  server, hard-bound to `127.0.0.1`. It rejects public bind destinations, accepts
  only `POST /evaluate`, requires TLS, bearer caller authentication, one run ID,
  JSON content type and a bounded body. It has no FastAPI route and is not mounted
  in the application.
- TLS certificate validation is enabled on both hops. A loopback certificate
  must be issued by a CA trusted by the machine; set `WOOFI_LLM_GATEWAY_CA_FILE`
  to the approved PEM CA when it is not in the system trust store. Verification
  cannot be disabled by configuration.
- `WOOFI_OPENAI_API_KEY` is read only by the gateway process. It is never in the
  JSON config, caller request, client process, log, or response. The client and
  gateway share a separate high-entropy `WOOFI_LLM_GATEWAY_TOKEN`; the API key
  and caller token must not be the same secret.
- Gateway responses and errors contain only the strict receipt or a stable
  rejection. The server logs no prompt, answer, key, headers, provider body,
  filesystem path or exception text. One request is sent upstream; no retries,
  redirects, streaming, hosted tools, web search, or SDK transport are enabled.
- The gateway reopens only the pinned development fixture via
  `load_dataset('development')`, recomputes the prompt digest, and requires exact
  equality with an approved synthetic context. Holdout remains unreachable.
  Private captures, SQLite and live retrieval are not read by this path.
- Strict Structured Outputs constrains `ModelDraft` JSON shape. The unchanged
  V5.15 deterministic verifier still decides whether its facts, values and
  citations are supported. A schema-valid false number or invented reference
  remains a failed draft and falls back to the deterministic answer.
- The durable usage file contains only the run ID, counters, reserved and
  reported token/cost totals, stop state and last latency. Store it in an
  operator-controlled directory with access limited to the service account.
  Do not point it into a shared repository or financial-data directory. A lost
  provider receipt stops the run and retains the entire reservation. An
  exclusive per-run process lock prevents two gateway processes from spending
  against the same ledger; after a crash, inspect the recorded PID and remove a
  stale `.lock` file only after confirming that process is no longer running.

The request is limited by exact top-level keys, the pinned provider/model/prompt,
the approved run reference, exact development contexts, per-request token caps,
and the exact worst-case cost reservation. UTF-8 request bytes plus an operator
overhead floor of 2,048 tokens are a conservative pre-egress input bound; actual
provider-reported input/output usage is checked before returning a receipt.
OpenAI enforces `max_output_tokens`. Per-run requests, reserved input/output
tokens and worst-case cost are durably reserved before each provider call. A
budget rejection makes no provider call. A provider error, timeout, malformed
JSON/schema, missing usage, excessive usage, or unreceipted spend stops the run;
there is no retry or refund.

`actual_cost_usd` is token usage priced at the gateway's reviewed standard rates,
not an invoice reconciliation. It is conservative when prompt caching discounts
input. Reconcile provider billing after any future authorized run. The per-run
hard spend control reserves each request at the full configured input and output
caps before egress.

## Operator example (placeholders only)

This example is intentionally not an active consent. Replace both hashes with
values emitted by `--describe`, choose a new run reference and near-term expiry,
review prompt and dataset contents, and obtain the separate owner approval before
creating a real config. Do not include credentials in this file.

```json
{
  "contract": "woofi-llm-gateway-v1",
  "provider": "openai",
  "model": "gpt-6-luna",
  "endpoint": "https://127.0.0.1:8765/evaluate",
  "gateway_enforces_hard_limits": true,
  "input_usd_per_million": "0.10",
  "output_usd_per_million": "0.50",
  "input_token_overhead": 4096,
  "budget": {
    "max_requests": 1,
    "max_input_tokens": 32768,
    "max_output_tokens": 1024,
    "max_cost_usd": "0.0037888",
    "per_request_input_tokens": 32768,
    "per_request_output_tokens": 1024
  },
  "approval": {
    "reference": "REPLACE_WITH_UNIQUE_RUN_ID",
    "classification": "synthetic_non_sensitive",
    "external_usage_approved": true,
    "dataset_sha256": "REPLACE_WITH_DEVELOPMENT_HASH_FROM_DESCRIBE",
    "prompt_sha256": "REPLACE_WITH_PROMPT_HASH_FROM_DESCRIBE",
    "provider": "openai",
    "model": "gpt-6-luna",
    "endpoint": "https://127.0.0.1:8765/evaluate",
    "expires_at": "REPLACE_WITH_NEAR_TERM_TIMEZONE_QUALIFIED_EXPIRY"
  }
}
```

The configured reservation above is one request with a maximum standard-rate
ceiling of $0.0037888. The baseline evaluator has 21 ordinary draft cases; a
complete run therefore requires a separately reviewed larger request/token/cost
budget, not a silent expansion of this example.

## Reproducible future operator procedure (not run here)

1. Review current official model pricing, feature support, account retention and
   data-processing terms. Use paid-tier credentials only. Confirm API `store:false`
   behavior and account-level abuse-monitoring/ZDR settings. This adapter does
   not claim zero retention.
2. Run the mock baseline and save its report. Inspect only the synthetic-only
   V5.15 development fixture and prompt source. Use `--describe` to get exact
   hashes. Do not use `--holdout` or `--release-holdout`.
3. Prepare the placeholder config with an expiring approval tied to exact hashes,
   model, endpoint and budget. Keep the JSON private if it contains internal
   approval details. Recheck prices and rates in `OPENAI_MODELS`.
4. Store TLS certificate/key, OpenAI API key, caller token, config and usage state
   outside the repository. Set restrictive filesystem ACLs. Export environment
   variables in both processes as applicable:

   ```powershell
   $env:WOOFI_LLM_GATEWAY_CONFIG = 'C:\private\woofi-gateway.json'
   $env:WOOFI_LLM_GATEWAY_STATE = 'C:\private\gateway-usage.json'
   $env:WOOFI_LLM_GATEWAY_TLS_CERT = 'C:\private\localhost-chain.pem'
   $env:WOOFI_LLM_GATEWAY_TLS_KEY = 'C:\private\localhost-key.pem'
   $env:WOOFI_LLM_GATEWAY_CA_FILE = 'C:\private\approved-root-ca.pem'
   $env:WOOFI_LLM_GATEWAY_TOKEN = '<independent-random-secret-at-least-32-characters>'
   $env:WOOFI_OPENAI_API_KEY = '<provider-secret-set-in-gateway-process-only>'
   ```

5. Verify the certificate SAN covers `127.0.0.1`; confirm no `0.0.0.0` or public
   interface listener; confirm caller token rejection and no network egress using
   the fake-transport suite. The bundled server binds loopback regardless of
   environment.
6. Start the gateway in a dedicated operator terminal with
   `python -m scripts.serve_financial_llm_gateway`. Confirm its non-secret startup
   message. Then, only after the separate approval, run from a second terminal:

   ```powershell
   python -m scripts.evaluate_financial_llm --mode mock
   python -m scripts.evaluate_financial_llm --describe
   # A future separately approved real run would require all three explicit gates:
   python -m scripts.evaluate_financial_llm --mode real --config C:\private\woofi-gateway.json --enable-real --authorize-synthetic-egress
   ```

   These commands were not used for a real run. The mock command remains local
   and deterministic. Do not pass holdout switches.
7. Review the raw model metrics before deterministic fallback, verifier/fallback
   rates, routing and arguments, actual reported tokens, standard-rate cost
   estimate, latency, gateway stop reason and provider invoice. Any invalid
   number/citation, missing-usage receipt, cost/token/request limit, timeout,
   authentication issue, unapproved egress or discrepancy means stop and
   investigate; do not retry by changing model or expanding the budget silently.
8. Preserve the run report and usage counters as private operator artifacts.
   Keep holdout sealed until an explicit separate release and evaluation plan.

## Results and delivery

- **PROVIDER_COMPARISON:** OpenAI GPT-6 Luna ($0.10/$0.50) and GPT-6.1 Sol
  ($1/$5); Google Gemini 3.1 Flash-Lite paid Standard ($0.25/$1.50). Official
  pricing/feature/privacy links above. No Woofi latency or Vietnamese quality
  results are claimed.
- **RECOMMENDED_FIRST_MODEL:** `gpt-6-luna`; stronger comparison `gpt-6.1-sol`.
- **GATEWAY_ARCHITECTURE:** separate HTTPS loopback server; provider adapter,
  existing contract and pinned V5.15 evaluation client; no app route.
- **SECURITY_BOUNDARIES:** synthetic development fixture only; exact prompt/data
  hash; bearer caller auth; provider key server-side; TLS verification; loopback
  bind; bounded request and sanitized single-attempt behavior.
- **CONFIGURATION_REQUIREMENTS:** reviewed JSON approval/budget; TLS keypair and
  trusted CA; independent caller token; gateway-only provider credential; private
  durable usage path; explicit current prices and expiry.
- **SYNTHETIC_EGRESS_VALIDATION:** exact development dataset context membership,
  prompt hash, provider/model, run ref and synthetic classification. Holdout is
  not loaded or released.
- **TOKEN_AND_COST_CONTROLS:** byte-plus-overhead input bound, output cap,
  provider usage check, whole-request worst-case cost reservation, durable
  per-run accounting and stop-on-uncertainty.
- **MOCK_GATEWAY_TEST_RESULTS:** all 205 focused gateway/evaluation/assistant/tool/
  insight/SQLite-serving tests passed; provider transport was fake, with no
  network/API calls. One existing Starlette/httpx deprecation warning.
- **REAL_LLM_CALLS:** 0.
- **LIVE_EVALUATION_PREREQUISITES:** owner spending approval; reviewed hashes and
  prompt; separate run consent; small cap; provider terms/retention review;
  operator-managed secrets/TLS; future approval to expose only this synthetic
  dataset. Holdout remains separately sealed.
- **KNOWN_LIMITATIONS:** OpenAI adapter only; fixed allowlist and rates; no direct
  Gemini adapter; token cost is a standard-rate estimate, not invoice; no
  provider or Vietnamese quality/latency measurements; provider terms permit
  certain abuse-monitoring retention; one local operator process; no active
  assistant, tools, public route or deployment.
- **TEST_RESULTS:** `pytest -q -p no:cacheprovider tests/test_financial_llm_gateway.py
  tests/test_financial_evaluation.py tests/test_financial_assistant.py
  tests/test_native_financial_tools.py tests/test_financial_insights.py
  tests/test_financial_sqlite_serving.py` — **205 passed**, one existing
  Starlette/httpx deprecation warning.
- **COMMIT_HASH:** final delivery response.
- **PUSH_STATUS:** NOT PUSHED.
