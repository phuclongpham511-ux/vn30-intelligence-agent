"""Explicit pilot bootstrap, no-write dry run, or one bounded supervised cycle."""
import argparse
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json
from pathlib import Path
import signal
from threading import Event
from sqlmodel import Session,create_engine

from src.config.settings import Settings
from src.db.session import create_tables
from src.models import Security
from src.providers.ssi import SsiMarketDataProvider
from src.schemas.stocks import SymbolRequest
from src.services.hose_eod_discovery import seed_calendar,publication_anchor,OfficialHoseSource
from src.services.provisional_eod import capture_fresh_ssi_read,HosePublicationEvidence
from src.services.technical_eod_supervision import (initialize_supervision,resume_supervision,
    discovery_plan,supervised_eod_cycle,supervision_status)

ROOT=Path(__file__).resolve().parents[1]


def configuration(path):
    path=Path(path).resolve()
    raw=path.read_bytes()
    if len(raw)>16000: raise ValueError('Pilot config too large')
    config=json.loads(raw)
    expected={'schema_version','ticker','database_file','calendar_seed','calendar_seed_sha256',
        'qualified_publication_anchor','qualified_publication_anchor_sha256','security_receipt','security_receipt_sha256'}
    if set(config)!=expected or config['schema_version']!='technical-supervised-pilot-v1':
        raise ValueError('Explicit single-ticker pilot configuration required')
    config['ticker']=SymbolRequest(symbol=config['ticker']).symbol
    paths={}
    for key in ('database_file','calendar_seed','qualified_publication_anchor','security_receipt'):
        candidate=(ROOT/config[key]).resolve()
        if not candidate.is_relative_to(ROOT):
            raise ValueError('Pilot paths must remain inside isolated worktree')
        if key=='database_file':
            if not candidate.is_relative_to(ROOT/'data'/'technical_eod') or candidate.suffix!='.db':
                raise ValueError('Explicit isolated runtime database required')
        else:
            if sha256(candidate.read_bytes()).hexdigest()!=config[key+'_sha256']:
                raise ValueError('Qualified pilot evidence checksum mismatch')
        paths[key]=candidate
    return config,paths


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(ROOT/'docs'/'TECHNICAL_FPT_PILOT_V1.json'))
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument('--dry-run',action='store_true')
    actions.add_argument('--status',action='store_true',help='Read-only pilot metadata, no network')
    actions.add_argument('--initialize',action='store_true')
    actions.add_argument('--run-once',action='store_true')
    actions.add_argument('--watch',action='store_true')
    parser.add_argument('--credentials-file',help='Existing authorized environment file; values are never copied or logged')
    parser.add_argument('--resume',action='store_true',help='Explicitly resume a halted configured pilot')
    args=parser.parse_args(argv)
    try:
        if args.resume and not (args.run_once or args.watch):
            raise ValueError('Resume requires an explicit live cycle')
        config,paths=configuration(args.config)
        now=datetime.now(timezone.utc)
        database=paths['database_file']
        if args.status:
            if not database.exists():raise ValueError('Pilot database unavailable')
            engine=create_engine('sqlite:///file:'+database.as_posix()+'?mode=ro&uri=true')
            try:
                with Session(engine) as session:result=supervision_status(session,now)
            finally:engine.dispose()
            print(json.dumps(result,sort_keys=True))
            return int(result['status'] in ('HALTED','UNCONFIGURED'))
        calendar=seed_calendar(paths['calendar_seed'].parent)
        source=OfficialHoseSource(publication_anchor(paths['qualified_publication_anchor'].parent))
        if args.dry_run or not any((args.initialize,args.run_once,args.watch)):
            # Read-only SQLite URI; no implicit schema creation or bootstrap writes.
            if database.exists():
                engine=create_engine('sqlite:///file:'+database.as_posix()+'?mode=ro&immutable=1&uri=true')
                try: result=supervised_eod_cycle(engine,source,dry_run=True)
                finally:engine.dispose()
            else:
                plan=discovery_plan(config['ticker'],calendar,{},source,now)
                candidate=plan['qualified']
                pub=HosePublicationEvidence.model_validate(candidate['publication']) if candidate else None
                result={'status':'DRY_RUN','ticker':config['ticker'],'discovery_status':plan['status'],
                    'calendar_through':plan['calendar'].coverage_end.isoformat(),
                    'publication_gate_at':(pub.published_at+timedelta(hours=24)).isoformat() if pub else None,
                    'second_read_due_at':None,'ssi_requests':0,'writes':0,
                    'qualified_source_receipt':candidate['receipt'] if candidate else None}
            print(json.dumps(result,sort_keys=True))
            return int(result.get('discovery_status')=='INCOMPLETE_EVIDENCE')
        if not args.initialize:
            if not database.exists():raise ValueError('Initialize the approved pilot before live cycles')
            settings=Settings(_env_file=Path(args.credentials_file).resolve() if args.credentials_file else ROOT/'.env')
            if not settings.ssi_api_key.get_secret_value() or not settings.ssi_api_secret.get_secret_value():
                raise ValueError('Authorized SSI credentials unavailable')
        database.parent.mkdir(parents=True,exist_ok=True)
        engine=create_engine('sqlite:///'+database.as_posix())
        try:
            create_tables(engine)
            with Session(engine) as session:
                if args.initialize:
                    metadata=json.loads(paths['security_receipt'].read_bytes())
                    received=datetime.fromisoformat(metadata['received_at'])
                    if (metadata['schema_version']!='ssi-security-receipt-v1' or metadata['symbol']!=config['ticker']
                            or metadata['exchange']!='HOSE' or metadata['instrument_type']!='Stock'
                            or metadata['source']!='SSI:FastConnect' or received.utcoffset() is None or received>now):
                        raise ValueError('Qualified pilot security metadata unavailable')
                    initialize_supervision(session,config['ticker'],calendar,now)
                    if session.get(Security,config['ticker']) is None:
                        session.add(Security(symbol=config['ticker'],exchange=metadata['exchange'],
                            instrument_type=metadata['instrument_type'],source=metadata['source'],last_synced_at=received))
                        session.commit()
                if args.resume:resume_supervision(session,now)
            if args.initialize:
                print(json.dumps({'status':'INITIALIZED','ticker':config['ticker'],'ssi_requests':0}))
                return 0
            def acquire(ticker,start,end):
                with SsiMarketDataProvider(settings) as provider:
                    return capture_fresh_ssi_read(ticker,start,end,provider=provider)
            stop=Event()
            previous=signal.signal(signal.SIGTERM,lambda *_:stop.set())
            try:
                while not stop.is_set():
                    result=supervised_eod_cycle(engine,source,acquire=acquire)
                    print(json.dumps(result,sort_keys=True),flush=True)
                    if not args.watch or result['status']=='HALTED':
                        return int(result['status'] in ('HALTED','INCOMPLETE_EVIDENCE','UNCONFIGURED','LEASE_LOST'))
                    stop.wait(600)
            except KeyboardInterrupt:return 0
            finally:signal.signal(signal.SIGTERM,previous)
            return 0
        finally:engine.dispose()
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','reason':'supervised_eod_preflight_failed','exception_type':type(exc).__name__}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
