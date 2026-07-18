from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.stock_repository import StockRepository
from app.schemas.forecast import ForecastResponse
from app.services.forecast_service import ForecastService, InsufficientForecastDataError

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.post("/{symbol}/train", response_model=ForecastResponse)
async def train_forecast(
    symbol: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> ForecastResponse:
    try:
        return await ForecastService(StockRepository(db)).train_and_forecast(symbol)
    except InsufficientForecastDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
