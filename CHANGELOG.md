# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.2.0] - 2025-12-04

### Added
- **LoggingMiddleware**: Streaming response body logging for complete response capture after streaming
- **LoggingMiddleware**: `log_response_body` parameter to enable response body logging (default: False)
- **LoggingMiddleware**: `log_response_body_paths` parameter for path-specific body logging
- **LoggingMiddleware**: `max_body_length` parameter to limit memory usage (default: 1000 characters)
- **LoggingMiddleware**: Automatic truncation when response exceeds max_body_length
- **LoggingMiddleware**: Smart content-type detection (text/JSON/binary)
- **LoggingMiddleware**: UTF-8 decode error handling for malformed responses
- **LoggingMiddleware**: Memory-efficient buffering that stops at limit
- Comprehensive test coverage for all streaming edge cases

### Changed
- **LoggingMiddleware**: `max_body_length` now represents characters (post UTF-8 decode), not bytes
- **LoggingMiddleware**: Empty streaming responses no longer logged
- **LoggingMiddleware**: Binary responses log metadata only (size, content-type)

### Fixed
- **LoggingMiddleware**: Memory leak prevention for large streaming responses
- **LoggingMiddleware**: Proper handling of empty chunks in streams
- **LoggingMiddleware**: Case-insensitive Content-Type header detection
- **LoggingMiddleware**: Correct logging when truncation occurs with no captured content

## [0.1.1] - 2025-11-28

### Changed
- **SecurityHeadersMiddleware**: Simplified Content-Security-Policy to `frame-ancestors 'none'` for better API security and Swagger UI compatibility
- **SecurityHeadersMiddleware**: Updated default headers to match OWASP API security best practices
- **SecurityHeadersMiddleware**: Fixed header processing order - now removes server identification headers before building existing headers set
- **SecurityHeadersMiddleware**: Added duplicate header prevention - checks if headers already exist before adding

### Added
- **SecurityHeadersMiddleware**: Now includes `Cache-Control: no-store, max-age=0` by default
- **SecurityHeadersMiddleware**: Now includes `Referrer-Policy: no-referrer` by default
- **SecurityHeadersMiddleware**: Now includes `Permissions-Policy: geolocation=(), microphone=(), camera=()` by default
- Automatic removal of `Server` and `X-Powered-By` headers to reduce information disclosure

### Removed
- **SecurityHeadersMiddleware**: Removed `X-XSS-Protection` header (deprecated and not recommended: [MDN Reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-XSS-Protection))
- **SecurityHeadersMiddleware**: Removed complex CSP with script/style/img sources (not needed for APIs)

## [0.1.0] - 2025-11-21

### Added
- Initial release of FastAPI Middlewares
- RequestIDMiddleware for request tracing
- RequestTimingMiddleware for performance monitoring
- SecurityHeadersMiddleware for OWASP compliance
- LoggingMiddleware for structured logging
- ErrorHandlingMiddleware for graceful error handling
- Helper functions: `add_cors()`, `add_gzip()`, `add_essentials()`
- Comprehensive test suite with 100% coverage
- Example application
- Documentation and contributing guidelines

[0.2.0]: https://github.com/mahdijafaridev/fastapi-middlewares/compare/v0.2.0...HEAD
[0.1.1]: https://github.com/mahdijafaridev/fastapi-middlewares/releases/tag/v0.1.1
[0.1.0]: https://github.com/mahdijafaridev/fastapi-middlewares/releases/tag/v0.1.0