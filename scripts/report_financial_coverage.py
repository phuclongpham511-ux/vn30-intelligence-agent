"""Offline VN30/VN100 coverage inventory; does not acquire or mutate evidence."""
import argparse
import json
from pathlib import Path

from src.services.financial_coverage import build_coverage
from scripts.ingest_financial_intelligence import private_destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', required=True, help='Existing V5.5 dedicated SQLite journal')
    parser.add_argument('--as-of', required=True, help='ISO date for membership snapshot selection')
    parser.add_argument('--industry-snapshot', help='Saved SSI observed classification review JSON')
    parser.add_argument('--output', required=True, help='Private .local machine-readable JSON output')
    args = parser.parse_args(argv)
    journal = private_destination(args.journal)
    if not journal.is_file():
        parser.error('Existing private financial journal is required')
    output = private_destination(args.output)
    if output.suffix != '.json':
        parser.error('Output must be a private JSON file')
    observed = None
    if args.industry_snapshot:
        path = private_destination(args.industry_snapshot)
        observed = json.loads(path.read_text(encoding='utf-8'))
    report = build_coverage(journal, as_of=args.as_of, industry_snapshot=observed)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    summary = report['summary']
    print(json.dumps(dict(contract=report['contract'], output=str(output),
        membership=report['membership'], financial_tickers_covered=summary['financial_tickers_covered'],
        tickers_missing=len(summary['tickers_missing']), backlog_counts=summary['backlog_counts']), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
