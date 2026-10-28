"""Explicit qualified-evidence ingress and one bounded operational worker cycle."""
import argparse
from datetime import date
import json
from pathlib import Path
from sqlmodel import Session
from src.db.session import create_tables, get_engine
from src.services.provisional_eod import parse_compact_ssi_receipt
from src.services.technical_api import MAX_LOCAL_BYTES
from src.services.technical_eod_store import ProvisionalEODDefinition, enqueue_provisional_eod, run_technical_eod_cycle


def load(path):
    with Path(path).open('rb') as stream:
        raw=stream.read(MAX_LOCAL_BYTES+1)
    if len(raw)>MAX_LOCAL_BYTES:
        raise ValueError('Evidence input exceeds bound')
    return json.loads(raw)


def main():
    parser=argparse.ArgumentParser(description='Queue qualified provisional EOD evidence; run at most one due read')
    parser.add_argument('--ticker',required=True)
    parser.add_argument('--session',required=True,type=date.fromisoformat)
    parser.add_argument('--evidence',required=True,help='Qualified history_start/calendar/publication JSON')
    parser.add_argument('--first-receipt',help='Previously audited metadata-only SSI receipt')
    parser.add_argument('--resume',action='store_true',help='Explicitly resume a stopped SSI job')
    args=parser.parse_args()
    try:
        definition=ProvisionalEODDefinition.model_validate(load(args.evidence))
        first=parse_compact_ssi_receipt(load(args.first_receipt)) if args.first_receipt else None
        create_tables()
        engine=get_engine()
        with Session(engine) as session:
            enqueue_provisional_eod(session,args.ticker,args.session,**definition.model_dump(),first=first,resume=args.resume)
        result=run_technical_eod_cycle(engine)
        print(json.dumps(result,sort_keys=True))
        return int(result['status'] in ('STOPPED','INCOMPLETE_EVIDENCE','LEASE_LOST'))
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','reason':'technical_eod_command_failed','exception_type':type(exc).__name__}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
