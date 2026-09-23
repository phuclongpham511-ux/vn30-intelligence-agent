"""Explicit scaffolds until user identity and watchlist behavior are implemented."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.schemas.stocks import SymbolRequest

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


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
