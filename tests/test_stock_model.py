import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from sqlmodel import SQLModel, select
from scripts.seed_stocks import seed_stocks
from src.models import Stock, User, Watchlist, WatchlistItem, MonitoringPreference, Dimension, Priority


def test_seed_is_idempotent(session):
    assert seed_stocks(session) == 3
    assert seed_stocks(session) == 0
    assert {stock.symbol for stock in session.exec(select(Stock)).all()} == {"TCB", "FPT", "HPG"}


def test_dynamic_ticker_and_unique_symbol(session):
    session.add(Stock(symbol="VNM"))
    session.commit()
    assert session.exec(select(Stock).where(Stock.symbol == "VNM")).one().is_active
    session.add(Stock(symbol="VNM"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_foreign_key_enforced(session):
    session.add(Watchlist(user_id=999, name="Invalid"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_core_relationships_and_preferences(session):
    user = User(email="demo@example.test")
    stock = Stock(symbol="VNM")
    session.add_all([user, stock])
    session.commit()
    watchlist = Watchlist(user_id=user.id, name="Research")
    session.add(watchlist)
    session.commit()
    session.add(WatchlistItem(watchlist_id=watchlist.id, stock_id=stock.id))
    session.add(MonitoringPreference(user_id=user.id, stock_id=stock.id, dimension=Dimension.news, priority=Priority.low))
    session.commit()
    assert session.exec(select(MonitoringPreference)).one().priority == Priority.low
    session.add(WatchlistItem(watchlist_id=watchlist.id, stock_id=stock.id))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.add(MonitoringPreference(user_id=user.id, stock_id=stock.id, dimension=Dimension.news, priority=Priority.primary))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_postgresql_schema_compiles():
    for table in SQLModel.metadata.sorted_tables:
        assert "CREATE TABLE" in str(CreateTable(table).compile(dialect=postgresql.dialect()))
