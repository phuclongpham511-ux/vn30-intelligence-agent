from datetime import date
from typing import Protocol
from src.schemas.data import FundamentalRecord, MarketBar, NewsItem


class ProviderError(RuntimeError):
    """Safe public error. Raw upstream errors must not reach clients."""


class ProviderNotReadyError(ProviderError):
    pass


class MarketDataProvider(Protocol):
    source: str
    def validate_symbol(self, symbol: str) -> bool: ...
    def get_history(self, symbol: str, start: date, end: date) -> list[MarketBar]: ...
    def get_latest(self, symbol: str) -> MarketBar | None: ...


class FundamentalDataProvider(Protocol):
    source: str
    def get_financials(self, symbol: str) -> list[FundamentalRecord]: ...


class NewsProvider(Protocol):
    source: str
    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]: ...
