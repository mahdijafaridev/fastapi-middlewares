"""Example FastAPI app using all middlewares."""

import logging

from fastapi import FastAPI, HTTPException, Request
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
            "error": "/error",
            "not_found": "/not-found",
            "slow": "/slow",
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
    print("\nTry these commands:")
    print("  curl http://localhost:8000/")
    print("  curl -I http://localhost:8000/users/1")
    print("  curl http://localhost:8000/error")
    print("  curl http://localhost:8000/slow")
    print("  curl -H 'Accept-Encoding: gzip' http://localhost:8000/large")
    print("\nCheck the response headers for:")
    print("  - X-Request-ID")
    print("  - X-Process-Time")
    print("  - X-Content-Type-Options")
    print("  - X-Frame-Options")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
