.PHONY: up down logs migrate migrate-local backend-dev frontend-dev test lint frontend-build clean

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm backend alembic upgrade head

migrate-local:
	backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini upgrade head

backend-dev:
	backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload

frontend-dev:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest

lint:
	cd backend && python -m ruff check .

frontend-build:
	cd frontend && npm run typecheck && npm run build

clean:
	docker compose down --remove-orphans
