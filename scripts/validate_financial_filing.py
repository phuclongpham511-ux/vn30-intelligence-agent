"""One offline reviewed filing -> canonical packet -> engine -> scoped display.

Usage: python -m scripts.validate_financial_filing MANIFEST EXTRACTION NEW_OUTPUT
       [--saved-vci SAVED_CAPTURE]
No acquisition, SQLite, worker, or runtime configuration. Never overwrites output.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from src.providers.financial_filings import filing_packet, reconcile_filing
from src.providers.vnstock.financial_packet import metadata_rows, packet_from_payloads
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response


def validate(manifest, extraction, output, saved_vci=None):
    if output.exists():
        raise ValueError('Evidence output already exists')
    evidence = json.loads(manifest.read_text(encoding='utf-8'))
    packet, audit = filing_packet(evidence, extraction.read_text(encoding='utf-8'))
    full = financial_engine(packet)
    public = display_financial_response(full)
    internal = display_financial_response(full,
        internal_authorization_reference=evidence['review_reference'])
    if any(m.value is not None for m in public.fundamental_summary.metrics):
        raise ValueError('Unreviewed filing rights must not enable public values')
    report = dict(source=packet.source, ticker=packet.ticker, audit=audit,
        evidence_kind='REAL_OFFICIAL_FILING_SAVED_PAGE_TEXT_NOT_LIVE',
        provider_requests=0, database_access=False, public_activation=False,
        internal_qualified=[dict(key=m.key, value=m.value, unit=m.unit)
            for m in internal.fundamental_summary.metrics if m.status == 'QUALIFIED'],
        rights=dict(internal_research='TASK_AUTHORIZED_NOT_PROVIDER_LICENSE',
            local_development='OFFLINE_SCOPED_REVIEW_ONLY',
            public_display='UNREVIEWED_DISABLED', commercial_redistribution='UNREVIEWED_DISABLED'))
    if saved_vci:
        raw = json.loads(saved_vci.read_text(encoding='utf-8'))
        if raw['ticker'] != packet.ticker or raw['source'] != 'vnstock:VCI':
            raise ValueError('Wrong comparison capture')
        names = {'income':'income_statement', 'balance':'balance_sheet', 'cash':'cash_flow'}
        reads = {kind:raw[name]['reads'][0] for kind, name in names.items()}
        comparison = packet_from_payloads(raw['ticker'], raw['source'], raw['company_type'],
            metadata_rows(raw['metadata']['reads'][0]['data']),
            {kind:r['data'] for kind,r in reads.items()}, source_version=raw['sdk_version'],
            observed_at={kind:datetime.fromisoformat(r['observed_at']) for kind,r in reads.items()},
            urls={kind:r['url'] for kind,r in reads.items()})
        report['comparison'] = reconcile_filing(packet, comparison)
    output.mkdir(parents=True)
    for name, model in [('canonical-packet',packet), ('internal-display',internal), ('public-display',public)]:
        (output/f'{name}.json').write_text(model.model_dump_json(indent=2),encoding='utf-8')
    (output/'RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('manifest',type=Path)
    cli.add_argument('extraction',type=Path)
    cli.add_argument('output',type=Path)
    cli.add_argument('--saved-vci',type=Path)
    args = cli.parse_args()
    result = validate(args.manifest,args.extraction,args.output,args.saved_vci)
    print(json.dumps(result,ensure_ascii=False,indent=2))
