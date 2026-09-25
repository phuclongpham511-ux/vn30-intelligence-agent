import json
import unittest
from dataclasses import replace
from itertools import product

from scripts.preview_materiality import preview
from src.materiality import (
    EvidenceItem, EventDirection, EventType, MaterialEventCandidate, MaterialityCategory,
    ScoringContext, detect_market_events, detect_fundamental_events,
    evaluate_candidate, detect_and_score_market_events, detect_and_score_fundamental_events,
)
from src.materiality.scoring import novelty


def candidate(**changes):
    base = MaterialEventCandidate("FPT", EventType.ABNORMAL_PRICE_MOVE, MaterialityCategory.MARKET,
        EventDirection.POSITIVE, "2026-01-02", evidence=(EvidenceItem("return", 0.03, "normalized_provider"),),
        own_history_abnormality=0.8)
    return replace(base, **changes)


class ScoringTests(unittest.TestCase):
    def test_missing_channels_renormalize(self):
        self.assertEqual(evaluate_candidate(candidate()).components.significance, 0.8)
        result = evaluate_candidate(candidate(market_relative_abnormality=0.4, economic_magnitude=0.0))
        self.assertAlmostEqual(result.components.significance, 0.4)
        self.assertAlmostEqual(result.base_score, (0.4 + 1 + 1) / 3)
        self.assertIn("unavailable:sector_relative_abnormality", result.reason_codes)

    def test_all_channels_absent_is_not_zero(self):
        result = evaluate_candidate(candidate(own_history_abnormality=None))
        self.assertTrue(result.excluded)
        self.assertIsNone(result.components.significance)
        self.assertIsNone(result.base_score)
        self.assertEqual(result.exclusion_reason, "no_significance_channels")

    def test_fixture_and_news_excluded(self):
        for category in MaterialityCategory:
            result = evaluate_candidate(candidate(category=category, is_fixture=True))
            self.assertEqual(result.components.confidence, 0)
            self.assertTrue(result.excluded)
            self.assertIsNone(result.base_score)
        self.assertEqual(evaluate_candidate(candidate(category=MaterialityCategory.NEWS)).exclusion_reason,
                         "news_not_supported_v0")

    def test_bounds_and_base_invariant(self):
        for own, market, quality, completeness in product((-10, 0, 0.5, 1, 10), repeat=4):
            result = evaluate_candidate(candidate(own_history_abnormality=own,
                market_relative_abnormality=market, source_quality=quality, data_completeness=completeness))
            s, n, c = result.components.significance, result.components.novelty, result.components.confidence
            for value in (s, n, c, result.base_score):
                self.assertTrue(0 <= value <= 1)
            self.assertAlmostEqual(result.base_score, (s + n + c) / 3)

    def test_invalid_inputs_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf"), True, "0.8"):
            with self.assertRaises(ValueError):
                candidate(own_history_abnormality=value)
        for value in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                candidate(days_since_similar_event=value)

    def test_completeness_and_missing_evidence(self):
        result = evaluate_candidate(candidate(source_quality=0.8, data_completeness=0.5))
        self.assertEqual(result.components.confidence, 0.4)
        self.assertIn("incomplete_evidence", result.reason_codes)
        self.assertTrue(evaluate_candidate(candidate(evidence=())).excluded)

    def test_novelty_boundaries(self):
        for days, expected in ((None, 1), (0, .25), (1, .25), (2, .5), (5, .5), (6, .75), (20, .75), (21, 1)):
            self.assertEqual(novelty(candidate(days_since_similar_event=days)), expected)
            self.assertEqual(novelty(candidate(days_since_similar_event=days, is_state_transition=True)), 1)

    def test_determinism_and_ticker_independence(self):
        expected = evaluate_candidate(candidate())
        self.assertEqual(expected, evaluate_candidate(candidate()))
        for ticker in ("HPG", "TCB", "VIC", "ANY"):
            actual = evaluate_candidate(candidate(ticker=ticker))
            self.assertEqual(actual.components, expected.components)
            self.assertEqual(actual.base_score, expected.base_score)


