"""Structured logging for the Hypertrophy RAG system."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with JSON formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self, logger: logging.Logger, endpoint: str):
        self.logger = logger
        self.endpoint = endpoint
        self.start: float = 0
        self.duration: float = 0
        self.extra: dict = {}

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = (time.perf_counter() - self.start) * 1000
        log_data = {
            "endpoint": self.endpoint,
            "duration_ms": round(self.duration, 2),
            **self.extra,
        }
        if exc_type:
            log_data["error"] = str(exc_val)
            self.logger.error(f"Request failed: {self.endpoint}", extra={"extra_data": log_data})
        else:
            self.logger.info(f"Request completed: {self.endpoint}", extra={"extra_data": log_data})
        return False
