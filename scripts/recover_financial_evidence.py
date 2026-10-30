"""Replay saved evidence into field-level metadata/coverage reports; zero requests."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
from src.analytics.financial_engine import financial_engine
from src.services.personal_financials import saved_packet, saved_research_packet, personal_projection
from src.services.financial_verification import DIMENSIONS


def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def observations(directory, *, preferred=False):
    root=Path(directory)
    index=json.loads((root/'index.json').read_text(encoding='utf-8'))
    output=[]
    for ticker in sorted(index['captures']):
        for frequency in ('annual','quarterly','ttm'):
            packet,digest=(saved_research_packet(root,ticker,frequency=frequency) if preferred else saved_packet(root,ticker))
            before=packet.model_dump()
            full=financial_engine(packet,frequency=frequency,limit=8)
            display=personal_projection(packet,frequency=frequency,limit=8,authorization_reference='task:free-data-evidence-recovery:'+digest)
            raw={r['period']:r for r in full.rows}
            states={p['period']:p['metrics'] for p in display['verification']['periods']}
            receipts=packet.reports
            source_rows={(kind,o.period):o for kind,r in receipts.items() for o in r.observations}
            for row in display['rows']:
                for field,state in states[row['period']].items():
                    if not state['display_eligible']:continue
                    refs=raw[row['period']]['calculations'][field]['inputs']
                    reported=len(refs)==1 and refs[0]['field']==field and refs[0]['value']==row[field]
                    for ref in refs:
                        original=source_rows[(ref['statement'],ref['period'])]
                        if (original.field_codes.get(ref['field'])!=ref['code'] or original.fields[ref['field']]!=ref['value']
                                or original.source_context.model_dump(mode='json')!=ref['source_context']):
                            raise ValueError('Displayed evidence does not trace to its source record')
                    contexts=[r['source_context'] for r in refs]
                    # Per-field units override statement headings (e.g. bank
                    # EPS is VND/share inside a million-VND income statement).
                    field_metadata=[(c['original_metadata'].get('fields') or {}).get(r['field'],{}) for r,c in zip(refs,contexts)]
                    pages=[c['original_metadata'].get('page_evidence',{}).get(str(f.get('page')),{}) for f,c in zip(field_metadata,contexts)]
                    unit_origin='reported_original_filing' if all(c['unit_evidence']=='original_filing' for c in contexts) else 'inferred_adapter_contract'
                    scope_origin='reported' if all(r['consolidation'] in ('consolidated','standalone') for r in refs) else 'unknown'
                    unique_id=hashlib.sha256(json.dumps([packet.source,ticker,field,[(r['statement'],r['period'],r['code'],r['source_context']['record_sha256']) for r in refs]],sort_keys=True).encode()).hexdigest()
                    output.append(dict(ticker=ticker,view_frequency=frequency,period=row['period'],metric_id=field,
                        metric_kind='reported' if reported else 'derived',source=packet.source,source_version=packet.source_version,
                        capture_sha256=digest,source_observation_id=unique_id,
                        source_statements=';'.join(r['statement'] for r in refs),source_periods=';'.join(r['period'] for r in refs),
                        source_codes=';'.join(r['code'] for r in refs),record_sha256=';'.join(c['record_sha256'] for c in contexts),
                        receipt_sha256=';'.join(r['content_sha256'] for r in refs),
                        source_urls=';'.join(c['original_metadata'].get('document_url',receipts[r['statement']].source_url) for r,c in zip(refs,contexts)),
                        source_fetched_at=';'.join(c['original_metadata'].get('original_observed_at',receipts[r['statement']].observed_at.isoformat()) for r,c in zip(refs,contexts)),
                        metadata_sha256=packet.metadata_sha256,
                        original_units=';'.join(f.get('original_unit') or c.get('original_unit') or 'UNKNOWN' for f,c in zip(field_metadata,contexts)),
                        original_currencies=';'.join(c.get('original_currency') or 'UNKNOWN' for c in contexts),
                        normalization_multipliers=';'.join(str(f.get('multiplier',c['amount_multiplier'])) for f,c in zip(field_metadata,contexts)),
                        fiscal_period_starts=';'.join(c.get('period_start') or 'UNKNOWN' for c in contexts),
                        fiscal_period_ends=';'.join(c.get('period_end') or 'UNKNOWN' for c in contexts),
                        flow_or_balance_basis=';'.join(r['basis'] for r in refs),
                        original_source_dates=json.dumps([{k:c['original_metadata'].get(k) for k in ('publicDate','updateDate','createDate','publication_date')} for c in contexts],sort_keys=True),
                        document_sha256=';'.join(c['original_metadata'].get('binary_sha256') or 'UNKNOWN' for c in contexts),
                        reviewed_source_pages=';'.join(str(f.get('page') or 'UNKNOWN') for f in field_metadata),
                        page_text_sha256=';'.join(p.get('text_sha256') or 'UNKNOWN' for p in pages),
                        page_image_sha256=';'.join(p.get('image_sha256') or 'UNKNOWN' for p in pages),
                        review_references=';'.join(c['original_metadata'].get('review_reference') or 'UNKNOWN' for c in contexts),
                        lineage='ORIGINAL_PDF_AND_REVIEWED_PAGES' if packet.source.startswith('issuer:') else
                            'CANONICAL_LINES_ONLY_ORIGINAL_TRANSPORT_ABSENT' if index['captures'][ticker].get('format')=='canonical-financial-packet-v1' else 'RAW_RESPONSE_REPLAY',
                        unit_origin=unit_origin,currency_origin='reported' if all(c['original_currency'] for c in contexts) else 'unknown_original_currency',
                        scope_origin=scope_origin,scope=';'.join(str(r['consolidation'] or 'UNKNOWN') for r in refs),
                        fiscal_boundaries_origin='reported' if all(c['period_end'] and (r['statement']=='balance' or c['period_start']) for r,c in zip(refs,contexts)) else 'unknown',
                        flow_basis_origin='reported_or_original_report' if all(c['unit_evidence']=='original_filing' or 'flowBasis'in c['original_metadata'] for c in contexts) else 'inferred_adapter_convention',
                        original_publication_values=';'.join(str(c['original_metadata'].get('publicDate') or c['original_metadata'].get('publication_date') or '') for c in contexts),
                        publication_origin='reported_unqualified' if any(c['original_metadata'].get('publicDate') for c in contexts) else 'unknown',
                        revision_origin='immutable_observed_content_hash_not_historical_correction_vintage',
                        **state['dimensions'],missing_evidence=';'.join(state['missing_evidence'])))
            if packet.model_dump()!=before:raise ValueError('Evidence recovery mutated original records')
    return output


def recover(baseline,bundle,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    original=observations(baseline)
    if any(r['metric_kind']!='reported' for r in original):raise ValueError('Baseline scope must be individually reported observations')
    current=observations(bundle,preferred=True)
    write_csv(output/'FIELD_LEVEL_EVIDENCE_MATRIX.csv',original)
    write_csv(output/'ACTIVATED_VIEW_EVIDENCE_MATRIX.csv',current)
    grouped=defaultdict(list)
    for row in current:grouped[(row['ticker'],row['source'],row['view_frequency'],row['metric_id'],row['metric_kind'])].append(row)
    coverage=[]
    for keys,rows in sorted(grouped.items()):
        coverage.append(dict(zip(('ticker','source','frequency','metric_id','metric_kind'),keys),
            observations=len(rows),**{k:sum(r[k] for r in rows) for k in DIMENSIONS}))
    write_csv(output/'VERIFIED_METRIC_COVERAGE.csv',coverage)
    def count(rows):
        return dict(observations=len(rows),distinct_source_metric_observations=len({r['source_observation_id'] for r in rows}),
            kinds=dict(Counter(r['metric_kind'] for r in rows)),**{k:sum(r[k] for r in rows) for k in DIMENSIONS},
            lineage_counts=dict(Counter(r['lineage'] for r in rows)),
            metadata_origins={k:dict(Counter(r[k] for r in rows)) for k in ('unit_origin','currency_origin','scope_origin','fiscal_boundaries_origin','flow_basis_origin','publication_origin')})
    result=dict(contract='free-data-evidence-recovery-v2',provider_requests=0,source_mutations=0,
        baseline=count(original),preferred_views=count(current),
        original_report_views=count([r for r in current if r['source'].startswith('issuer:')]),
        limitations=['Observation counts include separately requested quarterly/TTM balance presentations; distinct source IDs are also counted.',
            'Preferred annual filing views do not replace the selectable original provider history.',
            'Verification dimensions do not grant public rights or establish runtime/browser acceptance.'])
    (output/'EVIDENCE_RECOVERY_COUNTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',required=True);p.add_argument('--bundle',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(recover(a.baseline,a.bundle,a.output)))
