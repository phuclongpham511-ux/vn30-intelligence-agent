"""Evidence grades and activation eligibility; never a financial calculator."""
from collections import Counter
import math

STATUSES = ('VERIFIED', 'PARTIALLY_VERIFIED', 'UNAVAILABLE')
DIMENSIONS = ('SOURCE_VERIFIED', 'ACCOUNTING_VERIFIED', 'POINT_IN_TIME_VERIFIED',
              'PUBLICATION_RIGHTS_APPROVED', 'FULLY_VERIFIED')


def verification_dimensions(refs, *, computable, fixture=False):
    """Independent evidence decisions. None of these flags authorizes a value.

    Source verification authenticates the reviewed extraction and original units,
    not the accuracy of every issuer disclosure. Accounting adds compatible
    scope, fiscal boundaries and the applicable statement consistency check.
    Publication knowledge and redistribution permission are separate dimensions.
    """
    contexts = [r.get('source_context') or {} for r in refs]
    source = bool(refs) and computable and not fixture
    for ref, ctx in zip(refs, contexts):
        meta = ctx.get('original_metadata') or {}
        field = (meta.get('fields') or {}).get(ref.get('field'), {})
        source &= bool(ref.get('source') and ref.get('code') and ref.get('content_sha256')
            and ctx.get('record_sha256') and ctx.get('original_currency') == 'VND'
            and (field.get('original_unit') or ctx.get('original_unit'))
            and ctx.get('unit_evidence') == 'original_filing'
            and meta.get('extraction_verified') is True and meta.get('page_image_verified') is True
            and meta.get('binary_sha256'))
    accounting = bool(source and len({r.get('source') for r in refs}) == 1
        and len({r.get('consolidation') for r in refs}) == 1
        and {r.get('consolidation') for r in refs} <= {'consolidated', 'standalone'}
        and all(c.get('period_end') and (r.get('statement') == 'balance' or c.get('period_start'))
            and r.get('basis') in ('annual', 'standalone', 'ytd', 'point_in_time')
            and (r.get('statement') != 'balance' or c.get('original_metadata', {}).get('balance_identity') == 'PASS')
            and (r.get('statement') != 'cash' or c.get('original_metadata', {}).get('cash_flow_identity') == 'PASS')
            and (r.get('field') not in ('cash_beginning','cash_ending') or c.get('original_metadata', {}).get('cash_endpoint_identity') == 'PASS')
            for r,c in zip(refs,contexts)))
    pit = accounting and all(c.get('publication_time_qualified') is True for c in contexts)
    rights = bool(refs) and not fixture and all(c.get('display_rights') == 'permitted'
        and bool((c.get('display_rights_reference') or '').strip()) for c in contexts)
    return dict(SOURCE_VERIFIED=bool(source), ACCOUNTING_VERIFIED=accounting,
        POINT_IN_TIME_VERIFIED=pit, PUBLICATION_RIGHTS_APPROVED=rights,
        FULLY_VERIFIED=bool(source and accounting and pit and rights))


def verification_assessment(result, displayed_rows, *, audience):
    """Grade the canonical engine evidence separately from display permission.

    A reproducible provider number is partial evidence, not an original filing.
    These grades cannot grant access or place a withheld value into a response.
    """
    displayed = {row['period']: row for row in displayed_rows}
    periods = []
    for row in result.rows:
        metrics = {}
        for key, calculation in row.get('calculations', {}).items():
            refs = calculation.get('inputs', [])
            contexts = [ref.get('source_context') or {} for ref in refs]
            missing = []
            reason = calculation.get('reason')
            raw_value = row.get(key)
            computable = (type(raw_value) in (int, float) and math.isfinite(raw_value)
                and not reason and bool(refs) and not result.is_fixture)
            if not computable:
                missing.append('synthetic_not_real_evidence' if result.is_fixture else reason or 'required_source_fields')
            if not refs or any(not r.get('code') or not r.get('content_sha256') for r in refs):
                missing.append('source_identity_and_hash')
            scopes = {r.get('consolidation') for r in refs}
            if not scopes or not scopes <= {'consolidated', 'standalone'}:
                missing.append('reporting_scope')
            if len(scopes) > 1:
                missing.append('compatible_reporting_scope')
            if not contexts or any(not c.get('original_unit') for c in contexts):
                missing.append('original_unit')
            if not contexts or any(not c.get('original_currency') for c in contexts):
                missing.append('original_currency')
            if not contexts or any(not c.get('period_end') or
                    r.get('statement') != 'balance' and not c.get('period_start')
                    for r, c in zip(refs, contexts)):
                missing.append('fiscal_boundaries')
            if not contexts or any(c.get('publication_time_qualified') is not True for c in contexts):
                missing.append('qualified_publication_timestamp')
            if not contexts or any(c.get('unit_evidence') != 'original_filing'
                    or c.get('original_metadata', {}).get('extraction_verified') is not True
                    or c.get('original_metadata', {}).get('page_image_verified') is not True
                    or not c.get('original_metadata', {}).get('binary_sha256')
                    for c in contexts):
                missing.append('original_document_verification')
            public_permission = bool(contexts) and all(c.get('display_rights') == 'permitted'
                and bool((c.get('display_rights_reference') or '').strip()) for c in contexts)
            if not public_permission:
                missing.append('public_display_permission')
            # Rights and verification remain separate: even a verified original
            # fact does not acquire redistribution permission from this grade.
            evidence_missing = [m for m in missing if m != 'public_display_permission']
            grade = 'UNAVAILABLE' if not computable else 'PARTIALLY_VERIFIED' if evidence_missing else 'VERIFIED'
            displayed_value = displayed.get(row['period'], {}).get(key)
            eligible = (not result.is_fixture and type(displayed_value) in (int, float)
                and math.isfinite(displayed_value) and displayed_value == raw_value)
            metrics[key] = dict(status=grade, display_eligible=eligible,
                public_display_eligible=eligible and audience == 'public' and public_permission,
                missing_evidence=list(dict.fromkeys(missing)),
                dimensions=verification_dimensions(refs, computable=computable, fixture=result.is_fixture))
        periods.append(dict(period=row['period'], metrics=metrics))
    latest = periods[-1]['metrics'] if periods else {}
    counts = Counter(m['status'] for m in latest.values())
    return dict(contract='financial-verification-v1', ticker=result.ticker,
        frequency=result.period_type, audience=audience,
        statuses={s: counts.get(s, 0) for s in STATUSES},
        displayed_metric_ids=sorted(k for k, m in latest.items() if m['display_eligible']),
        dimension_counts={key: sum(m['dimensions'][key] for m in latest.values()) for key in DIMENSIONS},
        periods=periods, point_in_time_qualified=False)
