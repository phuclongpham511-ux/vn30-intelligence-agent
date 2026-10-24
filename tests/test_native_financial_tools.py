"""Offline public tool seam: real services, temporary synthetic journal only."""
import hashlib
import socket
import sqlite3

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.analytics.financial_engine import financial_engine
from src.providers.reviewed_reports import report_packet
from src.schemas.financial_tools import ScriptedQuestion, ToolResponse
from src.services.financial_journal import MetricJournal
from src.services.financial_tools import (
    FinancialToolError, NativeFinancialTools, answer_questions, tool_schemas,
)
from src.services.personal_financials import saved_financial_insights
from test_free_financial_sources import reviewed
from test_personal_financials import source


def local_request(peer='127.0.0.1', host='127.0.0.1'):
    return Request(dict(type='http', scheme='http', method='POST', path='/',
        query_string=b'', headers=[(b'host', host.encode())], client=(peer, 1234), server=(host, 8432)))


@pytest.fixture
def pilot(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail('Offline pilot attempted network access')
    monkeypatch.setattr(socket.socket, 'connect', no_network)
    monkeypatch.setattr(socket.socket, 'connect_ex', no_network)
    packet, _ = report_packet(reviewed(tmp_path), tmp_path)
    journal = MetricJournal(tmp_path / 'synthetic.sqlite')
    journal.initialize()
    capture = journal.import_packet(packet, 'a' * 64)
    for key, value in dict(APP_ENV='development', WOOFI_PERSONAL_RESEARCH='1',
        WOOFI_PERSONAL_BIND='127.0.0.1', WOOFI_PERSONAL_FINANCIAL_READS='sqlite',
        WOOFI_PERSONAL_SQLITE=str(journal.path)).items():
        monkeypatch.setenv(key, value)
    return NativeFinancialTools(local_request()), journal, packet, capture


def selection(pilot, **kwargs):
    return dict(ticker='ABC', capture_id=pilot[3]['capture_id'], frequency='annual', **kwargs)


def test_tools_preserve_engine_values_formula_lineage_and_read_idempotency(pilot):
    tools, journal, packet, capture = pilot
    before = hashlib.sha256(journal.path.read_bytes()).hexdigest()
    payload = selection(pilot, metrics=['revenue', 'net_margin', 'free_cash_flow'], periods=['2025'])
    result = tools.invoke('get_financial_metrics', payload)
    assert result == tools.invoke('get_financial_metrics', payload)
    row = financial_engine(packet).rows[-1]
    assert [m.value for m in result.metrics] == [1000, .1, None]
    for fact in result.metrics:
        assert fact.value == row[fact.metric]
        assert fact.formula == row['calculations'][fact.metric]['formula']
        assert all(r.capture_id == capture['capture_id'] and r.capture_sha256 == 'a' * 64
            and r.packet_sha256 == journal.captures(ticker='ABC')[0]['packet_sha256'] for r in fact.evidence_references)
    assert result.metrics[0].qualification_status == 'PARTIALLY_VERIFIED'
    assert 'public_display_permission' in result.metrics[0].missing_information
    assert result.metrics[-1].missing_information
    assert hashlib.sha256(journal.path.read_bytes()).hexdigest() == before
    assert ToolResponse.model_validate_json(result.model_dump_json()) == result


def test_insight_values_attention_and_reasons_match_saved_insight_engine(pilot):
    tools, journal, _, capture = pilot
    result = tools.invoke('get_financial_insights', selection(pilot, metrics=['revenue'], periods=['2025']))
    expected = saved_financial_insights(journal.path, capture['capture_id'], metrics=['revenue'],
        current_period='2025', authorization_reference='task:financial-v6-personal-research:' + 'a' * 64)
    actual = result.insights[0].insights[0]
    original = expected.insights[0]
    assert actual.absolute_change == 200 and actual.percentage_change == .25
    assert actual.model_dump(exclude={'evidence_references'}) == original.model_dump(exclude={'evidence_references'})
    for ref, raw in zip(actual.evidence_references, original.evidence_references):
        assert ref == {k: raw[k] for k in ref}
    assert actual.evidence_references and actual.causal_explanation is None


def test_statement_lines_and_missing_exact_period_are_reported_without_filling(pilot):
    result = pilot[0].invoke('get_financial_statements', selection(pilot, statement='income', periods=['2025', '2026']))
    assert result.missing_information == ['missing_period:2026']
    assert len(result.statements) == 1
    fact = result.statements[0]
    assert fact.scope == 'consolidated' and fact.basis == 'annual'
    assert fact.lines == pilot[2].reports['income'].observations[-1].items
    assert fact.evidence.document_sha256 and fact.evidence.record_sha256
    assert all(ref.code == line.code and ref.page == 1 for line, ref in zip(fact.lines, fact.line_evidence))


def test_unknown_scope_is_not_comparable_and_unknown_specialist_kpis_are_rejected(pilot):
    tools, journal, _, _ = pilot
    packet = source('NH')
    capture = journal.import_packet(packet, 'b' * 64)
    payload = dict(ticker='ABC', capture_id=capture['capture_id'], frequency='annual', periods=['2025'])
    result = tools.invoke('get_financial_metrics', dict(payload, metrics=['operating_income', 'loan_deposit_ratio']))
    assert result.metrics[0].value is not None
    assert result.metrics[1].value is None
    assert 'unverified_reporting_scope_for_derived_metric' in result.metrics[1].missing_information
    insight = tools.invoke('get_financial_insights', dict(payload, metrics=['customer_loans']))
    assert insight.insights[0].insights[0].qualification_status == 'INSUFFICIENT_COMPARABLE_DATA'
    assert insight.insights[0].insights[0].absolute_change is None
    with pytest.raises(FinancialToolError, match='unsupported_metric'):
        tools.invoke('get_financial_metrics', dict(payload, metrics=['nim']))


def test_prohibited_source_values_and_raw_private_paths_do_not_escape(pilot):
    tools, journal, packet, _ = pilot
    for receipt in packet.reports.values():
        receipt.source_url = 'file:///private/original.pdf'
        for obs in receipt.observations:
            obs.source_context.display_rights = 'prohibited'
            obs.source_context.original_metadata['secret_path'] = 'C:/private/credentials.json'
    capture = journal.import_packet(packet, 'b' * 64)
    common = dict(ticker='ABC', capture_id=capture['capture_id'], frequency='annual', periods=['2025'])
    for name, extra in [('get_financial_statements', dict(statement='income')),
        ('get_financial_metrics', dict(metrics=['revenue'])),
        ('get_financial_insights', dict(metrics=['revenue']))]:
        result = tools.invoke(name, dict(common, **extra))
        text = result.model_dump_json()
        assert 'private/original' not in text and 'credentials.json' not in text and 'secret_path' not in text
        assert all(line.value is None and line.raw_value is None for row in result.statements for line in row.lines)
        assert all(m.value is None and all(r.value is None for r in m.evidence_references) for m in result.metrics)
        assert all(i.current_value is None and all(r.get('value') is None and r.get('original_value') is None
            for r in i.evidence_references) for response in result.insights for i in response.insights)


@pytest.mark.parametrize('change', [dict(ticker='../ABC'), dict(capture_id='SELECT * FROM financial_capture'),
    dict(path='C:/private/financial.sqlite'), dict(sql='SELECT 1'), dict(url='https://example.test'),
    dict(periods=['2025', '2025']), dict(periods=['2025-Q1']), dict(metrics=['revenue'] * 9),
    dict(periods=['2021', '2022', '2023', '2024', '2025']), dict(frequency='ttm')])
def test_tool_arguments_are_closed_and_bounded(pilot, change):
    with pytest.raises(FinancialToolError, match='invalid_request'):
        pilot[0].invoke('get_financial_metrics', dict(selection(pilot, metrics=['revenue']), **change))


@pytest.mark.parametrize('change', [dict(ticker='XYZ'), dict(capture_id='0' * 64), dict(frequency='quarterly')])
def test_wrong_ticker_capture_and_frequency_fail_without_fallback(pilot, change):
    with pytest.raises(FinancialToolError, match='unavailable'):
        pilot[0].invoke('get_financial_metrics', dict(selection(pilot, metrics=['revenue']), **change))


@pytest.mark.parametrize('variable,value', [('APP_ENV', 'production'), ('WOOFI_PERSONAL_RESEARCH', '0'),
    ('WOOFI_PERSONAL_BIND', '0.0.0.0')])
def test_authorization_is_rechecked_on_every_invocation(pilot, monkeypatch, variable, value):
    pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))
    monkeypatch.setenv(variable, value)
    with pytest.raises(HTTPException) as denied:
        pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))
    assert denied.value.status_code == 404


