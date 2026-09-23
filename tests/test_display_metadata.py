from sqlmodel import select
from src.models import Stock
from scripts.seed_stocks import seed_stocks


def test_curated_english_seed_metadata(session):
    seed_stocks(session)
    seed_stocks(session)
    stocks = session.exec(select(Stock)).all()
    assert len(stocks) == 3
    assert all(stock.display_name_en for stock in stocks)


def test_raw_provider_name_is_not_promoted_to_english(session):
    stock = Stock(symbol="DYNAMIC", company_name="CTCP Cao su Viet Nam")
    session.add(stock)
    session.commit()
    session.refresh(stock)
    assert stock.display_name_en is None
