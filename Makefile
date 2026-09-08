.PHONY: help install up up-prod down logs migrate makemigration test lint format shell

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies via Poetry"
	@echo "  make up             - Start all services (docker compose up -d --build)"
	@echo "  make up-prod        - Start with production overlay (no DB/Redis ports)"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - Tail logs from all services"
	@echo "  make migrate        - Apply Alembic migrations"
	@echo "  make makemigration  - Create new Alembic migration (use: make makemigration name=init)"
	@echo "  make test           - Run pytest"
	@echo "  make lint           - Run ruff"
	@echo "  make format         - Run ruff format"
	@echo "  make shell          - Open Poetry shell"

install:
	poetry install --with dev

shell:
	poetry shell

up:
	docker compose up -d --build

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec bot alembic upgrade head

makemigration:
	docker compose exec bot alembic revision --autogenerate -m "$(name)"

test:
	poetry run pytest

lint:
	poetry run ruff check .

format:
	poetry run ruff format .
