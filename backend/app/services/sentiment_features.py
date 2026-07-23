from collections import defaultdict
from datetime import date, timedelta

from app.schemas.news import NewsArticle

SENTIMENT_FEATURE_COUNT = 5


def build_daily_sentiment(
    articles: list[NewsArticle],
) -> dict[date, list[tuple[float, float]]]:
    daily: dict[date, list[tuple[float, float]]] = defaultdict(list)
    for article in articles:
        daily[article.published_at.date()].append(
            (article.sentiment_score, article.relevance_score)
        )
    return dict(daily)


def _weighted_average(entries: list[tuple[float, float]]) -> tuple[float, float]:
    if not entries:
        return 0.0, 0.0
    weights = [max(relevance, 0.01) for _, relevance in entries]
    total_weight = sum(weights)
    sentiment = (
        sum(score * weight for (score, _), weight in zip(entries, weights, strict=True))
        / total_weight
    )
    relevance = sum(relevance for _, relevance in entries) / len(entries)
    return float(sentiment), float(relevance)


def sentiment_features_for_date(
    trading_date: date,
    daily_sentiment: dict[date, list[tuple[float, float]]],
) -> list[float]:
    one_day = daily_sentiment.get(trading_date, [])
    three_day: list[tuple[float, float]] = []
    seven_day: list[tuple[float, float]] = []
    for offset in range(7):
        day = trading_date - timedelta(days=offset)
        entries = daily_sentiment.get(day, [])
        if offset < 3:
            three_day.extend(entries)
        seven_day.extend(entries)

    sentiment_1d, _ = _weighted_average(one_day)
    sentiment_3d, _ = _weighted_average(three_day)
    sentiment_7d, relevance_7d = _weighted_average(seven_day)
    return [
        sentiment_1d,
        sentiment_3d,
        sentiment_7d,
        float(len(seven_day)),
        relevance_7d,
    ]
