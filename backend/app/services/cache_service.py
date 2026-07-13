import json
import logging
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


def _json_default(value: object) -> str:
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    raise TypeError(f"Unsupported cache value: {type(value).__name__}")


class CacheService:
    def __init__(self, redis: Redis, ttl_seconds: int = 300) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def stock_key(symbol: str, kind: str, filters: Mapping[str, Any] | None = None) -> str:
        suffix = ":".join(
            f"{key}={value}" for key, value in sorted((filters or {}).items()) if value is not None
        )
        return f"stocks:{symbol}:{kind}:{suffix}"

    async def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as exc:  # Redis is an optional read optimization.
            logger.warning("Redis read failed", extra={"error_type": type(exc).__name__})
            return None

    async def set_json(self, key: str, value: Mapping[str, Any]) -> None:
        try:
            await self.redis.set(key, json.dumps(value, default=_json_default), ex=self.ttl_seconds)
        except Exception as exc:
            logger.warning("Redis write failed", extra={"error_type": type(exc).__name__})

    async def invalidate_symbol(self, symbol: str) -> None:
        try:
            keys = [key async for key in self.redis.scan_iter(match=f"stocks:{symbol}:*")]
            if keys:
                await self.redis.delete(*keys)
        except Exception as exc:
            logger.warning("Redis invalidation failed", extra={"error_type": type(exc).__name__})

    async def ping(self) -> bool:
        try:
            return bool(await self.redis.ping())
        except Exception:
            return False
