"""Small process-local rate limiter for sensitive AI endpoints.

It is intentionally conservative and acts as a safety net. Production setups
with multiple workers should also enforce a shared limit at Nginx/API gateway.
"""
from collections import defaultdict, deque
from time import monotonic

from fastapi import Request
from fastapi.responses import JSONResponse

WINDOW_SECONDS = 60.0
MAX_AI_REQUESTS = 60
_requests: dict[str, deque[float]] = defaultdict(deque)


async def ai_rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/v1/ai/"):
        key = request.client.host if request.client else "unknown"
        now = monotonic()
        bucket = _requests[key]
        while bucket and now - bucket[0] > WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= MAX_AI_REQUESTS:
            return JSONResponse(status_code=429, content={"detail": "Too many AI requests; try again later"},
                                headers={"Retry-After": "60"})
        bucket.append(now)
    return await call_next(request)
