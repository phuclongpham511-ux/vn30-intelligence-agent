"""Canonical collector integration with deterministic, synthetic source seams."""
from datetime import timedelta
from threading import Thread
import pytest
from sqlmodel import Session

from test_supervised_eod import pilot
from test_technical_eod_persistence import fresh
from src.models.technical_eod import TechnicalEODJob
from src.services.technical_eod_store import read_latest_operational_packet, _hash
from test_technical_eod_persistence import setup
from src.services import technical_eod_supervision as supervision
from src.services.ingestion_owner import collector_owner
from scripts import ingest_data


@pytest.mark.parametrize('enabled', [False, True])
def test_canonical_launcher_reads_explicit_nonsecret_opt_in(session, monkeypatch, enabled):
    from types import SimpleNamespace
    monkeypatch.setattr('sys.argv', ['ingest_data', '--watch'])
    monkeypatch.setattr(ingest_data, 'get_engine', session.get_bind)
    monkeypatch.setattr(ingest_data, 'create_tables', lambda: None)
    monkeypatch.setattr(ingest_data, 'get_settings', lambda: SimpleNamespace(technical_eod_pilot=enabled), raising=False)
    calls = []
    monkeypatch.setattr(ingest_data, 'run', lambda *a, **kw: calls.append(kw) or 0)
    assert ingest_data.main() == 0
    assert calls[0]['technical_pilot'] is enabled


def test_pilot_setting_defaults_off_and_rejects_malformed_values(tmp_path, monkeypatch):
    from src.config.settings import Settings
    from pydantic import ValidationError
    monkeypatch.delenv('TECHNICAL_EOD_PILOT', raising=False)
    assert Settings(_env_file=None).technical_eod_pilot is False
    path = tmp_path/'pilot.env'
    path.write_text('TECHNICAL_EOD_PILOT=true\n')
    assert Settings(_env_file=path).technical_eod_pilot is True
    path.write_text('TECHNICAL_EOD_PILOT=unknown\n')
    with pytest.raises(ValidationError):
        Settings(_env_file=path)


def test_unconfigured_canonical_pilot_never_fetches(session):
    result = supervision.run_configured_technical_eod_cycle(session.get_bind(),
        source_factory=lambda: pytest.fail('unconfigured source'))
    assert result['status'] == 'UNCONFIGURED'


def test_canonical_pilot_restart_accepts_existing_engine_packet(session):
    target, cal, pub, read, now, source = pilot(session)
    engine = session.get_bind()
    first = supervision.run_configured_technical_eod_cycle(engine,
        source_factory=lambda: source, clock=lambda: now,
        acquire=lambda *a: fresh(read, now))
    assert first['status'] == 'WAITING_FOR_TIME'
    with Session(engine) as restarted:
        job = restarted.get(TechnicalEODJob, 'XYZ:' + target.isoformat())
        due = job.next_due_at.replace(tzinfo=now.tzinfo)
    result = supervision.run_configured_technical_eod_cycle(engine,
        source_factory=lambda: source, clock=lambda: due + timedelta(seconds=3),
        acquire=lambda *a: fresh(read, due + timedelta(seconds=3)))
    assert result['status'] == 'PROVISIONAL'


def test_canonical_owner_excludes_competing_pilot(session):
    engine = session.get_bind()
    output = []
    with collector_owner(engine) as owned:
        assert owned
        child = Thread(target=lambda: output.append(
            supervision.run_configured_technical_eod_cycle(engine,
                source_factory=lambda: pytest.fail('competing source'))))
        child.start(); child.join(timeout=5)
        assert not child.is_alive()
    assert output == [{'status': 'collector_busy'}]


def test_canonical_worker_opt_in_replaces_queue_consumer_not_other_domains(session, monkeypatch):
    engine = session.get_bind()
    for name in ('sync_universe', 'sync_index_groups', 'ingest_cycle', 'ingest_community'):
        monkeypatch.setattr(ingest_data, name, lambda *a, **kw: {'status': 'cached'})
    monkeypatch.setattr(ingest_data, 'load_sources', lambda *a: [])
    calls = []
    monkeypatch.setattr(ingest_data, 'run_configured_technical_eod_cycle',
        lambda e: calls.append(e) or {'status': 'UNCONFIGURED'})
    monkeypatch.setattr(ingest_data, 'run_technical_eod_cycle',
        lambda *a: pytest.fail('second EOD consumer'))
    result = ingest_data.run_cycle(engine, technical_pilot=True)
    assert calls == [engine]
    assert result['technical_eod']['status'] == 'UNCONFIGURED'
    assert all(result[d]['status'] == 'cached' for d in ('universe', 'groups', 'news', 'community'))


