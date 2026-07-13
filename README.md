# Stock Agent Ops

**AI-Driven Forecasting & Multi-Agent Platform — Phase 1 data foundation**

Stock Agent Ops is a modular full-stack application for synchronizing Alpha Vantage daily stock prices, storing them idempotently in PostgreSQL, serving them through FastAPI, caching reads in Redis, and displaying stored data in a responsive React dashboard.

Phase 1 does **not** implement forecasting, ML models, AI agents, automated reports, MLflow, Feast, Kubernetes, Terraform, AWS, or OpenAI integrations.

## Architecture and stack

The React/Vite dashboard calls a FastAPI API. Synchronization requests fetch `TIME_SERIES_DAILY` data from Alpha Vantage, normalize prices as decimal values, and upsert them into PostgreSQL. Read responses are cached in Redis for five minutes; Redis failures degrade caching without blocking PostgreSQL reads. See [docs/architecture.md](docs/architecture.md).

- Python 3.12, FastAPI, Pydantic v2, HTTPX
- SQLAlchemy 2 async, asyncpg, PostgreSQL 16, Alembic
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

For the recommended path, install Docker Desktop with Docker Compose. For direct local development, use Python 3.12, Node.js 22+, npm, PostgreSQL, and Redis.

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

## Run with Docker

```bash
docker compose up --build
```

Open:

- Dashboard: <http://localhost:5173>
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/v1/health>

The backend waits for PostgreSQL, applies Alembic migrations, and starts Uvicorn. PostgreSQL data persists in the `postgres_data` named volume.

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

For a host-run backend, override `DATABASE_URL` and `REDIS_URL` to use `localhost` instead of Docker service names.

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
```

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
- **No stored records (404):** synchronize the symbol first, or verify that the same PostgreSQL volume/database is in use.
- **Redis shows unavailable:** reads continue from PostgreSQL. Check `docker compose logs redis` to restore caching.
- **Port already in use:** stop the conflicting local service or change the published host-side port.
- **Database startup failure:** inspect `docker compose logs postgres backend`; ensure an old volume does not contain incompatible credentials.

## Current limitations

- Only Alpha Vantage daily adjusted-independent OHLCV ingestion is supported.
- Provider history and request frequency depend on the Alpha Vantage plan.
- Authentication, authorization, streaming updates, and background scheduling are not implemented.
- Synchronization is user-triggered and runs within the HTTP request.
- The dashboard displays the newest 100 stored records.

See [docs/roadmap.md](docs/roadmap.md) for future phases. Forecasting and agent capabilities remain future work.

## Disclaimer

This project is for educational and research use only. It does not provide investment advice, trading recommendations, or guarantees of data completeness.

## Contributors

- Prince Raval
- Deep Trivedi

