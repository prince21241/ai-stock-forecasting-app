from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ForecastMetrics(BaseModel):
    model_mae_percent: float = Field(ge=0)
    baseline_mae_percent: float = Field(ge=0)
    directional_accuracy_percent: float = Field(ge=0, le=100)
    validation_observations: int = Field(gt=0)
    beats_baseline: bool


class ForecastResponse(BaseModel):
    id: int | None = None
    symbol: str
    as_of_date: date
    latest_close: float = Field(gt=0)
    predicted_return_percent: float
    predicted_price: float = Field(gt=0)
    price_range_low: float = Field(gt=0)
    price_range_high: float = Field(gt=0)
    probability_up_percent: float = Field(ge=0, le=100)
    training_observations: int
    model_name: str = "ridge_regression_v1"
    model_version: str
    trained_at: datetime
    signal_status: Literal["qualified", "no_signal"]
    metrics: ForecastMetrics
    disclaimer: str = "Experimental forecast for research only; not investment advice."


class ForecastHistoryResponse(BaseModel):
    symbol: str
    count: int
    data: list[ForecastResponse]
