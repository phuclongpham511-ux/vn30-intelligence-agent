"""Offline acceptance of preserved pilot evidence on an isolated SQLite backup.

No provider requests, no canonical import, no receipt reconstruction. The source
must be an explicitly supplied existing pilot database. Outputs are Git ignored.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from main import app
from src.db.session import get_session
from src.models import Security
from src.models.technical_eod import TechnicalEODJob, TechnicalEODSnapshot, TechnicalEODRetrievalReceipt
from src.services.provisional_eod import AuthenticatedSsiReadReceipt, evaluate_provisional_technical_eod_packet
from src.services.technical_eod_store import AcceptedProvisionalEvidence, read_latest_operational_packet, _dbtime, _hash
from src.services.technical_api import BoundedCorporateActionReader
from src.services.watchlist_intelligence import technical_updates
from scripts.supervise_technical_eod import ROOT, configuration


def validate(source_db, output_dir):
    source_db, output_dir = Path(source_db).resolve(), Path(output_dir).resolve()
    if not source_db.is_file() or not output_dir.is_relative_to(ROOT / 'data'):
        raise ValueError('Existing source and isolated Git-ignored output required')
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / 'replay.db'
    if destination.exists() or destination == source_db:
        raise ValueError('Refuse to overwrite any database')
    config, paths = configuration(ROOT / 'docs' / 'TECHNICAL_FPT_PILOT_V1.json')
    identity = json.loads(paths['security_receipt'].read_bytes())
    before = sha256(source_db.read_bytes()).hexdigest()
    with sqlite3.connect(source_db.as_uri() + '?mode=ro', uri=True) as original:
        with sqlite3.connect(destination) as copy:
            original.backup(copy)
            assert copy.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert not copy.execute('PRAGMA foreign_key_check').fetchall()
    engine = create_engine('sqlite:///file:' + destination.as_posix() + '?mode=ro&uri=true')
    now = datetime.now(timezone.utc)
    try:
        with Session(engine) as session:
            ticker = config['ticker']
            security = session.get(Security, ticker)
            assert security and security.symbol == identity['symbol']
            assert security.exchange == identity['exchange'] == 'HOSE'
            assert security.instrument_type == identity['instrument_type'] == 'Stock'
            assert security.source == identity['source'] == 'SSI:FastConnect'
            result = read_latest_operational_packet(session, ticker, now)
            assert result.kind == 'provisional_packet', 'Preserved pilot has no accepted packet'
            row = session.get(TechnicalEODSnapshot, result.snapshot_id)
            job = session.get(TechnicalEODJob, row.job_id)
            assert job.active_snapshot_id == row.id and row.state == 'ACTIVE'
            evidence = AcceptedProvisionalEvidence.model_validate(row.evidence)
            for receipt in (evidence.first, evidence.second):
                from src.services.provisional_eod import compact_ssi_receipt
                compact = (compact_ssi_receipt(receipt) if hasattr(receipt, 'history') else receipt)
                audit = session.get(TechnicalEODRetrievalReceipt, _hash(compact.model_dump(mode='json')))
                assert audit and _hash(audit.payload) == audit.id
                AuthenticatedSsiReadReceipt.model_validate(audit.payload)
            accepted_at = _dbtime(row.accepted_at)
            replay = evaluate_provisional_technical_eod_packet(ticker, row.trading_session,
                history_start=evidence.history_start, calendar=evidence.calendar,
                publication=evidence.publication, first=evidence.first, second=evidence.second,
                evaluation_as_of=accepted_at, generated_at=accepted_at, db_session=session,
                corporate_actions=BoundedCorporateActionReader(session, ticker, accepted_at))
            assert replay.model_dump(mode='json') == row.packet, 'D1/D4/D5 replay differs'
            projection = technical_updates(session, ticker, now)
            assert projection['data']['snapshot_id'] == result.snapshot_id
            assert len(projection['items']) == len(result.packet.top_insights)
            def dependency():
                yield session
            app.dependency_overrides[get_session] = dependency
            try:
                response = TestClient(app).get('/technical/' + ticker + '/daily/operational/latest')
                assert response.status_code == 200
                payload = response.json()
                assert payload['snapshot_id'] == row.id and payload['packet'] == result.packet.model_dump(mode='json')
            finally:
                app.dependency_overrides.pop(get_session, None)
            (output_dir / 'packet.json').write_text(json.dumps(payload, sort_keys=True), encoding='utf-8')
            report = dict(evidence_origin='preserved_authenticated_SSI_pilot_offline_replay',
                source_database_unchanged=True, source_sha256=before, ticker=ticker,
                session=row.trading_session.isoformat(), assurance=result.assurance,
                packet_state=result.packet.packet_state, snapshot_version=row.version,
                freshness=result.freshness, d1_d4_d5_exact_replay=True,
                api_agreement=True, watchlist_agreement=True, observation_count=evidence.first.observation_count,
                first_received_at=evidence.first.received_at.isoformat(),
                second_received_at=evidence.second.received_at.isoformat(),
                publication_at=evidence.publication.published_at.isoformat(), ssi_requests=0)
    finally:
        engine.dispose()
    assert sha256(source_db.read_bytes()).hexdigest() == before, 'Source database changed during validation'
    (output_dir / 'acceptance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-db', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.source_db, args.output_dir), sort_keys=True))


if __name__ == '__main__':
    main()
