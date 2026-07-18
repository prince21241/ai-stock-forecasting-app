from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.schemas.news import NewsArticle
from app.schemas.stock import StockPriceCreate


class FakeCache:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.values: dict[str, dict] = {}

    async def ping(self) -> bool:
        return self.available

    async def get_json(self, key: str):
        if not self.available:
            return None
        value = self.values.get(key)
        return dict(value) if value else None

    async def set_json(self, key: str, value: dict) -> None:
        if self.available:
            self.values[key] = dict(value)

    async def invalidate_symbol(self, symbol: str) -> None:
        self.values = {
            key: value
            for key, value in self.values.items()
            if not key.startswith(f"stocks:{symbol}:")
        }

    @staticmethod
    def stock_key(symbol: str, kind: str, filters=None) -> str:
        from app.services.cache_service import CacheService

        return CacheService.stock_key(symbol, kind, filters)


class FakeAlphaVantage:
    async def fetch_daily(self, symbol: str) -> list[StockPriceCreate]:
        return [
            make_price(symbol, date(2024, 1, 2), "101.50"),
            make_price(symbol, date(2024, 1, 3), "103.25"),
        ]


class FakeNews:
    async def fetch(self, symbol: str, limit: int) -> list[NewsArticle]:
        return [
            NewsArticle(
                title=f"Latest {symbol} headline",
                url="https://example.test/article",
                source="Example News",
                published_at=datetime(2026, 7, 18, 12, 0, tzinfo=UTC),
                summary="A concise market update.",
                sentiment_label="Somewhat-Bullish",
                sentiment_score=0.25,
                relevance_score=0.91,
            )
        ][:limit]


def make_price(symbol: str, trading_date: date, close: str) -> StockPriceCreate:
    price = Decimal(close)
    return StockPriceCreate(
        symbol=symbol,
        trading_date=trading_date,
        open_price=price - 1,
        high_price=price + 1,
        low_price=price - 2,
        close_price=price,
        volume=1_000_000,
    )


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = override_db
    app.state.cache = FakeCache()
    app.state.alpha_vantage = FakeAlphaVantage()
    app.state.news = FakeNews()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def daily_payload() -> dict:
    return {
        "Meta Data": {"2. Symbol": "AAPL"},
        "Time Series (Daily)": {
            "2024-01-03": {
                "1. open": "101.0000",
                "2. high": "104.0000",
                "3. low": "100.5000",
                "4. close": "103.2500",
                "5. volume": "1234567",
            },
            "2024-01-02": {
                "1. open": "99.0000",
                "2. high": "102.0000",
                "3. low": "98.5000",
                "4. close": "101.5000",
                "5. volume": "987654",
            },
        },
    }
