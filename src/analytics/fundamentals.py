from src.schemas.data import FundamentalRecord, FundamentalSnapshot, FundamentalPeriod


def _period_values(current: FundamentalRecord, prior: FundamentalRecord | None) -> dict:
    values = current.model_dump()
    for field in ("revenue", "net_profit"):
        now, before = getattr(current, field), getattr(prior, field) if prior else None
        # Growth against negative or zero earnings is not economically comparable.
        values[field + "_growth_yoy"] = (now / before - 1) if now is not None and before is not None and before > 0 else None
    for field in ("gross_margin", "net_margin", "roe"):
        now, before = getattr(current, field), getattr(prior, field) if prior else None
        values[field + "_change"] = now - before if now is not None and before is not None else None
    return values


def _indexed(ticker: str, records: list[FundamentalRecord], source: str) -> dict:
    if any(row.ticker != ticker or row.source != source for row in records):
        raise ValueError("Mixed ticker or source")
    if len({row.period for row in records}) != len(records):
        raise ValueError("Duplicate reporting periods")
    return {row.period: row for row in records}


def fundamental_snapshot(ticker: str, records: list[FundamentalRecord], source: str) -> FundamentalSnapshot:
    indexed = _indexed(ticker, records, source)
    if not records:
        return FundamentalSnapshot(ticker=ticker, source=source)
    latest = indexed[max(indexed)]
    prior_period = str(int(latest.period[:4]) - 1) + latest.period[4:]
    return FundamentalSnapshot(**_period_values(latest, indexed.get(prior_period)))


def fundamental_history(ticker: str, records: list[FundamentalRecord], source: str, limit: int = 4) -> list[FundamentalPeriod]:
    indexed = _indexed(ticker, records, source)
    annual = sorted(period for period in indexed if len(period) == 4)
    # Compute before limiting so the first displayed year retains any available prior-year comparison.
    return [FundamentalPeriod(**_period_values(indexed[period], indexed.get(str(int(period) - 1))))
            for period in annual[-limit:]]
