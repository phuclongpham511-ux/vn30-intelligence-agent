"""Run a reviewed 3-5 issuer V5.6 P0 acquisition plan against existing private SQLite."""
import argparse
import json

from scripts.ingest_financial_intelligence import private_destination
from src.providers.vnstock import sdk
from src.providers.vnstock.financial_packet import fetch_packet
from src.services.financial_collector import _read_json, run_collector


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--backlog', required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--journal', required=True)
    parser.add_argument('--industry-snapshot')
    parser.add_argument('--pause-seconds', type=float, default=6)
    parser.add_argument('--refresh-documents', action='store_true',
        help='Fetch new document revisions; retain every previous binary and packet')
    parser.add_argument('--refresh-sdk', action='store_true', help='Explicitly refresh bounded SDK candidates')
    args = parser.parse_args(argv)
    if args.pause_seconds < 6:
        parser.error('SDK request pacing must be at least six seconds')
    plan, backlog = (_read_json(private_destination(p)) for p in (args.plan, args.backlog))
    industry = _read_json(private_destination(args.industry_snapshot)) if args.industry_snapshot else None
    result = run_collector(plan, backlog, root=private_destination(args.root),
        journal_path=private_destination(args.journal), industry_snapshot=industry,
        fetch_packet=lambda ticker: fetch_packet(ticker, sdk, request_pause_seconds=args.pause_seconds),
        refresh_documents=args.refresh_documents, refresh_sdk=args.refresh_sdk)
    print(json.dumps(dict(run_id=result['run_id'], tickers=result['tickers'],
        status_counts=result['status_counts'], results=result['results'],
        resolved_initial_p0_tasks=result['coverage']['resolved_initial_p0_tasks']), indent=2, ensure_ascii=False))
    return int(any(r['status'] in ('FAILED', 'EXTRACTION_FAILURE', 'SOURCE_UNAVAILABLE') for r in result['results']))


if __name__ == '__main__':
    raise SystemExit(main())
