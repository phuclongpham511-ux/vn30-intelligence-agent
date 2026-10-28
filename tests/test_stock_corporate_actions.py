from datetime import datetime, timedelta, timezone

from sqlalchemy import event

from src.corporate_actions.models import CorporateActionNotice
from src.corporate_actions.repository import CorporateActionRepository


def notice(**changes):
    return CorporateActionNotice(**dict(symbol='ABC', action_type='cash_dividend',
        source='VSDC', source_id='notice-1', component_id='issuer-action', source_url='https://vsdc.vn/notice/1',
        record_date='2026-10-01', payment_date='2026-10-20',
        terms={'cash_vnd_per_share': 1500}, verified=True, **changes))


def test_reader_preserves_missing_dates_terms_and_provenance_without_writes(client, session):
    repo = CorporateActionRepository(session)
    row = repo.ingest(notice(), received_at=datetime.now(timezone.utc)-timedelta(days=1)).observation
    statements = []
    def capture(_conn, _cursor, statement, *_args):
        statements.append(statement)
    event.listen(session.get_bind(), 'before_cursor_execute', capture)
    try:
        response = client.get('/stocks/abc/corporate-actions')
    finally:
        event.remove(session.get_bind(), 'before_cursor_execute', capture)
    assert response.status_code == 200
    body = response.json()
    assert body['ticker'] == 'ABC' and body['coverage'] == 'INCOMPLETE'
    assert body['items'] == [row.model_dump(mode='json')]
    assert body['items'][0]['effective_date'] is None
    assert statements and all(s.lstrip().upper().startswith('SELECT') for s in statements)


def test_latest_correction_precedes_symbol_filter_and_future_receipts_are_excluded(client, session):
    repo = CorporateActionRepository(session)
    now = datetime.now(timezone.utc)
    first = notice()
    repo.ingest(first, received_at=now-timedelta(days=2))
    repo.ingest(first.model_copy(update={'symbol':'XYZ', 'withdrawn':True}), received_at=now-timedelta(days=1))
    repo.ingest(first, received_at=now+timedelta(days=1))
    assert client.get('/stocks/ABC/corporate-actions').json()['items'] == []
    rows = client.get('/stocks/XYZ/corporate-actions').json()['items']
    assert len(rows) == 1 and rows[0]['withdrawn'] is True


def test_pending_revisions_and_pagination_remain_explicit(client, session):
    repo = CorporateActionRepository(session)
    now = datetime.now(timezone.utc)-timedelta(days=1)
    first = notice()
    repo.ingest(first, received_at=now-timedelta(hours=1))
    repo.ingest(first.model_copy(update={'verified':False, 'verification_note':'Unresolved correction'}), received_at=now)
    repo.ingest(first.model_copy(update={'source_id':'notice-2', 'is_fixture':True}), received_at=now-timedelta(minutes=1))
    body = client.get('/stocks/ABC/corporate-actions?limit=1').json()
    assert body['has_more'] is True
    assert body['items'][0]['verified'] is False
    assert body['items'][0]['verification_note'] == 'Unresolved correction'
    assert client.get('/stocks/ABC/corporate-actions?limit=101').status_code == 422
    assert client.get('/stocks/BAD%20SYMBOL/corporate-actions').status_code == 422
