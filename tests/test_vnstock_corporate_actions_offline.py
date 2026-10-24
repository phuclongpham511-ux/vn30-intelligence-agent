"""Synthetic fixtures only; exercise the adapter, existing repository and HTTP reader."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import pytest

from src.providers.vnstock.corporate_actions import normalize_event
from src.corporate_actions.repository import CorporateActionRepository


FIXTURES = json.loads((Path(__file__).parent / 'fixtures/vnstock_corporate_actions_v1.json').read_text(encoding='utf-8'))


def mapped(case):
    fixture = next(row for row in FIXTURES['records'] if row['case'] == case)
    return normalize_event(fixture['raw'], requested_symbol=fixture['requested_symbol'],
        amount_unit=fixture['amount_unit'], ratio_basis=fixture['ratio_basis'],
        semantics_reference=FIXTURES['semantics_reference'])


def test_cash_preserves_original_provenance_dates_and_unverified_fixture_status():
    notice = mapped('cash')
    assert notice.action_type == 'cash_dividend'
    assert notice.terms.cash_vnd_per_share == 1500
    assert notice.terms.new_shares_per_old is None
    assert notice.effective_date == date(2026, 9, 9)
    assert notice.record_date == date(2026, 9, 10)
    assert notice.payment_date == date(2026, 9, 30)
    assert notice.announced_on == date(2026, 9, 1)
    assert notice.announced_at is notice.source_updated_at is None
    assert notice.source == 'vnstock:VCI:events'
    assert notice.source_id == 'ABC:cash-1'
    assert notice.source_url is None
    assert notice.is_fixture is True and notice.verified is False and notice.withdrawn is False
    evidence = json.loads(notice.evidence_text)
    assert evidence['mapping_contract'] == 'vnstock-vci-events-offline-v1'
    assert evidence['amount_unit'] == 'VND/share'
    assert evidence['raw_record'] == FIXTURES['records'][0]['raw']


@pytest.mark.parametrize('case,action_type,ratio', [
    ('stock', 'stock_dividend', 0.1), ('bonus', 'bonus_shares', 0.2), ('rights', 'rights_offering', 0.25),
])
def test_share_types_require_explicit_ratio_basis_and_keep_unknown_terms_missing(case, action_type, ratio):
    notice = mapped(case)
    assert notice.action_type == action_type
    assert notice.terms.new_shares_per_old == ratio
    assert notice.terms.cash_vnd_per_share is notice.terms.subscription_price_vnd is None
    assert notice.payment_date is None
    assert notice.verified is False and notice.is_fixture is True
    evidence = json.loads(notice.evidence_text)
    if case == 'rights':
        assert evidence['raw_record']['value_per_share'] == 12000
        assert 'value_per_share' in evidence['unmapped_fields']
    if case == 'bonus':
        assert 'payout_date' in evidence['unmapped_fields']


@pytest.mark.parametrize('fixture', [r for r in FIXTURES['records'] if 'error' in r], ids=lambda row: row['case'])
def test_ambiguous_or_invalid_fields_are_rejected(fixture):
    with pytest.raises(ValueError, match='^' + fixture['error'] + '$'):
        mapped(fixture['case'])


def test_missing_fields_remain_missing_and_explicit_zero_is_not_missing():
    assert len(FIXTURES['records']) == 20
    before = json.dumps(FIXTURES, sort_keys=True)
    zero, missing, stock = mapped('missing_cash_zero'), mapped('missing_cash_amount'), mapped('missing_ratio')
    assert zero.terms.cash_vnd_per_share == 0
    assert missing.terms.cash_vnd_per_share is None
    assert stock.terms.new_shares_per_old is None
    for notice in (zero, missing, stock):
        assert notice.effective_date is notice.record_date is notice.payment_date is notice.announced_on is None
    assert json.dumps(FIXTURES, sort_keys=True) == before


@pytest.mark.parametrize('declarations,error', [
    ({'amount_unit': 'USD/share'}, 'unsupported_amount_unit'),
    ({'ratio_basis': 'old:new'}, 'unsupported_ratio_basis'),
    ({'semantics_reference': ''}, 'missing_semantics_reference'),
])
def test_unsupported_interpretation_declarations_fail_closed(declarations, error):
    fixture = FIXTURES['records'][0]
    arguments = dict(requested_symbol='ABC', amount_unit='VND/share', ratio_basis=None,
        semantics_reference=FIXTURES['semantics_reference'])
    arguments.update(declarations)
    with pytest.raises(ValueError, match='^' + error + '$'):
        normalize_event(fixture['raw'], **arguments)


def test_repeated_receipt_and_corrections_use_existing_immutable_repository(session):
    repo = CorporateActionRepository(session)
    t = datetime(2026, 10, 1, tzinfo=timezone.utc)
    first = repo.ingest(mapped('cash'), received_at=t)
    repeat = repo.ingest(mapped('cash'), received_at=t+timedelta(hours=1))
    corrected = repo.ingest(mapped('cash_corrected'), received_at=t+timedelta(hours=2))
    reclassified = repo.ingest(mapped('type_corrected'), received_at=t+timedelta(hours=3))
    assert (first.status, repeat.status, corrected.status, reclassified.status) == ('inserted', 'duplicate', 'revision', 'revision')
    assert first.observation.observation_id == repeat.observation.observation_id
    assert first.observation.action_id == corrected.observation.action_id == reclassified.observation.action_id
    assert first.observation.source_revision != corrected.observation.source_revision
    assert repo.get_actions_for_symbol('ABC', as_of=t)[0].terms.cash_vnd_per_share == 1500
    at_correction = repo.get_actions_for_symbol('ABC', as_of=t+timedelta(hours=2))
    assert len(at_correction) == 1 and at_correction[0].terms.cash_vnd_per_share == 1600
    assert at_correction[0].payment_date == date(2026, 10, 5)
    assert repo.get_actions_for_symbol('ABC', as_of=t+timedelta(hours=3))[0].action_type == 'stock_dividend'
    assert repo.context_for('ABC', date(2026, 9, 9), as_of=t).status == 'UNKNOWN'


def test_capped_omission_is_not_cancellation_and_existing_read_route_accepts_notices(client, session):
    repo = CorporateActionRepository(session)
    t = datetime(2026, 10, 1, tzinfo=timezone.utc)
    repo.ingest(mapped('cash'), received_at=t)
    # Another partial source response contains only a different event. No delete/reconcile action.
    repo.ingest(mapped('stock'), received_at=t+timedelta(minutes=1))
    body = client.get('/stocks/ABC/corporate-actions').json()
    assert body['coverage'] == 'INCOMPLETE' and body['has_more'] is False
    assert len(body['items']) == 2
    cash = next(row for row in body['items'] if row['source_id'] == 'ABC:cash-1')
    assert cash['withdrawn'] is False and cash['verified'] is False and cash['is_fixture'] is True
    assert cash['terms']['cash_vnd_per_share'] == 1500
    assert cash['effective_date'] == '2026-09-09'
    assert json.loads(cash['evidence_text'])['raw_record']['id'] == 'cash-1'
