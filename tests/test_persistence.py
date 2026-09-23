from sqlalchemy import text
from sqlmodel import Session, create_engine, select
from src.db.session import create_tables
from src.models import Stock


def test_disk_persistence_and_day0_migration(tmp_path):
    url="sqlite:///"+str(tmp_path/"persistent.db")
    engine=create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE stock (id INTEGER PRIMARY KEY, symbol VARCHAR(20) NOT NULL UNIQUE, exchange VARCHAR(30), company_name VARCHAR(255), sector VARCHAR(100), industry VARCHAR(100), is_active BOOLEAN NOT NULL, created_at DATETIME NOT NULL)"))
        connection.execute(text("INSERT INTO stock (symbol,is_active,created_at) VALUES ('XYZ',1,'2025-01-01')"))
    create_tables(engine)
    create_tables(engine)
    engine.dispose()
    reopened=create_engine(url)
    with Session(reopened) as session:
        stock=session.exec(select(Stock)).one()
        assert stock.symbol=="XYZ" and stock.updated_at is not None
    reopened.dispose()
