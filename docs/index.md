# FastAPI Middlewares Documentation

Welcome to FastAPI Middlewares - a collection of essential, production-ready middlewares for FastAPI applications.

## Overview

FastAPI Middlewares provides a set of commonly needed middlewares that follow best practices and are ready for production use. All middlewares are thoroughly tested, type-safe, and easy to integrate.

## Quick Links

- [Installation Guide](installation.md)
- [Quick Start](quickstart.md)
- [API Reference](api-reference.md)
- [Examples](examples.md)
- [Best Practices](best-practices.md)

## Available Middlewares

### RequestIDMiddleware
Adds a unique identifier to each request for distributed tracing.

**Use cases:**
- Debugging across microservices
- Log correlation
- Request tracking in distributed systems

### RequestTimingMiddleware
Measures and reports the time taken to process each request.

**Use cases:**
- Performance monitoring
- SLA tracking
- Identifying slow endpoints

### SecurityHeadersMiddleware
Adds OWASP-recommended security headers to all responses.

**Use cases:**
- XSS protection
- Clickjacking prevention
- Content type sniffing prevention

### LoggingMiddleware
Structured JSON logging for all requests and responses.

**Use cases:**
- Centralized logging systems
- Request auditing
- Performance analysis

### ErrorHandlingMiddleware
Catches exceptions and returns well-formatted error responses.

**Use cases:**
- Consistent error responses
- Error tracking
- Debug information in development

## Philosophy

1. **Simplicity**: Easy to use with sensible defaults
2. **Production-ready**: Battle-tested and secure
3. **Type-safe**: Full type hints for IDE support
4. **Well-tested**: 100% test coverage
5. **Zero config**: Works out of the box

## Support

- [GitHub Issues](https://github.com/mahdijafaridev/fastapi-middlewares/issues)
- [GitHub Discussions](https://github.com/mahdijafaridev/fastapi-middlewares/discussions)
- [Contributing Guide](../CONTRIBUTING.md)