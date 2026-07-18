from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    AlphaVantageMalformedResponseError,
    AlphaVantageNetworkError,
    AlphaVantageRateLimitError,
    AlphaVantageTimeoutError,
    InvalidSymbolError,
    MissingAPIKeyError,
)
from app.core.logging import configure_logging
from app.db.session import engine
from app.services.alpha_vantage import AlphaVantageClient
from app.services.alpha_vantage_news import AlphaVantageNewsClient
from app.services.cache_service import CacheService

settings = get_settings()
configure_logging(settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=settings.redis_timeout_seconds,
        socket_timeout=settings.redis_timeout_seconds,
        retry_on_timeout=False,
    )
    app.state.cache = CacheService(redis, settings.cache_ttl_seconds)
    app.state.alpha_vantage = AlphaVantageClient(
        settings.alpha_vantage_api_key,
        settings.alpha_vantage_base_url,
        settings.alpha_vantage_timeout_seconds,
    )
    app.state.news = AlphaVantageNewsClient(
        settings.alpha_vantage_api_key,
        settings.alpha_vantage_base_url,
        settings.alpha_vantage_timeout_seconds,
    )
    yield
    await redis.aclose()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Stock data foundation with an experimental Phase 2 forecast.",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


def safe_error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message})


@app.exception_handler(InvalidSymbolError)
async def invalid_symbol_handler(_: Request, exc: InvalidSymbolError) -> JSONResponse:
    return safe_error(422, str(exc))


@app.exception_handler(AlphaVantageRateLimitError)
async def rate_limit_handler(_: Request, exc: AlphaVantageRateLimitError) -> JSONResponse:
    return safe_error(429, str(exc))


@app.exception_handler(MissingAPIKeyError)
async def missing_key_handler(_: Request, exc: MissingAPIKeyError) -> JSONResponse:
    return safe_error(503, str(exc))


@app.exception_handler(AlphaVantageTimeoutError)
@app.exception_handler(AlphaVantageNetworkError)
@app.exception_handler(AlphaVantageMalformedResponseError)
async def upstream_handler(_: Request, exc: Exception) -> JSONResponse:
    return safe_error(502, str(exc))
