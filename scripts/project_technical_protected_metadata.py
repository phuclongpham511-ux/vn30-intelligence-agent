"""Owner-authorized B6B identity projection. Never evaluates or loads market data.

Only nine explicit files may be read. Non-identity JSON values are skipped
lexically, not decoded. No source records, labels, or evidence are printed.
"""
import argparse
from datetime import date, datetime
from hashlib import sha256
import json
from pathlib import Path
import re

from src.evaluation.benchmark.exclusions import admission_ledger

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('research/provenance/technical_protected_exclusions_v1')
VERSION = 'technical-protected-exclusions-v1'
STUDIES = (
    ('validation-v1', 'validation-v1-20260929', 64,
     'data/evaluation/validation_freezes/validation-v1-20260929/validation_manifest.json',
     'data/evaluation/validation_reviews/validation-v1-20260929/labels-v1-20260930',
     'human_reviews.jsonl', 'label_sha256', 'validation_manifest_sha256'),
    ('validation-v2', 'validation-v2-20260930', 64,
     'data/evaluation/validation_freezes/validation-v2-20260930/validation_manifest.json',
     'data/evaluation/validation_reviews/validation-v2-20260930/labels-v1-20261002',
     'human_reviews.jsonl', 'human_reviews_sha256', 'manifest_sha256'),
    ('development-v3', 'technical-v3-finalization-20261002', 160,
     'data/evaluation/development_freezes/technical-v3-finalization-20261002/case_manifest.json',
     'data/evaluation/development_evaluations/technical-v3-development-eval-v1-20261002/labels',
     'labels_verbatim.jsonl', 'label_sha256', 'case_manifest_sha256'),
)
ALLOWED = frozenset(p for _, _, _, manifest, folder, review, _, _ in STUDIES
                    for p in (manifest, folder + '/label_freeze.json', folder + '/' + review))
