import logging
from collections import Counter

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

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


@pytest.fixture
def app():
    """Create a FastAPI app for each test."""
    return FastAPI()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestRequestIDMiddleware:
    """Test RequestID middleware."""

    def test_generates_request_id(self, app, client):
        """Test that middleware generates a unique request ID."""
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

        import uuid

        try:
            uuid.UUID(response.headers["x-request-id"])
        except ValueError:
            pytest.fail("Request ID is not a valid UUID")

    def test_uses_existing_request_id(self, app, client):
        """Test that middleware preserves existing request ID from headers."""
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        custom_id = "custom-test-id-123"
        response = client.get("/test", headers={"X-Request-ID": custom_id})

        assert response.headers["x-request-id"] == custom_id

    def test_custom_header_name(self, app, client):
        """Test that middleware works with custom header name."""
        app.add_middleware(RequestIDMiddleware, header_name="X-Custom-ID")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert "x-custom-id" in response.headers
        assert "x-request-id" not in response.headers

    def test_request_id_in_scope(self, app, client):
        """Test that request ID is stored in scope for use by other middleware."""
        app.add_middleware(RequestIDMiddleware)

        request_id_from_scope = None

        @app.get("/test")
        def test_route(request: Request):
            nonlocal request_id_from_scope
            request_id_from_scope = request.scope.get("request_id")
            return {"status": "ok"}

        response = client.get("/test")

        assert request_id_from_scope is not None
        assert request_id_from_scope == response.headers["x-request-id"]


class TestRequestTimingMiddleware:
    """Test RequestTiming middleware."""

    def test_adds_timing_header(self, app, client):
        """Test that middleware adds process time header."""
        app.add_middleware(RequestTimingMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert response.status_code == 200
        assert "x-process-time" in response.headers

        timing = float(response.headers["x-process-time"])
        assert timing >= 0
        assert timing < 1.0  # Should be very fast for simple endpoint

    def test_timing_accuracy(self, app, client):
        """Test that timing is reasonably accurate."""
        import time

        app.add_middleware(RequestTimingMiddleware)

        @app.get("/slow")
        def slow_route():
            time.sleep(0.1)  # 100ms delay
            return {"status": "ok"}

        response = client.get("/slow")

        timing = float(response.headers["x-process-time"])
        assert timing >= 0.1  # At least 100ms
        assert timing < 0.2  # But not much more

    def test_custom_header_name(self, app, client):
        """Test that middleware works with custom header name."""
        app.add_middleware(RequestTimingMiddleware, header_name="X-Duration")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert "x-duration" in response.headers
        assert "x-process-time" not in response.headers


class TestSecurityHeadersMiddleware:
    """Test SecurityHeaders middleware."""

    def test_adds_all_default_security_headers(self, app, client):
        """Test that all default security headers are added."""
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert response.status_code == 200

        assert "cache-control" in response.headers
        assert response.headers["cache-control"] == "no-store, max-age=0"

        assert "content-security-policy" in response.headers
        assert response.headers["content-security-policy"] == "frame-ancestors 'none'"

        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

        assert "referrer-policy" in response.headers
        assert response.headers["referrer-policy"] == "no-referrer"

        assert "permissions-policy" in response.headers
        assert response.headers["permissions-policy"] == "geolocation=(), microphone=(), camera=()"

    def test_removes_server_identification_headers(self, app, client):
        """Test that Server and X-Powered-By headers are removed."""
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert "server" not in response.headers
        assert "x-powered-by" not in response.headers

    def test_hsts_added_for_https(self, app, client):
        """Test HSTS header is added for HTTPS connections."""
        app.add_middleware(SecurityHeadersMiddleware, hsts_max_age=63072000)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        # Simulate HTTPS request via proxy
        response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

        assert "strict-transport-security" in response.headers
        assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"

    def test_hsts_not_added_for_http(self, app, client):
        """Test HSTS header is NOT added for HTTP connections."""
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        # HSTS should not be present for HTTP
        assert "strict-transport-security" not in response.headers

    def test_hsts_default_max_age(self, app, client):
        """Test HSTS uses default max-age of 1 year."""
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

        assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"

    def test_custom_headers_override_defaults(self, app, client):
        """Test that custom headers completely override default headers."""
        custom_headers = {
            "Cache-Control": "no-cache",
            "Content-Security-Policy": "default-src 'self'",
            "X-Custom-Header": "custom-value",
        }
        app.add_middleware(SecurityHeadersMiddleware, headers=custom_headers)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        # Verify custom headers are used
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["content-security-policy"] == "default-src 'self'"
        assert "x-custom-header" in response.headers
        assert response.headers["x-custom-header"] == "custom-value"

        # Verify default headers are NOT present when custom headers are provided
        assert "referrer-policy" not in response.headers
        assert "permissions-policy" not in response.headers
        assert "x-frame-options" not in response.headers

    def test_no_duplicate_headers(self, app, client):
        """Test that security headers are not duplicated."""
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        # Check that each security header appears only once
        header_names = [key.lower() for key in response.headers.keys()]
        header_counts = Counter(header_names)

        security_headers = [
            "cache-control",
            "content-security-policy",
            "x-content-type-options",
            "x-frame-options",
            "referrer-policy",
            "permissions-policy",
        ]

        for header in security_headers:
            assert header_counts[header] == 1, f"Header {header} appears {header_counts[header]} times"

    def test_respects_existing_headers_from_route(self, app, client):
        """Test that middleware respects headers already set by the route."""
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return JSONResponse(content={"status": "ok"}, headers={"Cache-Control": "public, max-age=3600"})

        response = client.get("/test")

        # Route's cache-control should be preserved (not overridden)
        assert response.headers["cache-control"] == "public, max-age=3600"

        # Other security headers should still be added
        assert "content-security-policy" in response.headers
        assert "x-content-type-options" in response.headers
        assert "referrer-policy" in response.headers

    def test_hsts_not_duplicated_when_already_present(self, app, client):
        """Test HSTS is not added if already present in response."""
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return JSONResponse(content={"status": "ok"}, headers={"Strict-Transport-Security": "max-age=99999"})

        response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

        # Should keep the route's HSTS value
        assert response.headers["strict-transport-security"] == "max-age=99999"

        # Verify no duplicate HSTS headers
        hsts_count = sum(1 for k in response.headers.keys() if k.lower() == "strict-transport-security")
        assert hsts_count == 1


class TestLoggingMiddleware:
    """Test Logging middleware."""

    def test_logs_request_and_response(self, app, client, caplog):
        """Test that middleware logs both request start and completion."""
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/test?param=value")

        assert response.status_code == 200

        log_messages = [record.message for record in caplog.records if record.name == "test_logger"]
        assert any("Request started" in msg for msg in log_messages)
        assert any("Request completed" in msg for msg in log_messages)

        # Verify request details are logged
        started_msg = next(msg for msg in log_messages if "Request started" in msg)
        assert "/test" in started_msg
        assert "GET" in started_msg

    def test_logs_process_time(self, app, client, caplog):
        """Test that process time is included in logs."""
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/test")

        assert response.status_code == 200

        log_messages = [record.message for record in caplog.records if record.name == "test_logger"]
        completed_msg = next(msg for msg in log_messages if "Request completed" in msg)
        assert "process_time" in completed_msg

    def test_skips_configured_paths(self, app, client, caplog):
        """Test that configured paths are not logged."""
        app.add_middleware(LoggingMiddleware, logger_name="test_logger", skip_paths=["/health", "/metrics"])

        @app.get("/health")
        def health_route():
            return {"status": "ok"}

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="test_logger"):
            health_response = client.get("/health")
            test_response = client.get("/test")

        assert health_response.status_code == 200
        assert test_response.status_code == 200

        log_messages = [record.message for record in caplog.records if record.name == "test_logger"]

        # /health should not be logged
        assert not any("/health" in msg for msg in log_messages)

        # /test should be logged
        assert any("/test" in msg for msg in log_messages)

    def test_logs_errors_with_warning_level(self, app, client, caplog):
        """Test that error responses are logged with warning level."""
        app.add_middleware(ErrorHandlingMiddleware)
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")

        @app.get("/error")
        def error_route():
            raise HTTPException(status_code=500, detail="Server error")

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/error")

        assert response.status_code == 500

        # Find the completion log record
        completion_records = [
            record
            for record in caplog.records
            if record.name == "test_logger" and "Request completed" in record.message
        ]

        assert len(completion_records) > 0
        # Error responses should use warning level
        assert any(record.levelname == "WARNING" for record in completion_records)


