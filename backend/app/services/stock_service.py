from datetime import UTC, date, datetime
from typing import Literal

from app.repositories.stock_repository import StockRepository
from app.schemas.stock import (
    StockLatestResponse,
    StockListResponse,
    StockPriceRead,
    StockSyncResponse,
)
from app.services.alpha_vantage import AlphaVantageClient
from app.services.cache_service import CacheService
from app.utils.validation import normalize_symbol


class StockService:
    def __init__(
        self,
        repository: StockRepository,
        alpha_vantage: AlphaVantageClient,
        cache: CacheService,
    ) -> None:
        self.repository = repository
        self.alpha_vantage = alpha_vantage
        self.cache = cache

    async def sync(self, raw_symbol: str) -> StockSyncResponse:
        symbol = normalize_symbol(raw_symbol)
        prices = await self.alpha_vantage.fetch_daily(symbol)
        affected = await self.repository.bulk_upsert_prices(prices)
        await self.cache.invalidate_symbol(symbol)
        return StockSyncResponse(
            symbol=symbol,
            fetched_records=len(prices),
            inserted_or_updated_records=affected,
            latest_trading_date=max((price.trading_date for price in prices), default=None),
            synced_at=datetime.now(UTC),
        )

    async def get_prices(
        self,
        raw_symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
        order: Literal["asc", "desc"],
    ) -> StockListResponse:
        symbol = normalize_symbol(raw_symbol)
        filters = {"start": start_date, "end": end_date, "limit": limit, "order": order}
        key = self.cache.stock_key(symbol, "list", filters)
        cached = await self.cache.get_json(key)
        if cached:
            cached["cached"] = True
            return StockListResponse.model_validate(cached)
        records = await self.repository.get_prices_by_symbol(
            symbol, start_date=start_date, end_date=end_date, limit=limit, order=order
        )
        response = StockListResponse(
            symbol=symbol,
            count=len(records),
            start_date=start_date,
            end_date=end_date,
            order=order,
            cached=False,
            data=[StockPriceRead.model_validate(record) for record in records],
        )
        await self.cache.set_json(key, response.model_dump(mode="json"))
        return response

    async def get_latest(self, raw_symbol: str) -> StockLatestResponse | None:
        symbol = normalize_symbol(raw_symbol)
        key = self.cache.stock_key(symbol, "latest")
        cached = await self.cache.get_json(key)
        if cached:
            cached["cached"] = True
            return StockLatestResponse.model_validate(cached)
        record = await self.repository.get_latest_price(symbol)
        if not record:
            return None
        response = StockLatestResponse(
            symbol=symbol, cached=False, data=StockPriceRead.model_validate(record)
        )
        await self.cache.set_json(key, response.model_dump(mode="json"))
        return response
