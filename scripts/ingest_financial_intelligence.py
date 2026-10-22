"""Offline, dynamic saved-capture ingestion into a dedicated revision journal.

python -m scripts.ingest_financial_intelligence --captures PRIVATE_INDEX_FOLDER
    --journal .local/financial-metrics.sqlite --report research/data

No credentials, live endpoint, application DB or public rights promotion.
"""
import argparse
from collections import Counter
import csv
import json
import hashlib
from pathlib import Path
from src.services.personal_financials import saved_packet, saved_capture_entry, personal_projection, validated_canonical_packet
from src.services.financial_intelligence import normalized_metrics
from src.services.financial_journal import MetricJournal
from src.providers.vnstock.financial_statements import NON_FINANCIAL_ONLY, BANK_ONLY


def saved_entries(captures, tickers=None):
    """Bounded manifest inventory; each loader still validates source bytes."""
    root = Path(captures).resolve(strict=True)
    path = root / 'index.json'
    if path.stat().st_size > 2_000_000:
        raise ValueError('Saved capture index exceeds bound')
    index = json.loads(path.read_text(encoding='utf-8'))
    if index.get('contract') != 'personal-saved-captures-v1' or not isinstance(index.get('captures'), dict):
        raise ValueError('Invalid saved capture index')
    selected = sorted(set(tickers) if tickers is not None else index['captures'])
    if not selected or len(selected) > 2000 or set(selected) - set(index['captures']):
        raise ValueError('Select existing saved issuers only')
    for ticker in selected:
        yield root, ticker, 'captures', index['captures'][ticker]
        if ticker in index.get('reviewed_reports', {}):
            yield root, ticker, 'reviewed_reports', index['reviewed_reports'][ticker]
        for entry in index.get('capture_history', {}).get(ticker, []):
            yield root, ticker, 'capture_history', entry


def packet_coverage(packet):
    observations = [o for r in packet.reports.values() for o in r.observations]
    return dict(ticker=packet.ticker, source=packet.source,
        annual_periods=len({o.period for o in observations if o.frequency == 'annual'}),
        quarterly_periods=len({o.period for o in observations if o.frequency == 'quarterly'}),
        statement_observations=len(observations),
        source_line_slots=sum(len(o.items) for o in observations),
        source_values=sum(line.value is not None for o in observations for line in o.items),
        periods={f: sorted({o.period for o in observations if o.frequency == f}) for f in ('annual', 'quarterly')})


def mirror_saved(captures, journal_path, *, tickers=None, packet_paths=()):
    """Explicit offline mirror; existing source files and production reads stay intact."""
    entries = list(saved_entries(captures, tickers))
    journal = MetricJournal(journal_path)
    migration = journal.initialize()
    results = []
    for root, ticker, collection, entry in entries:
        packet, digest = saved_capture_entry(root, ticker, entry)
        result = journal.import_packet(packet, digest, provenance=dict(
            directory=str(root), collection=collection, entry=entry))
        results.append({**packet_coverage(packet), **result, 'capture_sha256': digest, 'collection': collection})
    for path in packet_paths:
        path = Path(path).resolve(strict=True)
        if path.stat().st_size > 32_000_000:
            raise ValueError('Canonical packet exceeds bound')
        body = path.read_bytes()
        packet = validated_canonical_packet(body)
        digest = hashlib.sha256(body).hexdigest()
        result = journal.import_packet(packet, digest, provenance=dict(file=str(path), collection='offline_packet'))
        results.append({**packet_coverage(packet), **result, 'capture_sha256': digest, 'collection': 'offline_packet'})
    return dict(contract='financial-storage-v55', database=str(journal.path), migration=migration,
        provider_requests=0, tickers=sorted({r['ticker'] for r in results}), captures=results,
        inserted_captures=sum(r['inserted_captures'] for r in results),
        inserted_observations=sum(r['inserted_observations'] for r in results),
        storage=journal.storage_summary())