@pytest.mark.parametrize('peer,host', [('203.0.113.1', '127.0.0.1'), ('127.0.0.1', 'example.test')])
def test_remote_socket_or_host_cannot_access_tools(pilot, peer, host):
    with pytest.raises(HTTPException):
        NativeFinancialTools(local_request(peer, host)).invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))


def test_size_and_call_limits_fail_explicitly_without_partial_output(pilot, monkeypatch):
    with pytest.raises(FinancialToolError, match='request_size_limit'):
        pilot[0].invoke('get_financial_metrics', dict(selection(pilot, metrics=['revenue']), extra='x' * 8192))
    monkeypatch.setattr('src.services.financial_tools.MAX_OUTPUT_BYTES', 50)
    with pytest.raises(FinancialToolError, match='output_size_limit'):
        pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))
    monkeypatch.setattr('src.services.financial_tools.MAX_OUTPUT_BYTES', 524288)
    for _ in range(8):
        pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))
    with pytest.raises(FinancialToolError, match='invocation_limit'):
        pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))


def test_scripted_answers_contain_actual_typed_outputs_and_schema_contracts(pilot):
    question = ScriptedQuestion(question='What changed in annual results?', tool='get_financial_insights',
        arguments=selection(pilot, metrics=['revenue'], periods=['2025']))
    answer = answer_questions(pilot[0], [question])[0]
    assert answer.question == question.question
    assert answer.result.insights[0].insights[0].absolute_change == 200
    assert 'do not establish causes' in answer.explanation
    assert set(tool_schemas()) == {'get_financial_statements', 'get_financial_metrics', 'get_financial_insights'}
    assert all(s['additionalProperties'] is False for s in tool_schemas().values())
    with pytest.raises(FinancialToolError, match='question_count_limit'):
        answer_questions(pilot[0], [question] * 11)