# Integration tests use the existing schemas and factual analytics directly.
from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from src.schemas.data import TechnicalBar, MarketBar, FundamentalRecord, FundamentalPeriod
from src.analytics.market import technical_history
from src.analytics.fundamentals import fundamental_history


def technical(day=1, **values):
    return TechnicalBar(ticker="FPT", date=date(2026, 1, day), open=100, high=101,
                        low=99, close=100, volume=1000, source="test", **values)


def annual(period="2025", **values):
    return FundamentalPeriod(ticker="FPT", period=period, source="test", **values)


def test_native_technical_transitions_and_continuation():
    prior = technical(1, ma20=99, ma50=100, rsi14=69)
    current = technical(2, ma20=101, ma50=100, rsi14=72)
    events = detect_market_events(prior, current)
    assert [e.event_type for e in events] == [EventType.MA_CROSS, EventType.RSI_REGIME_ENTRY]
    assert all(e.is_state_transition for e in events)
    assert len(events[0].evidence) == 4
    assert events[0].evidence[0].as_of == prior.date
    assert events[0].evidence[0].unit == "VND"
    assert detect_market_events(current, technical(3, ma20=102, ma50=100, rsi14=74)) == ()
    downward = detect_market_events(current, technical(3, ma20=99, ma50=100, rsi14=28))
    assert len(downward) == 2
    assert all(e.direction == EventDirection.NEGATIVE for e in downward)


@pytest.mark.parametrize("before,after,emitted", [(69,70,False),(70,71,True),
    (31,30,False),(30,29,True),(28,27,False),(72,69,False)])
def test_rsi_exact_boundaries(before, after, emitted):
    assert bool(detect_market_events(technical(1, rsi14=before), technical(2, rsi14=after))) == emitted


@pytest.mark.parametrize("before,after,emitted", [(99,100,False),(100,101,True),
    (101,100,False),(100,99,True),(101,102,False),(99,98,False)])
def test_ma_exact_boundaries(before, after, emitted):
    assert bool(detect_market_events(technical(1, ma20=before, ma50=100),
                                    technical(2, ma20=after, ma50=100))) == emitted


def test_missing_technicals_and_native_validation():
    assert detect_market_events(None, technical(2, ma20=101, ma50=100, rsi14=72)) == ()
    assert detect_market_events(technical(), technical(2, ma20=101, ma50=100, rsi14=72)) == ()
    for values in ({"rsi14": 101}, {"rsi14": float("nan")}, {"ma20": float("inf")}):
        with pytest.raises(ValidationError):
            technical(**values)


@pytest.mark.parametrize("field,value", [("ticker","TCB"),("source","other"),("currency","USD")])
def test_mixed_identity_rejected(field, value):
    with pytest.raises(ValueError, match="Mixed"):
        detect_market_events(technical(), technical(2).model_copy(update={field: value}))
    with pytest.raises(ValueError, match="Mixed"):
        detect_fundamental_events(annual("2024"), annual().model_copy(update={field: value}))


@pytest.mark.parametrize("prior_day,current_day", [(2,1),(1,1)])
def test_nonchronological_market_rejected(prior_day, current_day):
    with pytest.raises(ValueError, match="chronological"):
        detect_market_events(technical(prior_day), technical(current_day))


def test_market_context_required_and_existing_return_formula():
    prior = technical()
    current = technical(2).model_copy(update={"close": 100.1})
    assert detect_market_events(prior, current) == ()
    contexts = {kind: ScoringContext(own_history_abnormality=.9, market_relative_abnormality=.7)
                for kind in ("abnormal_price_move", "unusual_volume")}
    results = detect_and_score_market_events(prior, current, contexts)
    assert len(results) == 2
    assert all(not r.excluded for r in results)
    assert all(r.components.significance == pytest.approx(.8) for r in results)
    assert results[0].candidate.evidence[-1].metric == "daily_return"
    assert results[0].candidate.evidence[-1].value == pytest.approx(.001)
    assert results[1].candidate.direction == EventDirection.NEUTRAL
    assert results[1].candidate.evidence[0].unit == "shares"
    # A single row cannot supply a daily return, but can supply volume.
    assert len(detect_market_events(None, current, contexts)) == 1


