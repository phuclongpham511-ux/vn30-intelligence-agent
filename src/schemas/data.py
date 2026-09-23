from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class MarketBar(DataModel):
    ticker: str
    date: date
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    source: str
    currency: str = "VND"

    @model_validator(mode="after")
    def valid_range(self):
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close) or self.low > self.high:
            raise ValueError("Invalid OHLC range")
        return self


class MarketSnapshot(DataModel):
    ticker: str
    as_of: date | None = None
    close: float | None = None
    daily_return: float | None = None
    return_5d: float | None = None
    return_20d: float | None = None
    ma20: float | None = None
    ma50: float | None = None
    rsi14: float | None = None
    avg_volume_20d: float | None = None
    relative_volume_20d: float | None = None
    volatility_20d: float | None = None
    drawdown_from_20d_high: float | None = None
    source: str
    currency: str = "VND"


class FundamentalRecord(DataModel):
    ticker: str
    period: str = Field(pattern=r"^\d{4}(?:-Q[1-4])?$")
    revenue: float | None = None
    net_profit: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None
    roe: float | None = None
    source: str
    currency: str = "VND"


class FundamentalSnapshot(DataModel):
    ticker: str
    period: str | None = None
    revenue: float | None = None
    net_profit: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None
    roe: float | None = None
    revenue_growth_yoy: float | None = None
    net_profit_growth_yoy: float | None = None
    gross_margin_change: float | None = None
    net_margin_change: float | None = None
    roe_change: float | None = None
    source: str
    currency: str = "VND"


class NewsItem(DataModel):
    id: str
    ticker: str
    published_at: datetime
    title: str
    summary_or_content: str | None = None
    source: str
    url: str | None = None
    is_fixture: bool = False
