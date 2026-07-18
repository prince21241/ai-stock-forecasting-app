from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.schemas.news import StockNewsResponse
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/{symbol}", response_model=StockNewsResponse)
async def get_stock_news(
    symbol: str, request: Request, limit: Annotated[int, Query(ge=1, le=50)] = 10
) -> StockNewsResponse:
    return await NewsService(request.app.state.news, request.app.state.cache).get_latest(
        symbol, limit
    )
