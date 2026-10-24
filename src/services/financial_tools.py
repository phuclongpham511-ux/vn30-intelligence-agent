"""Offline read tools inside the existing loopback personal-research boundary.

No route registration, provider/LLM imports, execution tool or database writes.
The request and configured journal are trusted host context, never tool arguments.
"""
import json
import os
import sqlite3

from fastapi import Request
from pydantic import ValidationError

from routers.personal_research import require_personal_request
from src.analytics.financial_engine import financial_engine
from src.schemas.financial_tools import (
    CaptureReference, EvidenceReference, InsightsRequest, MetricFact, MetricsRequest,
    ScriptedAnswer, ScriptedQuestion, StatementFact, StatementsRequest, ToolResponse,
)
from src.services.financial_insights import SUPPORTED_METRICS
from src.services.financial_intelligence import metric_unit
from src.services.financial_journal import MetricJournal
from src.services.personal_financials import (
    configured_research_packet, personal_projection, saved_financial_insights,
)

MAX_REQUEST_BYTES = 8192
MAX_OUTPUT_BYTES = 524288
MAX_INVOCATIONS = 10
REQUEST_SCHEMAS = {
    'get_financial_statements': StatementsRequest,
    'get_financial_metrics': MetricsRequest,
    'get_financial_insights': InsightsRequest,
}


class FinancialToolError(ValueError):
    """Stable safe error codes; never include a database path or rejected payload."""


def tool_schemas():
    return {name: schema.model_json_schema() for name, schema in REQUEST_SCHEMAS.items()}


def _evidence(ref, capture):
    context = ref.get('source_context') or {}
    metadata = context.get('original_metadata') or {}
    field = metadata.get('fields', {}).get(ref.get('field'), {})
    return EvidenceReference(
        capture_id=capture.capture_id, capture_sha256=capture.capture_sha256,
        packet_sha256=capture.packet_sha256, source=ref['source'],
        statement=ref['statement'], period=ref['period'], field=ref.get('field'),
        code=ref.get('code'), value=ref.get('value') if context and context.get('display_rights') != 'prohibited' else None,
        currency=ref.get('currency', 'VND'), scope=ref.get('consolidation'), basis=ref.get('basis'),
        content_sha256=ref.get('content_sha256'), record_sha256=context.get('record_sha256'),
        document_sha256=metadata.get('binary_sha256'),
        original_unit=field.get('original_unit', context.get('original_unit')),
        amount_multiplier=field.get('multiplier', context.get('amount_multiplier')),
        period_start=context.get('period_start'), period_end=context.get('period_end'),
        page=field.get('page'))


