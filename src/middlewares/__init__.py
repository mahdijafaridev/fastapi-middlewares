"""FastAPI Middlewares - Essential middlewares for FastAPI applications."""

__version__ = "0.1.0"

from .middlewares import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
    RequestTimingMiddleware,
    SecurityHeadersMiddleware,
)

__all__ = [
    "RequestIDMiddleware",
    "RequestTimingMiddleware",
    "SecurityHeadersMiddleware",
    "LoggingMiddleware",
    "ErrorHandlingMiddleware",
    "add_cors",
    "add_gzip",
    "add_essentials",
]


def add_cors(
    app,
    allow_origins=None,
    allow_credentials=True,
    allow_methods=None,
    allow_headers=None,
):
    """
    Add CORS middleware using Starlette's built-in CORSMiddleware.

    Args:
        app: FastAPI application
        allow_origins: List of origins that are allowed (default: ["*"])
        allow_credentials: Allow credentials (default: True)
        allow_methods: List of HTTP methods allowed (default: ["*"])
        allow_headers: List of headers allowed (default: ["*"])

    Example:
        add_cors(app, allow_origins=["http://localhost:3000"])
    """
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_credentials=allow_credentials,
        allow_methods=allow_methods or ["*"],
        allow_headers=allow_headers or ["*"],
    )


def add_gzip(app, minimum_size=1000):
    """
    Add GZip compression middleware using Starlette's built-in.

    Args:
        app: FastAPI application
        minimum_size: Minimum response size to compress (default: 1000 bytes)

    Example:
        add_gzip(app, minimum_size=500)
    """
    from starlette.middleware.gzip import GZipMiddleware

    app.add_middleware(GZipMiddleware, minimum_size=minimum_size)


def add_essentials(
    app,
    cors_origins=None,
    include_traceback=False,
    logger_name="fastapi_middlewares",
):
    """
    Add all essential middlewares in the correct order.

    This adds:
    - Error Handling
    - CORS
    - Security Headers
    - Request ID
    - Timing
    - Logging
    - GZip Compression

    Args:
        app: FastAPI application
        cors_origins: List of allowed CORS origins (default: ["*"])
        include_traceback: Include traceback in error responses (default: False)
        logger_name: Name for the logger (default: "fastapi_middlewares")

    Example:
        from fastapi import FastAPI
        from middlewares import add_essentials

        app = FastAPI()
        add_essentials(app, cors_origins=["http://localhost:3000"])
    """
    # Add middlewares in correct order (last added = first executed)
    add_gzip(app)
    app.add_middleware(LoggingMiddleware, logger_name=logger_name)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    add_cors(app, allow_origins=cors_origins)
    app.add_middleware(ErrorHandlingMiddleware, include_traceback=include_traceback)
