# Roadmap

## Phase 1 — data foundation (complete)

- Alpha Vantage daily ingestion
- SQLite normalized storage and Alembic migrations
- Redis read caching with graceful fallback
- FastAPI endpoints and React dashboard
- Docker Compose, tests, linting, and documentation

## Phase 2 — experimental forecasting (current)

- User-triggered next-trading-day ridge-regression forecast
- OHLCV-derived momentum, volatility, moving-average, range, and volume features
- Expanding-window walk-forward evaluation against a zero-return baseline
- Empirical prediction range, direction estimate, and dashboard disclosure

The model requires at least 100 stored daily records, matching Alpha Vantage's compact daily feed.
It is an educational experiment, is not
automatically retrained, and does not provide investment advice or guaranteed probabilities.

## Future phases (not implemented)

- Feature engineering and feature-store decisions
- Multi-agent orchestration and approval workflows
- Experiment tracking and automated reporting
- Production observability, cloud infrastructure, and deployment

Future work must be designed and validated separately. The application must not represent these capabilities as available until they are implemented and tested.
