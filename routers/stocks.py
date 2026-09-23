from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from src.db.session import get_session
from src.models import Stock
from src.providers.base import MarketDataProvider
from src.schemas.stocks import SymbolRequest, SymbolValidation
from src.services.stocks import find_stock, get_market_provider, list_stocks, validate_symbol

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[Stock])
def stocks(session: Session = Depends(get_session)):
    return list_stocks(session)


@router.post("/validate", response_model=SymbolValidation)
def validate(body: SymbolRequest, provider: MarketDataProvider = Depends(get_market_provider)):
    return validate_symbol(body.symbol, provider)


@router.get("/{symbol}", response_model=Stock)
def stock(symbol: str, session: Session = Depends(get_session)):
    result = find_stock(session, symbol)
    if result is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return result
