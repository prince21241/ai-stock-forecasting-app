from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ForecastMetrics(BaseModel):
    model_mae_percent: float = Field(ge=0)
    baseline_mae_percent: float = Field(ge=0)
    directional_accuracy_percent: float = Field(ge=0, le=100)
    validation_observations: int = Field(gt=0)
    beats_baseline: bool
    brier_score: float | None = Field(default=None, ge=0, le=1)


class ModelComparisonEntry(BaseModel):
    model_name: str
    feature_set: Literal["price_only", "with_sentiment"] = "price_only"
    model_mae_percent: float = Field(ge=0)
    baseline_mae_percent: float = Field(ge=0)
    directional_accuracy_percent: float = Field(ge=0, le=100)
    validation_observations: int = Field(gt=0)
    beats_baseline: bool
    signal_status: Literal["qualified", "no_signal"]
    selected: bool


class SentimentComparison(BaseModel):
    available: bool
    price_only_mae_percent: float | None = Field(default=None, ge=0)
    with_sentiment_mae_percent: float | None = Field(default=None, ge=0)
    sentiment_improves_mae: bool | None = None
    selected_feature_set: Literal["price_only", "with_sentiment"] = "price_only"


class ReliabilityBin(BaseModel):
    bin_start_percent: float = Field(ge=0, le=100)
    bin_end_percent: float = Field(ge=0, le=100)
    mean_predicted_percent: float = Field(ge=0, le=100)
    observed_frequency_percent: float = Field(ge=0, le=100)
    sample_count: int = Field(gt=0)


class CalibrationSummary(BaseModel):
    method: str
    brier_score: float = Field(ge=0, le=1)
    reliability_bins: list[ReliabilityBin] = Field(default_factory=list)


class HorizonForecast(BaseModel):
    horizon: Literal["1d", "5d", "20d", "volatility"]
    label: str
    predicted_return_percent: float | None = None
    predicted_volatility_percent: float | None = Field(default=None, ge=0)
    predicted_price: float | None = Field(default=None, gt=0)
    probability_up_percent: float | None = Field(default=None, ge=0, le=100)
    signal_status: Literal["qualified", "no_signal", "insufficient_data"]
    metrics: ForecastMetrics | None = None


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
    model_name: str
    model_version: str
    trained_at: datetime
    sentiment_features_used: bool = False
    sentiment_comparison: SentimentComparison = Field(default_factory=SentimentComparison)
    model_comparison: list[ModelComparisonEntry] = Field(default_factory=list)
    calibration: CalibrationSummary | None = None
    horizons: list[HorizonForecast] = Field(default_factory=list)
    signal_status: Literal["qualified", "no_signal"]
    metrics: ForecastMetrics
    disclaimer: str = (
        "Experimental forecast for research only; not investment advice. "
        "Calibrated probabilities are in-sample Platt estimates."
    )


class ForecastHistoryResponse(BaseModel):
    symbol: str
    count: int
    data: list[ForecastResponse]
