"""Current acquisition decision preflight. Reads governance/cohort/B6 metadata only.

This is a blocked acquisition checkpoint, not a certificate issuer. No supplied
boolean, test result, or source website can certify an unacquired dataset.
"""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_technical_benchmark_smoke import verify_governance
from src.evaluation.benchmark.population import load_cohort
from src.evaluation.benchmark.exclusions import load_certified_ledger, HASHES

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'research/provenance/technical_data_readiness_v1/preflight.json'


def check():
    governance = verify_governance()
    cohort = load_cohort()
    ledger = load_certified_ledger()
    return {
        'version': 'technical-data-readiness-v1-20261004',
        'decision': 'REACQUIRE_CERTIFIED_DATA',
        'status': 'BLOCKED_BY_DATA_OR_PROVENANCE',
        'governance_hashes': governance,
        'cohort_sha256': cohort.normalized_cohort_sha256,
        'cohort_count': len(cohort.tickers),
        'B2': 'ELIGIBILITY_LOGIC_IMPLEMENTED; no real candidate listing/history certified',
        'B3': 'UNRESOLVED; no cutoff-safe price/volume comparability evidence',
        'B4': 'UNRESOLVED; no certified replacement snapshot acquired',
        'B5': 'UNRESOLVED; no verified session backbone for candidate windows',
        'B6': {'status': 'CERTIFIED_STOCK_DAY_EXCLUSIONS', 'artifact_sha256': HASHES,
               'counts': {s['protected_study_id']: s['exported_case_count'] for s in ledger['studies']},
               'episode_scope': 'UNRESOLVED; quarantine future candidate overlap rather than infer boundaries'},
        'real_data_PIT_prefix_check': 'NOT_RUN_NO_ADMITTED_DATA',
        'real_data_deterministic_rebuild': 'NOT_RUN_NO_ADMITTED_DATA',
        'benchmark_payload_loaded': False, 'official_generation_enabled': False,
        'remaining_evidence': [
            'Accessible bounded source/export with documented original price/volume units and vintage semantics',
            'Complete effective-dated corporate-action or equivalent comparability evidence for admitted windows',
            'Dated session evidence, exceptions and coverage sufficient to resolve admitted windows',
            'Historical listing identity and >=60 prior valid comparable sessions per representative candidate',
        ],
        'decision_basis': 'SOURCE_DECISION.md',
    }


def main():
    report = check()
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    if OUTPUT.exists():
        if OUTPUT.read_bytes() != raw:
            raise ValueError('Readiness checkpoint differs; create an explicitly versioned successor')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT.open('xb') as file:
            file.write(raw)
    print(json.dumps({'status': report['status'], 'decision': report['decision'],
                      'preflight_sha256': sha256(raw).hexdigest(), 'B6_counts': report['B6']['counts']}))


if __name__ == '__main__':
    main()
