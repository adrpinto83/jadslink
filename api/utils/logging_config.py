"""
Structured logging configuration with JSON output for production.

Logs are output as JSON for easy parsing by log aggregators (ELK, Loki, etc.)
"""

import json
import logging
import sys
from typing import Any
from datetime import datetime
from pythonjsonlogger import jsonlogger
from config import get_settings

settings = get_settings()


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that adds timestamp and environment."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["environment"] = settings.ENVIRONMENT
        log_record["level"] = record.levelname
        log_record["logger"] = record.name


def setup_logging():
    """Configure structured JSON logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # JSON formatter for structured logs
    json_formatter = CustomJsonFormatter(
        fmt="%(timestamp)s %(level)s %(name)s %(message)s"
    )

    # Console handler with JSON output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)

    # Configure uvicorn access logs
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.addHandler(console_handler)
    access_logger.propagate = False

    # Configure uvicorn error logs
    error_logger = logging.getLogger("uvicorn.error")
    error_logger.handlers.clear()
    error_logger.addHandler(console_handler)
    error_logger.propagate = False

    return root_logger
