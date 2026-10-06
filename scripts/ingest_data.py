"""Canonical single ingestion worker, separate from the HTTP process."""
import argparse
import json
import signal
from threading import Event
from sqlmodel import Session
from src.db.session import create_tables, get_engine
from src.news.registry import load_sources
from src.news.service import ingest_cycle
from src.community.daily import ingest_cycle as ingest_community
from src.services.universe import sync_universe


def run_cycle(engine, *, registry=None, force_news=False):
    results = {}
    # Separate sessions/transactions: a failed domain cannot poison the other.
    for domain in ('universe', 'news', 'community'):
        try:
            with Session(engine) as session:
                results[domain] = (sync_universe(session) if domain == 'universe' else
                    ingest_cycle(session, load_sources(registry), force=force_news)
                    if domain == 'news' else ingest_community(engine))
        except Exception as exc:
            results[domain] = {'status': 'error', 'error': type(exc).__name__}
    return results


def failed(results):
    return any(domain.get('status') == 'error' or any(
        isinstance(row, dict) and row.get('status') == 'error' for row in domain.values()
    ) for domain in results.values())


def run(engine, *, watch=False, registry=None, force_news=False, stop=None):
    stop = stop if stop is not None else Event()
    while not stop.is_set():
        result = run_cycle(engine, registry=registry, force_news=force_news)
        print(json.dumps({'event': 'ingestion_cycle', **result}), flush=True)
        if not watch:
            return int(failed(result))
        stop.wait(60)  # interruptible; persisted domain cadence decides due work
    return 0


def main():
    parser = argparse.ArgumentParser(description='SSI universe + News + Community metadata worker')
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--registry', help='Alternate News source registry JSON path')
    parser.add_argument('--force-news', action='store_true', help='One-off News cadence override; Community cadence remains intact')
    args = parser.parse_args()
    if args.watch and args.force_news:
        parser.error('--force-news cannot be combined with --watch')
    create_tables()
    stop = Event()
    previous = signal.signal(signal.SIGTERM, lambda *_: stop.set())
    try:
        return run(get_engine(), watch=args.watch, registry=args.registry,
            force_news=args.force_news, stop=stop)
    except KeyboardInterrupt:
        return 0
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == '__main__':
    raise SystemExit(main())
