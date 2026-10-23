"""Private, deterministic changes over existing engine outputs; no acquisition."""
from calendar import monthrange
from datetime import date
import math
from statistics import median

from src.analytics.financial_catalog import specialist_consistency
from src.analytics.financial_engine import compatible_refs, finite_result, financial_engine, previous
from src.providers.vnstock.financial_statements import content_hash
from src.schemas.financial_intelligence import FinancialAttention, FinancialInsight, FinancialInsightsResponse
from src.services.financial_intelligence import metric_unit
from src.services.financial_journal import _digest
from src.services.financial_verification import verification_dimensions
from src.services.personal_financials import personal_projection

SUPPORTED_METRICS = (
    'revenue', 'operating_income', 'net_profit', 'cash_operating', 'total_assets',
    'total_liabilities', 'equity', 'total_debt', 'gross_margin', 'net_margin',
    'debt_equity', 'liabilities_assets', 'customer_loans', 'customer_deposits',
    'loan_deposit_ratio', 'demand_deposit_share', 'npl_classified_ratio', 'classified_loan_coverage',
)


def _period_reasons(ref):
    """Validate reported boundaries, not dates inferred from a period label."""
    ctx = ref.get('source_context') or {}
    period = ref['period']
    year, quarter = int(period[:4]), int(period[-1]) if '-Q' in period else None
    month = quarter * 3 if quarter else 12
    end = date(year, month, monthrange(year, month)[1]).isoformat()
    balance = ref['statement'] == 'balance'
    basis = 'point_in_time' if balance else 'standalone' if quarter else 'annual'
    reasons = []
    if ref.get('basis') != basis:
        reasons.append('incompatible_period_basis')
    start = None if balance else date(year, month - 2 if quarter else 1, 1).isoformat()
    if (ctx.get('period_end') != end or ctx.get('period_start') != start
            or ctx.get('fiscal_year') != year or ctx.get('fiscal_quarter') != quarter):
        reasons.append('unverified_fiscal_boundaries')
    return reasons


def _source_line(packet, ref):
    observation = next((o for o in packet.reports[ref['statement']].observations if o.period == ref['period']), None)
    lines = [line for line in observation.items if line.code == ref.get('code')] if observation else []
    return lines[0] if len(lines) == 1 else None


def _pair_reasons(packet, current, prior, metric, current_value, prior_value):
    reasons = []
    if current_value is None:
        reasons.append('current_value_unavailable_or_withheld')
    if prior_value is None:
        reasons.append('comparison_value_unavailable_or_withheld')
    if current is None or prior is None:
        reasons.append('missing_exact_comparison_period' if prior is None else 'missing_current_period')
        return reasons
    calculations = [r['calculations'][metric] for r in (current, prior)]
    refs = [ref for calc in calculations for ref in calc['inputs']]
    if not refs or any(calc.get('reason') for calc in calculations):
        reasons.append('incomplete_metric_inputs')
    if len({calc['formula'] for calc in calculations}) != 1:
        reasons.append('incompatible_financial_definition')
    if not compatible_refs(refs):
        reasons.append('incompatible_source_scope_or_document_revision')
    if not refs or not {r.get('consolidation') for r in refs} <= {'consolidated', 'standalone'}:
        reasons.append('unverified_reporting_scope')
    signatures = []
    for calc in calculations:
        signatures.append({(r['statement'], r['field'], r.get('code'), r.get('basis'), metric_unit(r['field']))
            for r in calc['inputs']})
    if signatures[0] != signatures[1]:
        reasons.append('incompatible_financial_definition_or_basis')
    for ref in refs:
        ctx = ref.get('source_context') or {}
        line = _source_line(packet, ref)
        if (line is None or line.semantic_status != 'reported' or line.unit != metric_unit(ref['field'])
                or line.value != ref.get('value')):
            reasons.append('source_line_mapping_unverified')
        original = ctx.get('original_metadata', {}).get('fields', {}).get(ref['field'], {})
        money_units = {'VND', 'thousand VND', 'million VND', 'billion VND'}
        if (ref.get('currency') != 'VND' or ctx.get('original_currency') != 'VND'
                or ctx.get('original_unit') not in money_units
                or original.get('original_unit', ctx.get('original_unit')) not in money_units):
            reasons.append('unverified_currency_or_units')
        if not ref.get('code') or not ref.get('content_sha256') or not ctx.get('record_sha256'):
            reasons.append('incomplete_source_identity')
        if (any(ctx.get('original_metadata', {}).get(key) == 'FAIL'
                for key in ('balance_identity', 'cash_flow_identity')) or not specialist_consistency(ref)):
            reasons.append('statement_consistency_failed')
        reasons.extend(_period_reasons(ref))
    return list(dict.fromkeys(reasons))


