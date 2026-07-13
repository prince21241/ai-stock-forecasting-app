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

