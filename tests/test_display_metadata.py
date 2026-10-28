from sqlmodel import select
from src.models import Stock


def test_explicit_english_metadata_is_preserved(session):
    session.add(Stock(symbol='DYNAMIC',display_name_en='Example listed issuer'))
    session.commit()
    stocks = session.exec(select(Stock)).all()
    assert len(stocks) == 1
    assert all(stock.display_name_en for stock in stocks)


def test_raw_provider_name_is_not_promoted_to_english(session):
    stock = Stock(symbol="DYNAMIC", company_name="CTCP Cao su Viet Nam")
    session.add(stock)
    session.commit()
    session.refresh(stock)
    assert stock.display_name_en is None
