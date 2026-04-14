from __future__ import annotations

import logging
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..config import Settings
from ..logging import log_json
from ..sentry import bind_request_scope


REQUEST_ID_HEADER = "x-request-id"
_request_id_var: ContextVar[str | None] = ContextVar("store_control_plane_request_id", default=None)
logger = logging.getLogger("store_control_plane.request")


def get_current_request_id() -> str | None:
    return _request_id_var.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid4().hex
        request.state.request_id = request_id
        token = _request_id_var.set(request_id)
        bind_request_scope(
            request_id=request_id,
            route=request.url.path,
            method=request.method,
            environment=self._settings.deployment_environment,
            release_version=self._settings.release_version,
        )
        start = perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((perf_counter() - start) * 1000, 2)
            log_json(
                logger,
                "request.complete",
                payload={
                    "request_id": request_id,
                    "environment": self._settings.deployment_environment,
                    "release_version": self._settings.release_version,
                    "route": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms,
                },
            )
            _request_id_var.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
