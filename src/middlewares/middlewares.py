"""
FastAPI Middlewares - Essential middlewares for FastAPI applications.
"""

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    Add unique request ID to each request for tracing purposes.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        self.app = app
        self.header_name = header_name.lower().encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == self.header_name:
                request_id = header_value.decode()
                break

        if not request_id:
            request_id = str(uuid.uuid4())

        scope["request_id"] = request_id

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.header_name, request_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)


class RequestTimingMiddleware:
    """
    Measure and log the time taken to process each request.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Process-Time") -> None:
        self.app = app
        self.header_name = header_name.lower().encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        async def send_with_timing(message):
            if message["type"] == "http.response.start":
                process_time = time.perf_counter() - start_time
                headers = list(message.get("headers", []))
                headers.append((self.header_name, f"{process_time:.4f}".encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_timing)


class SecurityHeadersMiddleware:
    """
    Add security headers to protect against common web vulnerabilities.
    """

    def __init__(
        self,
        app: ASGIApp,
        headers: dict[str, str] | None = None,
        hsts_max_age: int = 31536000,
    ) -> None:
        self.app = app
        self.hsts_max_age = hsts_max_age

        self.headers = headers or {
            # These are default security headers recommended by OWASP: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html#security-headers
            "Cache-Control": "no-store, max-age=0",
            "Content-Security-Policy": "frame-ancestors 'none'",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                headers = [h for h in headers if h[0] not in [b"server", b"x-powered-by"]]

                existing_headers = {h[0].lower() for h in headers}

                for header_name, header_value in self.headers.items():
                    header_name_lower = header_name.lower().encode()
                    if header_name_lower not in existing_headers:
                        headers.append((header_name_lower, header_value.encode()))

                if self._is_https(scope) and b"strict-transport-security" not in existing_headers:
                    hsts_value = f"max-age={self.hsts_max_age}; includeSubDomains"
                    headers.append((b"strict-transport-security", hsts_value.encode()))

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    @staticmethod
    def _is_https(scope: Scope) -> bool:
        scheme: str = scope.get("scheme", "http")
        headers: list[tuple[bytes, bytes]] = scope.get("headers", [])

        for header_name, header_value in headers:
            if header_name.lower() == b"x-forwarded-proto":
                return header_value.decode().lower() == "https"

        return scheme == "https"


class LoggingMiddleware:
    """
    Log incoming requests and outgoing responses.
    """

    def __init__(
        self,
        app: ASGIApp,
        logger_name: str = "fastapi_middlewares",
        skip_paths: list[str] | None = None,
    ) -> None:
        self.app = app
        self.logger = logging.getLogger(logger_name)
        self.skip_paths = skip_paths or ["/health", "/metrics"]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if any(path.startswith(p) for p in self.skip_paths):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        request_id = scope.get("request_id", "N/A")
        start_time = time.perf_counter()
        status_code = 500

        client = scope.get("client", ("unknown", 0))
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "query_string": scope.get("query_string", b"").decode(),
            "client": client[0],
        }
        self.logger.info(f"Request started: {json.dumps(log_data)}")

        async def send_with_logging(message):
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)

            await send(message)

        try:
            await self.app(scope, receive, send_with_logging)
        finally:
            process_time = time.perf_counter() - start_time

            response_log = {
                "request_id": request_id,
                "status_code": status_code,
                "process_time": f"{process_time:.4f}s",
            }

            log_level = "info" if 200 <= status_code < 400 else "warning"
            getattr(self.logger, log_level)(f"Request completed: {json.dumps(response_log)}")


class ErrorHandlingMiddleware:
    """
    Catch exceptions and return formatted error responses.
    """

    def __init__(
        self,
        app: ASGIApp,
        include_traceback: bool = False,
        custom_handlers: dict[type, Callable[[Scope, Exception], Awaitable[JSONResponse]]] | None = None,
    ) -> None:
        self.app = app
        self.include_traceback = include_traceback
        self.custom_handlers = custom_handlers or {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            request_id = scope.get("request_id", "N/A")

            exc_type = type(exc)

            if exc_type in self.custom_handlers:
                handler = self.custom_handlers[exc_type]
                response = await handler(scope, exc)
                await response(scope, receive, send)
                return

            logger.error(
                f"Request {request_id} failed: {exc.__class__.__name__}: {str(exc)}",
                exc_info=True,
            )

            error_detail = {
                "error": exc.__class__.__name__,
                "message": str(exc),
                "request_id": request_id,
            }

            if self.include_traceback:
                import traceback

                error_detail["traceback"] = traceback.format_exc()

            status_code = getattr(exc, "status_code", 500)

            response = JSONResponse(
                status_code=status_code,
                content=error_detail,
            )

            await response(scope, receive, send)


def add_cors(app, allow_origins=None, allow_methods=None, allow_headers=None):
    """Add CORS middleware with sensible defaults."""
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=allow_methods or ["*"],
        allow_headers=allow_headers or ["*"],
    )


def add_gzip(app, minimum_size=1000):
    """Add gzip compression middleware."""
    from starlette.middleware.gzip import GZipMiddleware

    app.add_middleware(GZipMiddleware, minimum_size=minimum_size)


def add_essentials(
    app,
    cors_origins=None,
    enable_gzip=True,
    include_traceback=False,
    logger_name="fastapi_middlewares",
):
    """
    Add all essential middlewares in the correct order.
    Order matters! Add from outermost to innermost.
    """
    app.add_middleware(ErrorHandlingMiddleware, include_traceback=include_traceback)
    app.add_middleware(LoggingMiddleware, logger_name=logger_name)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)

    if cors_origins:
        add_cors(app, allow_origins=cors_origins)

    if enable_gzip:
        add_gzip(app)
