"""Synthetic-only Safeguard 6 checks; never load benchmark payloads."""
import pytest
from dataclasses import asdict, fields, replace
from datetime import date, datetime, time, timedelta
from math import sin
from types import SimpleNamespace

from src.analytics.market import market_snapshot, technical_history
from src.evaluation.context import build_context
from src.evaluation.event_memory import EventMemory
from src.evaluation.benchmark.facts import FAMILIES, factual_inputs, transition_inputs
from src.evaluation.benchmark.episodes import link_episodes
from src.materiality.detectors import ScoringContext
from src.materiality.models import MaterialEventCandidate, EvidenceItem
from src.materiality.service import detect_and_score_market_events, evaluate_candidate
from src.schemas.data import MarketBar, TechnicalBar

from scripts.check_technical_identity import identity_violations
from scripts.check_technical_identity import scan_engine


@pytest.mark.parametrize("source", [
    'if ticker == "FPT": score = 1',
    'thresholds = {"HPG": 0.1}',
    'if universe == "VN30": score = 1',
    'if is_vn100: score = 1',
    'if historical_membership_status == "YES": score = 1',
    'if ticker == "VND": score = 1',
])
def test_static_guard_rejects_identity_behavior(source):
    assert identity_violations(source)


def test_static_guard_allows_lookup_and_provenance():
    assert not identity_violations('''
"""FPT and VN30 are documentation examples."""
history = histories[ticker]
if current.ticker != prior.ticker:
    raise ValueError("Mixed identity")
result = {"ticker": ticker, "source": source}
provenance = {"source": "VN30", "currency": "VND"}
''')


def test_engine_source_has_no_identity_behavior():
    assert scan_engine() == []


def test_engine_input_schemas_exclude_population_features():
    # Exact field contracts catch even a newly named population feature. Metadata
    # certificates in the evaluation layer are deliberately outside this seam.
    assert set(MarketBar.model_fields) == {
        'ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'source', 'currency'}
    assert set(TechnicalBar.model_fields) == set(MarketBar.model_fields) | {'ma20', 'ma50', 'rsi14'}
    context = {f.name for f in fields(ScoringContext)}
    assert context == {'own_history_abnormality', 'market_relative_abnormality',
        'sector_relative_abnormality', 'economic_magnitude', 'days_since_similar_event', 'source_quality'}
    assert {f.name for f in fields(MaterialEventCandidate)} == context | {
        'ticker', 'event_type', 'category', 'direction', 'observed_at', 'evidence',
        'reason_codes', 'is_state_transition', 'data_completeness', 'is_fixture'}
    assert {f.name for f in fields(EvidenceItem)} == {'metric', 'value', 'source', 'prior_value', 'unit', 'as_of'}


def semantic_streams(aliases):
    """Two different, interleaved synthetic histories sharing real event memory."""
    memory = EventMemory()
    outputs = []
    for stream, ticker in enumerate(aliases):
        bars = []
        for i in range(150):
            close = 100 + (6 + stream * 3) * sin(i / (8 + stream * 3)) + .03 * i
            bars.append(MarketBar(ticker=ticker, date=date(2021, 1, 1) + timedelta(days=i),
                open=close, high=close + 1, low=close - 1, close=close,
                volume=1000 + 100 * (i % 7) + (4000 if i % (13 + stream) == 0 else 0),
                source='synthetic_safeguard6'))
        outputs.append({'bars': bars, 'technical': technical_history(ticker, bars, bars[0].source),
                        'raw': [], 'results': [], 'scoreable': [], 'facts': [], 'episodes': {f: [] for f in FAMILIES}})
    for i in range(150):
        for ticker, out in zip(aliases, outputs):
            current = out['technical'][i]
            prior = out['technical'][i - 1] if i else None
            snapshot = market_snapshot(ticker, out['bars'][:i + 1], current.source)
            raw, contexts = build_context(snapshot, current, out['raw'], current.volume, None,
                                           SimpleNamespace(lookback_sessions=252, min_history=60))
            now = datetime.combine(current.date, time(23, 59, 59))
            contexts = {kind: replace(ctx, days_since_similar_event=memory.days_since(ticker, kind, now))
                        for kind, ctx in contexts.items()}
            results = detect_and_score_market_events(prior, current, contexts, is_fixture=True)
            for result in results:
                memory.record(ticker, result.candidate.event_type.value, now)
            out['results'].append([asdict(r) for r in results])
            # Exercise numerical scoring as a synthetic unit-test scenario too;
            # keep the fixture-path results above, and never persist replay cases.
            out['scoreable'].append([asdict(evaluate_candidate(replace(
                r.candidate, is_fixture=False, source_quality=.8, data_completeness=.75))) for r in results])
            session = current.date.isoformat()
            for family in FAMILIES:
                if family in FAMILIES[:2]:
                    key = 'daily_return' if family == FAMILIES[0] else 'volume'
                    fact = factual_inputs(family, session, raw[key], [
                        {'session': out['bars'][j].date.isoformat(), 'value': r[key], 'comparable': True}
                        for j, r in enumerate(out['raw'])])
                else:
                    values = [None if row is None else
                              (None if row.ma20 is None or row.ma50 is None else row.ma20 - row.ma50)
                              if family == 'ma_cross' else row.rsi14 for row in (prior, current)]
                    fact = transition_inputs(family, *values)
                out['facts'].append(fact)
                out['episodes'][family].append({**fact, 'session': session, 'continuous': True})
            out['raw'].append(raw)
    semantic = []
    for ticker, out in zip(aliases, outputs):
        links = {family: link_episodes(ticker, family, rows) for family, rows in out['episodes'].items()}
        # Canonicalize identity-derived IDs, preserving equality/link structure.
        ids = {}
        for rows in links.values():
            for row in rows:
                for field in ('link_id', 'episode_id', 'closed_episode_id', 'prior_unresolved_episode_id'):
                    if row[field] is not None:
                        row[field] = ids.setdefault(row[field], len(ids))
        results = out['results']
        for day in results + out['scoreable']:
            for result in day:
                del result['candidate']['ticker']
        semantic.append({'technical': [r.model_dump(exclude={'ticker'}) for r in out['technical']],
                         'raw': out['raw'], 'facts': out['facts'], 'results': results,
                         'scoreable': out['scoreable'], 'episodes': links})
    return semantic


def test_identical_history_is_label_invariant():
    original = semantic_streams(('ABC', 'SECOND'))
    renamed = semantic_streams(('ALIAS_ABC', 'SECOND'))
    assert original == renamed
    assert {r['candidate']['event_type'].value for day in original[0]['results'] for r in day} == set(FAMILIES)
    assert any(f['predicate_result'] == 'UNRESOLVED' for f in original[0]['facts'])
    assert any(r['candidate']['days_since_similar_event'] == 1 for day in original[0]['results'] for r in day)
    assert any(r['base_score'] is not None for day in original[0]['scoreable'] for r in day)
    assert all(r['components']['confidence'] == pytest.approx(.6)
               for day in original[0]['scoreable'] for r in day)


def test_two_stream_alias_permutation_follows_history():
    original = semantic_streams(('X', 'Y'))
    swapped = semantic_streams(('Y', 'X'))
    assert original[0] != original[1]
    assert original == swapped
