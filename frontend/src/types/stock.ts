export interface StockPrice {
  trading_date: string;
  open_price: string;
  high_price: string;
  low_price: string;
  close_price: string;
  volume: number;
}

export interface StockListResponse {
  symbol: string;
  count: number;
  start_date: string | null;
  end_date: string | null;
  order: "asc" | "desc";
  source: string;
  cached: boolean;
  data: StockPrice[];
}

export interface StockSyncResponse {
  symbol: string;
  fetched_records: number;
  inserted_or_updated_records: number;
  latest_trading_date: string | null;
  source: string;
  synced_at: string;
}

export interface ForecastMetrics {
  model_mae_percent: number;
  baseline_mae_percent: number;
  directional_accuracy_percent: number;
  validation_observations: number;
  beats_baseline: boolean;
  brier_score?: number | null;
}

export interface ModelComparisonEntry {
  model_name: string;
  feature_set?: "price_only" | "with_sentiment";
  model_mae_percent: number;
  baseline_mae_percent: number;
  directional_accuracy_percent: number;
  validation_observations: number;
  beats_baseline: boolean;
  signal_status: "qualified" | "no_signal";
  selected: boolean;
}

export interface SentimentComparison {
  available: boolean;
  price_only_mae_percent?: number | null;
  with_sentiment_mae_percent?: number | null;
  sentiment_improves_mae?: boolean | null;
  selected_feature_set?: "price_only" | "with_sentiment";
}

export interface ReliabilityBin {
  bin_start_percent: number;
  bin_end_percent: number;
  mean_predicted_percent: number;
  observed_frequency_percent: number;
  sample_count: number;
}

export interface CalibrationSummary {
  method: string;
  brier_score: number;
  reliability_bins: ReliabilityBin[];
}

export interface HorizonForecast {
  horizon: "1d" | "5d" | "20d" | "volatility";
  label: string;
  predicted_return_percent?: number | null;
  predicted_volatility_percent?: number | null;
  predicted_price?: number | null;
  probability_up_percent?: number | null;
  signal_status: "qualified" | "no_signal" | "insufficient_data";
  metrics?: ForecastMetrics | null;
}

export interface ForecastResponse {
  id: number | null;
  symbol: string; as_of_date: string; latest_close: number;
  predicted_return_percent: number; predicted_price: number;
  price_range_low: number; price_range_high: number; probability_up_percent: number;
  training_observations: number; model_name: string; model_version: string;
  trained_at: string; disclaimer: string; signal_status: "qualified" | "no_signal";
  sentiment_features_used?: boolean;
  sentiment_comparison?: SentimentComparison;
  model_comparison?: ModelComparisonEntry[];
  calibration?: CalibrationSummary | null;
  horizons?: HorizonForecast[];
  metrics: ForecastMetrics;
}

export interface ForecastHistoryResponse {
  symbol: string; count: number; data: ForecastResponse[];
}

export interface NewsArticle {
  title: string; url: string; source: string; published_at: string; summary: string;
  banner_image: string | null; sentiment_label: string;
  sentiment_score: number; relevance_score: number;
}

export interface StockNewsResponse {
  symbol: string; count: number; cached: boolean; data: NewsArticle[];
}
