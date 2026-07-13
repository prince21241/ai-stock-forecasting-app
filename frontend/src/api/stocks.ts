import type { StockListResponse, StockSyncResponse } from "../types/stock";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "")
  ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new Error("Unable to reach the API. Confirm that the backend is running.");
  }
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Preserve the status-based fallback when the response is not JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function synchronizeStock(symbol: string): Promise<StockSyncResponse> {
  return request(`/stocks/${encodeURIComponent(symbol)}/sync`, { method: "POST" });
}

export function loadStockData(symbol: string): Promise<StockListResponse> {
  return request(`/stocks/${encodeURIComponent(symbol)}?limit=100&order=desc`);
}

