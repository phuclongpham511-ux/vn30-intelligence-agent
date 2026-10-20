# Financial Analysis V6 — local Personal Research

Base: `cfe1baaeadd315e3232682097e3daa44cdf485cd`. Development, 20 October 2026.
**Implementation, source replay and HTTP acceptance PASS. Browser visual
acceptance PENDING. Public activation unchanged/disabled for these captures.**

## Usable application

The local frontend is running at `http://127.0.0.1:3431/`.
Open `/stocks/FPT#stock-fundamentals`, `/stocks/PNJ#stock-fundamentals` or
`/stocks/VCB#stock-fundamentals`; the existing Financial Analysis navigation, Annual /
Quarterly / TTM selector, units, historical tables and source disclosures remain.
There is no replacement dashboard. Stock Detail's existing five financial
destinations now read a server-authorized personal projection in this runtime.
Normal configurations continue using the existing public financial endpoint.

Core application backend `8431` was not restarted. A separate read-only financial
API on **127.0.0.1:8432** imports the one canonical `main.app`, reads pinned source
captures only, denies all non-research paths, uses transient in-memory SQLite
during the normal app lifespan, and never calls a provider or schedules work.
The frontend's ordinary stock/news/watchlist proxies still use `8431`.
Existing `3430/8430` processes and database are unchanged.

## Source and observed coverage

FPT/PNJ/VCB reuse the exact saved receipts previously reviewed in V4/V5. No repeat
acquisition or VCI comparison for those issuers. The authorized additional sample
uses HPG (steel), MWG (retail) and REE (diversified infrastructure) as research
examples, not official industry classifications. The existing SDK transport made
**12 bounded financial reads**, four per additional issuer, sequential by issuer,
without application retries. SDK issuer-classification initialization is separate
from that financial endpoint count. Installed vnstock version: **4.0.2**; old
captures retain their recorded `unknown` version. No SSI requests or worker.

All six sample tickers returned income, balance and cash-flow source receipts:
**8 annual + 34 quarterly observations per statement, 756 observations total**.
Saved annual periods are 2018–2025; quarters 2018-Q1–2026-Q2. This is sample
coverage only. No claim of all-equity support or current publication freshness.
The UI/proxy loads 8 periods: annual 2018–2025, quarterly 2024-Q3–2026-Q2.
No gaps are invented or filled with zero. Full captured periods remain in receipts.

| Per issuer, displayed original statement subset | Annual / quarterly source coverage | Supported lines per displayed period |
| --- | --- | --- |
| FPT, PNJ, HPG, MWG, REE | 8 / 34, all three statement types | Income 7; balance 10; cash flow 7 |
| VCB | 8 / 34, all three statement types | Income 5; balance 5; cash flow 5 |

These counts describe the reviewed adapter subset, not a complete reproduction
of every provider statement row. Non-financial statement-only additions retain
the exact source codes/labels for operating profit (`isa11`), pre-tax profit
(`isa16`) and receivables (`bsa8`), with original VND ×1 amounts. Their source
labels must match; they introduce no new calculated metric or public mapping.
Unsupported rows are omitted from the personal table rather than filling a
large grid with dashes. Missing supported values still remain unavailable.

## Confidence and access are separate

The canonical source context now has independent typed classifications:

- Confidence: `OFFICIAL_VERIFIED`, `RECONCILED`, `SOURCE_REPORTED`, `UNVERIFIED`,
  `INVALID`.
- Access: `PERSONAL_RESEARCH`, `PUBLIC_DISPLAY_REVIEW_REQUIRED`,
  `PUBLIC_DISPLAY_APPROVED`.

The actual VCI observations in this increment are **SOURCE_REPORTED**, not
OFFICIAL_VERIFIED. Conflicting line definitions remain INVALID/withheld;
unsupported interpretations remain UNVERIFIED/withheld. V5's ten numerical
matches do not promote VCI basis or confidence. No provider permission is
inferred from owner authorization. Source contexts retain public-review-required
access; only the separate personal response is scoped PERSONAL_RESEARCH.

All 756 observations lack original unit metadata and reporting-basis metadata.
The saved-data adapter's documented/audited **VND ×1** engineering contract allows
individual amount display; original unit/currency absence, source code/label,
record and receipt hashes remain inspectable. EPS retains VND/share. No new
accounting scale is inferred from magnitude. Year/quarter labels and original
source date strings are retained; fiscal boundaries/publication timezone remain
unverified. Fetch/read time is never substituted for publication time.

Reporting basis remains **UNKNOWN**, visibly disclosed in EN/VI. Unknown does not
become consolidated because values match an issuer filing. Source raw receipts,
normalization, statement definitions and public qualification rules are preserved.

## Financial behavior

The projection calls the existing Python financial engine and public projection,
then independently selects supported **single reported observations** using their
source refs, codes, unit contract and flow basis. It does not mutate either the
canonical packet or the public result. No parallel financial calculation engine.

