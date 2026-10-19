"""Replay saved VCI captures through the real normalizer, engine and display API.

No transport, credentials, SQLite or acquisition. Output must be a new directory.
Run: python -m scripts.validate_financial_foundation_v2 SAVED_CAPTURE_DIR NEW_OUTPUT
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from src.analytics.financial_engine import financial_engine
from src.providers.vnstock.financial_packet import metadata_rows, packet_from_payloads
from src.providers.vnstock.financial_statements import content_hash
from src.services.financial_presentation import display_financial_response


def validate(captures: Path, destination: Path):
    if destination.exists():
        raise ValueError('Evidence output must not overwrite an existing directory')
    # Read all inputs before creating output; never use production database data.
    inputs = []
    for ticker in ('FPT', 'PNJ', 'VCB'):
        path = captures / f'{ticker}.json'
        raw_bytes = path.read_bytes()
        saved = json.loads(raw_bytes)
        if saved.get('ticker') != ticker or saved.get('source') != 'vnstock:VCI':
            raise ValueError('Wrong saved capture owner/source')
        inputs.append((ticker, saved, hashlib.sha256(raw_bytes).hexdigest()))
    destination.mkdir(parents=True)
    results = []
    for ticker, saved, capture_hash in inputs:
        names = {'income': 'income_statement', 'balance': 'balance_sheet', 'cash': 'cash_flow'}
        reads = {kind: saved[name]['reads'][0] for kind, name in names.items()}
        packet = packet_from_payloads(ticker, saved['source'], saved['company_type'],
            metadata_rows(saved['metadata']['reads'][0]['data']), {kind: read['data'] for kind, read in reads.items()},
            source_version=saved['sdk_version'],
            observed_at={kind: datetime.fromisoformat(read['observed_at']) for kind, read in reads.items()},
            urls={kind: read['url'] + '?section=' + read['params']['section'] for kind, read in reads.items()})
        for kind, receipt in packet.reports.items():
            if receipt.status != 'healthy' or receipt.content_sha256 != content_hash(reads[kind]['data']):
                raise ValueError('Saved normalization or receipt hash failed')
            source_rows = reads[kind]['data']['years'] + reads[kind]['data']['quarters']
            if sorted(o.source_context.record_sha256 for o in receipt.observations) != sorted(content_hash(row) for row in source_rows):
                raise ValueError('Record provenance mismatch')
        for frequency in ('annual', 'quarterly', 'ttm'):
            result = financial_engine(packet, frequency=frequency)
            view = display_financial_response(result)
            counts = {status: sum(m.status == status for m in view.fundamental_summary.metrics)
                      for status in ('QUALIFIED', 'UNQUALIFIED', 'UNAVAILABLE', 'DEMO')}
            if counts['QUALIFIED'] or counts['DEMO'] or packet.is_fixture:
                raise ValueError('Saved unknown-basis evidence must not acquire live qualification')
            filename = f'{ticker}-{frequency}-display.json'
            (destination / filename).write_text(view.model_dump_json(indent=2), encoding='utf-8')
            results.append(dict(ticker=ticker, frequency=frequency, profile=packet.profile,
                capture_sha256=capture_hash, latest_period=view.fundamental_summary.period,
                status_counts=counts, consolidation='UNKNOWN', display_rights='unreviewed',
                source_version=packet.source_version, output=filename,
                receipts={kind: dict(content_sha256=r.content_sha256,
                    observed_at=r.observed_at.isoformat(), records=len(r.observations), source_url=r.source_url)
                    for kind, r in packet.reports.items()}))
    report = dict(evidence_kind='REPLAY_OF_SAVED_REAL_VCI_CAPTURES_NOT_LIVE',
        provider_requests=0, database_access=False, public_activation=False, results=results)
    (destination / 'qualification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = validate(args.captures, args.output)
    print(json.dumps(dict(replayed=len(report['results']), provider_requests=0,
                         qualified=sum(r['status_counts']['QUALIFIED'] for r in report['results']))))
