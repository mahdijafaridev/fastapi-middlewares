"""Example FastAPI app using all middlewares."""

import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from middlewares import add_essentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="FastAPI Middlewares Example", description="Example app showing all middlewares in action", version="1.0.0"
)

add_essentials(
    app,
    cors_origins=["http://localhost:3000", "http://localhost:5173"],
    include_traceback=True,  # Set to False in production
    logger_name="example_app",
    log_response_body=True,  # Enable response body logging
    max_body_length=500,  # Max body length in characters (after UTF-8 decode). Keep ≤5000 for production.
)


@app.get("/")
def root(request: Request):
    """Root endpoint showing request ID."""
    return {
        "message": "FastAPI Middlewares Example",
        "request_id": request.scope.get("request_id"),
        "endpoints": {
            "root": "/",
            "health": "/health",
            "users": "/users/{user_id}",
            "items": "/items?limit=10",
            "stream": "/stream",
            "ai_chat": "/ai/chat",
            "error": "/error",
            "not_found": "/not-found",
            "slow": "/slow",
            "large": "/large",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health_check():
    """Health check endpoint (not logged)."""
    return {"status": "healthy"}


@app.get("/users/{user_id}")
def get_user(user_id: int, request: Request):
    """Get user by ID."""
    if user_id < 1:
        raise ValueError("User ID must be positive")

    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "request_id": request.scope.get("request_id"),
    }


@app.get("/items")
def get_items(limit: int = 10):
    """Get items with optional limit."""
    return {
        "items": [{"id": i, "name": f"Item {i}"} for i in range(1, min(limit, 100) + 1)],
        "total": min(limit, 100),
    }


@app.post("/items")
def create_item(item: dict):
    """Create a new item."""
    return {"message": "Item created", "item": item, "id": 123}


@app.get("/stream")
async def stream_example():
    """Example streaming endpoint (response body will be logged)."""

    async def generate():
        for i in range(5):
            yield f"Chunk {i + 1}\n"
            await asyncio.sleep(0.1)
        yield "Stream complete!\n"

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/ai/chat")
async def ai_chat_simulation():
    """Simulate AI/LLM streaming response - complete response will be logged after streaming."""

    async def generate():
        response = (
            "This is a simulated LLM/AI/ML response. "
            "The middleware will log the complete response after streaming finishes. "
            "This is useful for debugging and monitoring AI/LLM/ML applications."
        )

        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/error")
def trigger_error():
    """Endpoint that raises an error (for testing error handling)."""
    raise ValueError("This is a test error!")


@app.get("/not-found")
def not_found():
    """Endpoint that returns 404."""
    raise HTTPException(status_code=404, detail="Resource not found")


@app.get("/slow")
def slow_endpoint():
    """Slow endpoint to test timing middleware."""
    import time

    time.sleep(1)
    return {"message": "This took a while", "duration": "1 second"}


@app.get("/large")
def large_response():
    """Large response to test compression."""
    return {"data": "x" * 10000, "message": "This response is compressed with GZip"}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("FastAPI Middlewares Example App")
    print("=" * 60)
    print("\nRunning on: http://localhost:8000")
    print("Documentation: http://localhost:8000/docs")
    print("\nTry these commands:")
    print("  curl http://localhost:8000/")
    print("  curl -I http://localhost:8000/users/1")
    print("  curl http://localhost:8000/error")
    print("  curl http://localhost:8000/slow")
    print("  curl http://localhost:8000/stream")
    print("  curl http://localhost:8000/ai/chat")
    print("  curl -H 'Accept-Encoding: gzip' http://localhost:8000/large")
    print("\nStreaming Response Body Logging:")
    print("  ✓ Complete streamed responses logged after streaming finishes")
    print("  ✓ Handles text, JSON, and binary content automatically")
    print("  ✓ Truncates at max_body_length to prevent memory issues")
    print("  ✓ Perfect for debugging AI/LLM streaming endpoints")
    print("  Check console logs after calling /stream or /ai/chat")
    print("\nCheck the response headers for:")
    print("  - X-Request-ID: Unique request identifier")
    print("  - X-Process-Time: Request processing time")
    print("  - Cache-Control: no-store, max-age=0")
    print("  - Content-Security-Policy: frame-ancestors 'none'")
    print("  - X-Content-Type-Options: nosniff")
    print("  - X-Frame-Options: DENY")
    print("  - Referrer-Policy: no-referrer")
    print("  - Permissions-Policy: geolocation=(), microphone=(), camera=()")
    print("\nNote: Server and X-Powered-By headers are automatically removed")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
