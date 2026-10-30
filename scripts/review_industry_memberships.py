"""Recount a hash-pinned archived SSI response; no provider or application DB."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from src.services.industry_membership_review import review_memberships


def review_archive(path, *, expected_sha256, label, output, report, review_reference):
    path = Path(path)
    if path.stat().st_size > 32_000_000:
        raise ValueError('Industry archive exceeds bound')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError('Industry archive hash mismatch')
    archive = json.loads(data)
    selected = [r for r in archive['requests'] if r.get('label') == label]
    if len(selected) != 1:
        raise ValueError('Ambiguous archived response')
    request = selected[0]
    if request.get('status') != 'OK' or request.get('path') != '/api/v3/data/securitiesByBoard':
        raise ValueError('Unusable SecuritiesInfo response')
    reviewed = review_memberships(request['payload'], receipt=dict(
        fetched_at=request['received_at'], document_sha256=digest,
        request_label=label, source_path=request['path'], source_params=request['params']),
        review_reference=review_reference)
    destination = Path(output).resolve()
    if any(part.casefold() in ('public', 'static') for part in destination.parts):
        raise ValueError('Store unqualified membership observations privately')
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(reviewed, ensure_ascii=False, indent=2) + '\n'
    if destination.exists() and destination.read_text(encoding='utf-8') != payload:
        raise ValueError('Existing review differs; retain it and choose a new version path')
    destination.write_text(payload, encoding='utf-8')
    summary = {key: reviewed[key] for key in ('contract', 'review_reference', 'source', 'receipt',
        'basis', 'public_display_eligible', 'taxonomy_eligible', 'coverage',
        'excluded_nonordinary_rows', 'duplicate_rows', 'invalid_rows', 'missing_evidence', 'limitations')}
    summary['verification_counts'] = dict(Counter(e['verification_status'] for e in reviewed['entries']))
    summary['distinct_observed_codes'] = len({e['provider_code'] for e in reviewed['entries'] if e['provider_code']})
    summary['provider_requests'] = 0
    summary['private_dataset_sha256'] = hashlib.sha256(payload.encode()).hexdigest()
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('input', 'sha256', 'label', 'output', 'report', 'review-reference'):
        parser.add_argument('--' + option, required=True)
    args = parser.parse_args()
    result = review_archive(args.input, expected_sha256=args.sha256, label=args.label,
        output=args.output, report=args.report, review_reference=args.review_reference)
    print(json.dumps({'verification_counts': result['verification_counts'],
        'coverage': result['coverage'], 'taxonomy_eligible': result['taxonomy_eligible']}))
