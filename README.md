# Stock Agent Ops

**AI-Driven Forecasting & Multi-Agent Platform — Phase 2 experimental forecasting**

Stock Agent Ops is a modular full-stack application for synchronizing Alpha Vantage daily stock
prices, storing them idempotently in SQLite, serving them through FastAPI, optionally caching reads
in Redis, and displaying stored data, experimental forecasts, and ticker-specific news in a React
dashboard.

Phase 2 adds an experimental, user-triggered next-trading-day ridge-regression forecast with
walk-forward evaluation. AI agents, automated reports, MLflow, Feast, Kubernetes, Terraform, AWS,
and OpenAI integrations are not implemented.

## Architecture and stack

The React/Vite dashboard calls a FastAPI API. Synchronization requests fetch `TIME_SERIES_DAILY` data from Alpha Vantage, normalize prices as decimal values, and upsert them into SQLite. Read responses are cached in Redis for five minutes when Redis is available; Redis failures do not block SQLite reads. See [docs/architecture.md](docs/architecture.md).

- Python 3.12, FastAPI, Pydantic v2, HTTPX
- SQLAlchemy 2 async, aiosqlite, SQLite, Alembic
- Redis 7
- React 19, TypeScript, Vite
- pytest, pytest-asyncio, Ruff
- Docker Compose

## Folder structure

```text
.
├── backend/                 FastAPI application, migration, and tests
│   ├── app/
│   │   ├── api/             Thin HTTP routes
│   │   ├── core/            Configuration, exceptions, logging
│   │   ├── db/              SQLAlchemy session and model
│   │   ├── repositories/    Persistence queries and upserts
│   │   ├── schemas/         Pydantic contracts
│   │   ├── services/        Ingestion, caching, orchestration
│   │   └── utils/           Symbol validation
│   ├── migrations/          Alembic migration history
│   └── tests/               Isolated backend test suite
├── frontend/                React/Vite dashboard
├── docs/                    Architecture and roadmap
├── docker-compose.yml
└── Makefile
```

## Prerequisites

For the recommended no-Docker path, install Python 3.12, Node.js 22+, and npm. SQLite is included with Python and needs no database server. Redis is optional; without it, the API reads directly from SQLite and health reports a degraded cache status.

Create a free Alpha Vantage API key at [Alpha Vantage](https://www.alphavantage.co/support/#api-key). Never commit the key.

## Environment setup

Copy the example file and replace only the placeholder key:

```bash
cp .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

Set `ALPHA_VANTAGE_API_KEY` in `.env`. Docker Compose supplies safe local defaults for all other values and automatically reads `.env` when present. The key is never logged. `.env` is ignored by Git.

## Run locally without Docker (recommended)

From the repository root, install the backend and apply the SQLite migration:

```powershell
backend\.venv\Scripts\python.exe -m pip install -e ".\backend[dev]"
backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

Start the backend in the first PowerShell window:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Start the frontend in a second PowerShell window:

```powershell
Set-Location frontend
npm.cmd install
npm.cmd run dev
```

Redis is not required for this workflow. If it is not running, `/health` reports `degraded` while stock synchronization and SQLite reads continue to work.

## Run with Docker

```bash
docker compose up --build
```

Open:

- Dashboard: <http://localhost:5173>
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/v1/health>

The backend applies Alembic migrations and starts Uvicorn. When Compose is used, SQLite data persists in the `sqlite_data` named volume.

Stop the system with `docker compose down`. Use `make up`, `make down`, or `make logs` as shortcuts where Make is available.

## Local backend development

From `backend/`:

```bash
python -m venv .venv
# Activate the environment, then:
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

The default local database is `stock_agent_ops.db`. The file, its journal files, and `.env` are ignored by Git.

Database migration commands:

```bash
alembic upgrade head
alembic downgrade -1
alembic current
```

Inside Docker, use `make migrate` or `docker compose run --rm backend alembic upgrade head`.

## Local frontend development

From `frontend/`:

```bash
npm install
npm run dev
```

Vite reads `VITE_API_BASE_URL`; the local default is `http://localhost:8000/api/v1`.

## API examples

```bash
curl http://localhost:8000/api/v1/health
curl -X POST http://localhost:8000/api/v1/stocks/AAPL/sync
curl "http://localhost:8000/api/v1/stocks/AAPL?limit=100&order=desc"
curl http://localhost:8000/api/v1/stocks/AAPL/latest
curl -X POST http://localhost:8000/api/v1/forecasts/AAPL/train
curl http://localhost:8000/api/v1/forecasts/AAPL/latest
curl "http://localhost:8000/api/v1/forecasts/AAPL/history?limit=10"
curl "http://localhost:8000/api/v1/news/AAPL?limit=10"
```

The forecast requires at least 100 stored daily records, matching Alpha Vantage's compact daily
feed. It reports predicted return and price,
an empirical 90% range, a direction estimate, walk-forward MAE, directional accuracy, and the MAE
of a zero-return baseline. The dashboard explicitly reports when the model fails to beat that
baseline. Training runs within the request, and forecast runs and evaluation metrics are persisted
in SQLite for audit and history views. A forecast is marked `qualified` only when it beats the
baseline and achieves at least 55% directional accuracy; otherwise it is marked `no_signal`.

The news endpoint uses Alpha Vantage `NEWS_SENTIMENT`, requests the latest ticker-specific articles,
and caches normalized results for five minutes. News contains provider-generated sentiment and must
not be interpreted as an application trading recommendation.

The list endpoint also accepts ISO `start_date` and `end_date`. `limit` must be 1–5000. Supported symbols contain 1–15 letters, digits, periods, or hyphens.

## Quality checks

From `backend/`:

```bash
python -m pytest
python -m ruff check .
```

From `frontend/`:

```bash
npm run typecheck
npm run build
```

Tests use an in-memory SQLite database and mocks; they need no production database, Redis server, Alpha Vantage key, or external network.

Validate Compose configuration with `docker compose config`.

## Troubleshooting

- **Sync reports a missing key:** set a real `ALPHA_VANTAGE_API_KEY` in `.env` and recreate the backend container.
- **HTTP 429:** Alpha Vantage has throttled the key. Wait for the provider window to reset.
- **No stored records (404):** synchronize the symbol first and verify that the expected `stock_agent_ops.db` file is in use.
- **Redis shows unavailable:** reads continue from SQLite. Start Redis only if local caching is desired.
- **Port already in use:** stop the conflicting local service or change the published host-side port.
- **Database startup failure:** rerun `alembic upgrade head` and confirm the project directory is writable.

## Current limitations

- Only Alpha Vantage daily adjusted-independent OHLCV ingestion is supported.
- Provider history and request frequency depend on the Alpha Vantage plan.
- Authentication, authorization, streaming updates, and background scheduling are not implemented.
- Synchronization is user-triggered and runs within the HTTP request.
- The dashboard visualizes up to 500 stored daily records as an interactive candlestick and volume chart, with 1-month through all-history range controls.
- News availability, depth, sentiment labels, and request frequency depend on Alpha Vantage.

See [docs/roadmap.md](docs/roadmap.md) for future phases. Forecasting is experimental; agent
capabilities remain future work.

## Disclaimer

This project is for educational and research use only. It does not provide investment advice, trading recommendations, or guarantees of data completeness.

## Contributors

- Prince Raval
- Deep Trivedi
