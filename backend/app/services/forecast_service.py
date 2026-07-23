from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Literal

import numpy as np

from app.core.exceptions import MissingAPIKeyError
from app.repositories.forecast_repository import ForecastRepository, to_response
from app.repositories.stock_repository import StockRepository
from app.schemas.forecast import (
    CalibrationSummary,
    ForecastMetrics,
    ForecastResponse,
    HorizonForecast,
    ModelComparisonEntry,
    ReliabilityBin,
    SentimentComparison,
)
from app.services.alpha_vantage_news import AlphaVantageNewsClient
from app.services.forecast_calibration import calibrate_walk_forward
from app.services.forecast_features import (
    FeatureSet,
    build_feature_set,
    latest_feature_row,
    minimum_training_rows,
)
from app.services.forecast_models import DEFAULT_MODELS
from app.services.forecast_models.base import (
    ForecastModel,
    WalkForwardResult,
    walk_forward_evaluate,
)
from app.utils.validation import normalize_symbol

MINIMUM_PRICES = 100
MINIMUM_TRAINING_ROWS = 60
NEWS_FETCH_LIMIT = 200
QUALIFIED_DIRECTIONAL_ACCURACY = 0.55

HORIZON_CONFIG: tuple[tuple[str, str, int, Literal["return", "volatility"]], ...] = (
    ("1d", "Next trading day", 1, "return"),
    ("5d", "5 trading days", 5, "return"),
    ("20d", "20 trading days", 20, "return"),
    ("volatility", "Next-day volatility", 1, "volatility"),
)


class InsufficientForecastDataError(ValueError):
    pass


@dataclass(frozen=True)
class ModelEvaluation:
    model: ForecastModel
    evaluation: WalkForwardResult
    include_sentiment: bool


def _signal_status(evaluation: WalkForwardResult) -> Literal["qualified", "no_signal"]:
    if evaluation.model_mae < evaluation.baseline_mae and (
        evaluation.directional_accuracy >= QUALIFIED_DIRECTIONAL_ACCURACY
    ):
        return "qualified"
    return "no_signal"


def _metrics_from_evaluation(
    evaluation: WalkForwardResult, brier_score: float | None = None
) -> ForecastMetrics:
    return ForecastMetrics(
        model_mae_percent=round(evaluation.model_mae * 100, 3),
        baseline_mae_percent=round(evaluation.baseline_mae * 100, 3),
        directional_accuracy_percent=round(evaluation.directional_accuracy * 100, 1),
        validation_observations=len(evaluation.actuals),
        beats_baseline=evaluation.model_mae < evaluation.baseline_mae,
        brier_score=brier_score,
    )


def _comparison_entry(
    model_name: str,
    evaluation: WalkForwardResult,
    selected: bool,
    include_sentiment: bool,
) -> ModelComparisonEntry:
    return ModelComparisonEntry(
        model_name=model_name,
        feature_set="with_sentiment" if include_sentiment else "price_only",
        model_mae_percent=round(evaluation.model_mae * 100, 3),
        baseline_mae_percent=round(evaluation.baseline_mae * 100, 3),
        directional_accuracy_percent=round(evaluation.directional_accuracy * 100, 1),
        validation_observations=len(evaluation.actuals),
        beats_baseline=evaluation.model_mae < evaluation.baseline_mae,
        signal_status=_signal_status(evaluation),
        selected=selected,
    )


def _evaluate_models(
    models: tuple[ForecastModel, ...],
    dataset: FeatureSet,
    include_sentiment: bool,
) -> list[ModelEvaluation]:
    training_rows = minimum_training_rows(len(dataset.targets), MINIMUM_TRAINING_ROWS)
    evaluations: list[ModelEvaluation] = []
    for model in models:
        evaluation = walk_forward_evaluate(
            model, dataset.values, dataset.targets, training_rows
        )
        if len(evaluation.actuals) == 0:
            continue
        evaluations.append(ModelEvaluation(model, evaluation, include_sentiment))
    return evaluations


def _select_evaluation(evaluations: list[ModelEvaluation]) -> ModelEvaluation:
    return min(
        evaluations,
        key=lambda item: (
            item.evaluation.model_mae,
            -item.evaluation.directional_accuracy,
            item.model.name,
            0 if item.include_sentiment else 1,
        ),
    )


