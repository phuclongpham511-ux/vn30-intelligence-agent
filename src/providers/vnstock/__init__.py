"""vnstock 4.0.2 adapter. External DataFrames never cross this boundary."""
from datetime import date, timedelta
from functools import lru_cache
import logging
import math
import os
import re
import time

import pandas as pd

from src.providers.base import ProviderError
from src.schemas.data import FundamentalRecord, MarketBar

logger = logging.getLogger(__name__)


@lru_cache
def sdk():
    os.environ.setdefault("VNSTOCK_TELEMETRY", "off")
    os.environ.setdefault("VNSTOCK_DISABLE_AGENT_SETUP", "1")
    import truststore
    truststore.inject_into_ssl()
    import vnstock
    return vnstock


def guarded(symbol, operation, call):
    try:
        return call()
    except (Exception, SystemExit) as exc:
        logger.warning("provider=vnstock ticker=%s operation=%s error_type=%s", symbol, operation, type(exc).__name__)
        raise ProviderError("Data provider is temporarily unavailable. Please retry later.") from None


def normalize_history(frame: pd.DataFrame, symbol: str, start: date, end: date) -> list[MarketBar]:
    if frame.empty:
        return []
    required = {"time", "open", "high", "low", "close", "volume"}
    if not required.issubset(frame.columns):
        raise ValueError("Unexpected OHLCV schema")
    bars = {}
    for row in frame.to_dict("records"):
        day = pd.Timestamp(row["time"]).date()
        if not start <= day <= end:
            continue
        # VCI Quote returns prices in thousands of VND, volume in shares.
        bar = MarketBar(ticker=symbol, date=day, source="vnstock:VCI",
                        **{key: float(row[key]) * 1000 for key in ("open", "high", "low", "close")},
                        volume=row["volume"])
        key = (day, bar.source)
        if key in bars and bars[key] != bar:
            raise ValueError("Conflicting duplicate OHLCV")
        bars[key] = bar
    return sorted(bars.values(), key=lambda bar: bar.date)


def normalize_financials(frame: pd.DataFrame, symbol: str) -> list[FundamentalRecord]:
    if frame.empty:
        return []
    if "item_id" not in frame.columns or frame.columns.duplicated().any():
        raise ValueError("Unexpected financial schema")
    periods = [column for column in frame.columns if re.fullmatch(r"\d{4}", str(column))]
    if not periods:
        raise ValueError("Missing annual reporting periods")
    if frame["item_id"].duplicated().any():
        raise ValueError("Duplicate financial items")
    rows = frame.set_index("item_id")
    def value(code, period):
        if code not in rows.index:
            return None
        raw = rows.at[code, period]
        if pd.isna(raw):
            return None
        number = float(raw)
        return number if math.isfinite(number) else None
    records = []
    for period in periods:
        revenue, profit, gross = (value(code, period) for code in ("isa3", "isa20", "isa5"))
        records.append(FundamentalRecord(
            ticker=symbol, period=str(period), revenue=revenue, net_profit=profit,
            gross_margin=gross / revenue if gross is not None and revenue is not None and revenue > 0 else None,
            net_margin=profit / revenue if profit is not None and revenue is not None and revenue > 0 else None,
            # VCI ratio output is empty/unreliable in the verified SDK version.
            roe=None, source="vnstock:VCI",
        ))
    return sorted(records, key=lambda row: row.period)


class VnstockMarketDataProvider:
    source = "vnstock:VCI"

    @lru_cache(maxsize=4)
    def _universe(self, bucket: int) -> dict[str, str]:
        def fetch():
            frame = sdk().Listing(source="KBS").all_symbols()
            if frame.empty or not {"symbol", "organ_name"}.issubset(frame.columns):
                raise ValueError("Invalid listing response")
            return {str(row["symbol"]).upper(): str(row["organ_name"]) for row in frame.to_dict("records")}
        return guarded("*", "listing", fetch)

    def validate_symbol(self, symbol: str) -> bool:
        return symbol in self._universe(int(time.time() // 3600))

    def company_name(self, symbol: str) -> str | None:
        return self._universe(int(time.time() // 3600)).get(symbol)

    @lru_cache(maxsize=128)
    def _history(self, symbol: str, start: date, end: date, bucket: int) -> tuple[MarketBar, ...]:
        def fetch():
            frame = sdk().Quote(symbol=symbol, source="VCI").history(
                start=start.isoformat(), end=end.isoformat(), interval="1D")
            return tuple(normalize_history(frame, symbol, start, end))
        return guarded(symbol, "history", fetch)

    def get_history(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        return list(self._history(symbol, start, end, int(time.time() // 300)))

    def get_latest(self, symbol: str) -> MarketBar | None:
        bars = self.get_history(symbol, date.today() - timedelta(days=30), date.today())
        return bars[-1] if bars else None


class VnstockFundamentalDataProvider:
    source = "vnstock:VCI"

    @lru_cache(maxsize=128)
    def _financials(self, symbol: str, bucket: int) -> tuple[FundamentalRecord, ...]:
        def fetch():
            frame = sdk().Finance(symbol=symbol, source="VCI").income_statement(
                period="year", lang="en", dropna=False)
            return tuple(normalize_financials(frame, symbol))
        return guarded(symbol, "income_statement", fetch)

    def get_financials(self, symbol: str) -> list[FundamentalRecord]:
        return list(self._financials(symbol, int(time.time() // 3600)))
