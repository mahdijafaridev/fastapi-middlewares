import logging
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
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
    """Create a fresh FastAPI app for each test."""
    return FastAPI()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestRequestIDMiddleware:
    """Test RequestID middleware."""

    def test_generates_request_id(self, app, client):
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_uses_existing_request_id(self, app, client):
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        custom_id = "custom-test-id-123"
        response = client.get("/test", headers={"X-Request-ID": custom_id})

        assert response.headers["x-request-id"] == custom_id

    def test_custom_header_name(self, app, client):
        app.add_middleware(RequestIDMiddleware, header_name="X-Custom-ID")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert "x-custom-id" in response.headers
        assert "x-request-id" not in response.headers


class TestRequestTimingMiddleware:
    """Test RequestTiming middleware."""

    def test_adds_timing_header(self, app, client):
        app.add_middleware(RequestTimingMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert response.status_code == 200
        assert "x-process-time" in response.headers

        timing = float(response.headers["x-process-time"])
        assert timing >= 0

    def test_custom_header_name(self, app, client):
        app.add_middleware(RequestTimingMiddleware, header_name="X-Duration")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert "x-duration" in response.headers
        assert "x-process-time" not in response.headers


class TestSecurityHeadersMiddleware:
    """Test SecurityHeaders middleware."""

    def test_adds_security_headers(self, app, client):
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert response.status_code == 200
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

    def test_removes_server_header(self, app, client):
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert "server" not in response.headers

    def test_custom_headers(self, app, client):
        custom_headers = {"X-Custom-Header": "custom-value"}
        app.add_middleware(SecurityHeadersMiddleware, headers=custom_headers)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test")

        assert "x-custom-header" in response.headers
        assert response.headers["x-custom-header"] == "custom-value"


class TestLoggingMiddleware:
    """Test Logging middleware."""

    def test_logs_request(self, app, client, caplog):
        app.add_middleware(LoggingMiddleware, logger_name="test_logger")

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/test?param=value")

        assert response.status_code == 200

        log_messages = [
            record.message
            for record in caplog.records
            if record.name == "test_logger"
        ]
        assert any("Request started" in msg for msg in log_messages)
        assert any("Request completed" in msg for msg in log_messages)

    def test_skips_paths(self, app, client, caplog):
        app.add_middleware(LoggingMiddleware, logger_name="test_logger", skip_paths=["/health"])

        @app.get("/health")
        def health_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="test_logger"):
            response = client.get("/health")

        assert response.status_code == 200

        log_messages = [
            record.message
            for record in caplog.records
            if record.name == "test_logger"
        ]
        assert not any("/health" in msg for msg in log_messages)


class TestErrorHandlingMiddleware:
    """Test ErrorHandling middleware."""

    def test_catches_exceptions(self, app, client):
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error")

        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "ValueError"
        assert data["message"] == "Test error"

    def test_with_traceback(self, app, client):
        app.add_middleware(ErrorHandlingMiddleware, include_traceback=True)

        @app.get("/error")
        def error_route():
            raise ValueError("Test error")

        response = client.get("/error")

        data = response.json()
        assert "traceback" in data
        assert "ValueError" in data["traceback"]

    def test_http_exception_status_code(self, app, client):
        app.add_middleware(ErrorHandlingMiddleware)

        @app.get("/not-found")
        def not_found_route():
            raise HTTPException(status_code=404, detail="Not found")

        response = client.get("/not-found")

        assert response.status_code == 404


class TestHelperFunctions:
    """Test helper functions."""

    def test_add_cors(self, app, client):
        add_cors(app, allow_origins=["http://localhost:3000"])

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        response = client.get("/test", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_add_gzip(self, app, client):
        add_gzip(app)

        @app.get("/test")
        def test_route():
            return {"status": "ok", "data": "x" * 2000}

        response = client.get("/test", headers={"Accept-Encoding": "gzip"})

        assert response.status_code == 200

    def test_add_essentials(self, app, client, caplog):
        add_essentials(app, cors_origins=["http://localhost:3000"])

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        with caplog.at_level(logging.INFO, logger="fastapi_middlewares"):
            response = client.get("/test")

        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers
        assert "x-content-type-options" in response.headers

        log_messages = [
            record.message
            for record in caplog.records
            if record.name == "fastapi_middlewares"
        ]
        assert any("Request started" in msg for msg in log_messages)


class TestMiddlewareIntegration:
    """Test all middlewares working together."""

    def test_all_middlewares_together(self, app, client, caplog):
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
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers
        assert "x-content-type-options" in response.headers

        log_messages = [
            record.message
            for record in caplog.records
            if record.name == "test_logger"
        ]
        assert any("Request started" in msg for msg in log_messages)
        assert any("Request completed" in msg for msg in log_messages)

    def test_error_with_all_middlewares(self, app, client, caplog):
        app.add_middleware(ErrorHandlingMiddleware)
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

        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers

        log_messages = [record.message for record in caplog.records]
        assert any("failed" in msg.lower() for msg in log_messages)