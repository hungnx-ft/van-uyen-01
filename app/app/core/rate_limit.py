"""Small process-local rate limiters for login and sensitive AI endpoints.

They are intentionally conservative and act as a safety net. Production setups
with multiple workers should also enforce a shared limit at Nginx/API gateway.
Client IPs come from ``request.client``; behind a reverse proxy, run uvicorn
with ``--forwarded-allow-ips`` set to the proxy address so this is the real IP.
"""
from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = monotonic()
        bucket = self._requests[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        if len(self._requests) > 10_000:
            self._prune(now)
        return True

    def _prune(self, now: float):
        for key in [k for k, b in self._requests.items() if not b or now - b[-1] > self.window_seconds]:
            del self._requests[key]

    def reset(self):
        self._requests.clear()


ai_limiter = SlidingWindowLimiter(max_requests=60, window_seconds=60.0)
login_ip_limiter = SlidingWindowLimiter(max_requests=20, window_seconds=60.0)
login_user_limiter = SlidingWindowLimiter(max_requests=10, window_seconds=300.0)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def too_many(message: str, retry_after: int) -> HTTPException:
    return HTTPException(429, message, headers={"Retry-After": str(retry_after)})


def check_login_rate(request: Request, username: str):
    if not login_ip_limiter.allow(client_ip(request)):
        raise too_many("Too many login attempts; try again later", 60)
    if not login_user_limiter.allow(username.strip().lower()):
        raise too_many("Too many login attempts for this account; try again later", 300)


async def ai_rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/v1/ai/") and not ai_limiter.allow(client_ip(request)):
        return JSONResponse(status_code=429, content={"detail": "Too many AI requests; try again later"},
                            headers={"Retry-After": "60"})
    return await call_next(request)
