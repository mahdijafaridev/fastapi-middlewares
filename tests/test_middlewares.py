import json
import logging
import time
import uuid
from collections import Counter
from collections.abc import Callable

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse, StreamingResponse

from middlewares import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
    RequestTimingMiddleware,
    SecurityHeadersMiddleware,
    add_cors,
    add_essentials,
    add_gzip,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI app for each test."""
    return FastAPI()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


# ============================================================================
# Test Helpers
# ============================================================================


def assert_valid_uuid(value: str) -> None:
    """Assert that a string is a valid UUID."""
    try:
        uuid.UUID(value)
    except ValueError:
        pytest.fail(f"'{value}' is not a valid UUID")


def add_route(app: FastAPI, path: str = "/test", handler: Callable | None = None) -> None:
    """Add a simple test route to the app."""
    if handler is None:

        def handler():
            return {"status": "ok"}

    app.get(path)(handler)


def add_slow_route(app: FastAPI, delay: float = 0.1) -> None:
    """Add a route with artificial delay."""

    def slow_handler():
        time.sleep(delay)
        return {"status": "ok"}

    app.get("/slow")(slow_handler)


def add_error_route(app: FastAPI, exception: Exception) -> None:
    """Add a route that raises an exception."""

    def error_handler():
        raise exception

    app.get("/error")(error_handler)


def get_logs(caplog, logger_name: str, filter_text: str = "") -> list[str]:
    """Extract log messages from caplog for a specific logger."""
    messages = [record.message for record in caplog.records if record.name == logger_name]
    if filter_text:
        messages = [msg for msg in messages if filter_text in msg]
    return messages


# ============================================================================
# RequestID Middleware Tests
# ============================================================================


class TestRequestIDMiddleware:
    """Test RequestID middleware."""

    def test_generates_unique_request_id(self, app, client):
        """Middleware should generate a valid UUID for each request."""
        app.add_middleware(RequestIDMiddleware)
        add_route(app)

        response = client.get("/test")

        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert_valid_uuid(response.headers["x-request-id"])

    def test_preserves_existing_request_id(self, app, client):
        """Middleware should use request ID from incoming headers."""
        app.add_middleware(RequestIDMiddleware)
        add_route(app)

        custom_id = "custom-test-id-123"
        response = client.get("/test", headers={"X-Request-ID": custom_id})

        assert response.headers["x-request-id"] == custom_id

    def test_custom_header_name(self, app, client):
        """Middleware should work with custom header names."""
        app.add_middleware(RequestIDMiddleware, header_name="X-Custom-ID")
        add_route(app)

        response = client.get("/test")

        assert "x-custom-id" in response.headers
        assert "x-request-id" not in response.headers

    def test_request_id_available_in_scope(self, app, client):
        """Request ID should be accessible in request scope."""
        app.add_middleware(RequestIDMiddleware)

        captured_id = None

        def handler(request: Request):
            nonlocal captured_id
            captured_id = request.scope.get("request_id")
            return {"status": "ok"}

        add_route(app, handler=handler)
        response = client.get("/test")

        assert captured_id is not None
        assert captured_id == response.headers["x-request-id"]


# ============================================================================
# RequestTiming Middleware Tests
# ============================================================================


class TestRequestTimingMiddleware:
    """Test RequestTiming middleware."""

    def test_adds_timing_header(self, app, client):
        """Middleware should add process time header with valid value."""
        app.add_middleware(RequestTimingMiddleware)
        add_route(app)

        response = client.get("/test")

        assert response.status_code == 200
        assert "x-process-time" in response.headers

        timing = float(response.headers["x-process-time"])
        assert 0 <= timing < 1.0

    def test_timing_accuracy(self, app, client):
        """Process time should accurately reflect request duration."""
        app.add_middleware(RequestTimingMiddleware)
        add_slow_route(app, delay=0.1)

        response = client.get("/slow")
        timing = float(response.headers["x-process-time"])

        assert 0.1 <= timing < 0.5  # Allow CI overhead

    def test_custom_header_name(self, app, client):
        """Middleware should support custom header names."""
        app.add_middleware(RequestTimingMiddleware, header_name="X-Duration")
        add_route(app)

        response = client.get("/test")

        assert "x-duration" in response.headers
        assert "x-process-time" not in response.headers


# ============================================================================
# SecurityHeaders Middleware Tests
# ============================================================================


class TestSecurityHeadersMiddleware:
    """Test SecurityHeaders middleware."""

    DEFAULT_HEADERS = {
        "cache-control": "no-store, max-age=0",
        "content-security-policy": "frame-ancestors 'none'",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "no-referrer",
        "permissions-policy": "geolocation=(), microphone=(), camera=()",
    }

    def test_adds_all_default_headers(self, app, client):
        """Middleware should add all default security headers."""
        app.add_middleware(SecurityHeadersMiddleware)
        add_route(app)

        response = client.get("/test")

        for header, expected_value in self.DEFAULT_HEADERS.items():
            assert response.headers.get(header) == expected_value

    def test_removes_server_identification(self, app, client):
        """Middleware should remove server identification headers."""
        app.add_middleware(SecurityHeadersMiddleware)
        add_route(app)

        response = client.get("/test")

        assert "server" not in response.headers
        assert "x-powered-by" not in response.headers

    def test_hsts_added_for_https(self, app, client):
        """HSTS header should be added for HTTPS connections."""
        app.add_middleware(SecurityHeadersMiddleware, hsts_max_age=63072000)
        add_route(app)

        response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

        assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"

    def test_hsts_not_added_for_http(self, app, client):
        """HSTS header should not be added for HTTP connections."""
        app.add_middleware(SecurityHeadersMiddleware)
        add_route(app)

        response = client.get("/test")

        assert "strict-transport-security" not in response.headers

    def test_custom_headers_override_defaults(self, app, client):
        """Custom headers should completely replace defaults."""
        custom_headers = {
            "Cache-Control": "no-cache",
            "X-Custom-Header": "custom-value",
        }
        app.add_middleware(SecurityHeadersMiddleware, headers=custom_headers)
        add_route(app)

        response = client.get("/test")

        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["x-custom-header"] == "custom-value"
        assert "referrer-policy" not in response.headers
        assert "permissions-policy" not in response.headers

    def test_no_duplicate_headers(self, app, client):
        """Each security header should appear exactly once."""
        app.add_middleware(SecurityHeadersMiddleware)
        add_route(app)

        response = client.get("/test")
        header_counts = Counter(key.lower() for key in response.headers.keys())

        for header in self.DEFAULT_HEADERS.keys():
            assert header_counts[header] == 1

    def test_respects_route_headers(self, app, client):
        """Middleware should not override headers set by routes."""
        app.add_middleware(SecurityHeadersMiddleware)

        def handler():
            return JSONResponse(content={"status": "ok"}, headers={"Cache-Control": "public, max-age=3600"})

        add_route(app, handler=handler)
        response = client.get("/test")

        assert response.headers["cache-control"] == "public, max-age=3600"
        assert "content-security-policy" in response.headers


# ============================================================================
# Logging Middleware Tests
# ============================================================================


class TestLoggingMiddleware:
    """Test Logging middleware."""

    LOGGER_NAME = "test_logger"

    def test_logs_request_lifecycle(self, app, client, caplog):
        """Middleware should log request start and completion."""
        app.add_middleware(LoggingMiddleware, logger_name=self.LOGGER_NAME)
        add_route(app)

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            response = client.get("/test?param=value")

        assert response.status_code == 200
        logs = get_logs(caplog, self.LOGGER_NAME)

        assert any("Request started" in msg and "GET" in msg for msg in logs)
        assert any("Request completed" in msg for msg in logs)

    def test_logs_process_time(self, app, client, caplog):
        """Process time should be included in completion logs."""
        app.add_middleware(LoggingMiddleware, logger_name=self.LOGGER_NAME)
        add_route(app)

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/test")

        completed_logs = get_logs(caplog, self.LOGGER_NAME, "Request completed")
        assert any("process_time" in msg for msg in completed_logs)

    def test_skips_configured_paths(self, app, client, caplog):
        """Configured paths should not be logged."""
        app.add_middleware(LoggingMiddleware, logger_name=self.LOGGER_NAME, skip_paths=["/health", "/metrics"])
        add_route(app, "/health")
        add_route(app, "/test")

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/health")
            client.get("/test")

        logs = get_logs(caplog, self.LOGGER_NAME)
        assert not any("/health" in msg for msg in logs)
        assert any("/test" in msg for msg in logs)

    def test_logs_errors_with_warning_level(self, app, client, caplog):
        """Error responses should be logged at WARNING level."""
        app.add_middleware(ErrorHandlingMiddleware)
        app.add_middleware(LoggingMiddleware, logger_name=self.LOGGER_NAME)
        add_error_route(app, HTTPException(status_code=500, detail="Server error"))

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/error")

        completion_records = [
            r for r in caplog.records if r.name == self.LOGGER_NAME and "Request completed" in r.message
        ]
        assert any(r.levelname == "WARNING" for r in completion_records)


# ============================================================================
# Streaming Response Logging Tests
# ============================================================================


class TestStreamingResponseLogging:
    """Test streaming response body logging."""

    LOGGER_NAME = "test_logger"

    def setup_streaming_route(self, app, chunks: list[bytes], media_type: str = "text/plain"):
        """Setup a streaming response route."""

        async def generate():
            for chunk in chunks:
                yield chunk

        @app.get("/stream")
        def stream_route():
            return StreamingResponse(generate(), media_type=media_type)

    def test_logs_streaming_body_when_enabled(self, app, client, caplog):
        """Streaming response body should be logged when enabled."""
        app.add_middleware(
            LoggingMiddleware,
            logger_name=self.LOGGER_NAME,
            log_response_body=True,
        )
        self.setup_streaming_route(app, [b"Hello ", b"World", b"!"])

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            response = client.get("/stream")

        assert response.text == "Hello World!"
        body_logs = get_logs(caplog, self.LOGGER_NAME, "Response body:")

        assert len(body_logs) == 1
        assert "Hello World!" in body_logs[0]

    def test_does_not_log_body_by_default(self, app, client, caplog):
        """Response body should not be logged by default."""
        app.add_middleware(LoggingMiddleware, logger_name=self.LOGGER_NAME)
        self.setup_streaming_route(app, [b"Hello ", b"World"])

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/stream")

        body_logs = get_logs(caplog, self.LOGGER_NAME, "Response body:")
        assert len(body_logs) == 0

    def test_truncates_long_bodies(self, app, client, caplog):
        """Long response bodies should be truncated."""
        app.add_middleware(
            LoggingMiddleware,
            logger_name=self.LOGGER_NAME,
            log_response_body=True,
            max_body_length=50,
        )

        long_text = "x" * 200
        chunks = [long_text[i : i + 20].encode() for i in range(0, len(long_text), 20)]
        self.setup_streaming_route(app, chunks)

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/stream")

        body_logs = get_logs(caplog, self.LOGGER_NAME, "Response body:")
        assert "truncated" in body_logs[0]
        assert "full_length" in body_logs[0]

    def test_logs_json_streaming(self, app, client, caplog):
        """JSON streaming responses should be logged correctly."""
        app.add_middleware(
            LoggingMiddleware,
            logger_name=self.LOGGER_NAME,
            log_response_body=True,
        )
        chunks = [b'{"items": [', b'{"id": 1}, ', b'{"id": 2}', b"]}"]
        self.setup_streaming_route(app, chunks, media_type="application/json")

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/stream")

        body_logs = get_logs(caplog, self.LOGGER_NAME, "Response body:")
        log_json = json.loads(body_logs[0].replace("Response body: ", ""))

        assert log_json["body"] == '{"items": [{"id": 1}, {"id": 2}]}'

    def test_handles_binary_content(self, app, client, caplog):
        """Binary content should not be logged (only metadata)."""
        app.add_middleware(
            LoggingMiddleware,
            logger_name=self.LOGGER_NAME,
            log_response_body=True,
        )
        binary_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        self.setup_streaming_route(app, [binary_data], media_type="image/png")

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/stream")

        body_logs = get_logs(caplog, self.LOGGER_NAME, "Response body")
        assert "binary" in body_logs[0]
        assert "image/png" in body_logs[0]
        assert "size" in body_logs[0]

    def test_handles_unicode(self, app, client, caplog):
        """Unicode characters should be logged correctly."""
        app.add_middleware(
            LoggingMiddleware,
            logger_name=self.LOGGER_NAME,
            log_response_body=True,
        )
        chunks = ["Hello 世界 ".encode(), "🚀 Emoji".encode()]
        self.setup_streaming_route(app, chunks, media_type="text/plain; charset=utf-8")

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/stream")

        body_logs = get_logs(caplog, self.LOGGER_NAME, "Response body:")
        assert "Hello 世界" in body_logs[0]
        assert "🚀 Emoji" in body_logs[0]

    def test_large_streaming_response_memory_limit(self, app, client, caplog):
        """Test that large responses stop buffering at max_body_length."""
        app.add_middleware(
            LoggingMiddleware,
            logger_name=self.LOGGER_NAME,
            log_response_body=True,
            max_body_length=100,
        )

        async def generate():
            for _ in range(100):
                yield b"x" * 10000  # 10KB each = 1MB total

        @app.get("/huge")
        def huge():
            return StreamingResponse(generate(), media_type="text/plain")

        with caplog.at_level(logging.INFO, logger=self.LOGGER_NAME):
            client.get("/huge")

        body_logs = get_logs(caplog, self.LOGGER_NAME, "Response body:")
        assert len(body_logs) == 1
        assert "truncated" in body_logs[0]

        log_json = json.loads(body_logs[0].replace("Response body: ", ""))
        assert len(log_json["body"]) == 100


# ============================================================================
# ErrorHandling Middleware Tests
# ============================================================================


class TestErrorHandlingMiddleware:
    """Test ErrorHandling middleware."""

    def test_catches_value_error(self, app, client):
        """ValueError should be caught and formatted."""
        app.add_middleware(ErrorHandlingMiddleware)
        add_error_route(app, ValueError("Test error message"))

        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "ValueError"
        assert data["message"] == "Test error message"
        assert "request_id" in data

    def test_catches_generic_exceptions(self, app, client):
        """Any exception should be caught and formatted."""
        app.add_middleware(ErrorHandlingMiddleware)
        add_error_route(app, RuntimeError("Runtime error"))

        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "RuntimeError"
        assert data["message"] == "Runtime error"

    def test_includes_traceback_when_enabled(self, app, client):
        """Traceback should be included when explicitly enabled."""
        app.add_middleware(ErrorHandlingMiddleware, include_traceback=True)
        add_error_route(app, ValueError("Test error"))

        response = client.get("/error")
        data = response.json()

        assert "traceback" in data
        assert "ValueError" in data["traceback"]

    def test_excludes_traceback_by_default(self, app, client):
        """Traceback should be excluded by default."""
        app.add_middleware(ErrorHandlingMiddleware)
        add_error_route(app, ValueError("Test error"))

        response = client.get("/error")

        assert "traceback" not in response.json()

    def test_preserves_http_exception_codes(self, app, client):
        """HTTP exception status codes should be preserved."""
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/not-found")
        def not_found():
            raise HTTPException(status_code=404, detail="Not found")

        @app.get("/unauthorized")
        def unauthorized():
            raise HTTPException(status_code=401, detail="Unauthorized")

        assert client.get("/not-found").status_code == 404
        assert client.get("/unauthorized").status_code == 401

    def test_custom_error_handler(self, app, client):
        """Custom error handlers should be used when registered."""

        async def handle_value_error(scope, exc):
            return JSONResponse(status_code=400, content={"custom_error": "bad_request", "details": str(exc)})

        app.add_middleware(ErrorHandlingMiddleware, custom_handlers={ValueError: handle_value_error})
        add_error_route(app, ValueError("Invalid input"))

        response = client.get("/error")

        assert response.status_code == 400
        data = response.json()
        assert data["custom_error"] == "bad_request"


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestHelperFunctions:
    """Test helper functions."""

    def test_add_cors_with_specific_origins(self, app, client):
        """CORS should work with specific allowed origins."""
        add_cors(app, allow_origins=["http://localhost:3000"])
        add_route(app)

        response = client.get("/test", headers={"Origin": "http://localhost:3000"})

        assert "access-control-allow-origin" in response.headers

    def test_add_cors_with_wildcard(self, app, client):
        """CORS should work with wildcard origin."""
        add_cors(app)
        add_route(app)

        response = client.get("/test", headers={"Origin": "http://example.com"})

        assert "access-control-allow-origin" in response.headers

    def test_add_gzip(self, app, client):
        """GZip compression should be enabled."""
        add_gzip(app)

        @app.get("/test")
        def handler():
            return {"status": "ok", "data": "x" * 2000}

        response = client.get("/test", headers={"Accept-Encoding": "gzip"})

        assert response.status_code == 200

    def test_add_essentials_includes_all(self, app, client, caplog):
        """add_essentials should enable all essential middlewares."""
        add_essentials(app, cors_origins=["http://localhost:3000"])
        add_route(app)

        with caplog.at_level(logging.INFO, logger="fastapi_middlewares"):
            response = client.get("/test")

        # Check middleware headers
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers
        assert "x-content-type-options" in response.headers

        # Check logging
        logs = get_logs(caplog, "fastapi_middlewares", "Request started")
        assert len(logs) > 0

    def test_add_essentials_with_custom_logger(self, app, client, caplog):
        """add_essentials should support custom logger names."""
        add_essentials(app, logger_name="custom_logger")
        add_route(app)

        with caplog.at_level(logging.INFO, logger="custom_logger"):
            client.get("/test")

        assert len(get_logs(caplog, "custom_logger")) > 0

    def test_add_essentials_without_gzip(self, app, client):
        """add_essentials should allow disabling gzip."""
        add_essentials(app, enable_gzip=False)
        add_route(app)

        response = client.get("/test")

        assert "x-request-id" in response.headers


# ============================================================================
# Integration Tests
# ============================================================================


class TestMiddlewareIntegration:
    """Test middleware integration and ordering."""

    def test_all_middlewares_together(self, app, client, caplog):
        """All middlewares should work together without conflicts."""
        app.add_middleware(ErrorHandlingMiddleware)
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")
        app.add_middleware(RequestTimingMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestIDMiddleware)
        add_route(app)

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/test")

        assert response.status_code == 200
        assert all(
            h in response.headers for h in ["x-request-id", "x-process-time", "x-content-type-options", "cache-control"]
        )

        logs = get_logs(caplog, "test_logger")
        assert any("Request started" in msg for msg in logs)

    def test_error_handling_with_full_stack(self, app, client):
        """Error handling should work with all middlewares active."""
        app.add_middleware(ErrorHandlingMiddleware, include_traceback=True)
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")
        app.add_middleware(RequestTimingMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestIDMiddleware)
        add_error_route(app, ValueError("Test error"))

        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "ValueError"
        assert "traceback" in data
        assert all(h in response.headers for h in ["x-request-id", "x-process-time", "x-content-type-options"])

    def test_recommended_middleware_order(self, app, client, caplog):
        """Test recommended middleware ordering (outermost to innermost)."""
        add_gzip(app)
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")
        app.add_middleware(RequestTimingMiddleware)
        app.add_middleware(RequestIDMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)
        add_cors(app)
        app.add_middleware(ErrorHandlingMiddleware)
        add_route(app)

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/test")

        assert response.status_code == 200
        assert all(h in response.headers for h in ["x-request-id", "x-process-time", "x-content-type-options"])
