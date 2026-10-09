# D1 factual runtime integration V1

The prospective public seam is `src.materiality.evaluate_d1_market_events`.
It returns `D1MarketEvaluation(factual_decisions, results)`; both factual checks
remain inspectable even when no event is emitted. This is not a Daily Signal
Packet, ranking wrapper, Watchlist consumer or official benchmark activation.

## Input and validity

Call with an explicit ticker, completed session string, timezone-aware
`generated_at`, optional existing `ScoringContext` mappings and optional
corporate-action repository. The input follows the existing benchmark snapshot
layout (`calendar`, `bars`, `provenance`, `is_fixture`) without its research loader.

- `calendar` contains the declared exchange sessions, including missing-bar
  sessions. It must include the evaluated session. Do not derive it from returned
  ticker bars or invent a weekday/holiday calendar.
- Provenance requires `source = SSI:FastConnect`, `adjustment_semantics = adjusted`,
  logical source `version`, `calendar_version`, a `calendar_evidence` reference,
  and timezone-aware `downloaded_at` not later than generation.
- Rows retain `ticker`, `session`, OHLCV, `source`, `currency`, explicit
  `price_comparable`/`volume_comparable`, and `timeframe = 1d`. A provided
  `is_complete = false` is rejected. Currency is the existing normalized VND
  contract; volume provenance must explicitly establish `volume_unit = shares`.
- Only sessions before the Vietnam generation day are eligible, preserving SSI
  daily analytics' existing completion policy even after today's market close.
- Existing `visible_bar` applies audited availability or the explicitly labelled
  `end_of_day_assumption` at session EOD. Missing/late/invalid availability stays
  unresolved. Receipt is not represented as historical publication or vendor PIT.
- Price returns require the immediately previous declared calendar session's
  comparable close. Missing bars never create multi-session daily returns.
- Each family independently selects its last 252 valid prior values, minimum 60.
  Selected session/observation identities, availability, price interval endpoints,
  exclusions, n/k/q95, source subset hash and calculation hash remain in decisions.
  Fixture evidence contaminates scoring, including row-level fixture flags.

The SSI provider's existing bare `MarketBar` response does not prove a calendar
or carry this full evidence contract. A caller lacking that evidence receives
UNRESOLVED; this milestone does not manufacture it or certify historical vintages.
Official PIT-sensitive calibration remains blocked independently of this product
runtime seam. Tests use only generated synthetic inputs, never protected cases.

## Existence and compatibility

`src/analytics/factual.py` is the single nearest-rank implementation extracted
from the committed benchmark helper. New runtime decisions use canonical
`d1-empirical-q95-nearest-rank-v1`. The benchmark wrapper deliberately retains
`d1-nearest-rank-q95-v1` and identical output mechanics. No stored evidence,
baseline snapshot, research result or benchmark admission rule is migrated.

Only EXISTS emits abnormal-price/unusual-volume events. DOES_NOT_EXIST and
UNRESOLVED both emit no claimed event, but retain different decisions/reasons.
Existing significance, novelty, confidence and base scoring remain unchanged;
missing scoring context can exclude a supported event from scoring without
changing its factual existence. Midrank remains provisional scoring context.

Bollinger uses the very same D1 unusual-volume decision for abnormality, retaining
BB(50,2), sample standard deviation, inclusive touch, strict recovery and the
0–2 observation confirmation window. Its positive confirmation-day volume rule
is independent: genuine zero/q95-zero is D1 EXISTS but cannot confirm Bollinger.
Volume is not a new scoring channel. Corporate-action enrichment remains after
scoring and cannot change existence.

The old pair-based `detect_market_events` and `detect_and_score_market_events`
calls without `factual_decisions` remain explicitly legacy V0 compatibility seams,
including their provisional midrank Bollinger gate. Replay and frozen calibration
continue using those unchanged semantics. Prospective consumers must use the new
versioned entry point, which computes and always supplies D1 decisions.

## Verification

Focused public-runtime tests are in `tests/test_d1_runtime.py`. Existing Materiality,
benchmark, Bollinger, historical replay and corporate-action tests remain intact.
No frontend, News, Dividend redesign, D4/D5 or official calibration is introduced.
