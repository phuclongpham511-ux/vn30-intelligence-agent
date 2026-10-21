"""Assemble saved free-source evidence privately without replacing provider history."""
import argparse
import hashlib
import json
from pathlib import Path
from src.providers.reviewed_reports import report_packet, pinned_file
from src.providers.cafef_statements import cafef_packet
from src.services.personal_financials import saved_packet


def prepare(captures, destination, *, reports=(), summaries=(), memberships=None, dividends=None):
    source = Path(captures).resolve(strict=True)
    target = Path(destination).resolve()
    if target.exists() or source == target or any(p.casefold() in ('public','static') for p in target.parts):
        raise ValueError('Choose a new private evidence directory')
    original = json.loads((source/'index.json').read_text(encoding='utf-8'))
    if len(original.get('captures',{})) > 2000:
        raise ValueError('Source capture index exceeds bound')
    index = dict(contract='personal-saved-captures-v1', captures={}, reviewed_reports={})
    files = {}

    def add(name, data):
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or name in files and files[name] != data:
            raise ValueError('Evidence file collision or unsafe path')
        files[name] = data

    for ticker,entry in original['captures'].items():
        saved_packet(source,ticker)
        if entry.get('format') not in (None,'vci-raw-capture-v1','canonical-financial-packet-v1'):
            raise ValueError('Use original VCI baseline as capture input')
        data = pinned_file(source,entry['file'],entry['sha256'],32_000_000)
        add(entry['file'],data); index['captures'][ticker] = entry
    prior_revisions = original.get('capture_history', {})
    if not isinstance(prior_revisions, dict) or len(prior_revisions) > 2000:
        raise ValueError('Invalid capture revision history')
    for ticker, entries in prior_revisions.items():
        if ticker not in index['captures'] or not isinstance(entries, list) or len(entries) > 100:
            raise ValueError('Invalid capture revision history entry')
        kept = []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get('format') not in (
                    None, 'vci-raw-capture-v1', 'canonical-financial-packet-v1'):
                raise ValueError('Unsupported historical capture format')
            data = pinned_file(source, entry['file'], entry['sha256'], 32_000_000)
            add(entry['file'], data)
            kept.append(entry)
        index.setdefault('capture_history', {})[ticker] = kept
    for path in reports:
        path = Path(path).resolve(strict=True)
        if path.stat().st_size > 2_000_000:
            raise ValueError('Reviewed report manifest exceeds bound')
        body = path.read_bytes(); e=json.loads(body)
        history=e.get('contract')=='reviewed-report-history-v1'
        if history:
            from src.providers.reviewed_history import history_packet
            packet=history_packet(e,path.parent)
            originals=[]
            for d in e['documents']:
                data=pinned_file(path.parent,d['file'],d['sha256'],2_000_000)
                add(d['file'],data);originals.append(json.loads(data))
        else:
            packet,_=report_packet(e,path.parent)
            originals=[e]
        if packet.ticker in index['reviewed_reports']:
            raise ValueError('Conflicting reviewed source; choose a separate bundle')
        for original in originals:
            for name,digest,bound in [(original['document_file'],original['document_sha256'],40_000_000),
                    *((p['image_file'],p['image_sha256'],8_000_000) for p in original['pages'])]:
                add(name,pinned_file(path.parent,name,digest,bound))
        name=f'{packet.ticker}-reviewed-{hashlib.sha256(body).hexdigest()}.json';add(name,body)
        index['reviewed_reports'][packet.ticker]=dict(file=name,sha256=hashlib.sha256(body).hexdigest(),format=e['contract'])
    for path in summaries:
        path=Path(path)
        if path.stat().st_size > 2_000_000:raise ValueError('Summary capture exceeds bound')
        body=path.read_bytes();packet=cafef_packet(json.loads(body))
        if packet.ticker in index['captures']:raise ValueError('Do not replace original provider history')
        name=f'{packet.ticker}-cafef-{hashlib.sha256(body).hexdigest()}.json';add(name,body)
        index['captures'][packet.ticker]=dict(file=name,sha256=hashlib.sha256(body).hexdigest(),format='cafef-saved-annual-v1')
    if memberships:
        data=Path(memberships).read_bytes()
        if len(data)>2_000_000:raise ValueError('Membership review exceeds bound')
        review=json.loads(data)
        if review.get('contract')!='industry-membership-review-v1' or review.get('source')!='SSI:FastConnect:v3:SecuritiesInfo':
            raise ValueError('Unsupported membership evidence')
        name='observed-memberships.json';add(name,data)
        index['observed_memberships']=dict(file=name,sha256=hashlib.sha256(data).hexdigest())
    if dividends:
        from src.providers.vsdc_dividends import dividend_page
        data=Path(dividends).read_bytes()
        if len(data)>4_000_000:raise ValueError('Dividend evidence exceeds bound')
        dividend_page(json.loads(data),'NOTCOVERED')
        name='saved-dividends.json';add(name,data)
        index['dividends']=dict(file=name,sha256=hashlib.sha256(data).hexdigest())
    # Validate every source before creating the new bundle. Original bytes stay intact.
    target.mkdir(parents=True)
    for name,data in files.items():
        out=target/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    (target/'index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    return dict(tickers=sorted(index['captures']),reviewed_reports=sorted(index['reviewed_reports']),
        provider_history_preserved=True,provider_requests=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures',required=True);parser.add_argument('--destination',required=True)
    parser.add_argument('--report',action='append',default=[]);parser.add_argument('--summary',action='append',default=[])
    parser.add_argument('--memberships')
    parser.add_argument('--dividends')
    a=parser.parse_args();print(json.dumps(prepare(a.captures,a.destination,reports=a.report,summaries=a.summary,memberships=a.memberships,dividends=a.dividends)))
