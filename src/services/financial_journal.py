"""Explicit offline journal. Never uses the application's database or providers."""
from datetime import datetime, timezone
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from src.schemas.financial_intelligence import MetricObservation


def aware(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('An explicit timezone is required')
    return value.astimezone(timezone.utc)


class MetricJournal:
    def __init__(self, path, *, readonly=False):
        self.path = Path(path).resolve()
        self.readonly = readonly

    def connect(self):
        if self.readonly:
            return sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True)
        connection=sqlite3.connect(self.path)
        tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables-{'financial_metric'}:
            connection.close()
            raise ValueError('Use a dedicated financial journal, never an application database')
        return connection

    def append(self, observations):
        if self.readonly:
            raise ValueError('Read-only financial journal')
        with closing(self.connect()) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS financial_metric (identity TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            db.execute("CREATE INDEX IF NOT EXISTS financial_metric_period ON financial_metric (json_extract(payload,'$.period'),json_extract(payload,'$.period_type'))")
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
