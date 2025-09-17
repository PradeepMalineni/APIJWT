# COP Guard Makefile

.PHONY: help install install-dev test test-cov lint format type-check clean build run docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev,test]"

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linting
	ruff check app/ tests/

format: ## Format code
	ruff format app/ tests/

type-check: ## Run type checking
	mypy app/

check: lint type-check test ## Run all checks

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

build: clean ## Build package
	python -m build

run: ## Run the application
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

run-prod: ## Run the application in production mode
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4

docker-build: ## Build Docker image
	docker build -t cop-guard .

docker-run: ## Run Docker container
	docker run -p 8080:8080 \
		-e COP_AUDIENCE=TSIAM \
		-e ALLOWED_ISSUERS=https://idp.example/issuer \
		-e JWKS_URL_PRIMARY=https://jwks.example/apigee \
		cop-guard

docker-test: ## Run tests in Docker
	docker run --rm -v $(PWD):/app -w /app python:3.11-slim bash -c "pip install -e .[dev,test] && pytest"

security: ## Run security checks
	safety check
	bandit -r app/

ci: check security ## Run CI pipeline locally

dev-setup: install-dev ## Set up development environment
	@echo "Development environment set up successfully!"
	@echo "Run 'make run' to start the development server"

.PHONY: help
