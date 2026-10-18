"""Normalize saved market-only receipts offline. Does not import an API or DB."""
import argparse
import json
from pathlib import Path
from src.services.market_summary import normalize_provisional_market


def saved_packet(master_file, summary_file, now):
    master = json.loads(Path(master_file).read_text(encoding='utf-8'))
    summary = json.loads(Path(summary_file).read_text(encoding='utf-8'))
    receipt = lambda item: {'fetched_at': item['received_at'], 'document_sha256': item['evidence_sha256']}
    return normalize_provisional_market(master['record'], summary['record'], security=master['security']['record'],
        master_receipt=receipt(master), summary_receipt=receipt(summary),
        identity_receipt={'fetched_at': master['security']['received_at'], 'document_sha256': master['evidence_sha256']}, now=now)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--master', required=True)
    parser.add_argument('--summary', required=True)
    parser.add_argument('--as-of', required=True, help='Explicit evaluation clock; never a source timestamp')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    packet = saved_packet(args.master, args.summary, args.as_of)
    target = Path(args.output)
    if target.exists() or target.suffix.lower() != '.json':
        raise ValueError('Output must be a new JSON file; existing evidence is never overwritten')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as output:
        output.write(json.dumps(packet, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print('Saved PROVISIONAL_INTERNAL packet; no acquisition or public activation.')
