from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.stock_repository import StockRepository
from app.schemas.stock import StockLatestResponse, StockListResponse, StockSyncResponse
from app.services.stock_service import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])


def service(request: Request, db: AsyncSession) -> StockService:
    return StockService(
        StockRepository(db), request.app.state.alpha_vantage, request.app.state.cache
    )


@router.post(
    "/{symbol}/sync",
    response_model=StockSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronize daily stock prices",
    description="Fetches Alpha Vantage daily prices and idempotently stores them in PostgreSQL.",
)
async def sync_stock(
    symbol: str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> StockSyncResponse:
    return await service(request, db).sync(symbol)


@router.get(
    "/{symbol}",
    response_model=StockListResponse,
    summary="Read stored stock prices",
    description=(
        "Returns filtered PostgreSQL records, using Redis as an optional five-minute cache."
    ),
)
async def get_stock_prices(
    symbol: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 100,
    order: Literal["asc", "desc"] = "desc",
) -> StockListResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422, detail="start_date must be before or equal to end_date"
        )
    result = await service(request, db).get_prices(symbol, start_date, end_date, limit, order)
    if not result.data:
        raise HTTPException(status_code=404, detail=f"No stored prices found for {result.symbol}")
    return result


@router.get(
    "/{symbol}/latest",
    response_model=StockLatestResponse,
    summary="Read the latest stored price",
    description="Returns the newest stored daily record for a symbol.",
)
async def get_latest_stock_price(
    symbol: str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> StockLatestResponse:
    result = await service(request, db).get_latest(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail="No stored prices found for this symbol")
    return result
