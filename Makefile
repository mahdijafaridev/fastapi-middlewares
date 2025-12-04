.PHONY: help install test test-cov lint lint-fix format type-check clean check dev all

help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

test: ## Run tests
	uv run pytest -v

test-cov: ## Run tests with coverage
	uv run pytest -v --cov=src/middlewares --cov-report=html --cov-report=term

lint: ## Check code with ruff
	uv run ruff check src/ tests/ examples/

lint-fix: ## Fix linting issues
	uv run ruff check --fix src/ tests/ examples/

format: ## Format code with ruff
	uv run ruff format src/ tests/ examples/

type-check: ## Run type checking
	uv run mypy src/ --ignore-missing-imports

clean: ## Remove cache and build files
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

check: lint-fix format type-check test ## Run all checks before commit
	@echo "✅ All checks passed!"

dev: ## Run example app
	uv run uvicorn examples.example_app:app --reload

all: clean install check ## Fresh setup and full check
	@echo "✅ Ready to go!"