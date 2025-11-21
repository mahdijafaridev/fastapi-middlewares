# Contributing to FastAPI Middlewares

Thank you for considering contributing to FastAPI Middlewares! 

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/fastapi-middlewares.git
   cd fastapi-middlewares
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync
   ```

3. **Activate virtual environment**
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

## Running Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=middlewares --cov-report=html

# Run specific test file
pytest tests/test_middlewares.py -v
```

## Code Style

We follow PEP 8 and use automated formatters:

```bash
# Format code
ruff format src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/
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

3. **Ensure tests pass**
   ```bash
   pytest -v
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```
   
   Follow conventional commits:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for refactoring

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

## Adding a New Middleware

1. Create the middleware class in `src/middlewares/middlewares.py`
2. Add comprehensive tests in `tests/test_middlewares.py`
3. Export it in `src/middlewares/__init__.py`
4. Document it in `README.md` with examples
5. Add usage example in `examples/`

## Code Review Process

1. All PRs require at least one approval
2. CI must pass (tests, linting, type checking)
3. Maintain test coverage above 90%
4. Address reviewer feedback promptly

## Reporting Issues

When reporting bugs, include:
- Python version
- FastAPI version
- Minimal reproducible example
- Expected vs actual behavior
- Error messages/tracebacks

## Questions?

- Open a GitHub Discussion
- Check existing issues
- Read the documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.