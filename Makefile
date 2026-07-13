.PHONY: up down logs migrate test lint frontend-build clean

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm backend alembic upgrade head

test:
	cd backend && python -m pytest

lint:
	cd backend && python -m ruff check .

frontend-build:
	cd frontend && npm run typecheck && npm run build

clean:
	docker compose down --remove-orphans

