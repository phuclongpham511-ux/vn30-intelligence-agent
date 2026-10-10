"""Bounded public listing acquisition: python -m scripts.ingest_community [--watch]."""
import argparse
import json
import time
from src.db.session import create_tables, get_engine
from src.community.daily import ingest_cycle
from src.services.ingestion_owner import collector_owner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    engine = get_engine()
    with collector_owner(engine) as owned:
        if not owned:
            print(json.dumps({'status': 'collector_busy'}), flush=True)
            return 1
        return _run_owned(engine, args.watch)


def _run_owned(engine, watch):
    create_tables(engine)
    try:
        while True:
            result = ingest_cycle(engine)
            print(json.dumps(result), flush=True)
            if not watch:
                return int(any(row['status'] == 'error' for row in result.values()))
            time.sleep(60)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
