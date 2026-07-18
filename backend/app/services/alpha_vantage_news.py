from datetime import UTC, datetime

import httpx

from app.core.exceptions import (
    AlphaVantageMalformedResponseError,
    AlphaVantageNetworkError,
    AlphaVantageRateLimitError,
    AlphaVantageTimeoutError,
    MissingAPIKeyError,
)
from app.schemas.news import NewsArticle
from app.utils.validation import normalize_symbol


class AlphaVantageNewsClient:
    def __init__(self, api_key: str, base_url: str, timeout: float = 15.0) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    async def fetch(self, raw_symbol: str, limit: int) -> list[NewsArticle]:
        symbol = normalize_symbol(raw_symbol)
        if not self.api_key or self.api_key == "replace_with_your_key":
            raise MissingAPIKeyError("Alpha Vantage API key is not configured.")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "function": "NEWS_SENTIMENT",
                        "tickers": symbol,
                        "sort": "LATEST",
                        "limit": limit,
                        "apikey": self.api_key,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise AlphaVantageTimeoutError("Alpha Vantage news request timed out.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise AlphaVantageNetworkError("Alpha Vantage news request failed.") from exc
        return self.parse(symbol, payload, limit)

    @staticmethod
    def _published_at(value: str) -> datetime:
        for pattern in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M"):
            try:
                return datetime.strptime(value, pattern).replace(tzinfo=UTC)
            except ValueError:
                continue
        raise ValueError("Unsupported publication timestamp")

    @staticmethod
    def parse(symbol: str, payload: object, limit: int) -> list[NewsArticle]:
        if not isinstance(payload, dict):
            raise AlphaVantageMalformedResponseError("News response is malformed.")
        if "Note" in payload or "Information" in payload:
            raise AlphaVantageRateLimitError("Alpha Vantage news rate limit has been reached.")
        feed = payload.get("feed")
        if not isinstance(feed, list):
            raise AlphaVantageMalformedResponseError("News feed is missing from the response.")
        articles: list[NewsArticle] = []
        try:
            for item in feed[:limit]:
                ticker_data = next(
                    (
                        entry
                        for entry in item.get("ticker_sentiment", [])
                        if entry.get("ticker", "").upper() == symbol
                    ),
                    {},
                )
                published = AlphaVantageNewsClient._published_at(item["time_published"])
                articles.append(
                    NewsArticle(
                        title=item["title"],
                        url=item["url"],
                        source=item.get("source", "Unknown"),
                        published_at=published,
                        summary=item.get("summary", ""),
                        banner_image=item.get("banner_image") or None,
                        sentiment_label=ticker_data.get(
                            "ticker_sentiment_label", item.get("overall_sentiment_label", "Neutral")
                        ),
                        sentiment_score=float(
                            ticker_data.get(
                                "ticker_sentiment_score", item.get("overall_sentiment_score", 0)
                            )
                        ),
                        relevance_score=float(ticker_data.get("relevance_score", 0)),
                    )
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise AlphaVantageMalformedResponseError(
                "News feed contains invalid article data."
            ) from exc
        return articles
