from datetime import date, datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy import text
from src.corporate_actions.models import ActionType, ActionTerms, CorporateActionNotice
from src.corporate_actions.repository import CorporateActionRepository
from src.materiality.detectors import ScoringContext
from src.materiality.service import detect_and_score_market_events
from src.analytics.market import technical_history
from src.schemas.data import MarketBar
from tests.test_corporate_action_context import at, notice
from tests.test_bollinger import pattern


@pytest.mark.parametrize('changes', [
    {'effective_date': None}, {'action_type': 'other'}, {'verified': False}, {'withdrawn': True}
])
def test_unresolved_or_ineligible_notice_is_not_matched(session, changes):
    repo = CorporateActionRepository(session)
    repo.ingest(notice(**changes), received_at=at(1))
    assert len(repo.get_actions_for_symbol('ABC', as_of=at(10))) == 1
    assert repo.context_for('ABC', date(2024,6,10), as_of=at(10)).status == 'UNKNOWN'


@pytest.mark.parametrize('action_type', [v for v in ActionType if v != ActionType.OTHER])
def test_all_price_affecting_types_match_without_optional_fields(session, action_type):
    repo = CorporateActionRepository(session)
    minimal = CorporateActionNotice(symbol='XYZ', action_type=action_type, effective_date='2024-06-10',
        source='verified synthetic', source_id='one', verified=True, is_fixture=True)
    repo.ingest(minimal, received_at=at(1))
    match = repo.context_for('XYZ', date(2024,6,10), as_of=at(10)).actions[0]
    assert match.source_url is match.terms is match.announced_at is match.announced_on is match.record_date is match.payment_date is None
    assert match.action_type == action_type
    assert match.is_fixture


def test_source_unavailable_does_not_claim_no_action(session):
    repo = CorporateActionRepository(session)
    session.exec(text('DROP TABLE corporateactionrecord'))
    session.commit()
    context = repo.context_for('ABC', date(2024,6,10), as_of=at(10))
    assert context.status == 'UNKNOWN'
    assert context.coverage == 'INCOMPLETE'
    assert context.reason == 'source_unavailable'


def test_multiple_same_type_components_and_corrected_symbol(session):
    repo = CorporateActionRepository(session)
    for component in ('one', 'two'):
        repo.ingest(notice(component_id=component), received_at=at(1))
    assert len(repo.context_for('ABC', date(2024,6,10), as_of=at(2)).actions) == 2
    repo.ingest(notice(component_id='one', symbol='XYZ'), received_at=at(3))
    assert len(repo.context_for('ABC', date(2024,6,10), as_of=at(2)).actions) == 2
    assert len(repo.context_for('ABC', date(2024,6,10), as_of=at(3)).actions) == 1
    assert len(repo.context_for('XYZ', date(2024,6,10), as_of=at(3)).actions) == 1


def test_timezone_and_chronology_validation(session):
    repo = CorporateActionRepository(session)
    with pytest.raises(ValueError):
        repo.ingest(notice(), received_at=datetime(2024,6,1))
    repo.ingest(notice(), received_at=at(2))
    with pytest.raises(ValueError):
        repo.ingest(notice(), received_at=at(1))
    with pytest.raises(ValueError):
        repo.ingest(notice(effective_date='2024-06-12'), received_at=at(2))
    with pytest.raises(ValidationError):
        notice(announced_at='2024-06-01T00:00:00')
    with pytest.raises(ValidationError):
        notice(source_id=None)
    with pytest.raises(ValidationError):
        ActionTerms(cash_vnd_per_share=float('nan'))
    # Explicit offsets represent the same knowledge instant, including near midnight.
    n = notice(announced_at='2024-06-01T00:30:00+07:00')
    assert n.announced_at == datetime(2024,5,31,17,30,tzinfo=timezone.utc)
    assert repo.context_for('ABC', date(2024,6,10), as_of=at(2).astimezone(timezone(timedelta(hours=7)))).status == 'KNOWN_MATCH'


@pytest.mark.parametrize('scenario', ['ma_rsi', 'lower', 'upper'])
def test_context_preserves_ma_rsi_and_bollinger_outputs(session, scenario):
    if scenario == 'ma_rsi':
        closes = [100.0]*59 + [103.0]
        bars = [MarketBar(ticker='XYZ', date=date(2001,1,1)+timedelta(days=i), open=p, high=p, low=p,
            close=p, volume=100, source='synthetic') for i,p in enumerate(closes)]
        rows = technical_history('XYZ', bars, 'synthetic')
        expected = {'ma_cross', 'rsi_regime_entry'}
        contexts = {k: ScoringContext(own_history_abnormality=.8, days_since_similar_event=1) for k in expected}
    else:
        rows = pattern(scenario)
        expected = {'bollinger_'+scenario+'_reversal_volume'}
        contexts = {k: ScoringContext(own_history_abnormality=.8, days_since_similar_event=1) for k in expected}
        contexts['unusual_volume'] = ScoringContext(own_history_abnormality=1)
    now = datetime.combine(rows[-1].date, datetime.min.time(), timezone.utc)
    repo = CorporateActionRepository(session)
    repo.ingest(notice(symbol='XYZ', effective_date=rows[-1].date, record_date=None, payment_date=None, is_fixture=True),
        received_at=now-timedelta(days=1))
    kwargs = dict(recent_bars=rows[-4:], relative_volume=3, is_fixture=True)
    plain = detect_and_score_market_events(rows[-2], rows[-1], contexts, **kwargs)
    enriched = detect_and_score_market_events(rows[-2], rows[-1], contexts, corporate_actions=repo, generated_at=now, **kwargs)
    assert expected <= {r.candidate.event_type.value for r in enriched}
    for p,e in zip(plain,enriched, strict=True):
        assert p.candidate == e.candidate
        assert p.components == e.components
        assert p.base_score == e.base_score
        assert p.excluded == e.excluded
        assert p.reason_codes == e.reason_codes
        assert e.corporate_action_context.status == 'KNOWN_MATCH'


def test_no_new_signal_is_created_by_corporate_action(session):
    from tests.test_corporate_action_context import price_pair
    repo = CorporateActionRepository(session)
    repo.ingest(notice(), received_at=at(1))
    assert detect_and_score_market_events(*price_pair(), corporate_actions=repo, generated_at=at(10)) == ()
