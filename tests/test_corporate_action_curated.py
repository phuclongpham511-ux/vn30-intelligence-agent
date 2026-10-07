"""Verified notice facts + explicitly simulated receipts/prices, not vendor PIT."""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pytest
from src.corporate_actions.curated import load_curated, ingest_curated
from src.corporate_actions.repository import CorporateActionRepository
from src.materiality.detectors import ScoringContext
from src.materiality.service import detect_and_score_market_events
from tests.test_corporate_action_context import price_pair

PATH = Path(__file__).resolve().parents[1] / 'data/corporate_actions/verified_v1.json'


@pytest.mark.parametrize('symbol,day,types', [
    ('VNM', date(2020,9,29), {'cash_dividend','bonus_shares'}),
    ('HDB', date(2022,9,27), {'stock_dividend'}),
    ('GAS', date(2023,9,22), {'bonus_shares'}),
    ('SSI', date(2022,6,22), {'rights_offering'}),
])
def test_verified_notices_through_real_service_with_simulated_receipt(session, symbol, day, types):
    repo = CorporateActionRepository(session)
    received = datetime.combine(day, datetime.min.time(), timezone.utc)
    for n in load_curated(PATH).notices:
        if n.symbol == symbol:
            # No claim Woofi actually observed these historical notices then.
            repo.ingest(n.model_copy(update={'is_fixture': True}), received_at=received)
    before = repo.context_for(symbol, day, as_of=received-timedelta(seconds=1))
    assert before.status == 'UNKNOWN'
    contexts = {'abnormal_price_move': ScoringContext(own_history_abnormality=.99)}
    result = detect_and_score_market_events(*price_pair(symbol,day), contexts, is_fixture=True,
        corporate_actions=repo, generated_at=received+timedelta(hours=12))[0]
    match = result.corporate_action_context
    assert {a.action_type.value for a in match.actions} == types
    assert all(a.symbol == symbol and a.effective_date == day and a.observed_at == received
        and a.source and a.source_url and a.source_id and a.is_fixture for a in match.actions)
    for adjacent in (day-timedelta(days=1), day+timedelta(days=1)):
        assert repo.context_for(symbol, adjacent, as_of=received+timedelta(days=2)).status == 'UNKNOWN'
    assert repo.context_for('OTHER',day,as_of=received).status == 'UNKNOWN'


def test_real_additional_registration_does_not_invent_ex_date(session):
    notice = next(n for n in load_curated(PATH).notices if n.symbol == 'HFC')
    assert notice.action_type == 'additional_issuance'
    assert notice.effective_date is None
    assert notice.terms is None
    repo = CorporateActionRepository(session)
    received = datetime(2023,9,22,12,tzinfo=timezone.utc)
    repo.ingest(notice.model_copy(update={'is_fixture':True}), received_at=received)
    for day in (date(2023,9,22),date(2023,9,26)):
        assert repo.context_for('HFC',day,as_of=received+timedelta(days=5)).status == 'UNKNOWN'


def test_curated_import_stamps_actual_receipts_and_repeated_import_deduplicates(session):
    repo = CorporateActionRepository(session)
    dataset = load_curated(PATH)
    before = datetime.now(timezone.utc)
    assert ingest_curated(repo,dataset) == {'inserted':6,'duplicate':0,'revision':0}
    after = datetime.now(timezone.utc)
    observations = repo.get_known_actions_as_of(as_of=after)
    assert len(observations) == 6
    assert all(before <= a.observed_at <= after for a in observations)
    assert not repo.get_known_actions_as_of(as_of=before-timedelta(seconds=1))
    assert ingest_curated(repo,dataset) == {'inserted':0,'duplicate':6,'revision':0}
    assert repo.get_known_actions_as_of(as_of=datetime.now(timezone.utc)) == observations


def test_cli_import_appends_late_context_through_persisted_service(session, tmp_path, monkeypatch, capsys):
    import json
    from scripts import ingest_corporate_actions as command
    from src.corporate_actions.curated import CuratedDataset
    from src.corporate_actions.history import TechnicalContextHistory
    from tests.test_corporate_action_context import notice
    repo = CorporateActionRepository(session)
    history = TechnicalContextHistory(repo)
    result = detect_and_score_market_events(*price_pair(), {'abnormal_price_move':ScoringContext(own_history_abnormality=.99)})[0]
    original = history.record('live-event',result,generated_at=datetime.now(timezone.utc)-timedelta(seconds=10))
    dataset = CuratedDataset(dataset_version='cli-test',source_kind='curated_verified',limitations=('synthetic notice',),
        notices=(notice(is_fixture=True),))
    path = tmp_path/'notices.json'
    path.write_text(dataset.model_dump_json(),encoding='utf-8')
    monkeypatch.setattr(command, 'get_engine',lambda:session.get_bind())
    monkeypatch.setattr('sys.argv',['ingest_corporate_actions',str(path),'--append-updates'])
    command.main()
    output = json.loads(capsys.readouterr().out)
    assert output['inserted'] == output['context_updates_appended'] == 1
    stored = history.get('live-event',as_of=datetime.now(timezone.utc))
    assert stored.result == original.result
    assert stored.result.corporate_action_context.status == 'UNKNOWN'
    assert stored.updates[0].context.status == 'KNOWN_MATCH'
    assert stored.updates[0].enriched_at > original.generated_at
    command.main()
    repeated = json.loads(capsys.readouterr().out)
    assert repeated['duplicate'] == 1
    assert repeated['context_updates_appended'] == 0
