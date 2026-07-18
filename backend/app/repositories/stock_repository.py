from datetime import date
from typing import Literal

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.stock_price import StockPrice
from app.schemas.stock import StockPriceCreate


class StockRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_upsert_prices(self, prices: list[StockPriceCreate]) -> int:
        if not prices:
            return 0
        values = [price.model_dump() for price in prices]
        dialect = self.session.bind.dialect.name if self.session.bind else "postgresql"
        insert = sqlite_insert(StockPrice) if dialect == "sqlite" else pg_insert(StockPrice)
        statement = insert.values(values)
        statement = statement.on_conflict_do_update(
            index_elements=["symbol", "trading_date", "source"],
            set_={
                "open_price": statement.excluded.open_price,
                "high_price": statement.excluded.high_price,
                "low_price": statement.excluded.low_price,
                "close_price": statement.excluded.close_price,
                "volume": statement.excluded.volume,
                "updated_at": func.now(),
            },
        )
        await self.session.execute(statement)
        await self.session.commit()
        return len(prices)

    def _price_query(
        self, symbol: str, start_date: date | None = None, end_date: date | None = None
    ) -> Select[tuple[StockPrice]]:
        query = select(StockPrice).where(StockPrice.symbol == symbol)
        if start_date:
            query = query.where(StockPrice.trading_date >= start_date)
        if end_date:
            query = query.where(StockPrice.trading_date <= end_date)
        return query

    async def get_prices_by_symbol(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        order: Literal["asc", "desc"] = "desc",
    ) -> list[StockPrice]:
        ordering = (
            StockPrice.trading_date.asc() if order == "asc" else StockPrice.trading_date.desc()
        )
        result = await self.session.scalars(
            self._price_query(symbol, start_date, end_date).order_by(ordering).limit(limit)
        )
        return list(result.all())

    async def get_latest_price(self, symbol: str) -> StockPrice | None:
        result = await self.session.scalar(
            select(StockPrice)
            .where(StockPrice.symbol == symbol)
            .order_by(StockPrice.trading_date.desc())
            .limit(1)
        )
        return result

    async def get_latest_trading_date(self, symbol: str) -> date | None:
        return await self.session.scalar(
            select(func.max(StockPrice.trading_date)).where(StockPrice.symbol == symbol)
        )

    async def count_prices_by_symbol(self, symbol: str) -> int:
        return int(
            await self.session.scalar(
                select(func.count()).select_from(StockPrice).where(StockPrice.symbol == symbol)
            )
            or 0
        )

    async def get_all_prices_by_symbol(self, symbol: str) -> list[StockPrice]:
        result = await self.session.scalars(
            self._price_query(symbol).order_by(StockPrice.trading_date.asc())
        )
        return list(result.all())