def test_public_routes_do_not_register_or_serialize_native_tools(pilot):
    from main import app
    from src.services.financial_presentation import display_financial_response
    assert not any('get_financial_' in path or 'ai-tools' in path for path in app.openapi()['paths'])
    public = display_financial_response(financial_engine(pilot[2])).model_dump_json()
    assert pilot[3]['capture_id'] not in public and 'woofi-native-financial-tools' not in public
    assert all(m.value is None for m in display_financial_response(financial_engine(pilot[2])).fundamental_summary.metrics)


def test_each_connection_is_readonly_and_no_sql_write_is_attempted(pilot, monkeypatch):
    original = sqlite3.connect
    connections = []
    forbidden = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
        sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE,
        sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
    def read_only_connection(database, *args, **kwargs):
        assert database.endswith('?mode=ro') and kwargs.get('uri') is True
        connection = original(database, *args, **kwargs)
        def authorize(action, *_):
            assert action not in forbidden, 'Tool attempted a database write or attach'
            return sqlite3.SQLITE_OK
        connection.set_authorizer(authorize)
        connections.append(database)
        return connection
    monkeypatch.setattr(sqlite3, 'connect', read_only_connection)
    pilot[0].invoke('get_financial_statements', selection(pilot, statement='income'))
    pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))
    pilot[0].invoke('get_financial_insights', selection(pilot, metrics=['revenue']))
    assert connections


def test_missing_journal_configuration_is_sanitized_and_never_creates_database(pilot, monkeypatch, tmp_path):
    missing = tmp_path / 'private-new.sqlite'
    monkeypatch.setenv('WOOFI_PERSONAL_SQLITE', str(missing))
    with pytest.raises(FinancialToolError) as error:
        pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))
    assert str(missing) not in str(error.value) and not missing.exists()
    monkeypatch.setenv('WOOFI_PERSONAL_FINANCIAL_READS', 'captures')
    with pytest.raises(FinancialToolError, match='private_sqlite_mode_required'):
        pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue']))


def test_zero_is_preserved_and_different_revisions_are_never_spliced(pilot, tmp_path):
    from test_financial_insights import replace_amount
    evidence = reviewed(tmp_path)
    replace_amount(evidence, 'revenue', ['0', '800'])
    packet, _ = report_packet(evidence, tmp_path)
    capture = pilot[1].import_packet(packet, 'b' * 64)
    first = pilot[0].invoke('get_financial_metrics', selection(pilot, metrics=['revenue'], periods=['2025']))
    second = pilot[0].invoke('get_financial_metrics', dict(selection(pilot, metrics=['revenue'], periods=['2025']), capture_id=capture['capture_id']))
    assert first.metrics[0].value == 1000 and second.metrics[0].value == 0
    assert first.capture.capture_id != second.capture.capture_id
    assert all(r.value == 0 and r.capture_id == capture['capture_id'] for r in second.metrics[0].evidence_references)


def test_statement_preserves_per_line_original_units_and_page_in_mixed_unit_filing(pilot, tmp_path):
    evidence = reviewed(tmp_path)
    page = evidence['pages'][0]
    page['text'] += '\nthousand VND'
    page['text_sha256'] = hashlib.sha256(page['text'].encode()).hexdigest()
    for amount in evidence['amounts']:
        if amount['field'] == 'gross_profit':
            amount.update(unit='thousand VND', unit_quote=dict(page=1, text='thousand VND'))
    packet, _ = report_packet(evidence, tmp_path)
    capture = pilot[1].import_packet(packet, 'b' * 64)
    result = pilot[0].invoke('get_financial_statements', dict(selection(pilot, statement='income', periods=['2025']),
        capture_id=capture['capture_id']))
    fact = result.statements[0]
    lines = {line.code: line for line in fact.lines}
    refs = {ref.code: ref for ref in fact.line_evidence}
    assert lines['row:gross_profit'].value == 300000 and lines['row:gross_profit'].raw_value == 300
    assert refs['row:gross_profit'].original_unit == 'thousand VND'
    assert refs['row:gross_profit'].amount_multiplier == 1000
    assert refs['row:gross_profit'].page == 1 and refs['row:gross_profit'].field == 'gross_profit'
    assert refs['row:revenue'].original_unit == 'VND' and refs['row:revenue'].amount_multiplier == 1
    assert fact.evidence.original_unit is None and fact.evidence.amount_multiplier is None
