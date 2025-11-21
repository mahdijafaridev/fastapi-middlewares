.PHONY: help install test lint format type-check clean build publish-test publish all

help:
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:
	uv sync --dev

test:
	uv run pytest -v

test-cov:
	uv run pytest -v --cov=src/middlewares --cov-report=html --cov-report=term

lint:
	uv run ruff check src/ tests/

lint-fix:
	uv run ruff check --fix src/ tests/

format:
	uv run ruff format src/ tests/

format-check:
	uv run ruff format --check src/ tests/

type-check:
	uv run mypy src/ --ignore-missing-imports

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	uv build

check: lint-fix format type-check test
	@echo "✅ All checks passed!"

publish-test: build
	uv publish --index-url https://test.pypi.org/legacy/

publish: build
	@echo "⚠️  Publishing to PyPI (production)!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		uv publish; \
		echo "✅ Published to PyPI!"; \
	else \
		echo "❌ Cancelled"; \
	fi

release: check
	@echo "✅ Ready for release!"
	@echo "Next steps:"
	@echo "  1. Update version in pyproject.toml"
	@echo "  2. Update CHANGELOG.md"
	@echo "  3. git commit -am 'chore: bump version to X.Y.Z'"
	@echo "  4. git tag -a vX.Y.Z -m 'Release version X.Y.Z'"
	@echo "  5. git push && git push --tags"
	@echo "  6. make publish-test  # Test on TestPyPI"
	@echo "  7. make publish       # Publish to PyPI"

dev:
	uv run python examples/example_app.py

all: clean install check
	@echo "✅ All tasks completed successfully!"