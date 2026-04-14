from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware

from ..config import Settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if not self._settings.secure_headers_enabled:
            return response
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", self._settings.secure_headers_csp)
        if self._settings.secure_headers_hsts_enabled:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
