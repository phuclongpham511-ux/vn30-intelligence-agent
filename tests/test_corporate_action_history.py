"""Original scored events remain immutable while later evidence is appended."""
import pytest

from src.corporate_actions.history import TechnicalContextHistory
from src.corporate_actions.repository import CorporateActionRepository
from src.materiality.service import detect_and_score_market_events
from src.materiality.detectors import ScoringContext
from tests.test_corporate_action_context import at, notice, price_pair


def test_late_notice_and_correction_append_without_rewriting_original(session):
    repo = CorporateActionRepository(session)
    history = TechnicalContextHistory(repo)
    result = detect_and_score_market_events(*price_pair(), {'abnormal_price_move': ScoringContext(own_history_abnormality=.99)})[0]
    original = history.record('event-1', result, generated_at=at(10))
    assert original.result.corporate_action_context.status == 'UNKNOWN'
    repo.ingest(notice(), received_at=at(12))
    assert history.get('event-1', as_of=at(11)) == original
    updated = history.append_update('event-1', enriched_at=at(12))
    assert updated.result == original.result
    assert updated.generated_at == at(10)
    assert len(updated.updates) == 1
    assert updated.updates[0].enriched_at == at(12)
    assert updated.updates[0].context.actions[0].observed_at == at(12)
    assert history.append_update('event-1', enriched_at=at(13)) == updated
    repo.ingest(notice(effective_date='2024-06-14'), received_at=at(14))
    corrected = history.append_update('event-1', enriched_at=at(14))
    assert corrected.result == original.result
    assert corrected.updates[-1].context.status == 'UNKNOWN'
    assert history.get('event-1', as_of=at(13)) == updated
    assert history.get('event-1', as_of=at(11)) == original
    with pytest.raises(ValueError):
        history.append_update('event-1', enriched_at=at(13))
    with pytest.raises(ValueError):
        history.record('event-1', result, generated_at=at(12))
    with pytest.raises(KeyError):
        history.get('event-1', as_of=at(9))


def test_record_uses_generation_knowledge_not_pre_enriched_future_context(session):
    repo = CorporateActionRepository(session)
    repo.ingest(notice(), received_at=at(12))
    result = detect_and_score_market_events(*price_pair(), {'abnormal_price_move': ScoringContext(own_history_abnormality=.99)},
        corporate_actions=repo, generated_at=at(13))[0]
    history = TechnicalContextHistory(repo)
    original = history.record('event', result, generated_at=at(10))
    assert original.result.corporate_action_context.status == 'UNKNOWN'
    assert history.record('event', result, generated_at=at(10)) == original
    later = history.append_update('event', enriched_at=at(12))
    assert later.updates[0].context.status == 'KNOWN_MATCH'
