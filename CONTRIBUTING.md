# Contributing to FastAPI Middlewares

Thank you for considering contributing to FastAPI Middlewares! 

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/mahdijafaridev/fastapi-middlewares.git
   cd fastapi-middlewares
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync --dev
   ```

3. **Activate virtual environment**
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

## Running Tests

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/middlewares --cov-report=html --cov-report=term

# Run specific test file
uv run pytest tests/test_middlewares.py -v

# Run tests with verbose output
uv run pytest -vv
```

## Code Quality Checks

We follow PEP 8 and use automated formatters. Run these before committing:

```bash
# Fix all linting issues automatically
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/

# Check linting (without fixing)
uv run ruff check src/ tests/

# Check formatting (without fixing)
uv run ruff format --check src/ tests/

# Type checking
uv run mypy src/ --ignore-missing-imports
```

## Pre-commit Checklist

Before pushing your changes, run all checks:

```bash
# Run all checks at once
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
uv run mypy src/ --ignore-missing-imports
uv run pytest -v --cov=src/middlewares

# Or create this as a pre-commit script
```

## Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, concise code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   # Auto-fix linting and formatting
   uv run ruff check --fix src/ tests/
   uv run ruff format src/ tests/
   
   # Run tests
   uv run pytest -v
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: brief description of changes"
   ```
   
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for refactoring
   - `chore:` for maintenance tasks

5. **Push and create a PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- **Title**: Clear, descriptive title following conventional commits
- **Description**: Explain what and why, not how
- **Tests**: Include tests for new features or bug fixes
- **Documentation**: Update README.md if adding features
- **Small PRs**: Keep changes focused and atomic
- **CI Checks**: All checks must pass before merging

## Adding a New Middleware

1. Create the middleware class in `src/middlewares/middlewares.py`
2. Add comprehensive tests in `tests/test_middlewares.py`
3. Export it in `src/middlewares/__init__.py`
4. Document it in `README.md` with examples
5. Add usage example in `examples/example_app.py`
6. Update `CHANGELOG.md` with the new feature

Example middleware structure:

```python
class YourMiddleware:
    """
    Brief description of what this middleware does.
    """

    def __init__(self, app: ASGIApp, option: str = "default") -> None:
        self.app = app
        self.option = option

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Your middleware logic here
        
        await self.app(scope, receive, send)
```

## Testing Guidelines

- Write tests for all new features
- Aim for 100% code coverage
- Test edge cases and error conditions
- Use descriptive test names
- Group related tests in classes

```python
class TestYourMiddleware:
    """Test YourMiddleware."""

    def test_basic_functionality(self, app, client):
        app.add_middleware(YourMiddleware)
        
        @app.get("/test")
        def test_route():
            return {"status": "ok"}
        
        response = client.get("/test")
        assert response.status_code == 200
```

## Code Review Process

1. All PRs require at least one approval
2. CI must pass (tests, linting, type checking)
3. Maintain test coverage above 90%
4. Address reviewer feedback promptly
5. Keep PRs small and focused

## Reporting Issues

When reporting bugs, include:
- Python version (`python --version`)
- FastAPI version (`pip show fastapi`)
- Minimal reproducible example
- Expected vs actual behavior
- Full error messages/tracebacks
- Operating system

Use this template:

```markdown
**Environment:**
- Python version: 
- FastAPI version:
- OS:

**Bug Description:**
Clear description of the issue

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**
What you expected to happen

**Actual Behavior:**
What actually happened

**Code Example:**
```python
# Minimal reproducible example
```

**Error Output:**
```
# Full error traceback
```
```

## Development Tips

- Use `uv run` prefix for all commands to ensure correct environment
- Run tests frequently during development
- Check test coverage: `uv run pytest --cov=src/middlewares --cov-report=html` then open `htmlcov/index.html`
- Use type hints for better IDE support and catch errors early
- Write docstrings for all public APIs

## Questions?

- **GitHub Discussions**: For general questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check README.md and docs/

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Acknowledgments

Thank you for helping make FastAPI Middlewares better! 🎉