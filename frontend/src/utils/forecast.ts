import type { ForecastHistoryResponse, ForecastResponse } from "../types/stock";

export function normalizeForecast(forecast: ForecastResponse): ForecastResponse {
  return {
    ...forecast,
    sentiment_features_used: forecast.sentiment_features_used ?? false,
    sentiment_comparison: forecast.sentiment_comparison ?? { available: false },
    model_comparison: forecast.model_comparison ?? [],
    calibration: forecast.calibration ?? null,
    horizons: forecast.horizons ?? [],
    metrics: {
      ...forecast.metrics,
      brier_score: forecast.metrics.brier_score ?? forecast.calibration?.brier_score ?? null,
    },
  };
}

export function normalizeForecastHistory(
  history: ForecastHistoryResponse,
): ForecastHistoryResponse {
  return {
    ...history,
    data: history.data.map(normalizeForecast),
  };
}
