"""Run from repository root: uv run python -m scripts.seed_stocks."""
from sqlmodel import Session, select
from src.db.session import create_tables, get_engine
from src.models import Stock

SEEDS = [
    {"symbol": "TCB", "exchange": "HOSE", "company_name": "Techcombank"},
    {"symbol": "FPT", "exchange": "HOSE", "company_name": "FPT Corporation"},
    {"symbol": "HPG", "exchange": "HOSE", "company_name": "Hoa Phat Group"},
]


def seed_stocks(session: Session) -> int:
    added = 0
    for values in SEEDS:
        existing = session.exec(select(Stock).where(Stock.symbol == values["symbol"])).first()
        # Seed names are curated English metadata, unlike unverified provider names.
        if existing is None:
            session.add(Stock(**values, display_name_en=values["company_name"]))
            added += 1
        elif existing.display_name_en is None:
            existing.display_name_en = values["company_name"]
            session.add(existing)
    session.commit()
    return added


def run():
    create_tables()
    with Session(get_engine()) as session:
        print(f"Added {seed_stocks(session)} seed stocks.")


if __name__ == "__main__":
    run()
