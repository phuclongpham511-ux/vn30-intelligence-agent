"""Local question → approved tools → verified Vietnamese answer. No external I/O."""
import hashlib
import json
import os
import sqlite3
from typing import Protocol

from pydantic import ValidationError

from routers.personal_research import require_personal_request
from src.schemas.financial_assistant import (
    AssistantAnswer, AssistantCitation, AssistantQuestion, AssistantUsage, GroundedFact, ModelDraft,
)
from src.services.financial_assistant_intent import METRIC_LABELS, UnsupportedQuestion, select_intent
from src.services.financial_journal import MetricJournal
from src.services.financial_tools import FinancialToolError, NativeFinancialTools
from src.services.personal_financials import configured_research_packet

MAX_ANSWER_BYTES = 65536
INTRO = 'Kết quả từ bằng chứng đã lưu, trong phạm vi nghiên cứu riêng tư.'


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':'))


def _identity(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


class FinancialAnswerModel(Protocol):
    """Future adapters need a separate egress decision; none is wired here."""
    kind: str
    external_io: bool

    def generate(self, context_json: str, *, max_output_tokens: int) -> str: ...


class DeterministicFinancialModel:
    kind = 'deterministic_mock'
    external_io = False

    def generate(self, context_json: str, *, max_output_tokens: int) -> str:
        context = json.loads(context_json)
        facts = context['facts']
        return ModelDraft(answer=INTRO + '\n' + '\n'.join(f['text'] for f in facts),
            fact_ids=[f['id'] for f in facts],
            evidence_ids=sorted({ref for f in facts for ref in f['evidence_ids']})).model_dump_json()


def _number(value):
    return 'chưa có giá trị đủ điều kiện' if value is None else str(value)


def render_fact(fact: GroundedFact):
    """Formatting only: no arithmetic, rounding, unit conversion or causal prose."""
    label = METRIC_LABELS.get(fact.metric, ('', fact.metric))[1]
    if fact.kind == 'statement':
        text = f'{fact.ticker}, kỳ {fact.period}: báo cáo dòng tiền đã lưu; trạng thái {fact.qualification_status}.'
    elif fact.kind == 'metric':
        text = (f'{fact.ticker}, {label}, kỳ {fact.period}: {_number(fact.values["value"])}'
            f' ({fact.unit}); trạng thái bằng chứng {fact.qualification_status}.')
    else:
        text = (f'{fact.ticker}, {label}, {fact.period} so với {fact.comparison_period}: '
            f'{_number(fact.values["current_value"])} so với {_number(fact.values["comparison_value"])} ({fact.unit}). ')
        if fact.qualification_status == 'COMPARABLE':
            text += (f'Thay đổi tuyệt đối: {_number(fact.values["absolute_change"])}; '
                f'tỷ lệ thay đổi dạng phân số: {_number(fact.values["percentage_change"])}. ')
        else:
            text += 'Chưa đủ bằng chứng tương thích để kết luận mức thay đổi. '
        text += f'Trạng thái so sánh: {fact.qualification_status}.'
    if fact.missing_information:
        text += ' Còn thiếu bằng chứng; xem missing_information.'
    if fact.evidence_ids:
        text += ' [' + ','.join(fact.evidence_ids) + ']'
    return text


def grounded_catalog(results):
    """Project actual tool outputs, never accept model-written facts or citations."""
    facts, citations, missing = [], {}, []
    for result in results:
        missing.extend(result.missing_information)
        base = dict(ticker=result.capture.ticker, source=result.capture.source,
            capture_id=result.capture.capture_id, frequency=result.frequency)
        def add(kind, period, refs, **fields):
            ids = []
            for ref in refs:
                raw = ref.model_dump(mode='json') if hasattr(ref, 'model_dump') else dict(ref)
                citation = AssistantCitation(id=_identity(dict(tool=result.tool, reference=raw)), tool=result.tool, reference=raw)
                citations[citation.id] = citation
                ids.append(citation.id)
            content = dict(base, kind=kind, period=period, evidence_ids=list(dict.fromkeys(ids)), **fields)
            facts.append(GroundedFact(id=_identity(content), **content))
            missing.extend(fields['missing_information'])
        for metric in result.metrics:
            add('metric', metric.period, metric.evidence_references,
                metric=metric.metric, unit=metric.unit, values=dict(value=metric.value), formula=metric.formula,
                qualification_status=metric.qualification_status, missing_information=metric.missing_information)
        for response in result.insights:
            for insight in response.insights:
                add('insight', insight.current_period, insight.evidence_references,
                    metric=insight.metric, unit=insight.unit, comparison_period=insight.comparison_period,
                    values={k: getattr(insight, k) for k in ('current_value', 'comparison_value', 'absolute_change', 'percentage_change')},
                    formula=insight.metric_formula, qualification_status=insight.qualification_status,
                    missing_information=insight.missing_information, attention_reasons=insight.attention_reason.criteria)
        for statement in result.statements:
            add('statement', statement.period, [statement.evidence], statement=statement.evidence.statement,
                qualification_status=statement.qualification_status, missing_information=statement.missing_information)
    if len(facts) > 8:
        raise UnsupportedQuestion('fact_limit')
    return facts, citations, list(dict.fromkeys(missing))


def verify_draft(draft, facts, citations):
    """Exact permitted wording closes numerical, citation and causality escapes."""
    catalog = {f.id: f for f in facts}
    if len(set(draft.fact_ids)) != len(draft.fact_ids) or set(draft.fact_ids) != set(catalog):
        return False
    selected = [catalog[key] for key in draft.fact_ids]
    expected_refs = sorted({key for fact in selected for key in fact.evidence_ids})
    return (draft.evidence_ids == expected_refs and set(expected_refs) <= set(citations)
        and draft.answer == INTRO + '\n' + '\n'.join(render_fact(fact) for fact in selected))


def plan_tools(intent, capture_id, periods):
    """Shared deterministic plan; a model cannot choose executable tools."""
    arguments = dict(ticker=intent.ticker, capture_id=capture_id, frequency=intent.frequency, periods=periods)
    plans = ([('get_financial_statements', dict(arguments, statement=intent.statement))] if intent.kind == 'statement' else
        [('get_financial_insights', dict(arguments, metrics=intent.metrics, comparison=intent.comparison))] if intent.kind == 'comparison' else
        [('get_financial_metrics', dict(arguments, metrics=intent.metrics))])
    if intent.kind == 'performance':
        plans.append(('get_financial_insights', dict(arguments, metrics=intent.metrics, comparison=intent.comparison)))
    return plans


def model_context(intent, facts):
    """Identical minimal context for local inference and synthetic evaluation."""
    return _json(dict(intent=intent.model_dump(mode='json'),
        facts=[dict(id=f.id, text=render_fact(f), evidence_ids=f.evidence_ids) for f in facts]))


class LocalFinancialAssistant:
    def __init__(self, request, *, model: FinancialAnswerModel | None = None):
        self.request = request
        self.model = model if model is not None else DeterministicFinancialModel()

    def ask(self, payload: dict) -> AssistantAnswer:
        require_personal_request(self.request)
        usage = AssistantUsage()
        try:
            question = AssistantQuestion.model_validate(payload)
            intent = select_intent(question.question)
        except (ValidationError, UnsupportedQuestion, TypeError, ValueError) as error:
            code = str(error) if isinstance(error, UnsupportedQuestion) else 'invalid_request'
            return self._decline('REJECTED', code, usage)
        if self.model.kind != 'deterministic_mock' or self.model.external_io is not False:
            return self._decline('REJECTED', 'external_model_disabled', usage, intent)
        if os.getenv('WOOFI_PERSONAL_FINANCIAL_READS') != 'sqlite':
            return self._decline('REJECTED', 'private_sqlite_mode_required', usage, intent)
        calls = 2 if intent.kind == 'performance' else 1
        if calls > question.budget.tool_calls or question.budget.model_calls < 1:
            return self._decline('REJECTED', 'request_budget_exceeded', usage, intent)
        try:
            packet, digest = configured_research_packet('', intent.ticker, frequency=intent.frequency,
                capture_id=question.capture_id)
            matches = [c for c in MetricJournal(os.environ['WOOFI_PERSONAL_SQLITE'], readonly=True).captures(
                ticker=intent.ticker, source=packet.source) if c['capture_sha256'] == digest
                and (question.capture_id is None or c['capture_id'] == question.capture_id)]
            if len(matches) != 1:
                raise ValueError('Ambiguous capture')
        except FileNotFoundError:
            return self._decline('UNAVAILABLE', 'saved_capture_unavailable', usage, intent)
        except ValueError as error:
            if str(error).startswith('Ambiguous'):
                return self._decline('NEEDS_CAPTURE', 'select_valid_immutable_capture', usage, intent)
            return self._decline('UNAVAILABLE', 'saved_evidence_invalid_or_unavailable', usage, intent)
        except (KeyError, TypeError, OSError, sqlite3.DatabaseError):
            return self._decline('UNAVAILABLE', 'saved_evidence_invalid_or_unavailable', usage, intent)
        periods = intent.periods or sorted({o.period for receipt in packet.reports.values()
            for o in receipt.observations if o.frequency == intent.frequency})[-1:]
        plans = plan_tools(intent, matches[0]['capture_id'], periods)
        tools = NativeFinancialTools(self.request)
        results = []
        try:
            for name, args in plans:
                usage.tool_calls += 1
                results.append(tools.invoke(name, args))
            facts, citations, missing = grounded_catalog(results)
        except (FinancialToolError, UnsupportedQuestion):
            return self._decline('UNAVAILABLE', 'tool_selection_or_evidence_unavailable', usage, intent,
                [name for name, _ in plans[:usage.tool_calls]])
        used_tools = [name for name, _ in plans]
        if not facts:
            return AssistantAnswer(status='UNAVAILABLE', answer=(
                'Chưa có báo cáo dòng tiền cho kỳ ' + ', '.join(periods) + ' trong capture đã chọn.'),
                used_tools=used_tools, missing_information=missing, intent=intent, usage=usage)
        context = model_context(intent, facts)
        # UTF-8 bytes conservatively charge token bounds in mock mode. No vendor
        # tokenizer, pricing assumption or external provider call is involved.
        usage.input_token_upper_bound = len(context.encode('utf-8')) + len(question.question.encode('utf-8'))
        if usage.input_token_upper_bound > question.budget.input_tokens:
            return self._decline('REJECTED', 'model_input_budget_exceeded', usage, intent, used_tools)
        usage.model_calls = 1
        status = 'ANSWERED'
        answer = INTRO + '\n' + '\n'.join(render_fact(f) for f in facts)
        try:
            raw = self.model.generate(context, max_output_tokens=question.budget.output_tokens)
            usage.output_token_upper_bound = len(raw.encode('utf-8'))
            if usage.output_token_upper_bound > question.budget.output_tokens:
                raise ValueError('Model output bound')
            draft = ModelDraft.model_validate_json(raw)
            if not verify_draft(draft, facts, citations):
                raise ValueError('Ungrounded draft')
            answer = draft.answer
        except Exception:
            # Adapter failures are untrusted too; never echo exception payloads.
            status = 'SAFE_FALLBACK'
            missing.append('model_draft_rejected_safe_template_used')
        result = AssistantAnswer(status=status, answer=answer, used_tools=used_tools, facts=facts,
            evidence_references=list(citations.values()), missing_information=missing, intent=intent, usage=usage)
        if len(result.model_dump_json().encode('utf-8')) > MAX_ANSWER_BYTES:
            return self._decline('REJECTED', 'answer_size_limit', usage, intent, used_tools)
        return result

    @staticmethod
    def _decline(status, code, usage, intent=None, used_tools=None):
        return AssistantAnswer(status=status, answer=(
            'Cần chọn capture bất biến phù hợp trước khi trả lời.' if status == 'NEEDS_CAPTURE' else
            'Câu hỏi hoặc dữ liệu nằm ngoài phạm vi prototype; chưa thể đưa ra kết luận có bằng chứng.'),
            missing_information=[code], intent=intent, usage=usage, used_tools=used_tools or [])
