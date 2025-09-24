.PHONY: help install format lint test coverage run clean migrate upgrade rundb

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies with UV"
	@echo "  format     - Format code with ruff"
	@echo "  lint       - Lint code with ruff"
	@echo "  test       - Run tests"
	@echo "  coverage   - Run tests with coverage"
	@echo "  run        - Start development server"
	@echo "  rundb      - Start database services with Docker"
	@echo "  migrate    - Create new database migration"
	@echo "  upgrade    - Apply database migrations"
	@echo "  clean      - Clean cache and temp files"

install:
	uv sync

format:
	ruff check --select I --fix
	ruff format .

lint:
	ruff check .

test:
	PYTHONPATH=".:src/" pytest tests/

coverage:
	PYTHONPATH=".:src/" pytest --cov=src/
	coverage report -m --sort=miss

run:
	PYTHONPATH=".:src/:tests/" uvicorn --reload --host 127.0.0.1 --port 8000 src.server_api:app

rundb:
	docker compose -f docker-compose.dev.yml up

# Database migrations
migrate:
	@msg="$(msg)"; \
	if [ -z "$$msg" ]; then msg="Auto migration for $$(date +%Y-%m-%d)"; fi; \
	alembic revision --autogenerate -m "$$msg"

upgrade:
	alembic upgrade head

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .coverage coverage/