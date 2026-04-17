"""
Structured logging configuration using structlog.

Provides JSON-formatted logs with context and correlation IDs.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level
from structlog.stdlib import LoggerFactory, add_logger_name

from .settings import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Configure structlog processors
    processors = [
        add_log_level,
        add_logger_name,
        TimeStamper(fmt="iso", utc=True),
        structlog.contextvars.merge_contextvars,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.processors.ExceptionPrettyPrinter() if settings.debug else structlog.processors.format_exc_info,
    ]
    
    # Add JSON renderer for production
    if settings.log_format == "json":
        processors.append(JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_context(**kwargs: Any) -> Dict[str, Any]:
    """
    Create a logging context dictionary.
    
    Args:
        **kwargs: Key-value pairs to include in context
        
    Returns:
        Context dictionary
    """
    return kwargs


# Initialize logging on import
setup_logging() 