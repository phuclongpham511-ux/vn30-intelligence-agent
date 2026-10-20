"""Offline, dynamic saved-capture ingestion into a dedicated revision journal.

python -m scripts.ingest_financial_intelligence --captures PRIVATE_INDEX_FOLDER
    --journal .local/financial-metrics.sqlite --report research/data

No credentials, live endpoint, application DB or public rights promotion.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from src.services.personal_financials import saved_packet
from src.services.financial_intelligence import normalized_metrics
from src.services.financial_journal import MetricJournal
from src.providers.vnstock.financial_statements import NON_FINANCIAL_ONLY, BANK_ONLY


def ingest(captures, journal_path, report_path, packet_paths=()):
    root=Path(captures).resolve(strict=True)
    index=json.loads((root/'index.json').read_text(encoding='utf-8'))
    if index.get('contract')!='personal-saved-captures-v1' or not isinstance(index.get('captures'),dict) or len(index['captures'])>2000:
        raise ValueError('Invalid saved capture index')
    target=Path(journal_path).resolve()
    if 'public' in target.parts or target.suffix not in ('.sqlite','.db'):
        raise ValueError('Use a private dedicated SQLite journal')
    target.parent.mkdir(parents=True,exist_ok=True)
    journal=MetricJournal(target)
    rows=[];coverage=[];total_inserted=0
    packets=[saved_packet(root,ticker) for ticker in sorted(index['captures'])]
    import hashlib
    from src.schemas.financials import FinancialPacket
    for path in packet_paths:
        if Path(path).stat().st_size>32_000_000:
            raise ValueError('Canonical packet exceeds bound')
        data=Path(path).read_bytes()
        packets.append((FinancialPacket.model_validate_json(data),hashlib.sha256(data).hexdigest()))
    tickers=[packet.ticker for packet,_ in packets]
    if len(tickers)!=len(set(tickers)):
        raise ValueError('Import each issuer once per ingestion run')
    for packet,digest in packets:
        ticker=packet.ticker
        for kind,receipt in packet.reports.items():
            for frequency in ('annual','quarterly'):
                observations=[o for o in receipt.observations if o.frequency==frequency]
                for field in sorted({f for o in observations for f in o.fields}):
                    present=sum(o.fields.get(field) is not None for o in observations)
                    rows.append(dict(ticker=ticker,company_type=packet.company_type,statement=kind,frequency=frequency,
                        metric_id=field,expected_periods=len(observations),observed_periods=present,
                        coverage=present/len(observations) if observations and not (field in NON_FINANCIAL_ONLY and packet.profile!='non_financial' or field in BANK_ONLY and packet.profile!='bank') else None,source=packet.source,
                        applicability='not_applicable' if field in NON_FINANCIAL_ONLY and packet.profile!='non_financial' or field in BANK_ONLY and packet.profile!='bank' else 'applicable_or_common',
                        capture_sha256=digest,periods=';'.join(o.period for o in observations),
                        known_scope=sum(o.consolidation in ('consolidated','standalone') for o in observations),
                        known_original_unit=sum(o.source_context.original_unit is not None for o in observations)))
        for frequency in ('annual','quarterly','ttm'):
            facts=normalized_metrics(packet,frequency=frequency,limit=20)
            total_inserted+=journal.append(facts)
            coverage.append(dict(ticker=ticker,profile=packet.profile,frequency=frequency,
                periods=len({m.period for m in facts}),observations=len(facts),
                status_counts=dict(Counter(m.quality_status for m in facts)),capture_sha256=digest))
    destination=Path(report_path);destination.mkdir(parents=True,exist_ok=True)
    if rows:
        with (destination/'DATA_COVERAGE_MATRIX.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with journal.connect() as connection:
        stored_revisions=connection.execute('SELECT count(*) FROM financial_metric').fetchone()[0]
    report=dict(stored_revisions=stored_revisions,contract='financial-intelligence-ingestion-v1',provider_requests=0,database_scope='dedicated offline journal',
        tickers=sorted(tickers),inserted_revisions=total_inserted,
        period_limit_per_projection=20,coverage=coverage,
        limitations=['Raw coverage denominator is the captured sample only, not the listed market.',
            'Journal retains the most recent 20 periods per frequency per imported capture.',
            'Unknown scope and publication metadata remain unknown; no public permissions are added.'])
    (destination/'INGESTION_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures',required=True,type=Path)
    parser.add_argument('--journal',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--packet',action='append',default=[],type=Path,
        help='Additional canonical capture from the existing audited adapter; no rights promotion')
    args=parser.parse_args()
    result=ingest(args.captures,args.journal,args.report,args.packet)
    print(json.dumps({key:result[key] for key in ('tickers','inserted_revisions','provider_requests')}))