def _evidence(packet, refs, role):
    evidence = []
    for ref in refs:
        ctx = ref.get('source_context') or {}
        meta = ctx.get('original_metadata') or {}
        field = (meta.get('fields') or {}).get(ref['field'], {})
        allowed = ctx.get('display_rights') != 'prohibited' and not packet.is_fixture
        line = _source_line(packet, ref)
        evidence.append(dict(reference_id=content_hash(dict(role=role, input=ref)),
            role=role, source=ref['source'], statement=ref['statement'],
            period=ref['period'], field=ref['field'], statement_line=ref.get('code'),
            value=ref.get('value') if allowed else None,
            original_value=field.get('original_value', line.raw_value if line else None) if allowed else None,
            original_unit=field.get('original_unit', ctx.get('original_unit')),
            original_label=field.get('label', line.name_vi if line else None),
            amount_multiplier=field.get('multiplier', ctx.get('amount_multiplier')),
            page=field.get('page'), source_row=field.get('source_row') if allowed else None,
            column_header=field.get('column_header') if allowed else None,
            period_quote=field.get('period_quote') if allowed else None,
            source_url=meta.get('document_url') or packet.reports[ref['statement']].source_url,
            document_sha256=meta.get('binary_sha256'), content_sha256=ref.get('content_sha256'),
            record_sha256=ctx.get('record_sha256'),
            page_evidence=meta.get('page_evidence', {}).get(str(field.get('page'))),
            scope=ref.get('consolidation'), basis=ref.get('basis'),
            period_start=ctx.get('period_start'), period_end=ctx.get('period_end')))
    return evidence


def _reaches(value, threshold):
    # Inclusive policy thresholds tolerate only floating-point roundoff.
    return value >= threshold or math.isclose(value, threshold, rel_tol=1e-12, abs_tol=0.)


def _attention(change, percentage, before, after, unit):
    attention = FinancialAttention()
    if change is None:
        return attention
    if before * after < 0:
        attention.criteria.append('SIGN_REVERSAL')
    if before == 0 and after != 0:
        attention.criteria.append('ZERO_BASE_MOVEMENT')
    if unit == 'fraction' and _reaches(abs(change), attention.thresholds['fraction_change']):
        attention.criteria.append('FRACTION_MOVEMENT')
    elif unit == 'multiple' and _reaches(abs(change), attention.thresholds['multiple_change']):
        attention.criteria.append('MULTIPLE_MOVEMENT')
    elif unit not in ('fraction', 'multiple') and percentage is not None and _reaches(abs(percentage), attention.thresholds['relative_movement']):
        attention.criteria.append('RELATIVE_MOVEMENT')
    attention.noteworthy = bool(attention.criteria)
    return attention


def _historical_attention(packet, rows, displayed, current, metric, comparison, attention, delta):
    """Earlier exact-period changes only, all compatible with this observation."""
    evidence = []
    if delta is None:
        return evidence
    for period, row in sorted(rows.items()):
        if period >= current['period']:
            continue
        prior_period = previous(period, years=1) if comparison == 'yoy' else previous(period, quarters=1)
        prior = rows.get(prior_period)
        after = displayed.get(period, {}).get(metric)
        before = displayed.get(prior_period, {}).get(metric)
        if (_pair_reasons(packet, row, prior, metric, after, before)
                or _pair_reasons(packet, current, row, metric, displayed[current['period']].get(metric), after)):
            continue
        change = finite_result(after - before)
        if change is None:
            continue
        refs = row['calculations'][metric]['inputs'] + prior['calculations'][metric]['inputs']
        linked = _evidence(packet, refs, 'history')
        evidence.extend(linked)
        attention.historical_comparisons.append(dict(current_period=period,
            comparison_period=prior_period, absolute_change=change,
            evidence_reference_ids=[r['reference_id'] for r in linked]))
    if len(attention.historical_comparisons) >= attention.thresholds['minimum_historical_changes']:
        baseline = median(abs(p['absolute_change']) for p in attention.historical_comparisons)
        attention.historical_status = 'ASSESSED'
        attention.historical_median_absolute_change = baseline
        if abs(delta) > baseline and _reaches(abs(delta), attention.thresholds['historical_multiplier'] * baseline):
            attention.criteria.append('UNUSUAL_HISTORICAL_MOVEMENT')
            attention.noteworthy = True
    return list({r['reference_id']: r for r in evidence}.values())


