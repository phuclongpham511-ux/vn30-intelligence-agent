from functools import lru_cache
from sqlmodel import Session, select
from src.models import Stock
from src.providers.base import MarketDataProvider, ProviderNotReadyError
from src.providers.vnstock import VnstockMarketDataProvider
from src.providers.ssi import SsiMarketDataProvider
from src.config.settings import get_settings
from src.schemas.stocks import SymbolValidation


@lru_cache
def get_market_provider() -> MarketDataProvider:
    selected = get_settings().market_data_provider
    if selected == "ssi":
        return SsiMarketDataProvider()
    if selected == "vnstock":
        return VnstockMarketDataProvider()
    raise ProviderNotReadyError("Unknown MARKET_DATA_PROVIDER. Use ssi or vnstock.")


def list_stocks(session: Session):
    return session.exec(select(Stock).where(Stock.is_active == True).order_by(Stock.symbol)).all()


def find_stock(session: Session, symbol: str):
    return session.exec(select(Stock).where(Stock.symbol == symbol.strip().upper())).first()


def validate_symbol(symbol: str, provider: MarketDataProvider) -> SymbolValidation:
    try:
        valid = provider.validate_symbol(symbol)
    except ProviderNotReadyError as exc:
        return SymbolValidation(symbol=symbol, message=str(exc))
    return SymbolValidation(symbol=symbol, valid=valid, status="validated", message="Provider validation completed.")
