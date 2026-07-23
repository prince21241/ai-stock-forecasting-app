from dataclasses import dataclass
from datetime import date
from typing import Literal

import numpy as np

from app.schemas.news import NewsArticle
from app.services.sentiment_features import (
    SENTIMENT_FEATURE_COUNT,
    build_daily_sentiment,
    sentiment_features_for_date,
)

PRICE_FEATURE_COUNT = 9
TargetMode = Literal["return", "volatility"]


@dataclass(frozen=True)
class FeatureSet:
    values: np.ndarray
    targets: np.ndarray
    trading_dates: tuple[date, ...]


def _price_row(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    volume: np.ndarray,
    index: int,
) -> list[float]:
    returns = np.diff(close[index - 20 : index + 1]) / close[index - 20 : index]
    volume_window = volume[index - 20 : index + 1]
    return [
        returns[-1],
        close[index] / close[index - 5] - 1,
        close[index] / close[index - 20] - 1,
        float(np.std(returns[-5:])),
        float(np.std(returns)),
        close[index] / float(np.mean(close[index - 4 : index + 1])) - 1,
        close[index] / float(np.mean(close[index - 19 : index + 1])) - 1,
        (high[index] - low[index]) / close[index],
        volume[index] / float(np.mean(volume_window)) - 1,
    ]


def _target_value(
    close: np.ndarray,
    index: int,
    horizon_days: int,
    target_mode: TargetMode,
) -> float:
    next_return = close[index + 1] / close[index] - 1
    if target_mode == "volatility":
        return abs(next_return)
    return close[index + horizon_days] / close[index] - 1


def build_feature_set(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    volume: np.ndarray,
    record_dates: list[date],
    *,
    horizon_days: int = 1,
    target_mode: TargetMode = "return",
    include_sentiment: bool = False,
    articles: list[NewsArticle] | None = None,
) -> FeatureSet:
    target_offset = 1 if target_mode == "volatility" else horizon_days
    daily_sentiment = build_daily_sentiment(articles or []) if include_sentiment else {}
    rows: list[list[float]] = []
    targets: list[float] = []
    trading_dates: list[date] = []
    for index in range(20, len(close) - target_offset):
        row = _price_row(close, high, low, volume, index)
        if include_sentiment:
            row.extend(sentiment_features_for_date(record_dates[index], daily_sentiment))
        rows.append(row)
        targets.append(_target_value(close, index, horizon_days, target_mode))
        trading_dates.append(record_dates[index])
    return FeatureSet(
        np.asarray(rows, dtype=float),
        np.asarray(targets, dtype=float),
        tuple(trading_dates),
    )


def latest_feature_row(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    volume: np.ndarray,
    record_dates: list[date],
    *,
    include_sentiment: bool = False,
    articles: list[NewsArticle] | None = None,
) -> np.ndarray:
    extended_close = np.append(close, close[-1])
    extended_high = np.append(high, high[-1])
    extended_low = np.append(low, low[-1])
    extended_volume = np.append(volume, volume[-1])
    extended_dates = record_dates + [record_dates[-1]]
    dataset = build_feature_set(
        extended_close,
        extended_high,
        extended_low,
        extended_volume,
        extended_dates,
        include_sentiment=include_sentiment,
        articles=articles,
    )
    return dataset.values[-1]


def feature_count(include_sentiment: bool) -> int:
    return PRICE_FEATURE_COUNT + (SENTIMENT_FEATURE_COUNT if include_sentiment else 0)


def minimum_training_rows(target_count: int, default: int = 60) -> int:
    if target_count < 10:
        return target_count
    return min(default, target_count - 5)
