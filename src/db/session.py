from functools import lru_cache
from sqlalchemy import event, inspect, text
from sqlmodel import Session, SQLModel, create_engine
from src.config.settings import get_settings


@lru_cache
def get_engine():
    url = get_settings().database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return engine


def create_tables(engine=None):
    from src import models  # noqa: F401 - register tables
    target = engine if engine is not None else get_engine()
    SQLModel.metadata.create_all(target)
    if "display_name_en" not in {column["name"] for column in inspect(target).get_columns("stock")}:
        with target.begin() as connection:
            connection.execute(text("ALTER TABLE stock ADD COLUMN display_name_en VARCHAR(255)"))
    # Minimal additive migration for existing Day 0 databases.
    if "updated_at" not in {column["name"] for column in inspect(target).get_columns("stock")}:
        with target.begin() as connection:
            kind = "TIMESTAMP WITH TIME ZONE" if target.dialect.name == "postgresql" else "DATETIME"
            connection.execute(text(f"ALTER TABLE stock ADD COLUMN updated_at {kind}"))
            connection.execute(text("UPDATE stock SET updated_at = created_at WHERE updated_at IS NULL"))
    with target.begin() as connection:
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS stock_symbol_casefold ON stock (upper(trim(symbol)))"))


def get_session():
    with Session(get_engine()) as session:
        yield session
