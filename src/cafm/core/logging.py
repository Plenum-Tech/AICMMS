"""Structured logging setup using structlog."""

from __future__ import annotations

import logging
import sys

import structlog

from cafm.core.config import AppConfig


def setup_logging(config: AppConfig | None = None) -> None:
    """Configure structured logging for the platform."""
    config = config or AppConfig()

    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Standard library logging baseline
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if config.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger by name."""
    return structlog.get_logger(name)
