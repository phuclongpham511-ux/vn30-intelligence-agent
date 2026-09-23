from src.schemas.data import FundamentalRecord, FundamentalSnapshot


def fundamental_snapshot(ticker: str, records: list[FundamentalRecord], source: str) -> FundamentalSnapshot:
    if not records:
        return FundamentalSnapshot(ticker=ticker, source=source)
    if any(row.ticker != ticker or row.source != source for row in records):
        raise ValueError("Mixed ticker or source")
    if len({row.period for row in records}) != len(records):
        raise ValueError("Duplicate reporting periods")
    latest = max(records, key=lambda row: row.period)
    prior_period = str(int(latest.period[:4]) - 1) + latest.period[4:]
    prior = next((row for row in records if row.period == prior_period), None)
    values = latest.model_dump()
    for field in ("revenue", "net_profit"):
        now, before = getattr(latest, field), getattr(prior, field) if prior else None
        # Growth against negative or zero earnings is not economically comparable.
        values[field + "_growth_yoy"] = (now / before - 1) if now is not None and before is not None and before > 0 else None
    for field in ("gross_margin", "net_margin", "roe"):
        now, before = getattr(latest, field), getattr(prior, field) if prior else None
        values[field + "_change"] = now - before if now is not None and before is not None else None
    return FundamentalSnapshot(**values)
