"""Day 0 adapters. Real vnstock integration is scheduled for Day 1."""
from datetime import date
from typing import Any
from src.providers.base import ProviderNotReadyError


class VnstockMarketDataProvider:
    def validate_symbol(self, symbol: str) -> bool:
        raise ProviderNotReadyError("Ticker validation is scheduled for Day 1.")

    def get_history(self, symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        raise ProviderNotReadyError("Market history is scheduled for Day 1.")

    def get_latest(self, symbol: str) -> dict[str, Any]:
        raise ProviderNotReadyError("Latest market data is scheduled for Day 1.")


class VnstockFundamentalDataProvider:
    def get_financials(self, symbol: str) -> list[dict[str, Any]]:
        raise ProviderNotReadyError("Financial statements are scheduled for Day 2.")

    def get_key_metrics(self, symbol: str) -> dict[str, Any]:
        raise ProviderNotReadyError("Fundamental metrics are scheduled for Day 2.")