def _build_sentiment_comparison(
    price_only: ModelEvaluation | None,
    with_sentiment: ModelEvaluation | None,
    selected: ModelEvaluation,
    articles_available: bool,
) -> SentimentComparison:
    if not articles_available or price_only is None:
        return SentimentComparison(available=False, selected_feature_set="price_only")
    price_mae = round(price_only.evaluation.model_mae * 100, 3)
    sentiment_mae = (
        round(with_sentiment.evaluation.model_mae * 100, 3) if with_sentiment else None
    )
    improves = sentiment_mae is not None and sentiment_mae < price_mae
    selected_set: Literal["price_only", "with_sentiment"] = (
        "with_sentiment" if selected.include_sentiment else "price_only"
    )
    return SentimentComparison(
        available=True,
        price_only_mae_percent=price_mae,
        with_sentiment_mae_percent=sentiment_mae,
        sentiment_improves_mae=improves,
        selected_feature_set=selected_set,
    )


class ForecastService:
    def __init__(
        self,
        stock_repository: StockRepository,
        forecast_repository: ForecastRepository,
        news_client: AlphaVantageNewsClient | None = None,
        models: tuple[ForecastModel, ...] = DEFAULT_MODELS,
    ) -> None:
        self.stock_repository = stock_repository
        self.forecast_repository = forecast_repository
        self.news_client = news_client
        self.models = models

    async def _load_news(self, symbol: str):
        if self.news_client is None:
            return None, False
        try:
            articles = await self.news_client.fetch(symbol, NEWS_FETCH_LIMIT)
        except MissingAPIKeyError:
            return None, False
        return articles, bool(articles)

    def _evaluate_horizon(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        record_dates: list[date],
        articles,
        horizon_key: str,
        label: str,
        horizon_days: int,
        target_mode: Literal["return", "volatility"],
        selected_model: ForecastModel,
        include_sentiment: bool,
        latest_close: float,
    ) -> HorizonForecast:
        dataset = build_feature_set(
            close,
            high,
            low,
            volume,
            record_dates,
            horizon_days=horizon_days,
            target_mode=target_mode,
            include_sentiment=include_sentiment,
            articles=articles,
        )
        training_rows = minimum_training_rows(len(dataset.targets), MINIMUM_TRAINING_ROWS)
        evaluation = walk_forward_evaluate(
            selected_model,
            dataset.values,
            dataset.targets,
            training_rows,
        )
        if len(evaluation.actuals) == 0:
            return HorizonForecast(
                horizon=horizon_key,
                label=label,
                signal_status="insufficient_data",
            )

        final_model = selected_model.fit(dataset.values, dataset.targets)
        latest_row = latest_feature_row(
            close,
            high,
            low,
            volume,
            record_dates,
            include_sentiment=include_sentiment,
            articles=articles,
        )
        predicted_value = selected_model.predict(final_model, latest_row)
        calibration = None
        probability_up = None
        if target_mode == "return":
            calibration = calibrate_walk_forward(evaluation, predicted_value)
            probability_up = calibration.probability_up_percent

        metrics = _metrics_from_evaluation(
            evaluation,
            brier_score=calibration.brier_score if calibration else None,
        )
        if target_mode == "volatility":
            return HorizonForecast(
                horizon=horizon_key,
                label=label,
                predicted_volatility_percent=round(predicted_value * 100, 3),
                signal_status=_signal_status(evaluation),
                metrics=metrics,
            )

        predicted_price = latest_close * (1 + predicted_value)
        return HorizonForecast(
            horizon=horizon_key,
            label=label,
            predicted_return_percent=round(predicted_value * 100, 3),
            predicted_price=round(float(predicted_price), 4),
            probability_up_percent=probability_up,
            signal_status=_signal_status(evaluation),
            metrics=metrics,
        )

    async def train_and_forecast(self, raw_symbol: str) -> ForecastResponse:
        symbol = normalize_symbol(raw_symbol)
        records = await self.stock_repository.get_all_prices_by_symbol(symbol)
        if len(records) < MINIMUM_PRICES:
            message = (
                f"At least {MINIMUM_PRICES} stored daily records are required; "
                f"{len(records)} found."
            )
            raise InsufficientForecastDataError(message)

        articles, articles_available = await self._load_news(symbol)
        record_dates = [row.trading_date for row in records]
        close = np.asarray([float(row.close_price) for row in records])
        high = np.asarray([float(row.high_price) for row in records])
        low = np.asarray([float(row.low_price) for row in records])
        volume = np.asarray([float(row.volume) for row in records])

        price_only_dataset = build_feature_set(
            close, high, low, volume, record_dates, include_sentiment=False
        )
        price_only_evaluations = _evaluate_models(
            self.models, price_only_dataset, include_sentiment=False
        )
        if not price_only_evaluations:
            raise InsufficientForecastDataError(
                "Not enough observations for walk-forward validation."
            )

        with_sentiment_evaluations: list[ModelEvaluation] = []
        if articles_available:
            sentiment_dataset = build_feature_set(
                close,
                high,
                low,
                volume,
                record_dates,
                include_sentiment=True,
                articles=articles,
            )
            with_sentiment_evaluations = _evaluate_models(
                self.models, sentiment_dataset, include_sentiment=True
            )

        all_evaluations = price_only_evaluations + with_sentiment_evaluations
        selected = _select_evaluation(all_evaluations)
        selected_dataset = build_feature_set(
            close,
            high,
            low,
            volume,
            record_dates,
            include_sentiment=selected.include_sentiment,
            articles=articles if selected.include_sentiment else None,
        )

        price_only_best = min(
            price_only_evaluations,
            key=lambda item: (item.evaluation.model_mae, item.model.name),
        )
        with_sentiment_best = (
            min(
                with_sentiment_evaluations,
                key=lambda item: (item.evaluation.model_mae, item.model.name),
            )
            if with_sentiment_evaluations
            else None
        )

        comparison = [
            _comparison_entry(
                item.model.name,
                item.evaluation,
                selected=item.model.name == selected.model.name
                and item.include_sentiment == selected.include_sentiment,
                include_sentiment=item.include_sentiment,
            )
            for item in all_evaluations
        ]
        sentiment_comparison = _build_sentiment_comparison(
            price_only_best,
            with_sentiment_best,
            selected,
            articles_available,
        )

        final_model = selected.model.fit(selected_dataset.values, selected_dataset.targets)
        latest_row = latest_feature_row(
            close,
            high,
            low,
            volume,
            record_dates,
            include_sentiment=selected.include_sentiment,
            articles=articles if selected.include_sentiment else None,
        )
        predicted_return = selected.model.predict(final_model, latest_row)
        calibration = calibrate_walk_forward(selected.evaluation, predicted_return)
        errors = selected.evaluation.errors
        interval = float(np.quantile(np.abs(errors), 0.9))
        latest_close = float(close[-1])
        low_price = latest_close * (1 + predicted_return - interval)
        high_price = latest_close * (1 + predicted_return + interval)

        horizons = [
            self._evaluate_horizon(
                close,
                high,
                low,
                volume,
                record_dates,
                articles if selected.include_sentiment else None,
                horizon_key,
                label,
                horizon_days,
                target_mode,
                selected.model,
                selected.include_sentiment,
                latest_close,
            )
            for horizon_key, label, horizon_days, target_mode in HORIZON_CONFIG
        ]

        now = datetime.now(UTC)
        forecast = ForecastResponse(
            symbol=symbol,
            as_of_date=records[-1].trading_date,
            latest_close=round(latest_close, 4),
            predicted_return_percent=round(predicted_return * 100, 3),
            predicted_price=round(latest_close * (1 + predicted_return), 4),
            price_range_low=round(max(float(low_price), 0.0001), 4),
            price_range_high=round(float(high_price), 4),
            probability_up_percent=calibration.probability_up_percent,
            training_observations=len(selected_dataset.targets),
            model_name=selected.model.name,
            model_version=f"{symbol}-{records[-1].trading_date.isoformat()}-{len(records)}",
            trained_at=now,
            sentiment_features_used=selected.include_sentiment,
            sentiment_comparison=sentiment_comparison,
            model_comparison=comparison,
            calibration=CalibrationSummary(
                method=calibration.method,
                brier_score=calibration.brier_score,
                reliability_bins=[
                    ReliabilityBin(
                        bin_start_percent=bin_entry.bin_start_percent,
                        bin_end_percent=bin_entry.bin_end_percent,
                        mean_predicted_percent=bin_entry.mean_predicted_percent,
                        observed_frequency_percent=bin_entry.observed_frequency_percent,
                        sample_count=bin_entry.sample_count,
                    )
                    for bin_entry in calibration.reliability_bins
                ],
            ),
            horizons=horizons,
            signal_status=_signal_status(selected.evaluation),
            metrics=_metrics_from_evaluation(
                selected.evaluation, brier_score=calibration.brier_score
            ),
        )
        return to_response(await self.forecast_repository.save(forecast))

    async def get_latest(self, raw_symbol: str) -> ForecastResponse | None:
        run = await self.forecast_repository.get_latest(normalize_symbol(raw_symbol))
        return to_response(run) if run else None

    async def get_history(self, raw_symbol: str, limit: int) -> list[ForecastResponse]:
        symbol = normalize_symbol(raw_symbol)
        runs = await self.forecast_repository.get_history(symbol, limit)
        return [to_response(run) for run in runs]
