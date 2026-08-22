"""
Centralised Logging Configuration — Sahayak AI Backend
Sets up structured logging that is ready for production log aggregators
(Datadog, CloudWatch, etc.) by emitting JSON-compatible records in prod
and human-readable records in development.
"""

import logging
import sys
from app.core.config import settings


def configure_logging() -> None:
    """
    Configure the root logger once at application startup.
    Called from the FastAPI lifespan handler in main.py.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter: logging.Formatter
    if settings.is_production:
        # Structured format suitable for log aggregation
        formatter = logging.Formatter(
            fmt='{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        # Readable format for local development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    # Force UTF-8 encoding so emoji/unicode in log messages
    # (e.g. 🚀 🛑 ✅) don't raise UnicodeEncodeError on Windows.
    if hasattr(handler.stream, "reconfigure"):
        try:
            handler.stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers in production
    if settings.is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configured | level=%s | env=%s", settings.LOG_LEVEL, settings.APP_ENV
    )


def get_logger(name: str) -> logging.Logger:
    """
    Factory helper — returns a named logger.
    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
