"""Public read-only coverage seam on isolated V5.5 journals."""
from datetime import date

from src.services.financial_coverage import build_coverage, membership_snapshot, period_span, ticker_membership
from src.services.financial_journal import MetricJournal
from src.services.financial_intelligence import normalized_metrics
from test_financial_storage import history_packet


def _fpt_packet():
    packet = history_packet(3, start=2025 * 4)
    packet.ticker = 'FPT'
    for receipt in packet.reports.values():
        for observation in receipt.observations:
            observation.ticker = 'FPT'
    return packet


def test_dated_hose_snapshots_retain_history_and_exclude_reserves():
    january = membership_snapshot(date(2026, 2, 2))
    july = membership_snapshot(date(2026, 10, 22))
    assert january['effective_date'] == '2026-02-02'
    assert july['effective_date'] == '2026-08-03'
    assert 'MCH' not in january['vn30'] and 'MCH' in july['vn30']
    assert 'TPB' in january['vn30'] and 'TPB' not in july['vn30']
    assert 'VCK' not in july['vn30'] and 'VCK' in july['vnmidcap']
    assert set(july['vn100']) == set(july['vn30']) | set(july['vnmidcap'])
    assert len(july['vn30']) == 30 and len(july['vn100']) == 100
    assert ticker_membership('FPT', as_of='2025-12-31')['status'] == 'UNKNOWN'
    assert ticker_membership('MCH', as_of='2026-02-02')['status'] == 'NOT_IN_DATED_SNAPSHOT'
    assert ticker_membership('MCH', as_of='2026-08-03')['status'] == 'CONFIRMED_VN30'


def test_span_only_flags_internal_observed_period_gaps():
    assert period_span(['2025-Q1', '2025-Q3'], 'quarterly') == dict(
        earliest='2025-Q1', latest='2025-Q3', count=2, missing_between=['2025-Q2'])
    assert period_span([], 'annual')['missing_between'] == []


def test_coverage_uses_selected_revisions_without_writing_or_promoting_public_rights(tmp_path):
    path = tmp_path / 'financial.sqlite'
    journal = MetricJournal(path)
    journal.initialize()
    packet = _fpt_packet()
    for receipt in packet.reports.values():
        receipt.observations = [o for o in receipt.observations if o.period != '2025-Q2']
    journal.import_packet(packet, 'a' * 64)
    revision = _fpt_packet()
    journal.import_packet(revision, 'b' * 64)
    # Q1 and Q3 keep the first selected revision; only Q2 is added.
    before = path.read_bytes()
    report = build_coverage(path, as_of='2026-10-22')
    assert path.read_bytes() == before
    assert report['membership']['vn30_confirmed'] == 30
    assert report['membership']['vn100_confirmed'] == 100
    assert report['summary']['financial_tickers_covered'] == 1
    fpt = next(c for c in report['companies'] if c['ticker'] == 'FPT')
    assert fpt['statements']['income']['quarterly']['count'] == 3
    assert fpt['statements']['income']['quarterly']['missing_between'] == []
    assert 'isa3' in fpt['statements']['income']['quarterly']['source_lines_by_period']['2025-Q1'][0]['available_codes']
    assert fpt['statements']['income']['quarterly']['public_display_eligible'] is False
    assert fpt['metrics_by_period']['2025-Q1']['revenue']['status'] == 'AVAILABLE'
    assert fpt['metrics_by_period']['2025-Q1']['revenue']['public_display_eligible'] is False
    assert fpt['specialist_kpis']['nim']['status'] == 'UNKNOWN'  # no certified industry
    assert any(t['ticker'] == 'HDB' and t['priority'] == 'P0' for t in report['acquisition_backlog'])
    assert all(t['source_availability'] == 'UNTESTED' for t in report['acquisition_backlog'])


