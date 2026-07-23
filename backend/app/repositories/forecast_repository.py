import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.forecast_run import ForecastRun
from app.schemas.forecast import (
    CalibrationSummary,
    ForecastMetrics,
    ForecastResponse,
    HorizonForecast,
    ModelComparisonEntry,
    SentimentComparison,
)


def to_response(run: ForecastRun) -> ForecastResponse:
    comparison = [
        ModelComparisonEntry.model_validate(entry)
        for entry in json.loads(run.model_comparison_json or "[]")
    ]
    sentiment_comparison = SentimentComparison.model_validate(
        json.loads(run.sentiment_comparison_json or "{}")
    )
    calibration = (
        CalibrationSummary.model_validate(json.loads(run.calibration_json))
        if run.calibration_json
        else None
    )
    horizons = [
        HorizonForecast.model_validate(entry)
        for entry in json.loads(run.horizons_json or "[]")
    ]
    return ForecastResponse(
        id=run.id,
        symbol=run.symbol,
        as_of_date=run.as_of_date,
        latest_close=run.latest_close,
        predicted_return_percent=run.predicted_return_percent,
        predicted_price=run.predicted_price,
        price_range_low=run.price_range_low,
        price_range_high=run.price_range_high,
        probability_up_percent=run.probability_up_percent,
        training_observations=run.training_observations,
        model_name=run.model_name,
        model_version=run.model_version,
        trained_at=run.trained_at,
        sentiment_features_used=run.sentiment_features_used,
        sentiment_comparison=sentiment_comparison,
        model_comparison=comparison,
        calibration=calibration,
        horizons=horizons,
        signal_status=run.signal_status,
        metrics=ForecastMetrics(
            model_mae_percent=run.model_mae_percent,
            baseline_mae_percent=run.baseline_mae_percent,
            directional_accuracy_percent=run.directional_accuracy_percent,
            validation_observations=run.validation_observations,
            beats_baseline=run.beats_baseline,
            brier_score=json.loads(run.calibration_json).get("brier_score")
            if run.calibration_json
            else None,
        ),
    )


class ForecastRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, forecast: ForecastResponse) -> ForecastRun:
        values = forecast.model_dump(
            exclude={
                "id",
                "metrics",
                "disclaimer",
                "model_comparison",
                "sentiment_comparison",
                "calibration",
                "horizons",
            }
        )
        values.update(forecast.metrics.model_dump(exclude={"brier_score"}))
        values["model_comparison_json"] = json.dumps(
            [entry.model_dump(mode="json") for entry in forecast.model_comparison]
        )
        values["sentiment_comparison_json"] = json.dumps(
            forecast.sentiment_comparison.model_dump(mode="json")
        )
        values["calibration_json"] = (
            json.dumps(forecast.calibration.model_dump(mode="json"))
            if forecast.calibration
            else None
        )
        values["horizons_json"] = json.dumps(
            [horizon.model_dump(mode="json") for horizon in forecast.horizons]
        )
        run = ForecastRun(**values)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_latest(self, symbol: str) -> ForecastRun | None:
        return await self.session.scalar(
            select(ForecastRun)
            .where(ForecastRun.symbol == symbol)
            .order_by(ForecastRun.trained_at.desc(), ForecastRun.id.desc())
            .limit(1)
        )

    async def get_history(self, symbol: str, limit: int = 10) -> list[ForecastRun]:
        result = await self.session.scalars(
            select(ForecastRun)
            .where(ForecastRun.symbol == symbol)
            .order_by(ForecastRun.trained_at.desc(), ForecastRun.id.desc())
            .limit(limit)
        )
        return list(result.all())
