# =============================================================================
# TokenMeter — Development Makefile
# =============================================================================
# Common commands for local development, CI/CD, and deployment.
#
# Usage:
#   make install        — Install all dependencies (backend + frontend)
#   make dev            — Start all services for local development
#   make test           — Run the full test suite
#   make lint           — Run linters on backend and frontend
#   make format         — Auto-format all code
#   make clean          — Remove build artifacts and caches
# =============================================================================

.PHONY: install install-backend install-frontend \
        dev run-backend run-frontend \
        test test-backend test-sdk-python test-sdk-node test-cov \
        lint lint-backend lint-frontend \
        format format-backend format-frontend \
        docker-build docker-up docker-down docker-logs \
        db-migrate db-seed db-clickhouse \
        clean help

# Default target
.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
PYTHON      := python
PIP         := pip
PYTEST      := pytest
UVICORN     := uvicorn
NPM         := npm
DOCKER      := docker
COMPOSE     := docker compose

BACKEND_DIR := backend
FRONTEND_DIR := frontend
TESTS_DIR   := tests

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python backend dependencies (dev)
	cd $(BACKEND_DIR) && $(PIP) install -r requirements-dev.txt

install-frontend: ## Install Node.js frontend dependencies
	cd $(FRONTEND_DIR) && $(NPM) install

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: docker-up ## Start all services (DB, Redis, ClickHouse, backend, frontend)
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Starting backend and frontend..."
	@$(MAKE) -j2 run-backend run-frontend

run-backend: ## Run the FastAPI backend with auto-reload
	cd $(BACKEND_DIR) && $(UVICORN) backend.main:app --reload --host 0.0.0.0 --port 8000

run-frontend: ## Run the Next.js frontend dev server
	cd $(FRONTEND_DIR) && $(NPM) run dev

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: test-backend ## Run all tests

test-backend: ## Run Python backend tests
	$(PYTHON) -m $(PYTEST) $(TESTS_DIR) -v --cov=$(BACKEND_DIR)

test-sdk-python: ## Run Python SDK tests
	cd sdks/python && $(PYTHON) -m $(PYTEST) tests/ -v

test-sdk-node: ## Run Node.js SDK tests
	cd sdks/node && $(NPM) test

test-cov: ## Run tests with coverage report
	$(PYTHON) -m $(PYTEST) $(TESTS_DIR) -v --cov=$(BACKEND_DIR) --cov-report=term-missing --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

test-frontend: ## Run frontend tests (if configured)
	cd $(FRONTEND_DIR) && $(NPM) test --if-present

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint Python code with ruff
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff check .
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff format --check .

lint-frontend: ## Lint frontend code with ESLint
	cd $(FRONTEND_DIR) && $(NPM) run lint

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

format: format-backend format-frontend ## Auto-format all code

format-backend: ## Format Python code with ruff
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff check --fix .
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff format .

format-frontend: ## Format frontend code with Prettier
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,tsx,css}" 2>/dev/null || true

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-build: ## Build the backend Docker image
	cd $(BACKEND_DIR) && $(DOCKER) build -t tokenmeter-api:latest .

docker-up: ## Start Docker Compose services (PostgreSQL + Redis + ClickHouse)
	cd $(BACKEND_DIR) && $(COMPOSE) up -d postgres redis clickhouse

docker-down: ## Stop Docker Compose services
	cd $(BACKEND_DIR) && $(COMPOSE) down

docker-logs: ## Tail Docker Compose logs
	cd $(BACKEND_DIR) && $(COMPOSE) logs -f

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db-migrate: ## Run PostgreSQL migrations
	psql $(DATABASE_URL) -f database/postgresql/schema.sql

db-seed: ## Seed the database with sample data
	psql $(DATABASE_URL) -f database/seed.sql

db-clickhouse: ## Initialize ClickHouse schema
	clickhouse-client --host $${CLICKHOUSE_HOST:-localhost} < database/clickhouse/schema.sql

db-reset: docker-down docker-up ## Reset database (stop, start, migrate, seed)
	@echo "Waiting for services to start..."
	@sleep 3
	$(MAKE) db-migrate
	$(MAKE) db-seed

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

clean: ## Remove build artifacts and caches
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf coverage.xml
	rm -rf $(BACKEND_DIR)/dist
	rm -rf $(FRONTEND_DIR)/.next 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/node_modules/.cache 2>/dev/null || true
	rm -rf sdks/node/dist sdks/python/dist 2>/dev/null || true
	@echo "Done."

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help: ## Show this help message
	@echo "TokenMeter — Development Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