IDENTITY = frozenset(('case_id', 'ticker', 'instrument_id', 'date', 'session_date'))
STRING = re.compile(r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"')
SCALAR = re.compile(r'(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def white(text, i):
    while i < len(text) and text[i] in ' \r\n\t':
        i += 1
    return i


def end_value(text, i):
    """Validate/skip a JSON value without decoding its non-authorized content."""
    i = white(text, i)
    require(i < len(text), 'Truncated JSON')
    if text[i] == '"':
        match = STRING.match(text, i)
        require(match is not None, 'Invalid JSON string')
        return match.end()
    if text[i] in '[{':
        obj = text[i] == '{'
        close = '}' if obj else ']'
        i = white(text, i + 1)
        if i < len(text) and text[i] == close:
            return i + 1
        while True:
            if obj:
                require(i < len(text) and text[i] == '"', 'Invalid JSON key')
                i = white(text, end_value(text, i))
                require(i < len(text) and text[i] == ':', 'Missing colon')
                i += 1
            i = white(text, end_value(text, i))
            require(i < len(text), 'Truncated JSON container')
            if text[i] == close:
                return i + 1
            require(text[i] == ',', 'Missing comma')
            i = white(text, i + 1)
    match = SCALAR.match(text, i)
    require(match is not None, 'Invalid JSON scalar')
    return match.end()


def fields(text, start=0):
    """Return key-to-span metadata; never deserialize unselected values."""
    i = white(text, start)
    require(i < len(text) and text[i] == '{', 'Expected JSON object')
    i = white(text, i + 1)
    result = {}
    while text[i] != '}':
        stop = end_value(text, i)
        key = json.loads(text[i:stop])
        require(isinstance(key, str) and key not in result, 'Duplicate/invalid JSON key')
        i = white(text, stop)
        require(text[i] == ':', 'Missing colon')
        begin = white(text, i + 1)
        stop = end_value(text, begin)
        result[key] = (begin, stop)
        i = white(text, stop)
        if text[i] == '}':
            break
        require(text[i] == ',', 'Missing comma')
        i = white(text, i + 1)
    return result


def selected(text, spans, keys):
    return {key: json.loads(text[a:b]) for key, (a, b) in spans.items() if key in keys}


def cases(text):
    spans = fields(text)
    require('cases' in spans, 'Manifest missing cases')
    begin, stop = spans['cases']
    require(text[begin] == '[', 'Manifest cases is not an array')
    i = white(text, begin + 1)
    while i < stop - 1:
        yield selected(text, fields(text, i), IDENTITY)
        i = white(text, end_value(text, i))
        if i < stop - 1:
            require(text[i] == ',', 'Missing case separator')
            i = white(text, i + 1)


def safe_path(root, ref):
    # Exact allowlist also denies unrelated files, future reservations and aliases.
    require(ref in ALLOWED, 'DENIED: source outside authorized nine-file allowlist')
    path = root / ref
    for p in (path, *path.parents):
        require(not p.is_symlink() and not p.is_junction(), 'DENIED: redirected source path')
        if p == root:
            break
    require(path.resolve().is_relative_to(root.resolve()), 'DENIED: path escapes root')
    return path


def read_source(root, ref):
    raw = safe_path(root, ref).read_bytes()
    text = raw.decode('utf-8-sig')
    return text, sha256(raw).hexdigest()


def project(root):
    studies = []
    for study, version, expected, manifest, folder, review, label_hash, manifest_hash in STUDIES:
        freeze_ref, review_ref = folder + '/label_freeze.json', folder + '/' + review
        frozen_text, freeze_sha = read_source(root, freeze_ref)
        freeze = selected(frozen_text, fields(frozen_text),
                          {'version', 'count', 'integrity_passed', label_hash, manifest_hash})
        require(freeze.get('integrity_passed') is True, study + ': freeze integrity unresolved')
        require(type(freeze.get('count')) is int and freeze['count'] == expected,
                study + ': reviewed count unresolved')
        manifest_text, manifest_sha = read_source(root, manifest)
        review_text, review_sha = read_source(root, review_ref)
        require(freeze.get(manifest_hash) == manifest_sha, study + ': manifest hash mismatch')
        require(freeze.get(label_hash) == review_sha, study + ': reviewed source hash mismatch')
        reviewed = []
        for line in review_text.splitlines():
            if line.strip():
                row = selected(line, fields(line), {'case_id'})
                require(set(row) == {'case_id'}, study + ': reviewed identity missing')
                reviewed.append(row['case_id'])
        require(len(reviewed) == len(set(reviewed)) == expected, study + ': duplicate/missing reviewed IDs')
        metadata = list(cases(manifest_text))
        ids = [r.get('case_id') for r in metadata]
        require(len(ids) == len(set(ids)) == expected, study + ': duplicate/missing manifest IDs')
        require(set(ids) == set(reviewed), study + ': reviewed/manifest ID sets differ')
        records = []
        for row in metadata:
            cid, ticker = row.get('case_id'), row.get('ticker')
            require(isinstance(cid, str) and re.fullmatch('[0-9a-f]{24}', cid), study + ': invalid case ID')
            require(isinstance(ticker, str) and re.fullmatch('[A-Z0-9]+', ticker), study + ': invalid ticker')
            day = row.get('session_date', row.get('date'))
            require(isinstance(day, str) and date.fromisoformat(day).isoformat() == day
                    and day < '2025-01-01', study + ': invalid/unauthorized stock-day')
            require(not (row.get('date') and row.get('session_date')) or row['date'] == row['session_date'],
                    study + ': conflicting stock-day')
            record = dict(case_id=cid, ticker=ticker, session_date=day, episode_scope='UNRESOLVED',
                          exclusion_reason='PREVIOUSLY_REVIEWED_CASE',
                          provenance_ref=[manifest + '#case_id=' + cid, review_ref + '#case_id=' + cid])
            if row.get('instrument_id') is not None:
                require(isinstance(row['instrument_id'], str) and bool(row['instrument_id'].strip()),
                        study + ': invalid instrument ID')
                record['instrument_id'] = row['instrument_id']
            records.append(record)
        records.sort(key=lambda r: (r['ticker'], r['session_date'], r['case_id']))
        studies.append(dict(protected_study_id=study, source_version=version,
                            review_source_version=freeze.get('version'),
                            source_ref=[freeze_ref, manifest, review_ref],
                            source_sha256={freeze_ref: freeze_sha, manifest: manifest_sha, review_ref: review_sha},
                            reviewed_case_count=len(reviewed), exported_case_count=len(records),
                            exported_unique_case_id_count=len(set(ids)),
                            exported_unique_stock_day_count=len({(r['ticker'], r['session_date']) for r in records}),
                            completeness_status='COMPLETE',
                            completeness_attestation={
                                'basis': 'Existing completed label freeze; exact reviewed/manifest ID-set equality; both source hashes verified against freeze.',
                                'freeze_integrity_passed': True, 'reviewed_manifest_id_sets_equal': True,
                                'reviewed_and_manifest_hashes_verified': True,
                                'scope': 'All cases in the named frozen reviewed study version; no claim for later reviews or other studies.',
                                'episode_scope': 'UNRESOLVED; no semantic reconstruction or inferred boundaries.'},
                            records=records))
    return sorted(studies, key=lambda s: s['protected_study_id'])


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def build(studies, created_at):
    require(len(studies) == 3 and {s['protected_study_id'] for s in studies} == {s[0] for s in STUDIES},
            'Incomplete study coverage')
    union, identities = {}, {}
    for study in studies:
        seen = set()
        for record in study['records']:
            cid = record['case_id']
            require(cid not in seen, 'Duplicate case ID')
            seen.add(cid)
            key = record['ticker'], record['session_date']
            require(cid not in identities or identities[cid] == key, 'Conflicting case identity')
            identities[cid] = key
            union.setdefault(key, []).append({'protected_study_id': study['protected_study_id'], 'case_id': cid})
    ledger = dict(ledger_version=VERSION, created_at=created_at,
                  authorized_scope=[{'protected_study_id': s['protected_study_id'], 'source_version': s['source_version']}
                                    for s in studies], studies=studies)
    projection = dict(ledger_version=VERSION, created_at=created_at,
                      ledger_sha256=sha256(canonical(ledger)).hexdigest(),
                      completeness_status='COMPLETE' if all(s['completeness_status'] == 'COMPLETE' for s in studies) else 'INCOMPLETE',
                      unique_stock_day_count=len(union), records=[dict(ticker=t, session_date=d,
                      protected_cases=sorted(refs, key=lambda r: (r['protected_study_id'], r['case_id'])))
                      for (t, d), refs in sorted(union.items())])
    return canonical(ledger), canonical(projection)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--created-at', required=True, help='Fixed UTC timestamp for reproducible rebuilds')
    args = parser.parse_args()
    stamp = datetime.fromisoformat(args.created_at)
    require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0, 'Use a UTC timestamp')
    dest = ROOT / OUT
    names = ('PROTECTED_CASE_EXCLUSION_LEDGER_V1.json', 'PROTECTED_STOCK_DAY_EXCLUSIONS_V1.json')
    require(not any((dest / n).exists() for n in names), 'Refuse to overwrite existing projection')
    studies = project(ROOT)
    first, second = build(studies, args.created_at), build(studies, args.created_at)
    require(first == second, 'Non-deterministic output')
    # Verify the actual projected identities fit the existing metadata contract.
    from src.evaluation.benchmark.admission import Scope
    # Schema validation requires no payload/source/certificate access.
    scope = Scope(source='b6b-schema-check', source_version=VERSION, snapshot_id='metadata-only',
                  authorized_path=str(dest.resolve()), instruments=[{'instrument_id': 'metadata-only', 'ticker': 'METADATA'}],
                  start='2020-01-01', end='2024-12-31', exchange='HOSE')
    admission_ledger(json.loads(first[0]), scope)
    dest.mkdir(parents=True, exist_ok=True)
    for name, payload in zip(names, first):
        with (dest / name).open('xb') as f:
            f.write(payload)
    print(json.dumps({'studies': [{k: s[k] for k in ('protected_study_id', 'reviewed_case_count',
        'exported_case_count', 'exported_unique_stock_day_count', 'completeness_status')} for s in studies],
        'unique_stock_days': json.loads(first[1])['unique_stock_day_count'],
        'sha256': {n: sha256(p).hexdigest() for n, p in zip(names, first)}, 'byte_identical_rebuild': True}))


if __name__ == '__main__':
    main()
