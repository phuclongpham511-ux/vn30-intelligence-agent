"""Display transport is optional; financial facts and complete API evidence remain."""
from datetime import datetime, timezone
import pytest
from sqlalchemy import event
from main import app
from src.models import Security
from src.services.data import get_fundamental_provider
from test_financial_engine import packet


@pytest.mark.parametrize('frequency', ['annual', 'quarterly', 'ttm'])
def test_display_projection_preserves_every_displayed_fact_and_latest_evidence(client, session, frequency):
    session.add(Security(symbol='ABC', exchange='HOSE', last_synced_at=datetime.now(timezone.utc)))
    session.commit()
    saved = packet()
    class Provider:
        source = 'test:VCI'
        def get_reports(self, ticker): return saved.model_copy(deep=True)
    app.dependency_overrides[get_fundamental_provider] = Provider
    statements = []
    def inspect(conn, cursor, query, params, context, many): statements.append(query)
    event.listen(session.get_bind(), 'before_cursor_execute', inspect)
    try:
        url = f'/stocks/ABC/financials?frequency={frequency}&limit=3'
        full = client.get(url)
        display = client.get(url + '&projection=display')
        assert full.status_code == display.status_code == 200
        a, b = full.json(), display.json()
        assert len(display.content) < len(full.content) * .85
        assert a['rows'][-1] == b['rows'][-1]
        for x, y in zip(a['rows'], b['rows'], strict=True):
            assert {k:v for k,v in x.items() if k!='calculations'} == {k:v for k,v in y.items() if k!='calculations'}
        assert all('calculations' not in row for row in b['rows'][:-1])
        assert all('calculations' not in row for row in b['chart_rows'])
        for x, y in zip(a['chart_rows'], b['chart_rows'], strict=True):
            assert {k:v for k,v in x.items() if k!='calculations'} == y
        for key in ('source_receipts','statements','reconciliations','changes','read_kind','limitations','metadata_sha256','is_fixture'):
            assert a[key] == b[key]
        assert all('calculations' in row for row in a['rows'])
        assert client.get(url + '&projection=invalid').status_code == 422
        assert not any(query.lstrip().upper().startswith(('INSERT','UPDATE','DELETE','CREATE')) for query in statements)
    finally:
        event.remove(session.get_bind(), 'before_cursor_execute', inspect)
