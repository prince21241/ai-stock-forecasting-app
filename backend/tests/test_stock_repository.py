from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stock_repository import StockRepository
from tests.conftest import make_price


@pytest.mark.asyncio
async def test_bulk_upsert_and_idempotency(session: AsyncSession) -> None:
    repository = StockRepository(session)
    prices = [
        make_price("AAPL", date(2024, 1, 2), "100"),
        make_price("AAPL", date(2024, 1, 3), "101"),
    ]
    assert await repository.bulk_upsert_prices(prices) == 2
    assert await repository.bulk_upsert_prices(prices) == 2
    assert await repository.count_prices_by_symbol("AAPL") == 2


@pytest.mark.asyncio
async def test_retrieval_latest_filters_limits_and_order(session: AsyncSession) -> None:
    repository = StockRepository(session)
    prices = [
        make_price("AAPL", date(2024, 1, 1), "100"),
        make_price("AAPL", date(2024, 1, 2), "101"),
        make_price("AAPL", date(2024, 1, 3), "102"),
        make_price("MSFT", date(2024, 1, 3), "300"),
    ]
    await repository.bulk_upsert_prices(prices)

    ascending = await repository.get_prices_by_symbol("AAPL", limit=2, order="asc")
    assert [item.trading_date for item in ascending] == [date(2024, 1, 1), date(2024, 1, 2)]

    descending = await repository.get_prices_by_symbol("AAPL", limit=2, order="desc")
    assert [item.trading_date for item in descending] == [date(2024, 1, 3), date(2024, 1, 2)]

    filtered = await repository.get_prices_by_symbol(
        "AAPL", start_date=date(2024, 1, 2), end_date=date(2024, 1, 2)
    )
    assert len(filtered) == 1
    assert filtered[0].trading_date == date(2024, 1, 2)

    latest = await repository.get_latest_price("AAPL")
    assert latest is not None and latest.trading_date == date(2024, 1, 3)
    assert await repository.get_latest_trading_date("AAPL") == date(2024, 1, 3)
