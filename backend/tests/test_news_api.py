from httpx import AsyncClient

from app.services.alpha_vantage_news import AlphaVantageNewsClient


def test_parse_news_payload() -> None:
    payload = {
        "feed": [
            {
                "title": "Apple update",
                "url": "https://example.test/apple",
                "source": "Example",
                "time_published": "20260718T1200",
                "summary": "Summary",
                "banner_image": "",
                "overall_sentiment_label": "Neutral",
                "overall_sentiment_score": "0.1",
                "ticker_sentiment": [
                    {
                        "ticker": "AAPL",
                        "relevance_score": "0.95",
                        "ticker_sentiment_score": "0.3",
                        "ticker_sentiment_label": "Somewhat-Bullish",
                    }
                ],
            }
        ]
    }
    articles = AlphaVantageNewsClient.parse("AAPL", payload, 10)
    assert len(articles) == 1
    assert articles[0].published_at.isoformat() == "2026-07-18T12:00:00+00:00"
    assert articles[0].relevance_score == 0.95
    assert articles[0].sentiment_label == "Somewhat-Bullish"


async def test_news_endpoint_and_cache(client: AsyncClient) -> None:
    first = await client.get("/api/v1/news/aapl?limit=10")
    second = await client.get("/api/v1/news/AAPL?limit=10")
    assert first.status_code == 200
    assert first.json()["symbol"] == "AAPL"
    assert first.json()["data"][0]["title"].startswith("AAPL update")
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True


async def test_news_endpoint_validates_limit(client: AsyncClient) -> None:
    response = await client.get("/api/v1/news/AAPL?limit=100")
    assert response.status_code == 422
