from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from src.db.session import get_session
from src.models import Stock
from src.providers.base import MarketDataProvider, FundamentalDataProvider, NewsProvider
from src.schemas.stocks import SymbolRequest, SymbolValidation, StockOverview
from src.schemas.data import MarketBar, MarketSnapshot, FundamentalSnapshot, NewsItem, TechnicalBar, FundamentalPeriod
from src.services.stocks import find_stock, get_market_provider, list_stocks, validate_symbol
from src.services import data

router = APIRouter(prefix="/stocks", tags=["stocks"])


def require_stock(symbol: str, session: Session = Depends(get_session)) -> Stock:
    stock = find_stock(session, symbol)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.get("", response_model=list[Stock])
def stocks(session: Session = Depends(get_session)):
    return list_stocks(session)


@router.post("", response_model=Stock, status_code=201)
def add_stock(body: SymbolRequest, session: Session = Depends(get_session),
              provider: MarketDataProvider = Depends(get_market_provider)):
    existing = find_stock(session, body.symbol)
    if existing:
        return existing
    if not provider.validate_symbol(body.symbol):
        raise HTTPException(status_code=404, detail="Ticker was not found in the provider universe")
    name_lookup = getattr(provider, "company_name", None)
    record = Stock(symbol=body.symbol, company_name=name_lookup(body.symbol) if name_lookup else None)
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = find_stock(session, body.symbol)
        if existing:
            return existing
        raise
    session.refresh(record)
    return record


@router.post("/validate", response_model=SymbolValidation)
def validate(body: SymbolRequest, provider: MarketDataProvider = Depends(get_market_provider)):
    return validate_symbol(body.symbol, provider)


@router.get("/{symbol}", response_model=Stock)
def stock(record: Stock = Depends(require_stock)):
    return record


@router.get("/{symbol}/history", response_model=list[MarketBar])
def stock_history(start: date | None = None, end: date | None = None,
                  record: Stock = Depends(require_stock),
                  provider: MarketDataProvider = Depends(get_market_provider)):
    end = end or date.today()
    start = start or end - timedelta(days=180)
    if start > end or (end - start).days > 730 or end > date.today():
        raise HTTPException(status_code=422, detail="Use an ordered date range of at most 730 days, ending today or earlier")
    return data.history(record.symbol, provider, start, end)


@router.get("/{symbol}/market", response_model=MarketSnapshot)
def stock_market(record: Stock = Depends(require_stock),
                 provider: MarketDataProvider = Depends(get_market_provider)):
    return data.market(record.symbol, provider)


@router.get("/{symbol}/technical-history", response_model=list[TechnicalBar])
def stock_technicals(start: date | None = None, end: date | None = None,
                     record: Stock = Depends(require_stock),
                     provider: MarketDataProvider = Depends(get_market_provider)):
    end = end or date.today()
    start = start or end - timedelta(days=180)
    if start > end or (end - start).days > 730 or end > date.today():
        raise HTTPException(status_code=422, detail="Use an ordered date range of at most 730 days, ending today or earlier")
    return data.technicals(record.symbol, provider, start, end)


@router.get("/{symbol}/fundamentals/history", response_model=list[FundamentalPeriod])
def stock_fundamental_history(limit: int = Query(default=4, ge=1, le=20),
                              record: Stock = Depends(require_stock),
                              provider: FundamentalDataProvider = Depends(data.get_fundamental_provider)):
    return data.annual_history(record.symbol, provider, limit)


@router.get("/{symbol}/fundamentals", response_model=FundamentalSnapshot)
def stock_fundamentals(record: Stock = Depends(require_stock),
                       provider: FundamentalDataProvider = Depends(data.get_fundamental_provider)):
    return data.fundamentals(record.symbol, provider)


@router.get("/{symbol}/news", response_model=list[NewsItem])
def stock_news(limit: int = Query(default=5, ge=1, le=20),
               record: Stock = Depends(require_stock),
               provider: NewsProvider = Depends(data.get_news_provider)):
    return provider.get_news(record.symbol, limit)


@router.get("/{symbol}/overview", response_model=StockOverview)
def overview(record: Stock = Depends(require_stock),
             market: MarketDataProvider = Depends(get_market_provider),
             fundamental: FundamentalDataProvider = Depends(data.get_fundamental_provider),
             news: NewsProvider = Depends(data.get_news_provider)):
    bars = data.history(record.symbol, market)
    return {
        "stock": record,
        "history": bars,
        "market": data.market_snapshot(record.symbol, bars, market.source),
        "fundamentals": data.fundamentals(record.symbol, fundamental),
        "news": news.get_news(record.symbol, 5),
    }
