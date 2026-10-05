"""Bounded public listing acquisition: python -m scripts.ingest_community [--watch]."""
import argparse
import json
import time
from sqlmodel import Session
from src.db.session import create_tables, get_engine
from src.community.service import ingest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    create_tables()
    try:
        while True:
            with Session(get_engine()) as session:
                result = ingest(session)
                print(json.dumps(result), flush=True)
            if not args.watch:
                return int(result['status'] == 'error')
            time.sleep(60)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
