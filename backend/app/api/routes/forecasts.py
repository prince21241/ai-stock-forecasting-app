from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.stock_repository import StockRepository
from app.schemas.forecast import ForecastHistoryResponse, ForecastResponse
from app.services.forecast_service import ForecastService, InsufficientForecastDataError

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


def service(db: AsyncSession) -> ForecastService:
    return ForecastService(StockRepository(db), ForecastRepository(db))


@router.post("/{symbol}/train", response_model=ForecastResponse)
async def train_forecast(
    symbol: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> ForecastResponse:
    try:
        return await service(db).train_and_forecast(symbol)
    except InsufficientForecastDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{symbol}/latest", response_model=ForecastResponse)
async def latest_forecast(
    symbol: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> ForecastResponse:
    result = await service(db).get_latest(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail="No stored forecast found for this symbol")
    return result


@router.get("/{symbol}/history", response_model=ForecastHistoryResponse)
async def forecast_history(
    symbol: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ForecastHistoryResponse:
    data = await service(db).get_history(symbol, limit)
    normalized_symbol = data[0].symbol if data else symbol.strip().upper()
    return ForecastHistoryResponse(symbol=normalized_symbol, count=len(data), data=data)