def compare_saved(captures, journal_path, *, tickers=None):
    """Read-only exact packet and existing projection parity; never activates reads."""
    from src.analytics.financial_engine import financial_engine
    from src.services.financial_presentation import display_financial_response
    journal = MetricJournal(journal_path, readonly=True)
    available = {(c['ticker'], c['source'], c['capture_sha256']): c for c in journal.captures()}
    results = []
    for root, ticker, collection, entry in saved_entries(captures, tickers):
        packet, digest = saved_capture_entry(root, ticker, entry)
        capture = available.get((ticker, packet.source, digest))
        if capture is None:
            raise ValueError(f'Mirrored financial capture unavailable: {ticker}/{collection}')
        stored = journal.read_packet(capture['capture_id'])
        equal = stored == packet
        projections = {}
        for frequency in ('annual', 'quarterly', 'ttm'):
            pairs = []
            for value in (packet, stored):
                public = display_financial_response(financial_engine(value, frequency=frequency, limit=40)).model_dump(mode='json')
                private = personal_projection(value, frequency=frequency, limit=40,
                    authorization_reference='task:v55-parity:' + digest)
                # Read time is volatile, not financial evidence. Nothing else is excluded.
                public.pop('read_at', None)
                private.pop('read_at', None)
                pairs.append((public, private))
            projections[frequency] = pairs[0] == pairs[1]
        results.append({**packet_coverage(packet), 'capture_sha256': digest,
            'capture_id': capture['capture_id'], 'collection': collection,
            'packet_parity': equal, 'projection_parity': projections,
            'parity': equal and all(projections.values())})
    return dict(contract='financial-storage-parity-v55', database=str(journal.path),
        readonly=True, provider_requests=0, compared_captures=len(results),
        parity=all(r['parity'] for r in results), captures=results)


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
    journal.initialize()
    for packet,digest in packets:
        ticker=packet.ticker
        journal.import_packet(packet, digest, provenance=dict(directory=str(root), collection='legacy_ingestion'))
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
            facts=normalized_metrics(packet,frequency=frequency,limit=40)
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
        period_limit_per_projection=40,source_statement_period_limit=None,coverage=coverage,
        limitations=['Raw coverage denominator is the captured sample only, not the listed market.',
            'All source statement periods are retained; metric projections use the engine maximum of 40 periods.',
            'Unknown scope and publication metadata remain unknown; no public permissions are added.'])
    (destination/'INGESTION_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def private_destination(path):
    """New storage commands are restricted to this worktree's ignored private root."""
    path = Path(path).resolve()
    private = Path(__file__).resolve().parents[1] / '.local'
    if (not path.is_relative_to(private) or path == private
            or any(part.casefold() in {'public', 'static', 'dist'} for part in path.parts)):
        raise ValueError('Use a path inside this worktree private .local directory')
    return path


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures',type=Path)
    parser.add_argument('--journal',required=True,type=Path)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--packet',action='append',default=[],type=Path,
        help='Additional canonical capture from the existing audited adapter; no rights promotion')
    parser.add_argument('--tickers', nargs='+', help='Existing saved issuers for mirror/comparison')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--mirror', action='store_true', help='Mirror all source periods, reviewed reports and indexed history')
    mode.add_argument('--compare', action='store_true', help='Read-only saved/SQLite packet and projection parity')
    mode.add_argument('--initialize', action='store_true', help='Explicit private schema initialization/upgrade with backup')
    mode.add_argument('--backup', type=Path, help='Snapshot/restore into a new private SQLite path')
    args=parser.parse_args(argv)
    if args.mirror or args.compare or args.initialize or args.backup:
        target = private_destination(args.journal)
        if target.suffix not in ('.sqlite', '.db'):
            parser.error('Use a .sqlite or .db financial journal')
        if args.initialize or args.mirror:
            target.parent.mkdir(parents=True, exist_ok=True)
        if args.initialize:
            result = MetricJournal(target).initialize()
        elif args.backup:
            destination = private_destination(args.backup)
            destination.parent.mkdir(parents=True, exist_ok=True)
            result = dict(backup=MetricJournal(target, readonly=True).backup(destination))
        else:
            if args.captures is None or args.report is None:
                parser.error('--captures and --report are required for mirror/comparison')
            destination = private_destination(args.report)
            if args.compare and args.packet:
                parser.error('--compare validates indexed captures; --packet is for --mirror')
            result = (compare_saved(args.captures, target, tickers=args.tickers) if args.compare else
                      mirror_saved(args.captures, target, tickers=args.tickers, packet_paths=args.packet))
            destination.mkdir(parents=True, exist_ok=True)
            name = 'PARITY_REPORT.json' if args.compare else 'MIRROR_REPORT.json'
            (destination / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    else:
        if args.captures is None or args.report is None:
            parser.error('--captures and --report are required')
        if args.tickers:
            parser.error('--tickers requires --mirror or --compare')
        result=ingest(args.captures,args.journal,args.report,args.packet)
    print(json.dumps({key: value for key, value in result.items() if key not in ('captures', 'coverage')}, ensure_ascii=False))
    return 1 if result.get('parity') is False else 0


if __name__=='__main__':
    raise SystemExit(main())
