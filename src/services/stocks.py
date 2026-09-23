from sqlmodel import Session, select
from src.models import Stock
from src.providers.base import MarketDataProvider, ProviderNotReadyError
from src.providers.vnstock import VnstockMarketDataProvider
from src.schemas.stocks import SymbolValidation


def get_market_provider() -> MarketDataProvider:
    return VnstockMarketDataProvider()


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
