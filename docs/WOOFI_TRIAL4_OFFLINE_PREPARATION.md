# Trial #4: candidate C and private synthetic diagnostics

Preparation only. No provider request, billing change, live approval or Trial #4
runtime is created by this work. ModelDraft, financial calculations and verifier
rules are unchanged. Candidate compliance has only been exercised with fake
transports and deterministic fixture outputs, not measured on a real model.

## Explicit prompt selection

`default` remains the original prompt, SHA256
`69a55678664e5d40f9fd52e886f7520adbfa2a264825abec2b16a6838f3b9a87`.
The opt-in variant `candidate-c-v1` has SHA256
`ae26989e80bd9bdb21724efd7b9e8238548b696d7a2a9a330001856fcd429c22`.
It replaces only the instruction with an explicit construction rule:

> Return ModelDraft JSON: fact_ids = input fact IDs in order; answer = introduction + LF + input fact texts joined by LF; evidence_ids = sorted unique union of input evidence_ids. LF is a newline. Copy text exactly: punctuation, bracketed citations, warnings and whitespace. No extra prose or calculations.

The schema and introduction are unchanged. The development dataset remains
`40638a706ecaf922e6e7d2646a969b0a6e61331532854696146c33cbc2e01e6a`.
Old approvals cannot select the new prompt. Both client and gateway must opt in,
and a future approval must bind the new hash. Configuration digest and durable
reservation bindings are unchanged in shape; no new default config field is added.

The evaluator and operator accept `--prompt-variant candidate-c-v1`. A separately
configured server uses `WOOFI_LLM_PROMPT_VARIANT=candidate-c-v1`; the operator
passes the same explicit selection to its server and evaluator. Without these
selections, the existing default path remains active and rejects a candidate hash.
The existing `trial3-completion` budget profile can be reused for a separately
approved future experiment; its name does not authorize another request.

First-case `performance` admission: caller 3186 bytes, normalized provider 3697,
Groq wire 3777; largest plus 2048 overhead = **5825 <= 5888**. Output reservation
is **2048**, total **7936 <= 8000**. Worst-case standard-tariff reservation remains
**$0.002112** at the existing $0.15/$0.60 per million input/output rates. This is
not a Free-plan invoice or proof of current quota. It does not certify admission
of every development case at the one-request input cap.

Offline hash inspection only:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.evaluate_financial_llm --describe --prompt-variant candidate-c-v1
```

## Synthetic rejected-draft artifacts

Diagnostics are off by default. Enabling requires both
`--enable-rejected-draft-diagnostics` and an absolute `--diagnostics-directory`.
Use a new dedicated directory outside every Git repository on a fixed local
disk. A new leaf is created with restrictive permissions. Existing broad or
inherited directory ACLs are refused instead of repaired. Windows permits only
the current user and SYSTEM; POSIX requires the current owner and private mode.
UNC paths, symlinks/junctions, hardlinked artifacts and foreign files are refused.
ACL, path and ownership checks run again before capture. Same-user Python and
filesystem access are trusted; this is not isolation from the Windows owner.

Only the exact hash-pinned **development** dataset is accepted. Caller-supplied
facts, fixture flags, real financial contexts and the holdout cannot enable this
store. The evaluation preflights storage before generation and stops on capture
failure. No fallback to logs or unsafe storage is allowed.

Artifacts retain only a case/hash binding, assessment, actual fact/citation ID
lists and set differences, exact answer edits relative to the canonical fixture,
and missing-warning bindings when fact alignment is known. Newlines and whitespace
are preserved. Rejected text can be reconstructed from the pinned fixture and
edits. Invalid-schema output gets status/hash metadata, not arbitrary raw text.
No HTTP envelope, provider headers, credentials or cookies are retained. Recognized
credential-like text, including Unicode-escaped forms, is refused. A scanner is
not a general declassifier; the pinned synthetic-only boundary is still required.
Shared stdout reports include artifact counts, never these diffs.
Case/end-to-end latency includes capture overhead; use the separately recorded
request/provider latency when comparing inference performance.

Limits: **32 artifacts**, **64 KiB each**, **512 KiB total**, retention **1..3600
seconds** (default 3600). Capacity exhaustion stops evaluation; no truncation or
overwriting. Expired artifacts are refused and purged on startup/read/write.
There is no background timer: operators must arrange and run the explicit purge
after a stopped session. Files can remain physically present while no cleanup
process runs; expiry metadata alone is not guaranteed physical erasure.

Offline mock capture (not a test of model obedience):

```powershell
$diagnosticPath = Join-Path $env:LOCALAPPDATA 'Woofi\candidate-c-offline-diagnostics'
.\.venv\Scripts\python.exe -B -m scripts.evaluate_financial_llm --mode mock --prompt-variant candidate-c-v1 --enable-rejected-draft-diagnostics --diagnostics-directory $diagnosticPath
```

Explicit expiry purge, without inference:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.evaluate_financial_llm --prompt-variant candidate-c-v1 --enable-rejected-draft-diagnostics --diagnostics-directory $diagnosticPath --purge-expired-diagnostics
```

The operator forwards these same diagnostic flags only when explicitly selected;
use a separate dedicated diagnostic leaf, not the trial directory containing TLS,
approval and ledger files. No runnable live command or approval is supplied here.

## What remains for an LLM

This exact construction is already performed by `DeterministicFinancialModel`.
Python can copy fact text, assemble IDs and preserve warnings without inference.
An LLM adds little to this copying task. Evidence-grounded explanation, attention
prioritization or clarification could be useful future tasks, but require a new
bounded contract and evaluation. Canonical numbers, citations and missingness
should remain supplied and checked by deterministic code.

Before any future real experiment: approve the new prompt hash and one-request
budget, current account evidence, exact dataset/first case, private diagnostic
location and cleanup procedure; create a fresh review/ledger/TLS preflight.
No existing Trial #1/#2/#3 authorization or ledger is reusable.
