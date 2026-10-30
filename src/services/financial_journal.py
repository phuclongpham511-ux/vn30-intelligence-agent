"""Explicit offline journal. Never uses the application's database or providers."""
from datetime import datetime, timezone
from contextlib import closing
import json
import hashlib
from pathlib import Path
import re
import sqlite3
from src.schemas.financial_intelligence import MetricObservation
from src.schemas.financials import FinancialPacket, StatementObservation

SCHEMA_VERSION = 1
STORAGE_COLUMNS = {
    'financial_metric': {'identity', 'payload'},
    'financial_capture': {'id', 'ticker', 'source', 'capture_sha256', 'packet_sha256', 'header', 'provenance'},
    'financial_statement': {'capture_id', 'statement', 'period', 'frequency', 'scope', 'basis', 'position', 'payload'},
    'financial_selection': {'ticker', 'source', 'statement', 'period', 'frequency', 'scope', 'basis', 'capture_id'},
}


def _validate_schema(connection):
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    version = connection.execute('PRAGMA user_version').fetchone()[0]
    expected = set(STORAGE_COLUMNS) if version == SCHEMA_VERSION else {'financial_metric'}
    if version not in (0, SCHEMA_VERSION) or tables - expected or (version == SCHEMA_VERSION and tables != expected):
        raise ValueError('Use a dedicated financial journal, never an application database or unknown schema')
    for table in tables:
        columns = {r[1] for r in connection.execute(f'PRAGMA table_info({table})')}
        if columns != STORAGE_COLUMNS[table]:
            raise ValueError('Unrecognized financial journal schema')
    return version, tables


