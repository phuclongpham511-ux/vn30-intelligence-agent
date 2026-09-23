from datetime import date
from typing import Any, Protocol


class ProviderNotReadyError(RuntimeError):
    pass


class MarketDataProvider(Protocol):
    def validate_symbol(self, symbol: str) -> bool: ...
    def get_history(self, symbol: str, start: date, end: date) -> list[dict[str, Any]]: ...
    def get_latest(self, symbol: str) -> dict[str, Any]: ...


class FundamentalDataProvider(Protocol):
    def get_financials(self, symbol: str) -> list[dict[str, Any]]: ...
    def get_key_metrics(self, symbol: str) -> dict[str, Any]: ...
