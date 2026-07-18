from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp

import numpy as np

from app.repositories.stock_repository import StockRepository
from app.schemas.forecast import ForecastMetrics, ForecastResponse
from app.utils.validation import normalize_symbol

MINIMUM_PRICES = 100
MINIMUM_TRAINING_ROWS = 60
RIDGE_ALPHA = 1.0


class InsufficientForecastDataError(ValueError):
    pass


@dataclass(frozen=True)
class FeatureSet:
    values: np.ndarray
    targets: np.ndarray


def _features(
    close: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray
) -> FeatureSet:
    rows: list[list[float]] = []
    targets: list[float] = []
    for index in range(20, len(close) - 1):
        returns = np.diff(close[index - 20 : index + 1]) / close[index - 20 : index]
        volume_window = volume[index - 20 : index + 1]
        rows.append(
            [
                returns[-1],
                close[index] / close[index - 5] - 1,
                close[index] / close[index - 20] - 1,
                float(np.std(returns[-5:])),
                float(np.std(returns)),
                close[index] / float(np.mean(close[index - 4 : index + 1])) - 1,
                close[index] / float(np.mean(close[index - 19 : index + 1])) - 1,
                (high[index] - low[index]) / close[index],
                volume[index] / float(np.mean(volume_window)) - 1,
            ]
        )
        targets.append(close[index + 1] / close[index] - 1)
    return FeatureSet(np.asarray(rows, dtype=float), np.asarray(targets, dtype=float))


def _latest_features(
    close: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray
) -> np.ndarray:
    extended = np.append(close, close[-1])
    values = _features(
        extended, np.append(high, high[-1]), np.append(low, low[-1]), np.append(volume, volume[-1])
    )
    return values.values[-1]


def _fit(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale == 0] = 1
    normalized = (x - mean) / scale
    design = np.column_stack((np.ones(len(normalized)), normalized))
    penalty = np.eye(design.shape[1]) * RIDGE_ALPHA
    penalty[0, 0] = 0
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    return coefficients, mean, scale


def _predict(row: np.ndarray, model: tuple[np.ndarray, np.ndarray, np.ndarray]) -> float:
    coefficients, mean, scale = model
    return float(np.concatenate(([1.0], (row - mean) / scale)) @ coefficients)


class ForecastService:
    def __init__(self, repository: StockRepository) -> None:
        self.repository = repository

    async def train_and_forecast(self, raw_symbol: str) -> ForecastResponse:
        symbol = normalize_symbol(raw_symbol)
        records = await self.repository.get_all_prices_by_symbol(symbol)
        if len(records) < MINIMUM_PRICES:
            message = (
                f"At least {MINIMUM_PRICES} stored daily records are required; "
                f"{len(records)} found."
            )
            raise InsufficientForecastDataError(
                message
            )
        close = np.asarray([float(row.close_price) for row in records])
        high = np.asarray([float(row.high_price) for row in records])
        low = np.asarray([float(row.low_price) for row in records])
        volume = np.asarray([float(row.volume) for row in records])
        dataset = _features(close, high, low, volume)

        predictions: list[float] = []
        actuals: list[float] = []
        for index in range(MINIMUM_TRAINING_ROWS, len(dataset.targets)):
            model = _fit(dataset.values[:index], dataset.targets[:index])
            predictions.append(_predict(dataset.values[index], model))
            actuals.append(float(dataset.targets[index]))
        if not predictions:
            raise InsufficientForecastDataError(
                "Not enough observations for walk-forward validation."
            )

        prediction_array = np.asarray(predictions)
        actual_array = np.asarray(actuals)
        errors = actual_array - prediction_array
        model_mae = float(np.mean(np.abs(errors)))
        baseline_mae = float(np.mean(np.abs(actual_array)))
        directional_accuracy = float(np.mean(np.sign(prediction_array) == np.sign(actual_array)))

        final_model = _fit(dataset.values, dataset.targets)
        predicted_return = _predict(_latest_features(close, high, low, volume), final_model)
        residual_std = max(float(np.std(errors)), 1e-6)
        probability_up = 1 / (1 + exp(-predicted_return / residual_std * 1.7))
        interval = float(np.quantile(np.abs(errors), 0.9))
        latest_close = close[-1]
        low_price = latest_close * (1 + predicted_return - interval)
        high_price = latest_close * (1 + predicted_return + interval)
        now = datetime.now(UTC)
        return ForecastResponse(
            symbol=symbol,
            as_of_date=records[-1].trading_date,
            latest_close=round(float(latest_close), 4),
            predicted_return_percent=round(predicted_return * 100, 3),
            predicted_price=round(float(latest_close * (1 + predicted_return)), 4),
            price_range_low=round(max(float(low_price), 0.0001), 4),
            price_range_high=round(float(high_price), 4),
            probability_up_percent=round(probability_up * 100, 1),
            training_observations=len(dataset.targets),
            model_version=f"{symbol}-{records[-1].trading_date.isoformat()}-{len(records)}",
            trained_at=now,
            metrics=ForecastMetrics(
                model_mae_percent=round(model_mae * 100, 3),
                baseline_mae_percent=round(baseline_mae * 100, 3),
                directional_accuracy_percent=round(directional_accuracy * 100, 1),
                validation_observations=len(actuals),
                beats_baseline=model_mae < baseline_mae,
            ),
        )
