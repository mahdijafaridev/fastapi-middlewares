# Contributing to FastAPI Middlewares

Thank you for considering contributing to FastAPI Middlewares!

## Quick Start

```bash
# Clone and setup
git clone https://github.com/mahdijafaridev/fastapi-middlewares.git
cd fastapi-middlewares
make install

# See all available commands
make help
```

## Development Workflow

```bash
# Before committing
make check  # Runs lint-fix, format, type-check, and tests

# Run tests only
make test

# Run tests with coverage report
make test-cov

# Run the example app
make dev
```

## Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear code
   - Add tests for new features
   - Update docs if needed

3. **Run checks**
   ```bash
   make check
   ```

4. **Commit**
   ```bash
   git commit -m "feat: brief description"
   ```
   
   Use [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - new features
   - `fix:` - bug fixes
   - `docs:` - documentation
   - `test:` - tests
   - `refactor:` - code refactoring
   - `chore:` - maintenance

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Manual Commands (if needed)

```bash
# Fix linting issues
make lint-fix

# Format code
make format

# Type checking
make type-check

# Clean build artifacts
make clean
```

## Pull Request Guidelines

- Clear, descriptive title
- Explain what and why
- Include tests for new features
- Update README.md if adding features
- Keep PRs small and focused
- All CI checks must pass

## Adding a New Middleware

1. Create middleware in `src/middlewares/middlewares.py`
2. Add tests in `tests/test_middlewares.py`
3. Export in `src/middlewares/__init__.py`
4. Document in `README.md`
5. Add example in `examples/example_app.py`
6. Update `CHANGELOG.md`

Example structure:

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

- Test all new features
- Aim for 100% coverage
- Test edge cases
- Use descriptive test names

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

## Reporting Issues

Include:
- Python version
- FastAPI version
- Minimal code example
- Expected vs actual behavior
- Full error messages
- OS

## Questions?

- **GitHub Discussions** - General questions
- **GitHub Issues** - Bug reports and features
- **Documentation** - Check README.md

## License

By contributing, you agree your contributions will be licensed under the MIT License.

Thank you for helping make FastAPI Middlewares better! 🎉