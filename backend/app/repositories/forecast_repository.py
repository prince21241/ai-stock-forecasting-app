from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.forecast_run import ForecastRun
from app.schemas.forecast import ForecastMetrics, ForecastResponse


def to_response(run: ForecastRun) -> ForecastResponse:
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
        signal_status=run.signal_status,
        metrics=ForecastMetrics(
            model_mae_percent=run.model_mae_percent,
            baseline_mae_percent=run.baseline_mae_percent,
            directional_accuracy_percent=run.directional_accuracy_percent,
            validation_observations=run.validation_observations,
            beats_baseline=run.beats_baseline,
        ),
    )


class ForecastRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, forecast: ForecastResponse) -> ForecastRun:
        values = forecast.model_dump(exclude={"id", "metrics", "disclaimer"})
        values.update(forecast.metrics.model_dump())
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
