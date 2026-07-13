from httpx import AsyncClient

from app.main import app
from tests.conftest import FakeCache


async def test_sync_and_read_are_idempotent(client: AsyncClient) -> None:
    first = await client.post("/api/v1/stocks/aapl/sync")
    second = await client.post("/api/v1/stocks/AAPL/sync")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["fetched_records"] == 2

    response = await client.get("/api/v1/stocks/AAPL?order=asc")
    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert response.json()["data"][0]["trading_date"] == "2024-01-02"


async def test_latest_price(client: AsyncClient) -> None:
    await client.post("/api/v1/stocks/AAPL/sync")
    response = await client.get("/api/v1/stocks/AAPL/latest")
    assert response.status_code == 200
    assert response.json()["data"]["trading_date"] == "2024-01-03"


async def test_api_filters_and_limits(client: AsyncClient) -> None:
    await client.post("/api/v1/stocks/AAPL/sync")
    response = await client.get(
        "/api/v1/stocks/AAPL?start_date=2024-01-02&end_date=2024-01-02&limit=1&order=desc"
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1


async def test_missing_symbol_data_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/stocks/MSFT")
    assert response.status_code == 404


async def test_invalid_input_returns_422(client: AsyncClient) -> None:
    response = await client.get("/api/v1/stocks/AAPL%20BAD")
    assert response.status_code == 422


async def test_cache_fallback_when_redis_unavailable(client: AsyncClient) -> None:
    await client.post("/api/v1/stocks/AAPL/sync")
    app.state.cache = FakeCache(available=False)
    response = await client.get("/api/v1/stocks/AAPL")
    assert response.status_code == 200
    assert response.json()["cached"] is False
    assert response.json()["count"] == 2


async def test_second_read_is_cached(client: AsyncClient) -> None:
    await client.post("/api/v1/stocks/AAPL/sync")
    first = await client.get("/api/v1/stocks/AAPL")
    second = await client.get("/api/v1/stocks/AAPL")
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
