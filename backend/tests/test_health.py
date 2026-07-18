import pytest
from httpx import AsyncClient

from app.main import app
from tests.conftest import FakeCache


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "healthy"


@pytest.mark.asyncio
async def test_health_reports_degraded_redis(client: AsyncClient) -> None:
    app.state.cache = FakeCache(available=False)
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
