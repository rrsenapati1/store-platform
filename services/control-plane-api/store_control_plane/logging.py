from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from .config import Settings


SENSITIVE_KEYWORDS = (
    "authorization",
    "password",
    "secret",
    "token",
    "pin",
    "taxpayer_password",
    "client_secret",
)


def scrub_sensitive_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        scrubbed: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
                scrubbed[str(key)] = "[REDACTED]"
            else:
                scrubbed[str(key)] = scrub_sensitive_mapping(item)
        return scrubbed
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [scrub_sensitive_mapping(item) for item in value]
    return value


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_payload", None)
        if isinstance(extra, Mapping):
            payload.update(scrub_sensitive_mapping(dict(extra)))
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    root_logger = logging.getLogger()
    if settings.log_format == "json":
        formatter: logging.Formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)
    root_logger.setLevel(logging.INFO)


def log_json(logger: logging.Logger, message: str, *, payload: Mapping[str, Any]) -> None:
    logger.info(message, extra={"extra_payload": scrub_sensitive_mapping(dict(payload))})
