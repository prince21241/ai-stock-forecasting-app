from fastapi import APIRouter

from app.api.routes import forecasts, health, stocks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(stocks.router)
api_router.include_router(forecasts.router)
