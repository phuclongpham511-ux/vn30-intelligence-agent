"""Import curated notices with actual receipt times; optionally append event updates."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlmodel import Session, select
from src.db.session import create_tables, get_engine
from src.corporate_actions.curated import load_curated, ingest_curated
from src.corporate_actions.repository import CorporateActionRepository
from src.corporate_actions.history import TechnicalContextHistory
from src.corporate_actions.storage import TechnicalContextEvent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notices', type=Path)
    parser.add_argument('--append-updates', action='store_true', help='Append changed context to recorded Technical events')
    args = parser.parse_args()
    dataset = load_curated(args.notices)
    engine = get_engine()
    create_tables(engine)
    with Session(engine) as session:
        repository = CorporateActionRepository(session)
        counts = ingest_curated(repository, dataset)
        appended = 0
        if args.append_updates:
            history = TechnicalContextHistory(repository)
            for event in session.exec(select(TechnicalContextEvent)).all():
                # Stable records remain untouched; new evidence is a separate row.
                now = datetime.now(timezone.utc)
                prior = history.get(event.id, as_of=now)
                updated = history.append_update(event.id, enriched_at=now)
                appended += len(updated.updates) - len(prior.updates)
        print(json.dumps({'dataset_version': dataset.dataset_version, 'source_kind': dataset.source_kind,
            'coverage': 'INCOMPLETE', **counts, 'context_updates_appended': appended}, sort_keys=True))


if __name__ == '__main__':
    main()