def test_stale_metric_vintage_is_excluded_after_explicit_statement_selection(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    original = _fpt_packet()
    journal.import_packet(original, 'a' * 64)
    journal.append(normalized_metrics(original, frequency='quarterly', limit=3))
    before = build_coverage(journal.path, as_of='2026-10-22')
    fpt = next(c for c in before['companies'] if c['ticker'] == 'FPT')
    assert fpt['metrics_by_period']['2025-Q1']['gross_margin']['calculated'] is True
    revision = _fpt_packet()
    revision.reports['income'].observations[0].fields['revenue'] = 100
    revision.reports['income'].content_sha256 = 'b' * 64
    revised = journal.import_packet(revision, 'b' * 64)
    journal.select_revision(revised['capture_id'], statement='income', period='2025-Q1')
    after = build_coverage(journal.path, as_of='2026-10-22')
    fpt = next(c for c in after['companies'] if c['ticker'] == 'FPT')
    assert fpt['metrics_by_period']['2025-Q1']['gross_margin']['calculated'] is False


def test_null_only_capture_is_represented_but_not_financially_covered(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    packet = _fpt_packet()
    for receipt in packet.reports.values():
        for observation in receipt.observations:
            observation.fields = {key: None for key in observation.fields}
            for line in observation.items:
                line.value = None
    journal.import_packet(packet, 'c' * 64)
    report = build_coverage(journal.path, as_of='2026-10-22')
    fpt = next(c for c in report['companies'] if c['ticker'] == 'FPT')
    assert fpt['represented_in_sqlite'] is True
    assert fpt['financial_data_present'] is False
    assert fpt['statements']['income']['quarterly']['status'] == 'SOURCE_UNAVAILABLE'
    assert report['summary']['financial_tickers_covered'] == 0


def test_fixture_capture_is_visible_but_never_counts_as_real_coverage(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    packet = _fpt_packet()
    packet.is_fixture = True
    imported = journal.import_packet(packet, 'd' * 64)
    journal.append(normalized_metrics(packet, frequency='quarterly', limit=3))
    report = build_coverage(journal.path, as_of='2026-10-22')
    fpt = next(c for c in report['companies'] if c['ticker'] == 'FPT')
    assert fpt['represented_in_sqlite'] is True
    assert fpt['fixture_only'] is True
    assert fpt['fixture_capture_ids'] == [imported['capture_id']]
    assert fpt['financial_data_present'] is False
    assert fpt['metrics_by_period'] == {}
    assert report['summary']['financial_tickers_covered'] == 0
    assert report['summary']['fixture_only_tickers'] == ['FPT']


def test_specialist_history_applicability_and_core_gap_backlog(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    packet = _fpt_packet()
    packet.ticker = 'TCB'
    packet.profile = 'bank'
    packet.company_type = 'NH'
    for receipt in packet.reports.values():
        for observation in receipt.observations:
            observation.ticker = 'TCB'
    journal.import_packet(packet, 'e' * 64)
    report = build_coverage(journal.path, as_of='2026-10-22')
    tcb = next(c for c in report['companies'] if c['ticker'] == 'TCB')
    assert tcb['metrics_by_period']['2025-Q1']['gross_margin']['status'] == 'NOT_APPLICABLE'
    assert tcb['metrics_by_period']['2025-Q1']['gross_margin']['reason'] == 'not_applicable_to_issuer'
    nim = tcb['specialist_kpis']['nim']
    assert '2025-Q1' in nim['by_period']
    assert nim['by_period']['2025-Q1']['frequency'] == 'quarterly'
    assert nim['reference_period_release_verified'] is False
    assert any(t['task_id'] == 'financial:TCB:quarterly:pe' and t['priority'] == 'P4'
               for t in report['acquisition_backlog'])


def test_specialist_period_cells_keep_older_available_source_evidence(tmp_path):
    journal = MetricJournal(tmp_path / 'financial.sqlite')
    journal.initialize()
    packet = _fpt_packet()
    packet.ticker = 'VIC'
    for receipt in packet.reports.values():
        for observation in receipt.observations:
            observation.ticker = 'VIC'
    balance = packet.reports['balance'].observations[0]
    balance.fields['inventory'] = 123
    journal.import_packet(packet, 'f' * 64)
    report = build_coverage(journal.path, as_of='2026-10-22', industry_snapshot={
        'contract': 'industry-membership-review-v1', 'entries': [{
            'ticker': 'VIC', 'exchange': 'HOSE', 'source_status': 'OBSERVED_PAIR_UNQUALIFIED',
            'provider_label': 'Bất động sản'}]})
    vic = next(c for c in report['companies'] if c['ticker'] == 'VIC')
    inventory = vic['specialist_kpis']['inventory']
    period = balance.period
    assert inventory['by_period'][period]['status'] == 'AVAILABLE'
    assert inventory['by_period'][period]['sources'] == ['vnstock:VCI']
    assert inventory['by_period'][period]['source_fields'] == ['inventory']
    assert inventory['by_period'][period]['capture_ids']
    assert period in inventory['historical_available_periods']
