"""Structured logging configuration with correlation IDs."""

import logging
import sys
import uuid
from typing import Any, Dict, Optional

import structlog
from fastapi import Request


def add_correlation_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID to log events."""
    # Try to get correlation ID from context
    correlation_id = getattr(structlog.contextvars, 'correlation_id', None)
    if correlation_id:
        event_dict['correlation_id'] = correlation_id
    return event_dict


def add_request_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request information to log events."""
    # Add any request context that might be available
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with JSON output."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_correlation_id,
            add_request_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return getattr(structlog.contextvars, 'correlation_id', None)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())
