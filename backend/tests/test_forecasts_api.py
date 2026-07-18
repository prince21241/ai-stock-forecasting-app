from datetime import date, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stock_repository import StockRepository
from app.schemas.stock import StockPriceCreate


async def seed_prices(session: AsyncSession, count: int = 100) -> None:
    start = date(2023, 1, 2)
    prices = []
    close = Decimal("100")
    for index in range(count):
        close *= Decimal("1.001") + Decimal(index % 7 - 3) / Decimal("1000")
        prices.append(
            StockPriceCreate(
                symbol="AAPL",
                trading_date=start + timedelta(days=index),
                open_price=close * Decimal("0.998"),
                high_price=close * Decimal("1.008"),
                low_price=close * Decimal("0.992"),
                close_price=close,
                volume=1_000_000 + index * 1000,
            )
        )
    await StockRepository(session).bulk_upsert_prices(prices)


async def test_train_forecast_returns_evaluation(
    client: AsyncClient, session: AsyncSession
) -> None:
    await seed_prices(session)
    response = await client.post("/api/v1/forecasts/AAPL/train")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert body["training_observations"] == 79
    assert body["metrics"]["validation_observations"] == 19
    assert 0 <= body["probability_up_percent"] <= 100
    assert body["price_range_low"] < body["price_range_high"]
    assert body["id"] is not None
    assert body["signal_status"] in {"qualified", "no_signal"}

    latest = await client.get("/api/v1/forecasts/AAPL/latest")
    assert latest.status_code == 200
    assert latest.json()["id"] == body["id"]

    await client.post("/api/v1/forecasts/AAPL/train")
    history = await client.get("/api/v1/forecasts/AAPL/history?limit=5")
    assert history.status_code == 200
    assert history.json()["count"] == 2
    assert len(history.json()["data"]) == 2


async def test_train_forecast_requires_history(client: AsyncClient) -> None:
    response = await client.post("/api/v1/forecasts/MSFT/train")
    assert response.status_code == 422
    assert "At least 100" in response.json()["detail"]


async def test_latest_forecast_returns_404_when_missing(client: AsyncClient) -> None:
    response = await client.get("/api/v1/forecasts/MSFT/latest")
    assert response.status_code == 404
