from datetime import UTC, date, datetime, timedelta

from app.schemas.news import NewsArticle
from app.services.sentiment_features import (
    build_daily_sentiment,
    sentiment_features_for_date,
)


def make_article(day: date, score: float, relevance: float) -> NewsArticle:
    return NewsArticle(
        title="Headline",
        url="https://example.test/article",
        source="Example News",
        published_at=datetime(day.year, day.month, day.day, 12, tzinfo=UTC),
        summary="Summary",
        sentiment_label="Somewhat-Bullish",
        sentiment_score=score,
        relevance_score=relevance,
    )


def test_sentiment_features_use_rolling_windows() -> None:
    day = date(2024, 1, 10)
    articles = [
        make_article(day, 0.4, 0.9),
        make_article(day - timedelta(days=1), 0.2, 0.8),
        make_article(day - timedelta(days=2), -0.1, 0.7),
    ]
    daily = build_daily_sentiment(articles)
    features = sentiment_features_for_date(day, daily)
    assert len(features) == 5
    assert features[0] > 0
    assert features[2] != 0
    assert features[3] == 3
    assert features[4] > 0


def test_sentiment_features_default_to_neutral_without_news() -> None:
    features = sentiment_features_for_date(date(2024, 1, 10), {})
    assert features == [0.0, 0.0, 0.0, 0.0, 0.0]
