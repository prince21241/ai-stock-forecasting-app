# Phase 1 architecture

```text
Browser (React/Vite :5173)
          |
          v
FastAPI /api/v1 (:8000) -----> Alpha Vantage TIME_SERIES_DAILY
          |
          +-----> Redis (:6379), five-minute read cache
          |
          +-----> SQLite file, durable normalized prices
```

The API is separated into routes, services, repositories, schemas, and infrastructure adapters. Routes validate HTTP-specific inputs and delegate. `StockService` coordinates symbol validation, ingestion, persistence, cache invalidation, and reads. `StockRepository` owns SQLAlchemy queries and conflict-safe SQLite upserts. `CacheService` treats Redis as an optional optimization, so SQLite reads still work when Redis is unavailable.

The unique constraint on `(symbol, trading_date, source)` is the final idempotency boundary. Alpha Vantage values are converted to `Decimal`, `date`, and `int` before reaching persistence.

## Request flow

1. The user explicitly selects **Synchronize Data**.
2. FastAPI validates and normalizes the symbol.
3. The Alpha Vantage client fetches and parses daily values.
4. SQLite inserts or updates each unique price identity.
5. Cached reads for that symbol are invalidated.
6. The dashboard requests stored records and renders the result.

Phase 1 remains the data foundation. Phase 2 adds a separate, user-triggered forecast service that
reads stored prices through `StockRepository`, engineers features in memory, performs walk-forward
evaluation, and returns an experimental next-day forecast. It does not add AI agents or cloud
deployment.
