# FastAPI Middlewares

Essential middlewares for FastAPI applications.

[![CI](https://github.com/mahdijafaridev/fastapi-middlewares/actions/workflows/ci.yml/badge.svg)](https://github.com/mahdijafaridev/fastapi-middlewares/actions/workflows/ci.yml)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![PyPI Version](https://img.shields.io/pypi/v/fastapi-middlewares.svg)](https://pypi.org/project/fastapi-middlewares/)
[![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-middlewares.svg)](https://pypi.org/project/fastapi-middlewares/)
[![Downloads](https://static.pepy.tech/badge/fastapi-middlewares)](https://pepy.tech/project/fastapi-middlewares)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔍 **Request ID Tracking** - Unique IDs for request tracing
- ⏱️ **Request Timing** - Measure response times
- 🔒 **Security Headers** - OWASP-compliant security headers
- 📝 **Structured Logging** - JSON-formatted request/response logs
- 🌊 **Streaming Response Logging** - Log complete streamed responses (perfect for AI/LLM apps)
- 🚨 **Error Handling** - Graceful error responses with tracebacks
- ⚡ **Easy Setup** - One-line configuration with sensible defaults

## Installation

```bash
pip install fastapi-middlewares
```

Or with uv:
```bash
uv add fastapi-middlewares
```

## Quick Start

```python
from fastapi import FastAPI
from middlewares import add_essentials

app = FastAPI()

# Add all essential middlewares in one line
add_essentials(app)

@app.get("/")
def root():
    return {"message": "Hello World"}
```

That's it! Your app now has:
- ✅ Request ID tracking
- ✅ Request timing
- ✅ Security headers
- ✅ CORS support
- ✅ Error handling
- ✅ Logging
- ✅ GZip compression

## Middlewares

### 1. Request ID Middleware

Adds a unique ID to each request for tracing.

```python
from fastapi import FastAPI, Request
from middlewares import RequestIDMiddleware

app = FastAPI()
app.add_middleware(RequestIDMiddleware)

@app.get("/users/{user_id}")
def get_user(user_id: int, request: Request):
    request_id = request.scope.get("request_id")
    return {"user_id": user_id, "request_id": request_id}
```

**Response Headers:**
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Options:**
- `header_name`: Custom header name (default: "X-Request-ID")

### 2. Request Timing Middleware

Tracks how long each request takes.

```python
from middlewares import RequestTimingMiddleware

app.add_middleware(RequestTimingMiddleware)
```

**Response Headers:**
```
X-Process-Time: 0.0245
```

**Options:**
- `header_name`: Custom header name (default: "X-Process-Time")

### 3. Security Headers Middleware

Adds OWASP-recommended security headers to protect against common attacks.

```python
from middlewares import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

**Default Headers:**
- `Cache-Control: no-store, max-age=0` - Prevents caching of sensitive data
- `Content-Security-Policy: frame-ancestors 'none'` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME-sniffing attacks
- `X-Frame-Options: DENY` - Additional clickjacking protection
- `Referrer-Policy: no-referrer` - Prevents URL leakage
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` - Disables unnecessary browser features
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` - HTTPS enforcement (added automatically for HTTPS connections)

The middleware also removes server identification headers (`Server`, `X-Powered-By`) to reduce information disclosure.

**Custom Headers:**
```python
app.add_middleware(
    SecurityHeadersMiddleware,
    headers={
        "Cache-Control": "no-cache",
        "Content-Security-Policy": "default-src 'self'",
        "Custom-Header": "custom-value"
    },
    hsts_max_age=63072000  # 2 years
)
```

**Options:**
- `headers`: Dict of custom security headers (overrides defaults)
- `hsts_max_age`: HSTS max-age in seconds (default: 31536000 = 1 year)

**Note:** Default headers are compatible with FastAPI's Swagger UI and ReDoc. The middleware respects headers already set by your application routes.

### 4. Logging Middleware

Logs all requests and responses with structured output.

```python
from middlewares import LoggingMiddleware

app.add_middleware(
    LoggingMiddleware,
    logger_name="my_app",
    skip_paths=["/health", "/metrics"]
)
```

**Log Output:**
```json
{
  "request_id": "550e8400-...",
  "method": "GET",
  "path": "/users/123",
  "status_code": 200,
  "process_time": "0.0245s"
}
```

**Options:**
- `logger_name`: Logger name (default: "fastapi_middlewares")
- `skip_paths`: Paths to skip logging (default: ["/health", "/metrics"])
- `log_response_body`: Enable response body logging (default: False)
- `max_body_length`: Maximum response body length in characters to log after UTF-8 decoding (default: 1000). Prevents excessive memory usage for large streams.

#### Streaming Response Logging (NEW)

Perfect for AI/LLM applications! The middleware can now log the complete streamed response after streaming finishes.

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from middlewares import LoggingMiddleware

app = FastAPI()

app.add_middleware(
    LoggingMiddleware,
    log_response_body=True,  # Enable body logging
    max_body_length=500,      # The maximum number of characters (after UTF-8 decoding) to log for body (default: 1000)
)

@app.get("/ai/chat")
async def ai_chat():
    async def generate():
        # Simulate streaming AI response
        for word in "Hello from AI assistant!".split():
            yield word + " "
    
    return StreamingResponse(generate(), media_type="text/plain")
```

#### Important: Memory Considerations

The middleware buffers up to `max_body_length` characters in memory. For large streaming responses:

- ✅ **Safe:** `max_body_length=1000` (default) - ~1KB of text
- ⚠️ **Caution:** `max_body_length=100000` - ~100KB buffered
- ❌ **Risk:** `max_body_length=10000000` - ~10MB buffered per request

**Best practice:** Keep `max_body_length` small (≤5000) for production environments with high traffic.

**What gets logged:**
- The complete response after all chunks are sent
- Truncated if longer than `max_body_length`
- Only text-based responses (JSON, HTML, text)
- Binary responses only log size and content type

**Log output:**
```json
{
  "request_id": "550e8400-...",
  "body": "Hello from AI assistant! ",
  "truncated": false
}
```

**Use cases:**
- Debugging AI/LLM streaming responses
- Monitoring chatbot conversations
- Auditing API responses
- Testing streaming endpoints

### 5. Error Handling Middleware

Catches exceptions and returns formatted JSON errors.

```python
from middlewares import ErrorHandlingMiddleware

app.add_middleware(
    ErrorHandlingMiddleware,
    include_traceback=False  # Set True for development
)
```

**Error Response:**
```json
{
  "error": "ValueError",
  "message": "Invalid user ID",
  "request_id": "550e8400-..."
}
```

**Custom Error Handlers:**
```python
from starlette.responses import JSONResponse

async def handle_value_error(scope, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "bad_request", "message": str(exc)}
    )

app.add_middleware(
    ErrorHandlingMiddleware,
    custom_handlers={ValueError: handle_value_error}
)
```

**Options:**
- `include_traceback`: Include full traceback (default: False)
- `custom_handlers`: Dict mapping exception types to handler functions

### 6. CORS Middleware

Wrapper around Starlette's CORSMiddleware.

```python
from middlewares import add_cors

add_cors(
    app,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### 7. GZip Compression

Wrapper around Starlette's GZipMiddleware.

```python
from middlewares import add_gzip

add_gzip(app, minimum_size=1000)
```

## Middleware Ordering

**Order matters!** Middlewares execute in reverse order of addition.

### Recommended Order:

```python
from fastapi import FastAPI
from middlewares import (
    ErrorHandlingMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RequestTimingMiddleware,
    LoggingMiddleware,
    add_cors,
    add_gzip,
)

app = FastAPI()

# Last added = First executed
add_gzip(app)                               # 7. Compress response
app.add_middleware(LoggingMiddleware)       # 6. Log request/response
app.add_middleware(RequestTimingMiddleware) # 5. Time request
app.add_middleware(RequestIDMiddleware)     # 4. Add request ID
app.add_middleware(SecurityHeadersMiddleware) # 3. Add security headers
add_cors(app)                               # 2. Handle CORS
app.add_middleware(ErrorHandlingMiddleware) # 1. Catch errors (outermost)
```

### Why This Order?

1. **Error handling first** - Catches all exceptions from other middlewares
2. **CORS early** - Handles preflight requests before processing
3. **Security headers** - Added to all responses
4. **Request ID** - Available for all downstream middlewares and logging
5. **Timing** - Measures full request duration
6. **Logging** - Logs complete request/response cycle
7. **Compression last** - Compresses the final response body

## Complete Example

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from middlewares import add_essentials

app = FastAPI(title="My API")

# Add all middlewares with custom config
add_essentials(
    app,
    cors_origins=["http://localhost:3000"],
    include_traceback=False,  # Set True for development
    logger_name="my_api",
    log_response_body=True,   # NEW: Log response bodies
    max_body_length=500,      # NEW: max body length in characters
)

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id < 1:
        raise ValueError("Invalid user ID")
    return {"user_id": user_id, "name": "John"}

@app.get("/ai/chat")
async def ai_chat():
    """Streaming AI endpoint - response will be logged!"""
    async def generate():
        for word in "This is a streaming AI response".split():
            yield word + " "
    
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/error")
def error():
    raise HTTPException(status_code=404, detail="Not found")
```

Run it:
```bash
uvicorn main:app --reload
```

Test it:
```bash
# Check headers
curl -I http://localhost:8000/

# Test streaming with body logging
curl http://localhost:8000/ai/chat

# Check logs to see the complete streamed response
```

## Development

```bash
# Clone the repo
git clone https://github.com/mahdijafaridev/fastapi-middlewares.git
cd fastapi-middlewares

# Install dependencies
uv sync

# Run tests
pytest -v

# Run with coverage
pytest --cov=middlewares --cov-report=html

# Run example app
python examples/example_app.py
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built with ❤️ for the FastAPI community.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Links

- **PyPI:** https://pypi.org/project/fastapi-middlewares/
- **GitHub:** https://github.com/mahdijafaridev/fastapi-middlewares
- **Issues:** https://github.com/mahdijafaridev/fastapi-middlewares/issues