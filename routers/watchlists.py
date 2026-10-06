"""Browser-local monitoring; account-owned persistence remains an explicit scaffold."""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select
from src.db.session import get_session
from src.models import Stock, Security
from src.news.models import NewsArticle
from src.news.normalization import utc
from src.news.service import articles
from src.schemas.stocks import SymbolRequest

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


class MonitoringRequest(BaseModel):
    symbols: list[str] = Field(max_length=50)

    @field_validator('symbols')
    @classmethod
    def normalize_symbols(cls, values):
        return list(dict.fromkeys(SymbolRequest(symbol=value).symbol for value in values))


class Development(BaseModel):
    story_id: str
    title: str
    first_seen_at: datetime
    published_at: datetime | None
    source_count: int
    articles: list[NewsArticle]


class MonitoredStock(BaseModel):
    symbol: str
    status: Literal['ready', 'unavailable']
    developments: list[Development] | None


class MonitoringResponse(BaseModel):
    as_of: datetime
    window_start: datetime
    stocks: list[MonitoredStock]


@router.post('/monitoring', response_model=MonitoringResponse)
def monitoring(body: MonitoringRequest, session: Annotated[Session, Depends(get_session)]):
    """One development per Story, using only exact ticker-tagged evidence."""
    now = datetime.now(timezone.utc)
    available = {stock.symbol for stock in session.exec(
        select(Stock).where(Stock.symbol.in_(body.symbols), Stock.is_active == True)
    ).all()}
    available.update(stock.symbol for stock in session.exec(select(Security).where(
        Security.symbol.in_(body.symbols), Security.is_active == True)).all())
    recent = articles(session, now=now) if available else []
    output = []
    for symbol in body.symbols:
        if symbol not in available:
            output.append(MonitoredStock(symbol=symbol, status='unavailable', developments=None))
            continue
        grouped = {}
        for article in recent:
            if symbol in {ticker.upper() for ticker in article.tickers}:
                grouped.setdefault(article.story_id, []).append(article)
        developments = [Development(
            story_id=story_id, title=matching[0].title,
            first_seen_at=min(utc(article.first_seen_at) for article in matching),
            published_at=matching[0].published_at,
            source_count=len({article.publisher_group for article in matching}),
            articles=[article.model_copy(update={
                'published_at': utc(article.published_at) if article.published_at else None,
                'first_seen_at': utc(article.first_seen_at),
                'last_seen_at': utc(article.last_seen_at),
            }) for article in matching[:5]],
        ) for story_id, matching in grouped.items()]
        developments.sort(key=lambda row: (row.first_seen_at, row.story_id), reverse=True)
        output.append(MonitoredStock(symbol=symbol, status='ready', developments=developments))
    return MonitoringResponse(as_of=now, window_start=now-timedelta(hours=72), stocks=output)


class WatchlistCreate(BaseModel):
    user_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)


def not_ready():
    raise HTTPException(status_code=501, detail="Watchlist behavior is not implemented in Day 0.")


@router.get("")
def list_watchlists():
    not_ready()


@router.post("")
def create_watchlist(body: WatchlistCreate):
    not_ready()


@router.post("/{id}/stocks")
def add_stock(id: int, body: SymbolRequest):
    not_ready()


@router.delete("/{id}/stocks/{symbol}")
def remove_stock(id: int, symbol: str):
    not_ready()
