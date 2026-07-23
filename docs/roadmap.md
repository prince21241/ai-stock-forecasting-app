# Roadmap

## Phase 1 — data foundation (complete)

- Alpha Vantage daily ingestion
- SQLite normalized storage and Alembic migrations
- Redis read caching with graceful fallback
- FastAPI endpoints and React dashboard
- Docker Compose, tests, linting, and documentation

## Phase 2 — experimental forecasting (current)

- User-triggered next-trading-day forecast with automatic model selection
- Ridge regression and LightGBM compared via the same walk-forward evaluation
- OHLCV-derived momentum, volatility, moving-average, range, and volume features
- Optional Alpha Vantage news sentiment features (1d/3d/7d relevance-weighted scores and 7-day article volume)
- Sentiment A/B comparison: price-only versus with-sentiment walk-forward MAE on the dashboard
- Platt-scaled calibrated up-probabilities with Brier score and reliability bins
- Multi-horizon forecasts for 1-day, 5-day, 20-day returns and next-day volatility, each with its own quality gate
- Expanding-window walk-forward evaluation against a zero-return baseline
- Empirical prediction range, direction estimate, dashboard model comparison, and disclosure
- Persisted forecast-run history with model versions, comparison metrics, and evaluation metrics
- Quality gate that separates qualified experiments from `no_signal` results
- Latest ticker-specific news and provider sentiment with graceful failure and Redis caching

The model requires at least 100 stored daily records, matching Alpha Vantage's compact daily feed.
It is an educational experiment, is not
automatically retrained, and does not provide investment advice or guaranteed probabilities.

## Future phases (not implemented)

- Feature engineering and feature-store decisions
- Multi-agent orchestration and approval workflows
- Experiment tracking and automated reporting
- Production observability, cloud infrastructure, and deployment

Future work must be designed and validated separately. The application must not represent these capabilities as available until they are implemented and tested.