def financial_insights(packet, *, metrics=None, frequency='annual', comparison='yoy',
                       current_period=None, authorization_reference):
    """Describe private facts and exact compatible changes, never infer causes."""
    if not isinstance(authorization_reference, str) or not authorization_reference.strip():
        raise ValueError('Financial insights require explicit private research authorization')
    if frequency not in ('annual', 'quarterly') or comparison not in ('yoy', 'qoq') or frequency == 'annual' and comparison == 'qoq':
        raise ValueError('Supported comparisons are annual YoY, quarterly YoY and quarterly QoQ')
    metrics = list(SUPPORTED_METRICS if metrics is None else metrics)
    if not metrics or len(set(metrics)) != len(metrics) or set(metrics) - set(SUPPORTED_METRICS):
        raise ValueError('Choose distinct supported financial metrics')
    full = financial_engine(packet, frequency=frequency, limit=40)
    private = personal_projection(packet, frequency=frequency, limit=40, authorization_reference=authorization_reference)
    raw_rows = {row['period']: row for row in full.rows}
    displayed = {row['period']: row for row in private['rows']}
    period = current_period or max(raw_rows, default=None)
    if period is not None and (not isinstance(period, str) or len(period) != (4 if frequency == 'annual' else 7)
            or not period[:4].isdigit() or not 1900 <= int(period[:4]) <= 2200
            or frequency == 'quarterly' and period[4:] not in ('-Q1', '-Q2', '-Q3', '-Q4')):
        raise ValueError('Current period must match the selected frequency')
    prior_period = previous(period, years=1) if period and comparison == 'yoy' else previous(period, quarters=1) if period else None
    current, prior = raw_rows.get(period), raw_rows.get(prior_period)
    insights = []
    for metric in metrics:
        after = displayed.get(period, {}).get(metric)
        before = displayed.get(prior_period, {}).get(metric)
        reasons = _pair_reasons(packet, current, prior, metric, after, before)
        current_refs = current['calculations'][metric]['inputs'] if current else []
        prior_refs = prior['calculations'][metric]['inputs'] if prior else []
        delta = finite_result(after - before) if not reasons else None
        percentage = finite_result(delta / before) if delta is not None and before > 0 else None
        if not reasons and delta is None:
            reasons.append('nonfinite_change')
        missing = list(reasons)
        if delta is not None and before <= 0:
            missing.append('percentage_change_requires_positive_comparison_value')
        refs = current_refs + prior_refs
        dimensions = verification_dimensions(refs, computable=after is not None, fixture=packet.is_fixture)
        if not dimensions['POINT_IN_TIME_VERIFIED']:
            missing.append('qualified_publication_timestamp')
        if not dimensions['PUBLICATION_RIGHTS_APPROVED']:
            missing.append('public_display_permission')
        missing.append('cause_not_established_by_numerical_movement')
        attention = _attention(delta, percentage, before, after, metric_unit(metric))
        history_evidence = _historical_attention(packet, raw_rows, displayed, current, metric,
            comparison, attention, delta)
        if attention.historical_status == 'INSUFFICIENT_COMPARABLE_DATA':
            missing.append('historical_unusualness_requires_five_compatible_prior_changes')
        insights.append(FinancialInsight(ticker=packet.ticker, metric=metric, unit=metric_unit(metric),
            metric_formula=current['calculations'][metric]['formula'] if current else None,
            current_period=period, comparison_period=prior_period, current_value=after, comparison_value=before,
            absolute_change=delta, percentage_change=percentage,
            observed_change=('INCREASE' if delta > 0 else 'DECREASE' if delta < 0 else 'UNCHANGED') if delta is not None
                else 'OBSERVATION_ONLY' if after is not None else 'UNAVAILABLE',
            attention_reason=attention,
            evidence_references=_evidence(packet, current_refs, 'current') + _evidence(packet, prior_refs, 'comparison') + history_evidence,
            missing_information=list(dict.fromkeys(missing)),
            qualification_status='COMPARABLE' if not reasons else 'INSUFFICIENT_COMPARABLE_DATA',
            verification_dimensions=dimensions))
    return FinancialInsightsResponse(ticker=packet.ticker, source=packet.source, frequency=frequency,
        comparison=comparison, authorization_reference=authorization_reference,
        packet_sha256=_digest(packet.model_dump(mode='json')), is_fixture=packet.is_fixture, insights=insights)
