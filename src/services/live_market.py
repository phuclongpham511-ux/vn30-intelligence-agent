from functools import lru_cache

from src.providers.ssi import SsiMarketDataProvider
from src.providers.ssi.live import SsiLiveMarket
from src.providers.base import ProviderNotReadyError
from src.services.stocks import get_market_provider


@lru_cache(maxsize=1)
def get_live_market():
    provider = get_market_provider()
    if not isinstance(provider, SsiMarketDataProvider):
        raise ProviderNotReadyError('Live SSI market data is unavailable.')
    return SsiLiveMarket(provider)


def close_live_market():
    if get_live_market.cache_info().currsize:
        get_live_market().close()
        get_live_market.cache_clear()