class NativeFinancialTools:
    """One bounded question session; recheck current authorization on every call."""

    def __init__(self, request: Request):
        self.request = request
        self.invocations = 0

    def invoke(self, name: str, payload: dict) -> ToolResponse:
        require_personal_request(self.request)
        if os.getenv('WOOFI_PERSONAL_FINANCIAL_READS') != 'sqlite':
            raise FinancialToolError('private_sqlite_mode_required')
        if self.invocations >= MAX_INVOCATIONS:
            raise FinancialToolError('invocation_limit')
        self.invocations += 1
        try:
            size = len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8'))
            if size > MAX_REQUEST_BYTES:
                raise FinancialToolError('request_size_limit')
            if name not in REQUEST_SCHEMAS:
                raise FinancialToolError('unsupported_tool')
            selection = REQUEST_SCHEMAS[name].model_validate(payload)
        except (ValidationError, TypeError, ValueError) as error:
            if isinstance(error, FinancialToolError):
                raise
            raise FinancialToolError('invalid_request') from None
        try:
            packet, digest = configured_research_packet('', selection.ticker,
                frequency=selection.frequency, capture_id=selection.capture_id)
            journal = MetricJournal(os.environ['WOOFI_PERSONAL_SQLITE'], readonly=True)
            stored = next(c for c in journal.captures(ticker=selection.ticker, source=packet.source)
                if c['capture_id'] == selection.capture_id)
            capture = CaptureReference(ticker=packet.ticker, source=packet.source,
                source_version=packet.source_version, capture_id=selection.capture_id,
                capture_sha256=digest, packet_sha256=stored['packet_sha256'], is_fixture=packet.is_fixture)
            result = self._project(name, selection, packet, capture, journal.path)
            if len(result.model_dump_json().encode('utf-8')) > MAX_OUTPUT_BYTES:
                raise FinancialToolError('output_size_limit_reduce_selection')
            return result
        except FinancialToolError:
            raise
        except FileNotFoundError:
            raise FinancialToolError('capture_ticker_or_frequency_unavailable') from None
        except (ValueError, KeyError, TypeError, StopIteration, OSError, sqlite3.DatabaseError):
            raise FinancialToolError('saved_evidence_invalid_or_unavailable') from None

    def _project(self, name, selection, packet, capture, journal_path):
        kinds = [selection.statement] if isinstance(selection, StatementsRequest) else packet.reports
        available = sorted({o.period for kind in kinds for o in packet.reports[kind].observations
            if o.frequency == selection.frequency})
        periods = selection.periods if selection.periods is not None else available[-4:]
        missing = [f'missing_period:{p}' for p in periods if p not in available]
        response = ToolResponse(tool=name, capture=capture, frequency=selection.frequency,
            selected_periods=periods, available_periods=available, missing_information=missing)
        if isinstance(selection, StatementsRequest):
            receipt = packet.reports[selection.statement]
            if receipt.status != 'healthy':
                response.missing_information.append('statement_receipt:' + receipt.status)
            for obs in receipt.observations:
                if obs.frequency != selection.frequency or obs.period not in periods:
                    continue
                if len(obs.items) > 400:
                    raise FinancialToolError('statement_line_limit')
                context = obs.source_context
                withheld = context is None or context.display_rights == 'prohibited'
                reasons = list(obs.diagnostics)
                if withheld:
                    reasons.append('source_context_missing_or_display_prohibited')
                if obs.consolidation not in ('consolidated', 'standalone'):
                    reasons.append('reporting_scope')
                if obs.basis == 'unknown':
                    reasons.append('unknown_flow_basis')
                if any(line.value is None for line in obs.items):
                    reasons.append('missing_source_values')
                if any(line.semantic_status != 'reported' or line.unit == 'source_units' for line in obs.items):
                    reasons.append('unqualified_source_lines')
                ref = dict(source=obs.source, statement=obs.statement, period=obs.period,
                    currency=obs.currency, consolidation=obs.consolidation, basis=obs.basis,
                    content_sha256=(context.original_metadata.get('original_receipt_sha256', receipt.content_sha256)
                        if context else receipt.content_sha256),
                    source_context=context.model_dump(mode='json') if context else None)
                lines, line_evidence = [], []
                for line in obs.items:
                    fields = [field for field, code in obs.field_codes.items() if code == line.code]
                    field = fields[0] if len(fields) == 1 else None
                    evidence = _evidence(dict(ref, field=field, code=line.code, value=line.value), capture)
                    metadata = context.original_metadata if context else {}
                    if metadata.get('fields') and field not in metadata['fields']:
                        # A mixed-unit filing's first field is not a unit contract
                        # for an unrecognized line. Retain its normalized amount,
                        # but withhold the uninterpretable raw amount.
                        evidence = evidence.model_copy(update={'original_unit': None, 'amount_multiplier': None})
                    raw_known = evidence.original_unit is not None and evidence.amount_multiplier is not None
                    if not raw_known and line.raw_value is not None:
                        reasons.append('raw_unit_evidence_missing')
                    lines.append(line.model_copy(deep=True, update={
                        'value': None if withheld else line.value,
                        'raw_value': line.raw_value if not withheld and raw_known else None}))
                    line_evidence.append(evidence)
                statement_evidence = _evidence(ref, capture).model_copy(update={
                    'original_unit': None, 'amount_multiplier': None})
                response.statements.append(StatementFact(period=obs.period, frequency=obs.frequency,
                    scope=obs.consolidation, basis=obs.basis, currency=obs.currency, lines=lines,
                    line_evidence=line_evidence, evidence=statement_evidence,
                    missing_information=list(dict.fromkeys(reasons)),
                    qualification_status='WITHHELD' if withheld else 'UNQUALIFIED' if reasons else 'SOURCE_REPORTED'))
            return response
        authorization = 'task:financial-v6-personal-research:' + capture.capture_sha256
        if name == 'get_financial_insights':
            if set(selection.metrics) - set(SUPPORTED_METRICS):
                raise FinancialToolError('unsupported_insight_metric')
            for period in periods:
                insight = saved_financial_insights(journal_path, capture.capture_id,
                    authorization_reference=authorization, metrics=selection.metrics,
                    frequency=selection.frequency, comparison=selection.comparison, current_period=period)
                for item in insight.insights:
                    # Retain the engine's values, reasons and attention policy.
                    # Strip document text/URLs and raw metadata from tool evidence.
                    safe = []
                    for ref in item.evidence_references:
                        safe.append({k: v for k, v in ref.items() if k in {
                            'reference_id', 'role', 'source', 'statement', 'period', 'field',
                            'statement_line', 'value', 'original_value', 'original_unit', 'amount_multiplier',
                            'page', 'document_sha256', 'content_sha256', 'record_sha256', 'scope', 'basis',
                            'period_start', 'period_end', 'capture_id', 'capture_sha256', 'packet_sha256'}})
                    item.evidence_references = safe
                response.insights.append(insight)
            return response
        full = financial_engine(packet, frequency=selection.frequency, limit=40)
        projected = personal_projection(packet, frequency=selection.frequency, limit=40,
            authorization_reference=authorization)
        rows = {r['period']: r for r in full.rows}
        displayed = {r['period']: r for r in projected['rows']}
        verified = {r['period']: r['metrics'] for r in projected['verification']['periods']}
        known = {key for row in full.rows for key in row['calculations']}
        if set(selection.metrics) - known:
            raise FinancialToolError('unsupported_metric')
        for period in periods:
            for metric in selection.metrics:
                calc = rows.get(period, {}).get('calculations', {}).get(metric, {})
                refs = calc.get('inputs', [])
                grade = verified.get(period, {}).get(metric, {})
                value = displayed.get(period, {}).get(metric)
                reasons = list(grade.get('missing_evidence', []))
                if period not in rows:
                    reasons.append('missing_exact_period')
                # An individually reported fact may have unknown scope. A derived
                # result cannot treat unknown scopes as a compatible pair.
                reported = len(refs) == 1 and refs[0].get('field') == metric
                if not reported and (not refs or not {r.get('consolidation') for r in refs} <= {'consolidated', 'standalone'}):
                    value = None
                    reasons.append('unverified_reporting_scope_for_derived_metric')
                if calc.get('reason'):
                    reasons.append(calc['reason'])
                response.metrics.append(MetricFact(period=period, metric=metric, value=value,
                    unit=metric_unit(metric), formula=calc.get('formula'),
                    qualification_status=grade.get('status', 'UNAVAILABLE'),
                    display_eligible=value is not None, verification_dimensions=grade.get('dimensions', {}),
                    evidence_references=[_evidence(r, capture) for r in refs],
                    missing_information=list(dict.fromkeys(reasons))))
        return response


def answer_questions(tools: NativeFinancialTools, questions: list[ScriptedQuestion]) -> list[ScriptedAnswer]:
    """Explicit deterministic plans, never natural-language intent inference."""
    if not 1 <= len(questions) <= MAX_INVOCATIONS:
        raise FinancialToolError('question_count_limit')
    return [ScriptedAnswer(question=q.question, result=tools.invoke(q.tool, q.arguments)) for q in questions]
