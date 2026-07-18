from app.schemas.news import StockNewsResponse
from app.services.alpha_vantage_news import AlphaVantageNewsClient
from app.services.cache_service import CacheService
from app.utils.validation import normalize_symbol


class NewsService:
    def __init__(self, client: AlphaVantageNewsClient, cache: CacheService) -> None:
        self.client = client
        self.cache = cache

    async def get_latest(self, raw_symbol: str, limit: int) -> StockNewsResponse:
        symbol = normalize_symbol(raw_symbol)
        key = self.cache.stock_key(symbol, "news", {"limit": limit})
        cached = await self.cache.get_json(key)
        if cached:
            cached["cached"] = True
            return StockNewsResponse.model_validate(cached)
        articles = await self.client.fetch(symbol, limit)
        result = StockNewsResponse(symbol=symbol, count=len(articles), cached=False, data=articles)
        await self.cache.set_json(key, result.model_dump(mode="json"))
        return result