def _metric_schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS financial_metric (identity TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    db.execute("CREATE INDEX IF NOT EXISTS financial_metric_period ON financial_metric (json_extract(payload,'$.period'),json_extract(payload,'$.period_type'))")


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def _digest(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def _validated_packet(packet):
    packet = FinancialPacket.model_validate(packet.model_dump(mode='python'), strict=True)
    if not re.fullmatch(r'[A-Z0-9]{1,20}', packet.ticker) or not packet.source or set(packet.reports) != {'income', 'balance', 'cash'}:
        raise ValueError('Invalid financial packet identity or statements')
    for kind, receipt in packet.reports.items():
        if receipt.statement != kind:
            raise ValueError('Wrong financial receipt ownership')
        aware(receipt.observed_at)
        periods = set()
        for obs in receipt.observations:
            if (obs.ticker != packet.ticker or obs.source != packet.source or obs.statement != kind
                    or obs.period in periods or obs.frequency != ('quarterly' if '-Q' in obs.period else 'annual')
                    or len({line.code for line in obs.items}) != len(obs.items)):
                raise ValueError('Invalid financial period ownership or duplicate source lines')
            periods.add(obs.period)
    return packet


def aware(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('An explicit timezone is required')
    return value.astimezone(timezone.utc)


class MetricJournal:
    def __init__(self, path, *, readonly=False):
        self.path = Path(path).resolve()
        self.readonly = readonly

    def connect(self):
        connection = (sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True) if self.readonly
                      else sqlite3.connect(self.path))
        try:
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=5000')
            if self.readonly:
                connection.execute('PRAGMA query_only=ON')
            _validate_schema(connection)
        except Exception:
            connection.close()
            raise
        return connection

    def backup(self, destination):
        """Consistent, exclusive snapshot; also supports restoring to a NEW path."""
        target = Path(destination).resolve()
        if target == self.path:
            raise ValueError('Backup must use a different path')
        with closing(MetricJournal(self.path, readonly=True).connect()) as source:
            with target.open('xb'):
                pass
            try:
                with closing(sqlite3.connect(target)) as saved:
                    source.backup(saved)
                    if saved.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise ValueError('Backup integrity check failed')
            except Exception:
                target.unlink()
                raise
        return str(target)

    def initialize(self, *, backup_path=None):
        """Explicit additive migration; legacy metrics stay byte-for-byte intact."""
        if self.readonly:
            raise ValueError('Read-only financial journal')
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            version, tables = _validate_schema(db)
            if version == SCHEMA_VERSION:
                return dict(schema_version=version, migrated=False, backup=None)
            backup = self.backup(backup_path or self.path.with_suffix('.pre-v55.sqlite')) if tables else None
            _metric_schema(db)
            db.execute('''CREATE TABLE financial_capture (
                id TEXT PRIMARY KEY, ticker TEXT NOT NULL, source TEXT NOT NULL,
                capture_sha256 TEXT NOT NULL, packet_sha256 TEXT NOT NULL,
                header TEXT NOT NULL, provenance TEXT NOT NULL,
                UNIQUE(ticker, source, capture_sha256))''')
            db.execute('CREATE INDEX financial_capture_issuer ON financial_capture(ticker, source)')
            db.execute('''CREATE TABLE financial_statement (
                capture_id TEXT NOT NULL REFERENCES financial_capture(id),
                statement TEXT NOT NULL, period TEXT NOT NULL, frequency TEXT NOT NULL,
                scope TEXT NOT NULL, basis TEXT NOT NULL, position INTEGER NOT NULL,
                payload TEXT NOT NULL, PRIMARY KEY(capture_id, statement, period),
                UNIQUE(capture_id, statement, position))''')
            db.execute('CREATE INDEX financial_statement_period ON financial_statement(period, frequency, statement)')
            db.execute('''CREATE TABLE financial_selection (
                ticker TEXT NOT NULL, source TEXT NOT NULL, statement TEXT NOT NULL,
                period TEXT NOT NULL, frequency TEXT NOT NULL, scope TEXT NOT NULL,
                basis TEXT NOT NULL, capture_id TEXT NOT NULL,
                PRIMARY KEY(ticker, source, statement, period, frequency, scope, basis),
                FOREIGN KEY(capture_id, statement, period)
                    REFERENCES financial_statement(capture_id, statement, period))''')
            db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
        return dict(schema_version=SCHEMA_VERSION, migrated=True, backup=backup)

    def storage_summary(self):
        with closing(self.connect()) as db:
            version, _ = _validate_schema(db)
            return dict(schema_version=version,
                captures=db.execute('SELECT count(*) FROM financial_capture').fetchone()[0],
                statement_observations=db.execute('SELECT count(*) FROM financial_statement').fetchone()[0],
                selected_observations=db.execute('SELECT count(*) FROM financial_selection').fetchone()[0],
                metric_revisions=db.execute('SELECT count(*) FROM financial_metric').fetchone()[0])

    def import_packet(self, packet, capture_sha256, *, provenance=None):
        """Append a whole immutable revision; first accepted periods stay selected.

        This persists source observations without any engine or presentation limit.
        Overlapping revisions remain inspectable and require explicit selection.
        """
        if self.readonly:
            raise ValueError('Read-only financial journal')
        if not re.fullmatch(r'[a-f0-9]{64}', capture_sha256):
            raise ValueError('A source capture SHA-256 is required')
        packet = _validated_packet(packet)
        payload = packet.model_dump(mode='json')
        packet_sha256 = _digest(payload)
        capture_id = _digest([packet.ticker, packet.source, capture_sha256])
        header = packet.model_dump(mode='json')
        for receipt in header['reports'].values():
            receipt['observations'] = []
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            if _validate_schema(db)[0] != SCHEMA_VERSION:
                raise ValueError('Initialize financial storage explicitly before importing packets')
            previous = db.execute('SELECT packet_sha256 FROM financial_capture WHERE id=?', (capture_id,)).fetchone()
            if previous:
                if previous[0] != packet_sha256:
                    raise ValueError('Conflicting packet for an existing source capture revision')
                return dict(capture_id=capture_id, inserted_captures=0, inserted_observations=0, selected_observations=0)
            db.execute('INSERT INTO financial_capture VALUES (?,?,?,?,?,?,?)',
                (capture_id, packet.ticker, packet.source, capture_sha256, packet_sha256,
                 json.dumps(header, ensure_ascii=False, allow_nan=False), _json(provenance or {})))
            inserted = selected = 0
            for kind, receipt in packet.reports.items():
                for position, obs in enumerate(receipt.observations):
                    scope = obs.consolidation or 'unknown'
                    db.execute('INSERT INTO financial_statement VALUES (?,?,?,?,?,?,?,?)',
                        (capture_id, kind, obs.period, obs.frequency, scope, obs.basis, position,
                         _json(obs.model_dump(mode='json'))))
                    inserted += 1
                    selected += db.execute('''INSERT OR IGNORE INTO financial_selection
                        VALUES (?,?,?,?,?,?,?,?)''',
                        (packet.ticker, packet.source, kind, obs.period, obs.frequency, scope, obs.basis, capture_id)).rowcount
        return dict(capture_id=capture_id, inserted_captures=1, inserted_observations=inserted, selected_observations=selected)

    def captures(self, *, ticker=None, source=None):
        conditions, parameters = [], []
        for field, value in (('ticker', ticker), ('source', source)):
            if value is not None:
                conditions.append(field + '=?')
                parameters.append(value)
        query = 'SELECT id,ticker,source,capture_sha256,packet_sha256,provenance FROM financial_capture'
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        with closing(self.connect()) as db:
            rows = db.execute(query + ' ORDER BY ticker,source,id', parameters).fetchall()
        return [dict(capture_id=r[0], ticker=r[1], source=r[2], capture_sha256=r[3],
                     packet_sha256=r[4], provenance=json.loads(r[5])) for r in rows]

    def read_packet(self, capture_id):
        """Exact packet revision, not a synthetic mix of receipt vintages."""
        with closing(self.connect()) as db:
            row = db.execute('SELECT header,packet_sha256 FROM financial_capture WHERE id=?', (capture_id,)).fetchone()
            if row is None:
                raise FileNotFoundError('Financial capture unavailable')
            payload = json.loads(row[0])
            for kind, observation in db.execute('''SELECT statement,payload FROM financial_statement
                    WHERE capture_id=? ORDER BY statement,position''', (capture_id,)):
                payload['reports'][kind]['observations'].append(json.loads(observation))
        if _digest(payload) != row[1]:
            raise ValueError('Stored financial packet digest mismatch')
        return _validated_packet(FinancialPacket.model_validate_json(
            json.dumps(payload, ensure_ascii=False, allow_nan=False), strict=True))

    def selected_statements(self, ticker, source, *, frequency=None, scope=None):
        """Accumulated periods with individual receipt lineage, never a mixed packet.

        Different bases/scopes stay separate rows. This is storage inspection,
        not a claim that those rows form a comparable series or a PIT snapshot.
        """
        conditions = ['s.ticker=?', 's.source=?']
        parameters = [ticker, source]
        for field, value in (('frequency', frequency), ('scope', scope)):
            if value is not None:
                conditions.append('s.' + field + '=?')
                parameters.append(value)
        query = '''SELECT s.capture_id,o.payload,c.header,c.capture_sha256
            FROM financial_selection s
            JOIN financial_statement o ON o.capture_id=s.capture_id AND o.statement=s.statement AND o.period=s.period
            JOIN financial_capture c ON c.id=s.capture_id WHERE ''' + ' AND '.join(conditions)
        with closing(self.connect()) as db:
            rows = db.execute(query + ' ORDER BY s.statement,s.period,s.scope,s.basis', parameters).fetchall()
        result = []
        for capture_id, payload, header, digest in rows:
            observation = StatementObservation.model_validate_json(payload, strict=True)
            result.append(dict(capture_id=capture_id, capture_sha256=digest, observation=observation,
                receipt=json.loads(header)['reports'][observation.statement]))
        return result

    def select_revision(self, capture_id, *, statement, period):
        """Explicit operator selection; immutable revisions remain retrievable."""
        if self.readonly:
            raise ValueError('Read-only financial journal')
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('''SELECT c.ticker,c.source,o.frequency,o.scope,o.basis
                FROM financial_statement o JOIN financial_capture c ON c.id=o.capture_id
                WHERE o.capture_id=? AND o.statement=? AND o.period=?''',
                (capture_id, statement, period)).fetchone()
            if row is None:
                raise FileNotFoundError('Financial period revision unavailable')
            db.execute('''UPDATE financial_selection SET capture_id=? WHERE
                ticker=? AND source=? AND statement=? AND period=? AND frequency=? AND scope=? AND basis=?''',
                (capture_id, row[0], row[1], statement, period, row[2], row[3], row[4]))

    def append(self, observations):
        if self.readonly:
            raise ValueError('Read-only financial journal')
        with closing(self.connect()) as db, db:
            _metric_schema(db)
            inserted = 0
            for observation in observations:
                item = MetricObservation.model_validate(observation.model_dump())
                identity = json.dumps([item.ticker,item.metric_id,item.period,item.period_type,
                    item.report_scope,item.source,item.formula_version,item.revision],separators=(',',':'))
                payload = item.model_dump_json()
                previous = db.execute('SELECT payload FROM financial_metric WHERE identity=?',(identity,)).fetchone()
                if previous:
                    # Refetching an identical revision preserves its earliest capture.
                    before = MetricObservation.model_validate_json(previous[0])
                    if before.model_dump(exclude={'fetched_at'}) != item.model_dump(exclude={'fetched_at'}):
                        raise ValueError('Conflicting value for an existing financial revision')
                    if item.fetched_at < before.fetched_at:
                        raise ValueError('Cannot backdate an existing revision')
                    continue
                db.execute('INSERT INTO financial_metric VALUES (?,?)',(identity,payload))
                inserted += 1
            return inserted

    def read(self, *, as_of:datetime|None=None, period=None, frequency=None):
        cutoff = aware(as_of) if as_of else None
        with closing(self.connect()) as db:
            conditions=[];parameters=[]
            if period is not None:
                conditions.append("json_extract(payload,'$.period')=?");parameters.append(period)
            if frequency is not None:
                conditions.append("json_extract(payload,'$.period_type')=?");parameters.append(frequency)
            query='SELECT payload FROM financial_metric'+(' WHERE '+' AND '.join(conditions) if conditions else '')
            payloads = db.execute(query,parameters).fetchall()
        grouped = {}
        for payload, in payloads:
            item = MetricObservation.model_validate_json(payload)
            if cutoff and (item.published_at is None or aware(item.published_at)>cutoff or aware(item.fetched_at)>cutoff):
                continue
            key = (item.ticker,item.metric_id,item.period,item.period_type,item.report_scope,item.source,item.formula_version)
            current = grouped.get(key)
            if current is None or item.fetched_at > current.fetched_at:
                grouped[key] = item
            elif item.fetched_at == current.fetched_at and item.revision != current.revision:
                # Neither ordering nor row ID is evidence of which version wins.
                grouped[key] = current.model_copy(update={'value':None,'quality_status':'CONFLICT',
                    'metric_kind':'unavailable','quality_reasons':['ambiguous_revision_vintage']})
        return sorted(grouped.values(),key=lambda m:(m.ticker,m.period,m.metric_id,m.source,m.report_scope))