class TestErrorHandlingMiddleware:
    """Test ErrorHandling middleware."""

    def test_catches_value_error(self, app, client):
        """Test that middleware catches ValueError exceptions."""
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error message")

        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "ValueError"
        assert data["message"] == "Test error message"
        assert "request_id" in data

    def test_catches_generic_exception(self, app, client):
        """Test that middleware catches any exception."""
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/error")
        def error_route():
            raise RuntimeError("Runtime error")

        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "RuntimeError"
        assert data["message"] == "Runtime error"

    def test_includes_traceback_when_enabled(self, app, client):
        """Test that traceback is included when enabled."""
        app.add_middleware(ErrorHandlingMiddleware, include_traceback=True)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error")

        response = client.get("/error")

        data = response.json()
        assert "traceback" in data
        assert "ValueError" in data["traceback"]
        assert "Test error" in data["traceback"]

    def test_excludes_traceback_by_default(self, app, client):
        """Test that traceback is not included by default."""
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error")

        response = client.get("/error")

        data = response.json()
        assert "traceback" not in data

    def test_preserves_http_exception_status_code(self, app, client):
        """Test that HTTP exception status codes are preserved."""
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/not-found")
        def not_found_route():
            raise HTTPException(status_code=404, detail="Resource not found")

        @app.get("/unauthorized")
        def unauthorized_route():
            raise HTTPException(status_code=401, detail="Unauthorized")

        response_404 = client.get("/not-found")
        assert response_404.status_code == 404

        response_401 = client.get("/unauthorized")
        assert response_401.status_code == 401

    def test_custom_error_handler(self, app, client):
        """Test that custom error handlers work."""

        async def handle_value_error(scope, exc):
            return JSONResponse(status_code=400, content={"custom_error": "bad_request", "details": str(exc)})

        app.add_middleware(ErrorHandlingMiddleware, custom_handlers={ValueError: handle_value_error})

        @app.get("/error")
        def error_route():
            raise ValueError("Invalid input")

        response = client.get("/error")

        assert response.status_code == 400
        data = response.json()
        assert data["custom_error"] == "bad_request"
        assert data["details"] == "Invalid input"

    def test_includes_request_id_in_error(self, app, client):
        """Test that request ID is included in error response."""
        app.add_middleware(ErrorHandlingMiddleware)
        app.add_middleware(RequestIDMiddleware)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error")

        response = client.get("/error")

        data = response.json()
        assert "request_id" in data
        assert data["request_id"] != "N/A"


