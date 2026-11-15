.PHONY: help install run test lint docker-up docker-down docker-logs clean

help:
	@echo "Space Explorer Development Commands:"
	@echo "  make install      Install Python dependencies"
	@echo "  make run          Run FastAPI backend locally with uvicorn"
	@echo "  make test         Run pytest test suite"
	@echo "  make lint         Run ruff linter"
	@echo "  make docker-up    Start backend and PostGIS database using Docker Compose"
	@echo "  make docker-down  Stop Docker Compose services"
	@echo "  make docker-logs  View Docker Compose logs"
	@echo "  make clean        Remove cache and temporary files"

install:
	pip install -r backend/requirements.txt

run:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest backend/tests

lint:
	ruff check .

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
