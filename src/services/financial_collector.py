"""Explicit, bounded backlog-to-journal pilot. No scheduler or serving switch."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from uuid import uuid4

import httpx

from src.providers.financial_filings import _https
from src.providers.reviewed_reports import report_packet
from src.providers.reported_bank_ratios import reported_ratio_facts
from src.services.financial_batch import MAX_PACKET_BYTES, _atomic_bytes, _write_immutable, acquire_batch
from src.services.financial_coverage import build_coverage, membership_snapshot
from src.services.financial_intelligence import normalized_metrics
from src.services.financial_journal import MetricJournal, SCHEMA_VERSION
from src.services.personal_financials import saved_capture_entry, saved_packet

MAX_DOCUMENT_BYTES = 40_000_000
MAX_CANDIDATES = 10


def _json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _private(path, private_root):
    root = Path(private_root).resolve()
    target = Path(path).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError('Collector paths must stay inside the private root')
    return target


def _read_json(path, bound=12_000_000):
    if path.stat().st_size > bound:
        raise ValueError('Collector JSON exceeds size bound')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_plan(plan, backlog):
    """Bind a small explicit selection to a preserved, real V5.6 backlog."""
    complete = plan.get('contract') == 'financial-collector-plan-v513'
    expansion = complete or plan.get('contract') == 'financial-collector-plan-v512'
    if plan.get('contract') not in ('financial-collector-plan-v57', 'financial-collector-plan-v512', 'financial-collector-plan-v513') or backlog.get('contract') != 'financial-coverage-v56':
        raise ValueError('Unknown collector or backlog contract')
    if plan.get('backlog_sha256') != _sha(_json(backlog)):
        raise ValueError('Backlog fingerprint mismatch')
    if not expansion and backlog['membership']['effective_date'] != '2026-08-03':
        raise ValueError('Pilot requires the dated August 2026 membership snapshot')
    if expansion and plan['as_of'] != backlog['as_of']:
        raise ValueError('Plan and backlog date must match')
    snapshot = membership_snapshot(plan['as_of'] if expansion else '2026-08-03')
    if snapshot['effective_date'] != backlog['membership']['effective_date']:
        raise ValueError('Backlog membership date differs from preserved snapshot')
    tasks = {t['task_id']: t for t in backlog['acquisition_backlog']}
    chosen = plan['task_ids']
    if not chosen or len(chosen) != len(set(chosen)) or any(t not in tasks for t in chosen):
        raise ValueError('Choose unique existing backlog task IDs')
    selected = [tasks[t] for t in chosen]
    if expansion:
        families = {f'{frequency}_{kind}' for frequency in ('annual', 'quarterly') for kind in ('income', 'balance', 'cash')}
        if any(t['priority'] not in (('P0', 'P3') if complete else ('P3',)) or t['ticker'] not in snapshot['vn100']
               or (not complete and t['ticker'] in snapshot['vn30']) or t['family'] not in families for t in selected):
            raise ValueError('Expansion requires actual non-VN30 VN100 P3 statement gaps')
        if complete:
            companies = {c['ticker']: c for c in backlog['companies']}
            for task in selected:
                frequency, kind = task['family'].split('_', 1)
                if companies[task['ticker']]['statements'][kind][frequency]['count']:
                    raise ValueError('Complete queue only accepts absent statement families')
    elif any(t['priority'] != 'P0' or t['ticker'] not in snapshot['vn30'] for t in selected):
        raise ValueError('Pilot tasks must be actual VN30 P0 statement gaps')
    tickers = {t['ticker'] for t in selected}
    candidates = plan['candidates']
    if not (1 if complete else 3) <= len(tickers) <= 5 or not 1 <= len(candidates) <= MAX_CANDIDATES:
        raise ValueError('Pilot requires 3-5 issuers and at most 10 source candidates')
    identifiers = []
    for c in candidates:
        identifiers.append(c['id'])
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', c['id']) or c['ticker'] not in tickers:
            raise ValueError('Invalid candidate identity')
        if c['kind'] not in ('vci', 'document') or c['access'] not in ('public_no_login', 'restricted'):
            raise ValueError('Unsupported collector source or access status')
        for key in ('url', 'discovery_url'):
            _https(c[key])
        for key in ('title', 'issuer', 'reporting_period', 'document_type', 'access_notes'):
            if not isinstance(c.get(key), str) or not c[key]:
                raise ValueError('Source discovery metadata is incomplete')
        if c.get('published_date'):
            date.fromisoformat(c['published_date'])
        if c['kind'] == 'document' and c.get('format') not in ('pdf', 'html'):
            raise ValueError('Only PDF and HTML source documents are supported')
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate source candidate ID')
    date.fromisoformat(plan['as_of'])
    return tickers


def download_document(url, document_format, *, client, pause=time.sleep):
    """Retain decoded original HTTP body bytes; never retry access/rate limits."""
    _https(url)
    for attempt in range(2):
        try:
            # Redirects are recorded as unavailable, not followed to unreviewed hosts.
            with client.stream('GET', url, follow_redirects=False) as response:
                status = response.status_code
                if status in (401, 403, 429, 451):
                    return dict(status='ACCESS_RESTRICTED', http_status=status, attempts=attempt + 1)
                if status >= 500 and attempt == 0:
                    pause(2)
                    continue
                if status != 200:
                    return dict(status='SOURCE_UNAVAILABLE', http_status=status, attempts=attempt + 1)
                if int(response.headers.get('content-length', '0')) > MAX_DOCUMENT_BYTES:
                    raise ValueError('Source document exceeds size bound')
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_DOCUMENT_BYTES:
                        raise ValueError('Source document exceeds size bound')
                data = bytes(body)
                content_type = response.headers.get('content-type', '').split(';')[0]
                if document_format == 'pdf' and not data.startswith(b'%PDF-'):
                    raise ValueError('Downloaded source is not a PDF')
                if document_format == 'html' and (content_type not in ('text/html', 'application/xhtml+xml')
                        or b'<html' not in data[:10000].lower()):
                    raise ValueError('Downloaded source is not HTML')
                return dict(status='DOWNLOADED', body=data, content_type=content_type,
                    http_status=status, attempts=attempt + 1)
        except httpx.TransportError:
            if attempt == 0:
                pause(2)
                continue
            return dict(status='SOURCE_UNAVAILABLE', error='transport_error', attempts=attempt + 1)


def _packet_valid(packet, candidate, as_of):
    if packet.ticker != candidate['ticker'] or packet.is_fixture:
        raise ValueError('Extracted packet ticker or fixture status is ineligible')
    periods = set()
    for kind, receipt in packet.reports.items():
        for obs in receipt.observations:
            if obs.ticker != packet.ticker or obs.source != packet.source or obs.statement != kind:
                raise ValueError('Extracted statement ownership mismatch')
            if int(obs.period[:4]) > date.fromisoformat(as_of).year:
                raise ValueError('Future financial period is ineligible')
            periods.add(obs.period)
            if obs.frequency != ('quarterly' if '-Q' in obs.period else 'annual'):
                raise ValueError('Extracted financial period/frequency mismatch')
    if not periods or (candidate.get('expected_periods') and periods - set(candidate['expected_periods'])):
        raise ValueError('Extracted financial period differs from reviewed candidate')


def _evidence_rows(packet):
    observations = [o for r in packet.reports.values() for o in r.observations]
    return dict(statement_observations=len(observations),
        source_values=sum(i.value is not None for o in observations for i in o.items),
        source_unqualified_values=sum(i.value is not None and (i.unit == 'source_units'
            or i.semantic_status != 'reported') for o in observations for i in o.items),
        periods=sorted({o.period for o in observations}))


def coverage_delta(before, after, tasks):
    """Resolve only the exact saved statement-family gaps, not complete histories."""
    old = {c['ticker']: c for c in before['companies']}
    new = {c['ticker']: c for c in after['companies']}
    resolved, cells = [], []
    for task in tasks:
        task_id = task['task_id']
        frequency, kind = task['family'].split('_', 1)
        ticker = task['ticker']
        a, b = old[ticker]['statements'][kind][frequency], new[ticker]['statements'][kind][frequency]
        item = dict(task_id=task_id, ticker=ticker, family=task['family'],
            before_status=a['status'], after_status=b['status'], before_periods=a['count'],
            after_periods=b['count'], added_periods=b['count'] - a['count'])
        cells.append(item)
        if a['count'] == 0 and b['count'] > 0:
            resolved.append(task_id)
    return dict(before=before['summary'], after=after['summary'], cells=cells,
        resolved_initial_p0_tasks=resolved if all(t['priority'] == 'P0' for t in tasks) else [],
        resolved_initial_tasks=resolved,
        new_issuer_period_pairs=sum(len({p for cell in c['statements'].values()
            for span in cell.values() for p in span['source_lines_by_period']}
            - {p for cell in old[c['ticker']]['statements'].values() for span in cell.values()
               for p in span['source_lines_by_period']}) for c in after['companies']))


def run_collector(plan, backlog, *, journal_path, root, fetch_packet, industry_snapshot=None,
                  client=None, refresh_documents=False, refresh_sdk=False, private_root=None):
    """Resume cached bytes/packets, isolate source failures and append immutable rows.

    Operator-reviewed manifests use the existing ``reviewed-report-v2`` adapter.
    Download alone never creates an AVAILABLE financial cell. State is a private
    acquisition manifest, not a second store of financial facts.
    """
    tickers = validate_plan(plan, backlog)
    local = Path(private_root or Path(__file__).resolve().parents[2] / '.local').resolve()
    root = _private(root, local)
    journal_path = _private(journal_path, local)
    if not journal_path.is_file():
        raise ValueError('Existing V5.5 financial journal is required')
    journal = MetricJournal(journal_path)
    if journal.storage_summary()['schema_version'] != SCHEMA_VERSION:
        raise ValueError('Collector never initializes or migrates a journal')
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / 'state.json'
    state = _read_json(state_path) if state_path.exists() else dict(contract='financial-collector-state-v57', candidates={})
    if state.get('contract') != 'financial-collector-state-v57':
        raise ValueError('Unknown acquisition state')
    before = build_coverage(journal_path, as_of=plan['as_of'], industry_snapshot=industry_snapshot)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid4().hex[:8]
    run_dir = root / 'runs' / run_id
    run_dir.mkdir(parents=True)
    _write_immutable(run_dir / 'before.json', _json(before))
    _write_immutable(run_dir / 'plan.json', _json(plan))
    results = []
    owned_client = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(40), headers={'User-Agent': 'WoofiFinancialResearch/5.7'})
    try:
        for c in plan['candidates']:
            row = dict(candidate_id=c['id'], ticker=c['ticker'], source_url=c['url'],
                status='INTERRUPTED',
                documents_acquired=0, documents_reused=0, inserted_observations=0,
                inserted_captures=0, inserted_metric_facts=0)
            entry = state['candidates'].setdefault(c['id'], dict(identity=_sha(_json({
                k: c[k] for k in ('ticker', 'url', 'kind')})), revisions=[]))
            identity = _sha(_json({k: c[k] for k in ('ticker', 'url', 'kind')}))
            if entry['identity'] != identity:
                raise ValueError('Candidate ID cannot be reused for another source identity')
            try:
                entry['status'] = 'ACQUIRING'
                _atomic_bytes(state_path, _json(state))
                if c['access'] == 'restricted':
                    row['status'] = 'ACCESS_RESTRICTED'
                    continue
                if c['kind'] == 'vci':
                    cached_candidate = entry.get('sdk_candidate')
                    if cached_candidate and not refresh_sdk:
                        packet, digest = saved_capture_entry(root, c['ticker'], cached_candidate)
                        row['documents_reused'] = 1
                    else:
                        fetched = []
                        def fetch_candidate(ticker):
                            packet = fetch_packet(ticker)
                            fetched.append(packet)
                            return packet
                        acquired = acquire_batch(root / 'sdk', [c['ticker']], fetch_packet=fetch_candidate,
                            refresh=refresh_sdk, private_root=local)
                        if acquired['errors']:
                            error = acquired['errors'][c['ticker']]
                            row.update(status='EXTRACTION_FAILURE' if error in ('ValueError', 'ValidationError')
                                else 'SOURCE_UNAVAILABLE', error=error)
                            continue
                        outcome = acquired['results'][0]['status']
                        row['sdk_acquisition_status'] = outcome
                        if outcome == 'refresh_deferred_shorter_history':
                            # Keep the legacy longer capture selected in its file index.
                            # SQLite can independently append this candidate's new periods.
                            packet = fetched[0]
                            body = (packet.model_dump_json(indent=2) + '\n').encode('utf-8')
                            if len(body) > MAX_PACKET_BYTES:
                                raise ValueError('Normalized financial candidate exceeds size bound')
                            digest = _sha(body)
                            name = f'sdk-candidates/{c["ticker"]}-{digest}.json'
                            _write_immutable(root / name, body)
                            cached_candidate = dict(file=name, sha256=digest, format='canonical-financial-packet-v1')
                            row['sdk_candidate_file'] = name
                            row['status'] = 'EXTRACTION_FAILURE'
                            packet, digest = saved_capture_entry(root, c['ticker'], cached_candidate)
                            entry['sdk_candidate'] = cached_candidate
                            history = entry.setdefault('sdk_candidate_revisions', [])
                            if cached_candidate not in history:
                                history.append(cached_candidate)
                            _atomic_bytes(state_path, _json(state))
                        else:
                            packet, digest = saved_packet(root / 'sdk', c['ticker'])
                            entry.pop('sdk_candidate', None)
                        row['documents_reused' if outcome in ('skipped_existing', 'unchanged') else 'documents_acquired'] = 1
                    row['evidence_kind'] = 'sdk_canonical_capture_not_wire_response'
                else:
                    document = entry.get('document')
                    if document and not refresh_documents:
                        path = _private(root / document['file'], local)
                        if not path.is_relative_to(root) or _sha(path.read_bytes()) != document['sha256']:
                            raise ValueError('Cached source bytes failed integrity check')
                        row['documents_reused'] = 1
                    else:
                        receipt = download_document(c['url'], c['format'], client=client)
                        if receipt['status'] != 'DOWNLOADED':
                            row.update(receipt)
                            continue
                        data = receipt.pop('body')
                        digest = _sha(data)
                        name = f'documents/{digest}.{c["format"]}'
                        _write_immutable(root / name, data)
                        document = dict(file=name, sha256=digest, bytes=len(data),
                            fetched_at=datetime.now(timezone.utc).isoformat(), **receipt)
                        entry['document'] = document
                        if document not in entry['revisions']:
                            entry['revisions'].append(document)
                        _atomic_bytes(state_path, _json(state))
                        row['documents_acquired'] = 1
                    row['document_sha256'] = document['sha256']
                    manifest_name = c.get('review_manifest')
                    if not manifest_name:
                        row['status'] = 'DOWNLOADED_AWAITING_REVIEW'
                        continue
                    row['status'] = 'EXTRACTION_FAILURE'
                    manifest_path = _private(root / manifest_name, local)
                    if not manifest_path.is_relative_to(root):
                        raise ValueError('Review manifest must stay inside collector directory')
                    evidence = _read_json(manifest_path)
                    if evidence['document_sha256'] != document['sha256'] or evidence['document_url'] != c['url']:
                        raise ValueError('Review manifest refers to a different document revision')
                    if evidence['ticker'] != c['ticker'] or evidence['issuer'] != c['issuer']:
                        raise ValueError('Review manifest issuer/ticker mismatch')
                    packet, audit = report_packet(evidence, root)
                    digest = document['sha256']
                    row['extraction_audit'] = audit
                    row['evidence_kind'] = 'reviewed_original_pdf'
                _packet_valid(packet, c, plan['as_of'])
                facts = [f for frequency in ('annual', 'quarterly')
                         for f in normalized_metrics(packet, frequency=frequency, limit=40)]
                if c.get('ratio_review'):
                    if c['kind'] != 'document' or not c.get('review_manifest'):
                        raise ValueError('Ratio review requires an authenticated original report')
                    ratio_path = _private(root / c['ratio_review'], local)
                    if not ratio_path.is_relative_to(root):
                        raise ValueError('Ratio review must stay inside collector directory')
                    ratio_facts = reported_ratio_facts(_read_json(ratio_path), evidence, packet)
                    facts.extend(ratio_facts)
                    row['unqualified_reported_ratios'] = len(ratio_facts)
                row.update(_evidence_rows(packet))
                row['receipt_statuses'] = {kind: receipt.status for kind, receipt in packet.reports.items()}
                row.update(journal.import_packet(packet, digest, provenance=dict(
                    collector='v57', candidate=c, run_id=run_id, source_capture_sha256=digest)))
                row['inserted_metric_facts'] = journal.append(facts)
                row['qualified_metric_facts'] = sum(f.quality_status == 'QUALIFIED' for f in facts)
                row['unqualified_reported_metric_facts'] = sum(f.metric_kind == 'reported'
                    and f.quality_status == 'UNQUALIFIED' for f in facts)
                row['status'] = 'IMPORTED' if row['source_values'] else 'IMPORTED_UNQUALIFIED'
            except Exception as exc:
                row.update(status='EXTRACTION_FAILURE' if row.get('status') == 'EXTRACTION_FAILURE' else 'FAILED',
                    error=type(exc).__name__, reason=str(exc)[:300])
            finally:
                entry.update(status=row['status'], last_run=run_id, last_result=row)
                _atomic_bytes(state_path, _json(state))
                results.append(row)
    finally:
        if owned_client:
            client.close()
    after = build_coverage(journal_path, as_of=plan['as_of'], industry_snapshot=industry_snapshot)
    _write_immutable(run_dir / 'after.json', _json(after))
    result = dict(contract='financial-collector-run-v57', run_id=run_id, tickers=sorted(tickers),
        task_ids=plan['task_ids'], sources=plan['candidates'], results=results,
        status_counts=dict(Counter(r['status'] for r in results)),
        coverage=coverage_delta(before, after, [t for t in backlog['acquisition_backlog'] if t['task_id'] in plan['task_ids']]),
        public_display_activated=False, journal_path=str(journal_path))
    _write_immutable(run_dir / 'result.json', _json(result))
    return result
