.PHONY: help install dev dev-supabase test lint format migrate clean

help:
	@echo "Available commands:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make dev            - Start development environment (self-hosted)"
	@echo "  make dev-supabase   - Start development environment (Supabase)"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make migrate        - Run database migrations"
	@echo "  make clean          - Clean up temporary files"

install:
	pip install -r requirements.txt

dev:
	docker-compose up

dev-supabase:
	docker-compose -f docker-compose.supabase.yml up

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	ruff check src/
	black --check src/

format:
	black src/ tests/
	ruff check --fix src/

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache/

build:
	docker build -t anpr-city-api:latest .

push:
	docker tag anpr-city-api:latest $(REGISTRY)/anpr-city-api:latest
	docker push $(REGISTRY)/anpr-city-api:latest