def test_persisted_gates_project_distinct_wait_states_and_due_evidence(session):
    target, cal, pub, first, second, now = setup(session)
    job = session.get(TechnicalEODJob, 'XYZ:' + target.isoformat())
    publication_gate = pub.published_at + timedelta(hours=24)
    result = read_latest_operational_packet(session, 'XYZ', publication_gate - timedelta(seconds=1))
    assert result.operational_state == 'WAITING_PUBLICATION_GATE'
    due = result.next_eligible_read_at
    if due > publication_gate:
        assert read_latest_operational_packet(session, 'XYZ', publication_gate).operational_state == 'WAITING_SECOND_READ'
    assert read_latest_operational_packet(session, 'XYZ', due).operational_state == 'PENDING_EVIDENCE'
    assert 'matching_second_authenticated_ssi_read' in result.missing_evidence
    job.status = 'STOPPED'; session.add(job); session.commit()
    assert read_latest_operational_packet(session, 'XYZ', now).operational_state == 'SOURCE_UNAVAILABLE'


def test_missing_calendar_remains_incomplete_not_waiting(session):
    target, cal, pub, first, second, now = setup(session)
    job = session.get(TechnicalEODJob, 'XYZ:' + target.isoformat())
    job.definition = {**job.definition, 'calendar': None}
    job.definition_hash = _hash(job.definition)
    session.add(job); session.commit()
    result = read_latest_operational_packet(session, 'XYZ', now)
    assert result.operational_state == 'INCOMPLETE'
    assert 'calendar_session_evidence' in result.missing_evidence


def test_corrupt_definition_cannot_claim_a_valid_wait_gate(session):
    target, *_, now = setup(session)
    job = session.get(TechnicalEODJob, 'XYZ:' + target.isoformat())
    job.definition_hash = '0' * 64
    session.add(job); session.commit()
    result = read_latest_operational_packet(session, 'XYZ', now)
    assert result.operational_state == 'INCOMPLETE'
    assert result.next_eligible_read_at is None
    assert result.reason_codes == ('invalid_evidence_definition',)


@pytest.mark.parametrize('invalid', ['publication', 'receipt'])
def test_unqualified_persisted_inputs_cannot_advertise_eligible_read_time(session, invalid):
    target, cal, pub, first, second, now = setup(session)
    job = session.get(TechnicalEODJob, 'XYZ:' + target.isoformat())
    if invalid == 'publication':
        job.definition = {**job.definition, 'publication': {
            **job.definition['publication'], 'source_ref': 'https://example.com/not-an-exchange'}}
        job.definition_hash = _hash(job.definition)
    else:
        job.first_receipt = {**job.first_receipt, 'requested_ticker': 'OTHER'}
    job.status = 'WAITING_FOR_TIME'
    job.next_due_at = now + timedelta(hours=1)
    session.add(job); session.commit()
    result = read_latest_operational_packet(session, 'XYZ', now)
    assert result.operational_state == 'INCOMPLETE'
    assert result.next_eligible_read_at is None
    assert result.safe_to_display_as_verified is False
    from src.services.watchlist_intelligence import technical_updates
    watchlist = technical_updates(session, 'XYZ', now)
    assert not watchlist['waiting_for_gate'] and not watchlist['awaiting_source_check']
    assert watchlist['next_check_due_at'] is None


def test_incomplete_packet_state_is_not_projected_as_accepted(session):
    from src.services.technical_eod_store import TechnicalOperationalAPIPacket
    from test_technical_eod_persistence import run
    target, cal, pub, first, second, now = setup(session)
    assert run(session, second, now)['status'] == 'PROVISIONAL'
    payload = read_latest_operational_packet(session, 'XYZ', now).model_dump(mode='json')
    payload.pop('operational_state')
    payload['packet']['packet_state'] = 'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'
    assert TechnicalOperationalAPIPacket.model_validate(payload).operational_state == 'INCOMPLETE'
