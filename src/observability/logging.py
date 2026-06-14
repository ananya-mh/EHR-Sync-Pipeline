"""Structured logging configuration for the EHR-Sync-Pipeline.

Configures ``structlog`` with either JSON output (for production log
aggregators) or coloured console output (for local development), based on
the ``log_format`` setting.  Also bridges the standard-library ``logging``
module so third-party libraries (kafka-python, uvicorn, etc.) emit
structured output through the same pipeline.
"""

from __future__ import annotations

import logging
import sys

import structlog

from src.config.settings import settings


def setup_logging() -> None:
    """Configure structlog and stdlib logging using centralised settings."""
    log_level = settings.log_level.upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # ------------------------------------------------------------------
    # Shared processors used by both structlog and the stdlib bridge
    # ------------------------------------------------------------------
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # ------------------------------------------------------------------
    # Configure structlog
    # ------------------------------------------------------------------
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ------------------------------------------------------------------
    # Bridge stdlib logging so kafka-python, uvicorn, etc. use structlog
    # ------------------------------------------------------------------
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)


def get_logger(stream_name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger with ``stream_name`` pre-bound."""
    return structlog.get_logger(stream_name=stream_name)
