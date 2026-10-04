"""Pinned B6 identity-only artifacts; never follows protected provenance paths."""
from hashlib import sha256
import json
from pathlib import Path

from .admission import REQUIRED_STUDIES

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = Path('research/provenance/technical_protected_exclusions_v1')
HASHES = {
    'PROTECTED_CASE_EXCLUSION_LEDGER_V1.json': '6e27c02b28b158aa360ba899b25865ff7981e562f582ae9cae684ad862af8c90',
    'PROTECTED_STOCK_DAY_EXCLUSIONS_V1.json': 'e2baabba2256f18eb2b677f32ef8077eb82e74f7adbeaa531cdd764831783a53',
}


def load_certified_ledger(root=ROOT):
    objects = []
    for name, expected in HASHES.items():
        path = Path(root) / DIRECTORY / name
        for part in (path, *path.parents):
            if part.is_symlink() or part.is_junction():
                raise ValueError('Redirected exclusion artifact')
            if part == Path(root):
                break
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise ValueError('Certified exclusion artifact hash mismatch')
        objects.append(json.loads(raw))
    ledger, union = objects
    studies = ledger['studies']
    if ({s['protected_study_id'] for s in studies} != REQUIRED_STUDIES or len(studies) != 3
            or any(s['completeness_status'] != 'COMPLETE' for s in studies)
            or union['completeness_status'] != 'COMPLETE'):
        raise ValueError('Incomplete protected coverage')
    if union['ledger_sha256'] != HASHES['PROTECTED_CASE_EXCLUSION_LEDGER_V1.json']:
        raise ValueError('Exclusion projection lineage mismatch')
    return ledger


def attach_certified_exclusions(metadata, root=ROOT):
    """Bind the pinned ledger to a declared request scope before admission.

    Does not open the requested payload, assert its safety, or enable loading.
    Admission still validates source identity, range, certificates and overlaps.
    """
    from copy import deepcopy
    bound = deepcopy(metadata)
    ledger = load_certified_ledger(root)
    bound['ledger'] = admission_ledger(ledger, bound['manifest']['scope'])
    bound['manifest']['protected_ledger_version'] = ledger['ledger_version']
    return bound


def request_certified_payload(metadata, *, payload_loader, root=ROOT, **eligibility):
    """Enforce pinned B6 exclusions before the existing disabled loader boundary."""
    from .admission import request_real_payload
    bound = attach_certified_exclusions(metadata, root)
    return request_real_payload(bound, payload_loader=payload_loader, **eligibility)


def admission_ledger(ledger, scope):
    """In-memory shape adapter only. Does not certify scope or enable loading.

    The existing contract uses UNKNOWN where the export uses UNRESOLVED.
    Unknown episode bounds stay absent; only stock-day exclusion is certified.
    """
    from src.evaluation.benchmark.admission import ExclusionLedger
    studies = ledger['studies']
    complete = len(studies) == 3 and {s['protected_study_id'] for s in studies} == REQUIRED_STUDIES
    complete = complete and all(s['completeness_status'] == 'COMPLETE' for s in studies)
    state = lambda s: 'UNKNOWN' if s == 'UNRESOLVED' else s
    records = []
    for study in studies:
        for r in study['records']:
            if r['episode_scope'] != 'UNRESOLVED':
                raise ValueError('Explicit episode scope needs an approved adapter')
            records.append(dict(study_id=study['protected_study_id'], ticker=r['ticker'],
                                instrument_id=r.get('instrument_id'), session=r['session_date'], event_ids=[r['case_id']],
                                reason=r['exclusion_reason'], provenance='; '.join(r['provenance_ref']) + '; episode_scope=UNRESOLVED',
                                completeness=state(study['completeness_status'])))
    return ExclusionLedger.model_validate(dict(schema_version='d2-exclusions-v1', version=ledger['ledger_version'],
        scope=scope, completeness='COMPLETE' if complete else 'INCOMPLETE', issuer='owner-authorized-b6b-projection',
        provenance='PROTECTED_CASE_EXCLUSION_LEDGER_V1.json; stock-day coverage only; episode scope unresolved',
        coverage=[dict(study_id=s['protected_study_id'], completeness=state(s['completeness_status']),
                       provenance='; '.join(s['source_ref'])) for s in studies], records=records)).model_dump(mode='json')