def test_fundamental_comparability_and_margin_contexts():
    before = annual("2024", revenue_growth_yoy=.1, net_profit_growth_yoy=.2, gross_margin=.3, net_margin=.2)
    after = annual("2025", revenue_growth_yoy=.2, net_profit_growth_yoy=.1, gross_margin=.4, net_margin=.25)
    results = detect_and_score_fundamental_events(before, after,
        {"gross_margin": ScoringContext(economic_magnitude=.3), "net_margin": ScoringContext(economic_magnitude=.6)})
    assert len(results) == 4
    assert results[2].components.significance == .3
    assert results[3].components.significance == .6
    assert detect_fundamental_events(before, after.model_copy(update={"period": "2026"})) == ()
    assert detect_fundamental_events(None, after) == ()
    assert detect_fundamental_events(before, before.model_copy(update={"period": "2025"})) == ()
    with pytest.raises(ValueError, match="chronological"):
        detect_fundamental_events(after, before)
    with pytest.raises(ValidationError):
        annual("2025-Q1")


def test_bank_nulls_and_growth_reuse_existing_analytics():
    records = [FundamentalRecord(ticker="TCB", period=str(year), net_profit=profit, source="test")
               for year, profit in ((2023,100),(2024,120),(2025,180))]
    periods = fundamental_history("TCB", records, "test")
    results = detect_and_score_fundamental_events(periods[-2], periods[-1],
                {"net_profit_growth_change": ScoringContext(economic_magnitude=.6)})
    assert len(results) == 1
    result = results[0]
    assert result.candidate.event_type == EventType.NET_PROFIT_GROWTH_CHANGE
    assert result.components.confidence == 1 and not result.excluded
    assert result.candidate.evidence[0].value == pytest.approx(.2)
    assert result.candidate.evidence[1].value == pytest.approx(.5)
    assert all(row.revenue is None and row.roe is None and row.gross_margin is None for row in periods)
    # Two statements provide only one growth observation; no change can be inferred.
    assert detect_fundamental_events(periods[0], periods[1]) == ()


def test_missing_strength_and_fixture_provenance():
    before, after = technical(1, rsi14=69), technical(2, rsi14=72)
    result = detect_and_score_market_events(before, after)[0]
    assert result.exclusion_reason == "no_significance_channels"
    result = detect_and_score_market_events(before, after,
                {"rsi_regime_entry": ScoringContext(own_history_abnormality=.5)}, is_fixture=True)[0]
    assert result.exclusion_reason == "fixture_evidence" and result.components.confidence == 0
    result = detect_and_score_fundamental_events(annual("2024", net_margin=.1), annual(net_margin=.2),
                {"margin_change": ScoringContext(economic_magnitude=.5)}, is_fixture=True)[0]
    assert result.exclusion_reason == "fixture_evidence" and result.base_score is None


def test_technical_history_integration_and_determinism():
    closes = [100.0] * 59 + [103.0]
    bars = [MarketBar(ticker="FPT", date=date(2026,1,1) + timedelta(days=i),
                     open=c, high=c, low=c, close=c, volume=100, source="test") for i,c in enumerate(closes)]
    rows = technical_history("FPT", bars, "test")
    context = {"ma_cross": ScoringContext(own_history_abnormality=.8),
               "rsi_regime_entry": ScoringContext(own_history_abnormality=.6)}
    results = detect_and_score_market_events(rows[-2], rows[-1], context)
    assert len(results) == 2 and all(not r.excluded for r in results)
    assert results == detect_and_score_market_events(rows[-2], rows[-1], context)
    assert all(r.components.novelty == 1 for r in results)


def test_preview_is_deterministic_and_honest():
    result = preview(" fpt ")
    assert result == preview("FPT")
    assert len(result["results"]) == 8
    assert len({r["candidate"]["event_type"] for r in result["results"]}) == 7
    assert all(r["excluded"] and r["base_score"] is None for r in result["results"])
    assert all(r["candidate"]["is_fixture"] for r in result["results"])
    json.dumps(result, default=str, allow_nan=False)
