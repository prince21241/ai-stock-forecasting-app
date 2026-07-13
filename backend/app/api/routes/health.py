from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.stock import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health",
    description="Reports application, PostgreSQL, and optional Redis status.",
)
async def health(request: Request, db: Annotated[AsyncSession, Depends(get_db)]) -> HealthResponse:
    database_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"
    redis_status = "healthy" if await request.app.state.cache.ping() else "unavailable"
    if database_status == "unavailable":
        status = "unavailable"
    elif redis_status == "unavailable":
        status = "degraded"
    else:
        status = "healthy"
    return HealthResponse(
        status=status,
        application="healthy",
        postgresql=database_status,
        redis=redis_status,
    )
