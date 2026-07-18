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

export interface ForecastResponse {
  id: number | null;
  symbol: string; as_of_date: string; latest_close: number;
  predicted_return_percent: number; predicted_price: number;
  price_range_low: number; price_range_high: number; probability_up_percent: number;
  training_observations: number; model_name: string; model_version: string;
  trained_at: string; disclaimer: string; signal_status: "qualified" | "no_signal";
  metrics: { model_mae_percent: number; baseline_mae_percent: number;
    directional_accuracy_percent: number; validation_observations: number; beats_baseline: boolean; };
}

export interface ForecastHistoryResponse {
  symbol: string; count: number; data: ForecastResponse[];
}
