import pytest
from datetime import datetime, timezone
from sqlalchemy import event
from src.schemas.data import FundamentalRecord
from src.analytics.financial_research import financial_research, financial_identity_guard
from src.models import Security, Stock
from src.services.data import get_fundamental_provider
from main import app


def row(year, revenue=None, profit=None, **extra):
    return FundamentalRecord(ticker="ABC", period=str(year), source="test", revenue=revenue, net_profit=profit, **extra)


def test_comparable_changes_use_exact_prior_year_and_preserve_zero():
    result=financial_research("ABC", [row(2022, 80, 2),row(2024, 0, -2),row(2025, 0, 0)], "test", limit=1)
    assert len(result['rows'])==1
    profit=next(c for c in result['changes'] if c['metric']=='net_profit')
    assert profit['previous']==-2 and profit['absolute_change']==2 and profit['growth_yoy'] is None
    assert result['changes'][0]['absolute_change']==0 and result['changes'][0]['growth_yoy'] is None
    gap=financial_research("ABC", [row(2022, 80),row(2025, 100)], "test")['changes'][0]
    assert gap['prior_period']=='2024' and gap['previous'] is None and gap['absolute_change'] is None


def test_financial_identity_is_a_generic_safety_exclusion_not_ticker_logic():
    original=row(2025, 100, 20, gross_margin=.3, net_margin=.2)
    result=financial_research("ABC", [original], "test", names=("Ngân hàng ABC",))
    assert result['financial_identity_guard'] and result['rows'][0].revenue is None
    assert result['rows'][0].gross_margin is None and result['rows'][0].net_margin is None
    assert result['rows'][0].net_profit==20 and original.revenue==100
    assert result['sector'] is None and result['consolidation'] is None and result['publication_date'] is None
    assert financial_identity_guard("Banking") and financial_identity_guard("Chứng khoán ABC")
    assert not financial_identity_guard("ABC manufacturing") and not financial_identity_guard("Riverbank tools")


@pytest.mark.parametrize('bad', [[row(2025,100,currency='USD')], [row(2025,100),row(2025,110)],
    [row(2025,100).model_copy(update={'ticker':'OTHER'})]])
def test_rejects_wrong_currency_duplicate_or_foreign_ownership(bad):
    with pytest.raises(ValueError): financial_research('ABC',bad,'test')


def test_empty_or_quarter_only_data_cannot_claim_supported_annuals():
    data=financial_research('ABC',[row('2025-Q1',100)],'test')
    assert data['rows']==[] and data['changes']==[] and data['available_period_types']==[]


def test_endpoint_reads_existing_identity_without_stock_creation(client, session):
    session.add(Security(symbol='ABC',exchange='HOSE',company_name='ABC manufacturer',last_synced_at=datetime.now(timezone.utc)))
    session.commit()
    class Provider:
        source='test'
        def get_financials(self,symbol): return [row(2024,100,10),row(2025,120,12)]
    app.dependency_overrides[get_fundamental_provider]=Provider
    statements=[]
    def inspect(conn,cursor,statement,params,context,many): statements.append(statement)
    event.listen(session.get_bind(),'before_cursor_execute',inspect)
    try:
        response=client.get('/stocks/ABC/fundamentals/research')
        assert response.status_code==200
        result=response.json()
        assert result['ticker']=='ABC' and result['changes'][0]['absolute_change']==20
        assert result['rows'][-1]['revenue_growth_yoy']==pytest.approx(.2)
        assert not any(s.lstrip().upper().startswith(('INSERT','UPDATE','DELETE','CREATE')) for s in statements)
        assert client.get('/stocks/UNKNOWN/fundamentals/research').status_code==404
        assert client.get('/stocks/ABC/fundamentals/research?limit=21').status_code==422
    finally: event.remove(session.get_bind(),'before_cursor_execute',inspect)
