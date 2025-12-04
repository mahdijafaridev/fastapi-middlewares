# Contributing to FastAPI Middlewares

Thank you for considering contributing to FastAPI Middlewares! 🎉

## 🚀 Quick Start
````bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/fastapi-middlewares.git
cd fastapi-middlewares

# Install dependencies
make install

# See all available commands
make help
````

## 💻 Development Workflow
````bash
# Before committing - runs all checks
make check  # Runs lint-fix, format, type-check, and tests

# Individual commands
make test        # Run tests
make test-cov    # Run tests with coverage
make lint-fix    # Fix linting issues
make format      # Format code
make type-check  # Type checking
make dev         # Run example app

# Clean build artifacts
make clean
````

## 🔨 Making Changes

### 1. Start with an Issue
**Always start by creating or finding an issue first:**

- **For bugs**: [Create a bug report](https://github.com/mahdijafaridev/fastapi-middlewares/issues/new?template=bug_report.md)
- **For features**: [Create a feature request](https://github.com/mahdijafaridev/fastapi-middlewares/issues/new?template=feature_request.md)
- **Or** comment on an existing issue to claim it

Wait for feedback before starting work to ensure:
- The change aligns with project goals
- You're not duplicating someone else's work
- The approach makes sense

### 2. Create a Branch
After the issue is confirmed, create a branch directly from the issue page.
GitHub will show a “Create a branch” button and give you the exact command to switch branch locally.

### 3. Make Your Changes
- Write clear, readable code
- Add tests for new features
- Update documentation if needed
- Follow existing code style

### 4. Run Checks
```bash
make check
```
This must pass before you commit.

### 5. Commit Your Changes
Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add rate limiting middleware (#123)"
git commit -m "fix: resolve CORS header issue (#456)"
git commit -m "docs: update README examples (#789)"
```

**Commit format:**
- Include issue number in parentheses: `(#123)`
- Use commit types: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `chore:`, `ci:`

### 6. Push and Create PR
```bash
git push origin feature/123-add-rate-limiting
```

Then create a Pull Request on GitHub:
- **Title**: Same as commit message (e.g., `feat: add rate limiting middleware (#123)`)
- **Description**: Reference the issue with `Fixes #123` or `Closes #123`
- Fill out the PR template

## 📋 Pull Request Guidelines

**Before submitting:**
- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Linting passes (`make lint-fix`)
- [ ] Type checking passes (`make type-check`)
- [ ] Documentation is updated
- [ ] Commits follow Conventional Commits

**PR Requirements:**
- Clear, descriptive title
- Explain what and why (not just what)
- Link related issues (`Fixes #123`)
- Keep PRs focused and reasonably sized
- All CI checks must pass
- Requires 1 approval before merging

## 🆕 Adding a New Middleware

### File Structure
````
src/middlewares/
├── __init__.py          # Export your middleware here
└── middlewares.py       # Implement your middleware here

tests/
└── test_middlewares.py  # Add tests here

examples/
└── example_app.py       # Add usage example
````

### Implementation Template
````python
from starlette.types import ASGIApp, Receive, Scope, Send

class YourMiddleware:
    """
    Brief description of what this middleware does.
    
    Args:
        app: The ASGI application
        option: Description of option (default: "value")
    
    Example:
```python
        from fastapi import FastAPI
        from middlewares import YourMiddleware
        
        app = FastAPI()
        app.add_middleware(YourMiddleware, option="custom")
```
    """

    def __init__(self, app: ASGIApp, option: str = "default") -> None:
        self.app = app
        self.option = option

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Your middleware logic here
        
        await self.app(scope, receive, send)
````

### Checklist for New Middleware
1. [ ] Implement in `src/middlewares/middlewares.py`
2. [ ] Export in `src/middlewares/__init__.py`
3. [ ] Add comprehensive tests in `tests/test_middlewares.py`
4. [ ] Document in README.md with example
5. [ ] Add usage example in `examples/example_app.py`
7. [ ] Add type hints and docstrings
8. [ ] Ensure 100% test coverage for new code

## 🧪 Testing Guidelines
````python
import pytest
from starlette.testclient import TestClient

class TestYourMiddleware:
    """Test YourMiddleware functionality."""

    def test_basic_functionality(self, app, client):
        """Test basic middleware operation."""
        app.add_middleware(YourMiddleware, option="test")
        
        @app.get("/test")
        def test_route():
            return {"status": "ok"}
        
        response = client.get("/test")
        assert response.status_code == 200
        # Add more assertions

    def test_edge_case(self, app, client):
        """Test edge case handling."""
        # Test edge cases
        pass

    def test_error_handling(self, app, client):
        """Test error scenarios."""
        # Test error handling
        pass
````

**Testing Best Practices:**
- Test all new features
- Aim for 100% coverage (`make test-cov`)
- Test edge cases and error conditions
- Use descriptive test names

## 🐛 Reporting Issues

**Before creating an issue:**
1. Search existing issues
2. Check if it's already fixed in `main`
3. Try the latest version

**Include in your report:**
- Clear description of the issue
- Python version (`python --version`)
- FastAPI version (`pip show fastapi`)
- fastapi-middlewares version (`pip show fastapi-middlewares`)
- Minimal reproducible code example
- Expected vs actual behavior
- Full error messages/tracebacks
- Operating system

## 💬 Getting Help

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/mahdijafaridev/fastapi-middlewares/issues/new?template=bug_report.md)
- **✨ Feature Requests**: [GitHub Issues](https://github.com/mahdijafaridev/fastapi-middlewares/issues/new?template=feature_request.md)
- **📚 Documentation**: [README.md](https://github.com/mahdijafaridev/fastapi-middlewares#readme)

## 📜 Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to FastAPI Middlewares! Your help makes this project better for everyone. 🙏