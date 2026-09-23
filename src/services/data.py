from datetime import date, timedelta
from functools import lru_cache

from src.analytics.fundamentals import fundamental_snapshot
from src.analytics.market import market_snapshot
from src.providers.vnstock import VnstockFundamentalDataProvider
from src.providers.news import FixtureNewsProvider
from src.providers.base import MarketDataProvider, FundamentalDataProvider, NewsProvider
from src.schemas.data import MarketBar, MarketSnapshot, FundamentalSnapshot


@lru_cache
def get_fundamental_provider() -> FundamentalDataProvider:
    return VnstockFundamentalDataProvider()


@lru_cache
def get_news_provider() -> NewsProvider:
    return FixtureNewsProvider()


def history(symbol: str, provider: MarketDataProvider, start: date | None = None, end: date | None = None) -> list[MarketBar]:
    end = end or date.today()
    start = start or end - timedelta(days=180)
    return provider.get_history(symbol, start, end)


def market(symbol: str, provider: MarketDataProvider) -> MarketSnapshot:
    return market_snapshot(symbol, history(symbol, provider), provider.source)


def fundamentals(symbol: str, provider: FundamentalDataProvider) -> FundamentalSnapshot:
    return fundamental_snapshot(symbol, provider.get_financials(symbol), provider.source)
