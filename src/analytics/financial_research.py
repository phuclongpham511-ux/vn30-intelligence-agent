"""Source-limited annual research; no acquisition, persistence or new ratio inputs."""
import re
import unicodedata
from datetime import datetime, timezone

from src.analytics.fundamentals import fundamental_history


def financial_identity_guard(*labels: str | None) -> bool:
    """Conservative exclusion, not a substitute for an authoritative sector master."""
    text = " ".join(label or "" for label in labels).casefold().replace("đ", "d")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))
    return bool(re.search(r"\b(bank|banking|ngan hang|securities|chung khoan|insurance|bao hiem|financial services)\b", text))


def financial_research(ticker, records, source, *, limit=8, sector=None, industry=None, names=()):
    if any(row.currency != "VND" for row in records):
        raise ValueError("Unsupported or mixed financial currency")
    restricted = financial_identity_guard(sector, industry, *names)
    # Preserve original input evidence. Existing annual analytics owns all calculations.
    safe = [row.model_copy(update={"revenue": None, "gross_margin": None, "net_margin": None})
            if restricted else row for row in records]
    history = fundamental_history(ticker, safe, source, 20)
    indexed = {row.period: row for row in history}
    changes = []
    latest = history[-1] if history else None
    prior = indexed.get(str(int(latest.period) - 1)) if latest else None
    for metric in ("revenue", "net_profit"):
        current_value = getattr(latest, metric) if latest else None
        prior_value = getattr(prior, metric) if prior else None
        if current_value is not None:
            changes.append(dict(metric=metric, current_period=latest.period,
                prior_period=str(int(latest.period) - 1), current=current_value, previous=prior_value,
                absolute_change=current_value-prior_value if prior_value is not None else None,
                growth_yoy=getattr(latest, metric+"_growth_yoy")))
    return dict(ticker=ticker, source=source, currency="VND", period_type="annual",
        rows=history[-limit:], changes=changes, sector=sector, industry=industry,
        financial_identity_guard=restricted, publication_date=None, consolidation=None,
        read_at=datetime.now(timezone.utc), read_kind="provider_or_process_cache",
        available_period_types=["annual"] if history else [],
        available_statements=["income_summary"] if history else [])
