from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..config import Settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, *, bucket: str, subject: str, limit: int, window_seconds: int) -> bool:
        now = monotonic()
        key = (bucket, subject)
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= window_seconds:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: Settings, limiter: InMemoryRateLimiter | None = None) -> None:
        super().__init__(app)
        self._settings = settings
        self._limiter = limiter or InMemoryRateLimiter()

    def _resolve_bucket(self, path: str) -> tuple[str, int] | None:
        if path == "/v1/auth/oidc/exchange":
            return ("auth", self._settings.rate_limit_auth_requests)
        if path.startswith("/v1/auth/store-desktop/"):
            return ("activation", self._settings.rate_limit_activation_requests)
        if path.startswith("/v1/billing/webhooks/"):
            return ("webhook", self._settings.rate_limit_webhook_requests)
        return None

    async def dispatch(self, request, call_next):
        bucket = self._resolve_bucket(request.url.path)
        if bucket is None:
            return await call_next(request)
        bucket_name, limit = bucket
        subject = request.client.host if request.client and request.client.host else "unknown"
        allowed = self._limiter.allow(
            bucket=bucket_name,
            subject=subject,
            limit=limit,
            window_seconds=self._settings.rate_limit_window_seconds,
        )
        if not allowed:
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(self._settings.rate_limit_window_seconds)},
            )
        return await call_next(request)
