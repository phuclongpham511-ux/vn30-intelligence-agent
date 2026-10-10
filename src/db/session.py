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
    from src.news import models as news_models  # noqa: F401 - additive news tables
    from src.community import models as community_models  # noqa: F401
    from src.corporate_actions import storage as corporate_action_models  # noqa: F401
    from src.models import technical_eod as technical_eod_models  # noqa: F401
    target = engine if engine is not None else get_engine()
    SQLModel.metadata.create_all(target)
    if 'items_received' not in {column['name'] for column in inspect(target).get_columns('communitysourcestate')}:
        with target.begin() as connection:
            connection.execute(text('ALTER TABLE communitysourcestate ADD COLUMN items_received INTEGER'))
    news_columns = {column['name'] for column in inspect(target).get_columns('newsarticle')}
    state_columns = {column['name'] for column in inspect(target).get_columns('newssourcestate')}
    if 'read_cache_dirty' not in {column['name'] for column in inspect(target).get_columns('newsstory')}:
        with target.begin() as connection:
            connection.execute(text('ALTER TABLE newsstory ADD COLUMN read_cache_dirty BOOLEAN NOT NULL DEFAULT TRUE'))
    with target.begin() as connection:
        dates = ('next_due_at', 'lease_until', 'refresh_requested_at', 'last_refresh_request_at')
        types = {'priority': 'VARCHAR', 'lease_token': 'VARCHAR',
                 'fetch_duration_seconds': 'FLOAT',
                 **{field: ('TIMESTAMP WITH TIME ZONE' if target.dialect.name == 'postgresql' else 'DATETIME') for field in dates},
                 **{field: 'INTEGER NOT NULL DEFAULT 0' for field in
                    ('consecutive_failures', 'newly_inserted_articles', 'refresh_requests',
                     'fetch_attempts', 'successful_fetches', 'failed_fetches')}}
        for field, kind in types.items():
            if field not in state_columns:
                connection.execute(text(f'ALTER TABLE newssourcestate ADD COLUMN {field} {kind}'))
    with target.begin() as connection:
        for field in ('thumbnail_url', 'thumbnail_provenance'):
            if field not in news_columns:
                connection.execute(text(f'ALTER TABLE newsarticle ADD COLUMN {field} VARCHAR'))
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
