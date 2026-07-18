from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StockPriceBase(BaseModel):
    symbol: str
    trading_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int = Field(ge=0)
    source: str = "alpha_vantage"


class StockPriceCreate(StockPriceBase):
    pass


class StockPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trading_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int


class StockListResponse(BaseModel):
    symbol: str
    count: int
    start_date: date | None
    end_date: date | None
    order: Literal["asc", "desc"]
    source: str = "alpha_vantage"
    cached: bool
    data: list[StockPriceRead]


class StockLatestResponse(BaseModel):
    symbol: str
    source: str = "alpha_vantage"
    cached: bool
    data: StockPriceRead


class StockSyncResponse(BaseModel):
    symbol: str
    fetched_records: int
    inserted_or_updated_records: int
    latest_trading_date: date | None
    source: str = "alpha_vantage"
    synced_at: datetime


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unavailable"]
    application: str
    database: Literal["healthy", "unavailable"]
    redis: Literal["healthy", "unavailable"]
