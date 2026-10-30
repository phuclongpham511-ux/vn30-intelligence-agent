"""Controlled pilot through real adapters and isolated journals; synthetic sources only."""
import copy
import hashlib
import json

import httpx
import pytest

from src.services.financial_collector import _json, _sha, download_document, run_collector, validate_plan
from src.services.financial_coverage import build_coverage
from src.services.financial_journal import MetricJournal
from test_financial_storage import history_packet
from test_free_financial_sources import reviewed


def packet(ticker, quarters=2, start=2025 * 4):
    value = history_packet(quarters, start=start)
    value.ticker = ticker
    for receipt in value.reports.values():
        for obs in receipt.observations:
            obs.ticker = ticker
    return value


def setup(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    backlog = build_coverage(journal.path, as_of='2026-10-22')
    candidates = [dict(id=t.lower(), ticker=t, kind='vci', title='Synthetic financial data',
        issuer='Synthetic company', url='https://example.test/' + t, discovery_url='https://example.test/ir',
        reporting_period='latest four periods', document_type='sdk_capture',
        access='public_no_login', access_notes='synthetic public source', published_date=None) for t in ('HDB', 'MSN', 'VJC')]
    plan = dict(contract='financial-collector-plan-v57', backlog_sha256=_sha(_json(backlog)),
        as_of='2026-10-22', task_ids=[t['task_id'] for t in backlog['acquisition_backlog']
            if t['priority'] == 'P0' and t['ticker'] in ('HDB', 'MSN', 'VJC')], candidates=candidates)
    return journal, backlog, plan


def run(tmp_path, journal, backlog, plan, **kwargs):
    return run_collector(plan, backlog, journal_path=journal.path, root=tmp_path / 'collector',
        private_root=tmp_path, fetch_packet=kwargs.pop('fetch_packet', packet), **kwargs)


def test_backlog_to_sqlite_coverage_and_repeat_are_idempotent(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    first = run(tmp_path, journal, backlog, plan)
    assert len(first['coverage']['resolved_initial_p0_tasks']) == 18
    assert first['coverage']['before']['financial_tickers_covered'] == 0
    assert first['coverage']['after']['financial_tickers_covered'] == 3
    before = journal.storage_summary()
    second = run(tmp_path, journal, backlog, plan,
        fetch_packet=lambda _: pytest.fail('Cached packet must not be downloaded again'))
    assert sum(r['documents_reused'] for r in second['results']) == 3
    assert sum(r['inserted_observations'] + r['inserted_metric_facts'] for r in second['results']) == 0
    assert second['coverage']['resolved_initial_p0_tasks'] == []
    assert journal.storage_summary() == before


def test_wrong_ticker_and_interruption_are_isolated_and_resumable(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    def fetch(ticker):
        if ticker == 'MSN':
            raise KeyboardInterrupt()
        return packet(ticker)
    with pytest.raises(KeyboardInterrupt):
        run(tmp_path, journal, backlog, plan, fetch_packet=fetch)
    state = json.loads((tmp_path / 'collector/state.json').read_text())
    assert state['candidates']['hdb']['status'] == 'IMPORTED'
    resumed = run(tmp_path, journal, backlog, plan,
        fetch_packet=lambda t: packet('BAD') if t == 'MSN' else packet(t))
    assert resumed['results'][0]['documents_reused'] == 1
    assert resumed['results'][1]['status'] == 'EXTRACTION_FAILURE'
    assert resumed['results'][2]['status'] == 'IMPORTED'


@pytest.mark.parametrize('status', [403, 429, 404, 503])
def test_document_failures_respect_access_and_bound_retries(status):
    calls = []
    def transport(request):
        calls.append(request.url)
        return httpx.Response(status)
    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        result = download_document('https://example.test/report.pdf', 'pdf', client=client, pause=lambda _: None)
    assert len(calls) == (2 if status == 503 else 1)
    assert result['status'] == ('ACCESS_RESTRICTED' if status in (403, 429) else 'SOURCE_UNAVAILABLE')


def test_download_only_never_changes_financial_coverage_and_revisions_are_retained(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    c = dict(plan['candidates'][0], id='html', kind='document', format='html')
    plan['candidates'] = [c]
    data = [b'<html>first source</html>']
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            headers={'content-type': 'text/html'}, content=data[0]))) as client:
        first = run(tmp_path, journal, backlog, plan, client=client)
        assert first['results'][0]['status'] == 'DOWNLOADED_AWAITING_REVIEW'
        assert first['coverage']['after']['financial_tickers_covered'] == 0
        cached = run(tmp_path, journal, backlog, plan, client=client)
        assert cached['results'][0]['documents_reused'] == 1
        data[0] = b'<html>new revision</html>'
        run(tmp_path, journal, backlog, plan, client=client, refresh_documents=True)
    assert len(list((tmp_path / 'collector/documents').glob('*.html'))) == 2


def test_original_pdf_uses_existing_reviewed_adapter_and_keeps_old_rows(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    root = tmp_path / 'collector'
    root.mkdir()
    evidence = reviewed(root)
    evidence['ticker'] = 'MSN'
    (root / 'review.json').write_text(json.dumps(evidence), encoding='utf-8')
    c = dict(plan['candidates'][1], id='original', kind='document', format='pdf',
        url=evidence['document_url'], issuer=evidence['issuer'], review_manifest='review.json',
        expected_periods=['2024', '2025'])
    plan['candidates'] = [c]
    original = packet('MSN', quarters=34, start=2018 * 4)
    imported = journal.import_packet(original, 'a' * 64)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            content=(root / evidence['document_file']).read_bytes()))) as client:
        result = run(tmp_path, journal, backlog, plan, client=client)
    assert result['results'][0]['status'] == 'IMPORTED'
    assert result['results'][0]['extraction_audit']['selected_reported_fields'] > 0
    assert journal.read_packet(imported['capture_id']) == original
    assert len([r for r in journal.selected_statements('MSN', 'vnstock:VCI')
                if r['observation'].frequency == 'quarterly' and r['observation'].statement == 'income']) == 34


