"""Bounded public listing acquisition: python -m scripts.ingest_community [--watch]."""
import argparse
import json
import time
from src.db.session import create_tables, get_engine
from src.community.daily import ingest_cycle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    create_tables()
    try:
        while True:
            result = ingest_cycle(get_engine())
            print(json.dumps(result), flush=True)
            if not args.watch:
                return int(any(row['status'] == 'error' for row in result.values()))
            time.sleep(60)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
