from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    __table_args__ = (Index("ix_forecast_runs_symbol_trained", "symbol", "trained_at"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    latest_close: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_return_percent: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_range_low: Mapped[float] = mapped_column(Float, nullable=False)
    price_range_high: Mapped[float] = mapped_column(Float, nullable=False)
    probability_up_percent: Mapped[float] = mapped_column(Float, nullable=False)
    training_observations: Mapped[int] = mapped_column(Integer, nullable=False)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    model_mae_percent: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_mae_percent: Mapped[float] = mapped_column(Float, nullable=False)
    directional_accuracy_percent: Mapped[float] = mapped_column(Float, nullable=False)
    validation_observations: Mapped[int] = mapped_column(Integer, nullable=False)
    beats_baseline: Mapped[bool] = mapped_column(Boolean, nullable=False)
    signal_status: Mapped[str] = mapped_column(String(20), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