Annual and standalone-quarter amounts populate the existing tables. YTD amounts
are not relabelled as standalone reported quarters; unknown-basis YTD differences
and TTM sums are withheld. The TTM selector does not falsely certify flow sums;
period-end balances and original quarterly statements retain their own meaning.

Existing chart components receive actual source amounts: revenue/profit trends
(operating income/profit for VCB) and separate historical assets/liabilities/equity
bars. Each annual sample has **16 performance points and 24 balance-history
points**. The latter is explicitly a historical amount comparison, not a stacked
or reconciled capital/asset composition. Confirmed different bases across history
suppress the chart while retaining individual table observations.

UNKNOWN basis does **not** qualify growth percentages, margins, ROE/ROA, debt
ratios, P/E/P/B or other derived comparisons. Those remain unavailable. Banking
does not acquire industrial net revenue, gross margin, inventory ratios, NIM,
CASA or NPL. No speculative performance narrative is generated.

## Security boundary

Both services require deliberate development configuration. Default public
startup does not enable personal values. The supported Next custom server binds
to literal **127.0.0.1:3431**, verifies the real socket peer and literal Host,
rejects foreign Origin/cross-site browser requests and never trusts forwarded
identity. Its internal server configuration enables the research consumer; URL
parameters, cookies and headers cannot do so.

The financial backend binds to literal **127.0.0.1:8432**, disables proxy headers,
checks the socket peer/host and development opt-in, and permits only research
routes. It does not use the development or production ingestion locks. Its
response and frontend proxy are `private, no-store` with `noindex, nofollow`.

Capture files are outside Git, the Next public directory and production runtime.
The loader validates ticker/source, confines paths to the configured private
directory, bounds file size and verifies SHA-256 before normalization. There is
no live fallback, discovery-on-miss, provider call, cache promotion or polling.
An uncovered ticker returns 404. Arbitrary tickers work through this shared
architecture once a corresponding authorized capture is prepared; none of the
sample ticker names occurs in application branching.

Public financial endpoints retain their existing contracts and guards. These
private packets are not inserted into the public provider cache or database.
The normal public frontend parser rejects personal payloads. Internal filing
scope and replay fixtures keep their existing, separate boundaries. This is
local owner-authorized research, not a source-issued redistribution license.

## Validation and runtime receipts

- Focused backend financial regression: **133 PASS**, including 28 personal-mode
  cases. One existing Starlette/httpx deprecation warning.
- Full frontend regression: **321 PASS, 1 existing SKIP**.
- Typecheck PASS; supported webpack production build PASS.
- Real saved-data contracts: **18 projections** (six issuers × three frequencies)
  accepted by the research consumer and rejected by the normal public consumer.
- Actual HTTP acceptance: **34 checks PASS**, including 18 populated private
  responses, existing app/routes/proxy and five negative access/coverage checks.
- Real-component source HTML rendering: **12 EN/VI artifacts** for annual and
  quarterly FPT/PNJ/VCB. Each contains the real supported statement amounts and
  an available chart projection. These are not screenshots or browser interaction.
- Cloud Browser is unavailable. No personal/local browser was launched or used.

Private evidence:
`C:/Users/PC/.codex/tmp/woofi-personal-financial-v6-runtime-20261020/`:
`index.json`, raw captures, canonical projections, `COVERAGE.json`, HTTP responses,
`HTTP_ACCEPTANCE.json`, `FRONTEND_ACCEPTANCE.json`, final EN/VI source renders,
`VALIDATION.json`. Additional raw capture receipts are preserved separately in
`../woofi-personal-financial-v6-additional-20261020/`.
Do not copy these private artifacts into public/static hosting or Git.

Supported restart instructions (only if these development ports are stopped;
never start duplicate listeners):

```powershell
# From the integration worktree, with its existing Python environment:
python -B -m scripts.serve_personal_financials C:/Users/PC/.codex/tmp/woofi-personal-financial-v6-runtime-20261020
# Separate terminal, frontend directory; existing core backend remains 8431:
$env:APP_ENV='development'
$env:BACKEND_URL='http://127.0.0.1:8431'
$env:WOOFI_PERSONAL_RESEARCH='1'
$env:WOOFI_PERSONAL_BACKEND='http://127.0.0.1:8432'
npm.cmd run start:personal
```

Only the newly created research API was refreshed via its own session Ctrl+C
after final backend changes; release of its PID/listener was verified before
starting its final version. The existing 8431 and 3430/8430 services were never
stopped. No production Supervisor, Collector, database, journals, application
pin, SSI configuration, News V3 or Market Board color change. No push/merge/deploy.

Next product step: inspect the running Financial Analysis in the permitted Cloud
Browser when available, or let the user review it manually. Keep all public
activation gates intact. Extend saved coverage only through bounded authorized
reads; neither more PDF uploads nor a new dashboard is required for this mode.
