from functools import lru_cache
from sqlalchemy import event
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
    SQLModel.metadata.create_all(engine if engine is not None else get_engine())


def get_session():
    with Session(get_engine()) as session:
        yield session