@pytest.mark.parametrize('mutation', ['ticker', 'period', 'unit'])
def test_bad_document_identity_period_or_units_are_never_imported(tmp_path, mutation):
    journal, backlog, plan = setup(tmp_path)
    root = tmp_path / 'collector'
    root.mkdir()
    evidence = reviewed(root)
    evidence['ticker'] = 'MSN'
    c = dict(plan['candidates'][1], id='original', kind='document', format='pdf',
        url=evidence['document_url'], issuer=evidence['issuer'], review_manifest='review.json',
        expected_periods=['2024', '2025'])
    if mutation == 'ticker':
        evidence['ticker'] = 'BAD'
    elif mutation == 'period':
        c['expected_periods'] = ['2023']
    else:
        evidence['amounts'][0]['unit'] = 'billion VND'
    (root / 'review.json').write_text(json.dumps(evidence), encoding='utf-8')
    plan['candidates'] = [c]
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            content=(root / evidence['document_file']).read_bytes()))) as client:
        result = run(tmp_path, journal, backlog, plan, client=client)
    assert result['results'][0]['status'] == 'EXTRACTION_FAILURE'
    assert journal.storage_summary()['captures'] == 0


def test_plan_requires_actual_backlog_and_small_confirmed_universe(tmp_path):
    _, backlog, plan = setup(tmp_path)
    bad = copy.deepcopy(plan)
    bad['backlog_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='fingerprint'):
        validate_plan(bad, backlog)
    bad = copy.deepcopy(plan)
    bad['task_ids'] = ['financial:UNKNOWN:annual_income']
    with pytest.raises(ValueError, match='existing backlog'):
        validate_plan(bad, backlog)


def test_vn100_expansion_reuses_collector_and_resumes_without_acquisition(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    tickers = sorted({t['ticker'] for t in backlog['acquisition_backlog'] if t['priority'] == 'P3'})[:3]
    plan.update(contract='financial-collector-plan-v512', task_ids=[t['task_id'] for t in
        backlog['acquisition_backlog'] if t['priority'] == 'P3' and t['ticker'] in tickers])
    plan['candidates'] = [dict(plan['candidates'][0], id=t.lower(), ticker=t,
        url='https://example.test/' + t) for t in tickers]
    first = run(tmp_path, journal, backlog, plan)
    assert first['coverage']['after']['financial_tickers_covered'] == 3
    assert len(first['coverage']['resolved_initial_tasks']) == 18
    before = journal.storage_summary()
    repeat = run(tmp_path, journal, backlog, plan,
        fetch_packet=lambda _: pytest.fail('Repeat must not acquire'))
    assert journal.storage_summary() == before
    assert repeat['coverage']['resolved_initial_tasks'] == []
    legacy = dict(plan, contract='financial-collector-plan-v57')
    with pytest.raises(ValueError, match='VN30'):
        validate_plan(legacy, backlog)


def test_vn100_expansion_rejects_non_statement_tasks_and_mismatched_dates(tmp_path):
    _, backlog, plan = setup(tmp_path)
    plan['contract'] = 'financial-collector-plan-v512'
    plan['as_of'] = '2026-10-23'
    with pytest.raises(ValueError, match='date'):
        validate_plan(plan, backlog)
    plan['as_of'] = backlog['as_of']
    task = next(t for t in backlog['acquisition_backlog'] if t['priority'] == 'P3')
    task['family'] = 'net_margin'
    plan['backlog_sha256'] = _sha(_json(backlog))
    plan['task_ids'] = [task['task_id']]
    with pytest.raises(ValueError, match='statement gaps'):
        validate_plan(plan, backlog)


def test_refresh_appends_new_periods_and_keeps_selected_old_values(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    run(tmp_path, journal, backlog, plan)
    original = journal.selected_statements('MSN', 'vnstock:VCI')
    changed = run(tmp_path, journal, backlog, plan, refresh_sdk=True,
        fetch_packet=lambda t: packet(t, start=2025 * 4 + 1))
    assert sum(r['inserted_captures'] for r in changed['results']) == 3
    selected = journal.selected_statements('MSN', 'vnstock:VCI')
    assert len(selected) > len(original)
    assert all(any(r['capture_id'] == o['capture_id'] and r['observation'] == o['observation']
                   for r in selected) for o in original)


def test_shorter_refresh_is_archived_and_appends_its_new_period_without_index_replacement(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    run(tmp_path, journal, backlog, plan)
    original = journal.selected_statements('MSN', 'vnstock:VCI')
    index_before = (tmp_path / 'collector/sdk/index.json').read_bytes()
    changed = run(tmp_path, journal, backlog, plan, refresh_sdk=True,
        fetch_packet=lambda t: packet(t, quarters=1, start=2025 * 4 + 2))
    assert all(r['sdk_acquisition_status'] == 'refresh_deferred_shorter_history' for r in changed['results'])
    assert all(r['inserted_observations'] > 0 for r in changed['results'])
    assert (tmp_path / 'collector/sdk/index.json').read_bytes() == index_before
    selected = journal.selected_statements('MSN', 'vnstock:VCI')
    assert any(r['observation'].period == '2025-Q3' for r in selected)
    assert all(any(r['capture_id'] == o['capture_id'] and r['observation'] == o['observation']
                   for r in selected) for o in original)
    repeat = run(tmp_path, journal, backlog, plan,
        fetch_packet=lambda _: pytest.fail('Pinned short candidate should resume without network'))
    assert all(r['documents_reused'] == 1 for r in repeat['results'])
    assert all(r['inserted_captures'] == 0 for r in repeat['results'])


def test_shorter_candidate_cannot_bypass_source_line_validation(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    run(tmp_path, journal, backlog, plan)
    before = journal.storage_summary()
    def invalid(ticker):
        value = packet(ticker, quarters=1, start=2025 * 4 + 2)
        value.reports['income'].observations[0].fields['revenue'] = 999
        return value
    changed = run(tmp_path, journal, backlog, plan, refresh_sdk=True, fetch_packet=invalid)
    assert all(r['status'] == 'EXTRACTION_FAILURE' for r in changed['results'])
    assert journal.storage_summary() == before
    state = json.loads((tmp_path / 'collector/state.json').read_text())
    assert all('sdk_candidate' not in entry for entry in state['candidates'].values())


def test_new_document_revision_needs_fresh_review_and_keeps_valid_old_capture(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    root = tmp_path / 'collector'
    root.mkdir()
    evidence = reviewed(root)
    evidence['ticker'] = 'MSN'
    (root / 'review.json').write_text(json.dumps(evidence), encoding='utf-8')
    plan['candidates'] = [dict(plan['candidates'][1], id='original', kind='document', format='pdf',
        url=evidence['document_url'], issuer=evidence['issuer'], review_manifest='review.json')]
    body = [(root / evidence['document_file']).read_bytes()]
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=body[0]))) as client:
        run(tmp_path, journal, backlog, plan, client=client)
        before = journal.storage_summary()
        body[0] += b'new-revision'
        result = run(tmp_path, journal, backlog, plan, client=client, refresh_documents=True)
    assert result['results'][0]['status'] == 'EXTRACTION_FAILURE'
    assert journal.storage_summary() == before
    assert len(list((root / 'documents').glob('*.pdf'))) == 2


def test_reported_bank_ratio_retains_numeric_evidence_without_claiming_available(tmp_path):
    journal, backlog, plan = setup(tmp_path)
    root = tmp_path / 'collector'
    root.mkdir()
    evidence = reviewed(root)
    evidence.update(ticker='HDB', profile='bank', company_type='NH')
    evidence['amounts'] = [a for a in evidence['amounts'] if a['field'] not in ('revenue', 'gross_profit')]
    row = '2024 Net interest margin (NIM) 5.58%'
    evidence['pages'][0]['text'] += '\n' + row
    evidence['pages'][0]['text_sha256'] = hashlib.sha256(evidence['pages'][0]['text'].encode()).hexdigest()
    ratio = dict(contract='reported-bank-ratio-review-v57', ticker='HDB',
        document_sha256=evidence['document_sha256'], ratios=[dict(metric_id='nim',
        period='2024', original_label='Net interest margin (NIM)', raw_token='5.58%',
        source_row=dict(page=1, text=row), period_quote=dict(page=1, text=row))])
    (root / 'ratio.json').write_text(json.dumps(ratio), encoding='utf-8')
    (root / 'review.json').write_text(json.dumps(evidence), encoding='utf-8')
    plan['candidates'] = [dict(plan['candidates'][0], id='original', kind='document', format='pdf',
        url=evidence['document_url'], issuer=evidence['issuer'], review_manifest='review.json', ratio_review='ratio.json')]
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            content=(root / evidence['document_file']).read_bytes()))) as client:
        result = run(tmp_path, journal, backlog, plan, client=client)
    assert result['results'][0]['unqualified_reported_ratios'] == 1
    fact = next(f for f in journal.read() if f.metric_id == 'nim')
    assert fact.value is None and fact.quality_status == 'UNQUALIFIED'
    assert fact.input_refs[0]['value'] == .0558
    assert fact.input_refs[0]['page'] == 1
    report = build_coverage(journal.path, as_of='2026-10-22')
    hdb = next(c for c in report['companies'] if c['ticker'] == 'HDB')
    assert hdb['specialist_kpis']['nim']['by_period']['2024']['status'] == 'PARTIAL'
