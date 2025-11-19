"""
FastAPI Middlewares - Essential middlewares for FastAPI applications.
"""

import json
import logging
import time
import uuid

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
        if scope["type"] == "http":
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
                headers.append([self.header_name, f"{process_time:.4f}".encode()])
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
        headers: dict = None,
        hsts_max_age: int = 31536000,
    ) -> None:
        self.app = app
        self.headers = headers or {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "0",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss: https:;"
            ),
        }
        self.hsts_max_age = hsts_max_age

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                for header_name, header_value in self.headers.items():
                    headers.append([header_name.lower().encode(), header_value.encode()])

                if self._is_https(scope):
                    hsts_value = f"max-age={self.hsts_max_age}; includeSubDomains"
                    headers.append([b"strict-transport-security", hsts_value.encode()])

                headers = [h for h in headers if h[0] not in [b"server", b"x-powered-by"]]

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    @staticmethod
    def _is_https(scope: Scope) -> bool:
        """
        Determine if the request is over HTTPS.
        """
        scheme = scope.get("scheme", "http")

        for header_name, header_value in scope.get("headers", []):
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
        skip_paths: list = None,
    ) -> None:
        self.app = app
        self.logger = logging.getLogger(logger_name)
        self.skip_paths = skip_paths or ['/health', '/metrics']

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
        custom_handlers: dict = None,
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