class TestHelperFunctions:
    """Test helper functions."""

    def test_add_cors_with_origins(self, app, client):
        """Test CORS middleware with specific origins."""
        add_cors(app, allow_origins=["http://localhost:3000"])

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_add_cors_with_wildcard(self, app, client):
        """Test CORS middleware with wildcard origin."""
        add_cors(app)  # Default is ["*"]

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test", headers={"Origin": "http://example.com"})

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_add_gzip_compression(self, app, client):
        """Test GZip compression middleware."""
        add_gzip(app)

        @app.get("/test")
        def test_route():
            # Return large response to trigger compression
            return {"status": "ok", "data": "x" * 2000}

        response = client.get("/test", headers={"Accept-Encoding": "gzip"})

        assert response.status_code == 200
        # Content should be returned (TestClient handles decompression)

    def test_add_essentials_includes_all_middlewares(self, app, client, caplog):
        """Test that add_essentials includes all essential middlewares."""
        add_essentials(app, cors_origins=["http://localhost:3000"])

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="fastapi_middlewares"):
            response = client.get("/test")

        assert response.status_code == 200

        # Verify all middleware headers are present
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers
        assert "x-content-type-options" in response.headers
        assert "cache-control" in response.headers

        # Verify logging happened
        log_messages = [record.message for record in caplog.records if record.name == "fastapi_middlewares"]
        assert any("Request started" in msg for msg in log_messages)

    def test_add_essentials_with_custom_logger(self, app, client, caplog):
        """Test add_essentials with custom logger name."""
        add_essentials(app, logger_name="custom_logger")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="custom_logger"):
            response = client.get("/test")

        assert response.status_code == 200

        log_messages = [record.message for record in caplog.records if record.name == "custom_logger"]
        assert len(log_messages) > 0

    def test_add_essentials_without_gzip(self, app, client):
        """Test add_essentials with gzip disabled."""
        add_essentials(app, enable_gzip=False)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert response.status_code == 200
        # Other middlewares should still work
        assert "x-request-id" in response.headers


class TestMiddlewareIntegration:
    """Test all middlewares working together."""

    def test_all_middlewares_together(self, app, client, caplog):
        """Test that all middlewares work together without conflicts."""
        app.add_middleware(ErrorHandlingMiddleware)
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")
        app.add_middleware(RequestTimingMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/test")

        assert response.status_code == 200

        # Verify all middleware features work
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers
        assert "x-content-type-options" in response.headers
        assert "cache-control" in response.headers

        log_messages = [record.message for record in caplog.records if record.name == "test_logger"]
        assert any("Request started" in msg for msg in log_messages)
        assert any("Request completed" in msg for msg in log_messages)

    def test_error_handling_with_all_middlewares(self, app, client, caplog):
        """Test that error handling works with all middlewares active."""
        app.add_middleware(ErrorHandlingMiddleware, include_traceback=True)
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")
        app.add_middleware(RequestTimingMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestIDMiddleware)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error")

        with caplog.at_level(logging.ERROR):
            response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "ValueError"
        assert "traceback" in data

        # Verify all middleware headers are still present on error
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers
        assert "x-content-type-options" in response.headers

        # Verify error was logged
        log_messages = [record.message for record in caplog.records]
        assert any("failed" in msg.lower() or "error" in msg.lower() for msg in log_messages)

    def test_middleware_ordering_matters(self, app, client):
        """Test that middleware ordering affects behavior (request ID in error response)."""
        # Add RequestIDMiddleware AFTER ErrorHandlingMiddleware (wrong order)
        app.add_middleware(RequestIDMiddleware)
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error")

        response = client.get("/error")

        data = response.json()
        # Request ID should still be present because RequestIDMiddleware runs first
        assert "request_id" in data
        assert data["request_id"] != "N/A"

    def test_correct_middleware_order(self, app, client, caplog):
        """Test recommended middleware ordering."""
        # Recommended order: outermost to innermost
        add_gzip(app)
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")
        app.add_middleware(RequestTimingMiddleware)
        app.add_middleware(RequestIDMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)
        add_cors(app)
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/test")

        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers
        assert "x-content-type-options" in response.headers
