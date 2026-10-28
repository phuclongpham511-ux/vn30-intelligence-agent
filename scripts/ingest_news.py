"""Manual ingestion, optional scheduler, and non-persisting live smoke check.

uv run python -m scripts.ingest_news
uv run python -m scripts.ingest_news --watch
uv run python -m scripts.ingest_news --smoke
"""
import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from src.db.session import create_tables, get_engine
from src.news.adapters import acquire
from src.news.registry import load_sources
from src.news.normalization import utc
from src.news.service import ingest_cycle
from src.services.ingestion_owner import collector_owner


def main():
    parser = argparse.ArgumentParser(description='Public-feed metadata ingestion')
    parser.add_argument('--registry', help='Alternate source registry JSON path')
    parser.add_argument('--watch', action='store_true', help='Single scheduler process; per-source cadence is respected')
    parser.add_argument('--force', action='store_true', help='Ignore cadence for a one-off refresh')
    parser.add_argument('--smoke', action='store_true', help='Fetch/parse feeds without writing to the database')
    args = parser.parse_args()
    if args.force and args.watch:
        parser.error('--force cannot be combined with --watch')
    engine = get_engine()
    with collector_owner(engine) as owned:
        if not owned:
            print(json.dumps({'status': 'collector_busy'}), flush=True)
            return 1
        return _run_owned(args, engine)


def _run_owned(args, engine):
    if args.smoke:
        failed = False
        for source in load_sources(args.registry):
            if not source.enabled:
                continue
            try:
                items = acquire(source)
                checked_at = datetime.now(timezone.utc)
                fresh = sum(a.published_at is not None and checked_at - timedelta(hours=72) <= utc(a.published_at) <= checked_at + timedelta(minutes=10) for a in items)
                if not items or not fresh:
                    raise ValueError('Empty or stale feed')
                print(json.dumps({'source': source.source_id, 'status': 'ok', 'received': len(items),
                    'dated': sum(a.published_at is not None for a in items), 'recent_72h': fresh,
                    'checked_at': datetime.now(timezone.utc).isoformat()}))
            except Exception as exc:
                failed = True
                print(json.dumps({'source': source.source_id, 'status': 'error', 'error': type(exc).__name__}))
        return 1 if failed else 0
    create_tables(engine)
    try:
        while True:
            with Session(engine) as session:
                result = ingest_cycle(session, load_sources(args.registry), force=args.force)
                print(json.dumps(result), flush=True)
            if not args.watch:
                return int(any(x['status'] == 'error' for x in result.values()))
            time.sleep(60)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
