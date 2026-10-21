# V4 verification artifacts

These artifacts contain coverage, metadata, hashes and test outcomes, not financial
amounts, original PDFs, transcribed tables or screenshots. Original reviewed
evidence and real API payloads remain in the ignored private `.local` bundles.

- `TEST_RESULTS.json` records the completed regression/build/contract checks.
- `RUNTIME_HTTP_ACCEPTANCE.json` records actual live proxy and Host-boundary checks.
- `V4_ACCEPTANCE.json` records actual integrated-browser desktop scope, private
  screenshot fingerprints/dimensions and remaining acceptance work.
- `EVIDENCE_RECOVERY_COUNTS.json`, `VERIFIED_METRIC_COVERAGE.csv` and
  `ACTIVATED_VIEW_EVIDENCE_MATRIX.csv` distinguish each verification dimension.
- `SOURCE_RESPONSE_AUDIT.json` records successful originals and excluded/denied
  responses. HTTP 200 alone does not establish a valid filing or its metadata.
- `BASELINE_REFERENCE.json` pins the unchanged original 2,816-row matrix in V3.

The reused static/ASGI validators deliberately still say runtime/browser PENDING
inside their own outputs: they do not operate a browser or launch a server. Read
the separate live/browser artifacts for those checks. The reused V3 script name
and output contract identify the validator, not a claim that V3 is current.
Static financial renders include unavailable-section fallbacks; 144 render cases
do not mean every metric/dashboard is available for every issuer.

Reproduction and the remaining manual checklist are in
[V4 dashboard verification](../../DASHBOARD_VERIFICATION_V4.md).
