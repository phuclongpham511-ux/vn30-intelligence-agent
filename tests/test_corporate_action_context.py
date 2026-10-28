"""Public ingestion/query/enrichment behavior; source dates are not receipt dates."""
from datetime import date, datetime, timezone

from src.corporate_actions.models import CorporateActionNotice
from src.corporate_actions.repository import CorporateActionRepository
from src.analytics.market import technical_history
from src.materiality.detectors import ScoringContext
from src.materiality.service import detect_and_score_market_events
from src.schemas.data import MarketBar


def at(day):
    return datetime(2024, 6, day, 10, tzinfo=timezone.utc)


def notice(**changes):
    return CorporateActionNotice.model_validate(dict(
        symbol=' abc ', action_type='cash_dividend', effective_date='2024-06-10',
        record_date='2024-06-11', payment_date='2024-06-20', source='curated_verified',
        source_id='notice-1', verified=True) | changes)


def test_received_notice_is_visible_only_when_known_and_on_exact_session(session):
    repo = CorporateActionRepository(session)
    outcome = repo.ingest(notice(), received_at=at(1))
    assert outcome.status == 'inserted'
    assert repo.context_for('ABC', date(2024, 6, 10), as_of=at(1)).status == 'KNOWN_MATCH'
    assert repo.context_for('ABC', date(2024, 6, 10), as_of=at(1)).actions[0].observed_at == at(1)
    assert repo.context_for('ABC', date(2024, 6, 10), as_of=at(1)).actions[0].record_date == date(2024, 6, 11)
    assert repo.context_for('ABC', date(2024, 6, 10), as_of=datetime(2024, 5, 31, tzinfo=timezone.utc)).status == 'UNKNOWN'
    assert repo.context_for('ABC', date(2024, 6, 9), as_of=at(10)).status == 'UNKNOWN'
    assert repo.context_for('ABC', date(2024, 6, 11), as_of=at(11)).status == 'UNKNOWN'


def test_revisions_duplicates_and_multiple_components_preserve_knowledge(session):
    repo = CorporateActionRepository(session)
    original = repo.ingest(notice(), received_at=at(1)).observation
    duplicate = repo.ingest(notice(), received_at=at(2))
    assert duplicate.status == 'duplicate'
    assert duplicate.observation.observed_at == at(1)
    repo.ingest(notice(action_type='stock_dividend'), received_at=at(2))
    repo.ingest(notice(source='second_verified_source'), received_at=at(2))
    assert len(repo.context_for('ABC', date(2024, 6, 10), as_of=at(2)).actions) == 3
    revised = repo.ingest(notice(effective_date='2024-06-12', source_revision='v2'), received_at=at(3))
    assert revised.status == 'revision'
    assert revised.observation.action_id == original.action_id
    assert repo.get_actions_for_symbol('ABC', as_of=at(1)) == (original,)
    assert len(repo.context_for('ABC', date(2024, 6, 10), as_of=at(3)).actions) == 2
    assert repo.context_for('ABC', date(2024, 6, 12), as_of=at(3)).actions == (revised.observation,)
    # A→B→A is a new revision, rather than losing the intervening knowledge state.
    restored = repo.ingest(notice(), received_at=at(4))
    assert restored.status == 'revision'
    assert restored.observation.observation_id != original.observation_id


def test_distinct_issuers_in_the_same_source_document_do_not_overwrite(session):
    repo = CorporateActionRepository(session)
    repo.ingest(notice(), received_at=at(1))
    repo.ingest(notice(symbol='XYZ'), received_at=at(2))
    assert len(repo.get_known_actions_as_of(as_of=at(3))) == 2


def price_pair(symbol='ABC', day=date(2024, 6, 10)):
    from datetime import timedelta
    bars = [MarketBar(ticker=symbol, date=day-timedelta(days=1-i), open=100+i*5,
        high=100+i*5, low=100+i*5, close=100+i*5, volume=1000+i*200, source='test') for i in range(2)]
    return technical_history(symbol, bars, 'test')


def test_context_enriches_results_without_changing_candidates_or_scores(session):
    repo = CorporateActionRepository(session)
    repo.ingest(notice(), received_at=at(1))
    prior, current = price_pair()
    contexts = {k: ScoringContext(own_history_abnormality=.99) for k in ('abnormal_price_move', 'unusual_volume')}
    plain = detect_and_score_market_events(prior, current, contexts)
    enriched = detect_and_score_market_events(prior, current, contexts,
        corporate_actions=repo, generated_at=at(10))
    assert len(enriched) == len(plain) == 2
    for before, after in zip(plain, enriched):
        assert after.candidate == before.candidate
        assert after.components == before.components
        assert after.base_score == before.base_score
        assert after.reason_codes == before.reason_codes
        assert after.corporate_action_context.status == 'KNOWN_MATCH'
        assert after.corporate_action_context.actions[0].source_id == 'notice-1'
