"""Stock Detail discovers accepted sessions, never inferred sessions or vendor reads."""
from datetime import timedelta
from sqlalchemy import event
from test_technical_eod_persistence import setup, run
from src.models.technical_eod import TechnicalEODJob


def clock(now):
    from main import app
    from routers.technical import get_evaluation_clock
    app.dependency_overrides[get_evaluation_clock] = lambda: now


def test_latest_empty_has_no_invented_session(client):
    result = client.get('/technical/XYZ/daily/operational/latest')
    assert result.status_code == 200
    assert result.json()['kind'] == 'diagnostic'
    assert result.json()['requested_session'] is None
    assert result.headers['cache-control'] == 'no-store'


def test_latest_accepted_ignores_newer_unqualified_job_and_is_select_only(session, client, monkeypatch):
    target, cal, pub, first, second, now = setup(session)
    run(session, second, now)
    later = target + timedelta(days=1)
    session.add(TechnicalEODJob(id='XYZ:'+later.isoformat(), ticker='XYZ',
        trading_session=later, definition={}, definition_hash='unqualified', next_due_at=now))
    session.commit()
    clock(now)
    monkeypatch.setattr('src.services.technical_eod_store.capture_fresh_ssi_read', lambda *a: (_ for _ in ()).throw(AssertionError('SSI in HTTP')))
    monkeypatch.setattr('src.services.technical_eod_store.evaluate_provisional_technical_eod_packet', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('scoring in HTTP')))
    statements = []
    def capture(conn, cursor, statement, parameters, context, executemany): statements.append(statement)
    event.listen(session.get_bind(), 'before_cursor_execute', capture)
    try:
        response = client.get('/technical/XYZ/daily/operational/latest')
    finally:
        event.remove(session.get_bind(), 'before_cursor_execute', capture)
    assert response.status_code == 200
    result = response.json()
    assert result['packet']['trading_session'] == target.isoformat()
    assert result['assurance'] == 'PROVISIONAL'
    assert result['safe_to_display_as_verified'] is False
    assert statements and all(s.lstrip().upper().startswith('SELECT') for s in statements)


def test_latest_retraction_is_diagnostic_without_resurrecting_an_older_snapshot(session, client):
    target, cal, pub, first, second, now = setup(session)
    run(session, second, now)
    session.expire_all()
    job = session.get(TechnicalEODJob, 'XYZ:'+target.isoformat())
    job.active_snapshot_id = None
    job.reason_codes = ['source_revision_detected']
    session.add(job)
    older = target-timedelta(days=1)
    session.add(TechnicalEODJob(id='XYZ:'+older.isoformat(), ticker='XYZ', trading_session=older,
        definition={}, definition_hash='older', version=1, active_snapshot_id='older-snapshot', next_due_at=now))
    session.commit()
    clock(now)
    result = client.get('/technical/XYZ/daily/operational/latest').json()
    assert result['kind'] == 'diagnostic'
    assert result['requested_session'] == target.isoformat()
    assert result['reason_codes'] == ['source_revision_detected']


def test_latest_pending_reports_actual_job_and_rejects_queries(session, client):
    target, *_, now = setup(session)
    clock(now)
    result = client.get('/technical/XYZ/daily/operational/latest').json()
    assert result['kind'] == 'diagnostic'
    assert result['requested_session'] == target.isoformat()
    assert client.get('/technical/XYZ/daily/operational/latest?session=2026-01-01').status_code == 422
    assert client.get('/technical/BAD%24/daily/operational/latest').status_code == 422


def test_latest_infrastructure_failure_is_sanitized(session, client, monkeypatch):
    monkeypatch.setattr(session, 'exec', lambda *a: (_ for _ in ()).throw(RuntimeError('API_SECRET=SECRET')))
    result = client.get('/technical/XYZ/daily/operational/latest')
    assert result.status_code == 503
    assert result.json()['kind'] == 'diagnostic'
    assert 'SECRET' not in result.text
