from pydantic import AliasChoices, BaseModel, Field, field_validator
from src.models import Stock
from src.schemas.data import MarketBar, MarketSnapshot, FundamentalSnapshot, NewsItem


class SecurityMetadata(BaseModel):
    symbol: str
    exchange: str
    instrument_type: str = 'Stock'
    company_name: str | None = None
    display_name_en: str | None = None
    source: str = 'SSI:FastConnect'


class SecurityUniverse(BaseModel):
    securities: list[SecurityMetadata]
    raw_count: int
    exclusions: dict[str, int]
    duplicate_count: int = 0


def normalize_symbol(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Symbol must be a string")
    return value.strip().upper()


class SymbolRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20, pattern=r"^[A-Z0-9]+$", validation_alias=AliasChoices("symbol", "ticker"))
    normalize = field_validator("symbol", mode="before")(normalize_symbol)


class SymbolValidation(BaseModel):
    symbol: str
    valid: bool | None = None
    status: str = "not_implemented"
    message: str = "Provider validation is not implemented in Day 0."


class StockOverview(BaseModel):
    stock: Stock
    history: list[MarketBar]
    market: MarketSnapshot
    fundamentals: FundamentalSnapshot
    news: list[NewsItem]
