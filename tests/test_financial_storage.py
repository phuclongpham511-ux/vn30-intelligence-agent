"""Dedicated SQLite storage seams; synthetic packets, no source acquisition."""
import pytest

from src.services.financial_journal import MetricJournal
from src.services.financial_intelligence import normalized_metrics
from test_financial_intelligence import balanced
from datetime import datetime, timezone
from src.providers.vnstock.financial_packet import packet_from_payloads
from test_financial_engine import fixture


def history_packet(quarters=34, *, start=2018 * 4, marker=1):
    metadata, original = fixture()
    next(row for row in metadata if row['field_name'] == 'isa5')['parent'] = 'isa3'
    reports = {}
    for kind, data in original.items():
        rows = []
        for serial in range(start, start + quarters):
            row = dict(data['quarters'][0], yearReport=serial // 4, lengthReport=serial % 4 + 1)
            if kind == 'income':
                row['isa3'] = 25 * marker
            rows.append(row)
        reports[kind] = dict(years=data['years'], quarters=rows)
    return packet_from_payloads('ABC', 'vnstock:VCI', 'CT', metadata, reports,
        source_version='synthetic', observed_at={k: datetime(2026, 7, 1, tzinfo=timezone.utc) for k in reports})


def test_legacy_journal_upgrade_preserves_metrics_and_has_a_restorable_backup(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    facts = normalized_metrics(balanced())
    journal.append(facts)
    before = journal.read()
    backup = tmp_path / 'before-v55.sqlite'
    assert journal.initialize(backup_path=backup)['schema_version'] == 1
    assert journal.read() == before
    assert MetricJournal(backup, readonly=True).read() == before
    assert journal.initialize()['migrated'] is False
    assert journal.storage_summary()['captures'] == 0


def test_full_packet_roundtrip_keeps_34_quarters_nulls_hierarchy_and_capture_digest(tmp_path):
    packet = history_packet()
    journal = MetricJournal(tmp_path / 'mirror.sqlite')
    journal.initialize()
    imported = journal.import_packet(packet, 'a' * 64, provenance={'collection': 'captures'})
    stored = MetricJournal(journal.path, readonly=True).read_packet(imported['capture_id'])
    assert stored == packet
    assert len([o for o in stored.reports['income'].observations if o.frequency == 'quarterly']) == 34
    oldest = next(o for o in stored.reports['income'].observations if o.period == '2018-Q1')
    assert next(line for line in oldest.items if line.code == 'isa5').parent == 'isa3'
    assert oldest.field_codes['revenue'] == 'isa3'
    assert next(o for o in stored.reports['balance'].observations if o.period == '2018-Q1').fields['cash_equivalents'] is None
    capture = journal.captures(ticker='ABC')[0]
    assert capture['capture_sha256'] == 'a' * 64
    assert capture['source'] == 'vnstock:VCI' and capture['provenance'] == {'collection': 'captures'}
    assert journal.import_packet(packet, 'a' * 64)['inserted_observations'] == 0
    assert journal.storage_summary()['captures'] == 1


def test_short_increment_adds_new_quarter_without_replacing_old_period_revisions(tmp_path):
    journal = MetricJournal(tmp_path / 'mirror.sqlite')
    journal.initialize()
    original = history_packet()
    old = journal.import_packet(original, 'a' * 64)
    # Q4 2025 through Q3 2026, after the 34-quarter Q2 2026 history.
    candidate = history_packet(4, start=2025 * 4 + 3, marker=2)
    new = journal.import_packet(candidate, 'b' * 64)
    assert new['selected_observations'] == 3  # one new quarter in each statement
    selected = journal.selected_statements('ABC', 'vnstock:VCI', frequency='quarterly')
    income = {row['observation'].period: row for row in selected if row['observation'].statement == 'income'}
    assert len(income) == 35 and '2018-Q1' in income and '2026-Q3' in income
    assert income['2026-Q2']['capture_id'] == old['capture_id']
    assert income['2026-Q2']['observation'].fields['revenue'] == 25
    assert income['2026-Q3']['observation'].fields['revenue'] == 50
    assert journal.read_packet(new['capture_id']) == candidate
    assert journal.read_packet(old['capture_id']) == original
    journal.select_revision(new['capture_id'], statement='income', period='2026-Q2')
    selected = journal.selected_statements('ABC', 'vnstock:VCI', frequency='quarterly')
    assert next(r['observation'] for r in selected if r['observation'].statement == 'income'
                and r['observation'].period == '2026-Q2').fields['revenue'] == 50
    assert journal.read_packet(old['capture_id']) == original


def save_bundle(root, packet, *, ticker='ABC'):
    import hashlib
    import json
    root.mkdir(parents=True)
    body = packet.model_dump_json().encode('utf-8')
    digest = hashlib.sha256(body).hexdigest()
    (root / 'packet.json').write_bytes(body)
    (root / 'index.json').write_text(json.dumps({'contract': 'personal-saved-captures-v1',
        'captures': {ticker: {'file': 'packet.json', 'sha256': digest,
                              'format': 'canonical-financial-packet-v1'}}}), encoding='utf-8')
    return digest


def test_private_import_and_readonly_comparison_reuse_saved_contracts(tmp_path):
    from scripts.ingest_financial_intelligence import mirror_saved, compare_saved
    packet = history_packet()
    # Use the real saved-reader validation contract, not a mocked loader.
    packet.source_version = '4.0.2'
    root = tmp_path / 'captures'
    digest = save_bundle(root, packet)
    original_files = {p: p.read_bytes() for p in root.iterdir()}
    target = tmp_path / 'financial.sqlite'
    first = mirror_saved(root, target, tickers=['ABC'])
    second = mirror_saved(root, target, tickers=['ABC'])
    assert first['inserted_captures'] == 1 and first['inserted_observations'] == 111
    assert second['inserted_captures'] == second['inserted_observations'] == 0
    before = target.read_bytes()
    parity = compare_saved(root, target, tickers=['ABC'])
    assert parity['parity'] is True and parity['compared_captures'] == 1
    assert parity['captures'][0]['capture_sha256'] == digest
    assert parity['captures'][0]['quarterly_periods'] == 34
    assert target.read_bytes() == before
    assert {p: p.read_bytes() for p in root.iterdir()} == original_files


def test_legacy_ingestion_now_keeps_full_34_quarter_base_and_metric_projection(tmp_path):
    from scripts.ingest_financial_intelligence import ingest
    root = tmp_path / 'captures'
    packet = history_packet()
    packet.source_version = '4.0.2'
    save_bundle(root, packet)
    target = tmp_path / 'financial.sqlite'
    report = ingest(root, target, tmp_path / 'report')
    quarter = next(c for c in report['coverage'] if c['frequency'] == 'quarterly')
    assert quarter['periods'] == 34
    journal = MetricJournal(target, readonly=True)
    assert len({o.period for o in journal.read(frequency='quarterly')}) == 34
    assert journal.storage_summary()['statement_observations'] == 111


def test_persistence_is_not_limited_by_engine_or_display_windows(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    packet = history_packet(60)
    result = journal.import_packet(packet, 'c' * 64)
    assert len([o for o in journal.read_packet(result['capture_id']).reports['income'].observations
                if o.frequency == 'quarterly']) == 60
    assert len(journal.selected_statements('ABC', 'vnstock:VCI', frequency='quarterly')) == 180


def test_conflicting_same_capture_and_invalid_packet_cannot_change_existing_history(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    journal.import_packet(history_packet(), 'a' * 64)
    before = journal.storage_summary()
    with pytest.raises(ValueError, match='existing source capture'):
        journal.import_packet(history_packet(marker=2), 'a' * 64)
    invalid = history_packet()
    invalid.reports['cash'].observations[-1].ticker = 'OTHER'
    with pytest.raises(ValueError, match='ownership'):
        journal.import_packet(invalid, 'b' * 64)
    assert journal.storage_summary() == before


def test_basis_scope_and_source_are_never_silently_combined(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    original = history_packet(4)
    journal.import_packet(original, 'a' * 64)
    other = history_packet(4)
    other.source = 'other:source'
    for receipt in other.reports.values():
        for obs in receipt.observations:
            obs.source = other.source
            obs.consolidation = 'consolidated'
            if obs.statement == 'income' and obs.frequency == 'quarterly':
                obs.basis = 'ytd'
    journal.import_packet(other, 'b' * 64)
    assert len(journal.selected_statements('ABC', 'vnstock:VCI', frequency='quarterly')) == 12
    selected = journal.selected_statements('ABC', 'other:source', frequency='quarterly', scope='consolidated')
    assert len(selected) == 12
    assert {r['observation'].basis for r in selected if r['observation'].statement == 'income'} == {'ytd'}


def test_backup_rollback_and_readonly_guards(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    old = journal.import_packet(history_packet(), 'a' * 64)
    snapshot = tmp_path / 'snapshot.sqlite'
    journal.backup(snapshot)
    journal.import_packet(history_packet(4, start=2025 * 4 + 3), 'b' * 64)
    restored = tmp_path / 'restored.sqlite'
    MetricJournal(snapshot, readonly=True).backup(restored)
    recovery = MetricJournal(restored, readonly=True)
    assert recovery.storage_summary()['captures'] == 1
    assert recovery.read_packet(old['capture_id']) == journal.read_packet(old['capture_id'])
    with pytest.raises(FileExistsError):
        journal.backup(snapshot)
    with pytest.raises(ValueError, match='Read-only'):
        recovery.initialize()
    with pytest.raises(ValueError, match='Read-only'):
        recovery.import_packet(history_packet(), 'c' * 64)
    with pytest.raises(ValueError, match='Read-only'):
        recovery.select_revision(old['capture_id'], statement='income', period='2026-Q2')


def test_failed_upgrade_and_unknown_schemas_leave_legacy_bytes_intact(tmp_path):
    import sqlite3
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.append(normalized_metrics(balanced()))
    before = journal.path.read_bytes()
    occupied = tmp_path / 'occupied.sqlite'
    occupied.write_bytes(b'keep this backup')
    with pytest.raises(FileExistsError):
        journal.initialize(backup_path=occupied)
    assert journal.path.read_bytes() == before
    assert occupied.read_bytes() == b'keep this backup'
    foreign = tmp_path / 'application.sqlite'
    with sqlite3.connect(foreign) as db:
        db.execute('CREATE TABLE stock (id INTEGER)')
    before = foreign.read_bytes()
    with pytest.raises(ValueError, match='dedicated'):
        MetricJournal(foreign).initialize()
    assert foreign.read_bytes() == before
    future = tmp_path / 'future.sqlite'
    with sqlite3.connect(future) as db:
        db.execute('PRAGMA user_version=9')
    before = future.read_bytes()
    with pytest.raises(ValueError, match='unknown schema'):
        MetricJournal(future).initialize()
    assert future.read_bytes() == before


def test_private_api_contract_matches_mirrored_packet_without_switching_route(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from main import app
    from scripts.ingest_financial_intelligence import mirror_saved
    from src.services.personal_financials import personal_projection
    root = tmp_path / 'captures'
    packet = history_packet()
    packet.source_version = '4.0.2'
    digest = save_bundle(root, packet)
    target = tmp_path / 'financial.sqlite'
    result = mirror_saved(root, target)
    journal = MetricJournal(target, readonly=True)
    for name, value in dict(APP_ENV='development', WOOFI_PERSONAL_RESEARCH='1',
            WOOFI_PERSONAL_BIND='127.0.0.1', WOOFI_PERSONAL_CAPTURES=str(root)).items():
        monkeypatch.setenv(name, value)
    client = TestClient(app, client=('127.0.0.1', 1234), base_url='http://127.0.0.1')
    response = client.get('/personal-research/financials/ABC?frequency=quarterly&evidence=provider&limit=34')
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'private, no-store'
    expected = personal_projection(journal.read_packet(result['captures'][0]['capture_id']),
        frequency='quarterly', limit=34, authorization_reference='task:financial-v6-personal-research:' + digest)
    body = response.json()
    body.pop('read_at'); expected.pop('read_at')
    assert body == expected


def test_new_cli_rejects_public_database_and_missing_readonly_database(tmp_path):
    from scripts.ingest_financial_intelligence import main, compare_saved
    with pytest.raises(ValueError, match='private .local'):
        main(['--initialize', '--journal', str(tmp_path / 'public' / 'financial.sqlite')])
    assert not (tmp_path / 'public').exists()
    missing = tmp_path / 'missing.sqlite'
    import sqlite3
    with pytest.raises(sqlite3.OperationalError):
        compare_saved(tmp_path, missing)
    assert not missing.exists()


def test_imports_indexed_history_and_accepts_short_offline_candidates_without_editing_index(tmp_path):
    import json
    import hashlib
    from scripts.ingest_financial_intelligence import mirror_saved
    old = history_packet(); old.source_version = '4.0.2'
    current = history_packet(4, start=2025 * 4 + 3, marker=2); current.source_version = '4.0.2'
    root = tmp_path / 'captures'
    save_bundle(root, current)
    body = old.model_dump_json().encode('utf-8')
    (root / 'old.json').write_bytes(body)
    path = root / 'index.json'
    index = json.loads(path.read_text(encoding='utf-8'))
    index['capture_history'] = {'ABC': [{'file': 'old.json', 'sha256': hashlib.sha256(body).hexdigest(),
                                        'format': 'canonical-financial-packet-v1'}]}
    path.write_text(json.dumps(index), encoding='utf-8')
    before = path.read_bytes()
    target = tmp_path / 'financial.sqlite'
    first = mirror_saved(root, target)
    assert first['inserted_captures'] == 2
    journal = MetricJournal(target, readonly=True)
    assert len(journal.selected_statements('ABC', 'vnstock:VCI', frequency='quarterly')) == 105
    future = history_packet(4, start=2026 * 4, marker=3); future.source_version = '4.0.2'
    candidate = tmp_path / 'candidate.json'
    candidate.write_text(future.model_dump_json(), encoding='utf-8')
    appended = mirror_saved(root, target, packet_paths=[candidate])
    assert appended['inserted_captures'] == 1
    assert len(journal.selected_statements('ABC', 'vnstock:VCI', frequency='quarterly')) == 108
    assert path.read_bytes() == before
