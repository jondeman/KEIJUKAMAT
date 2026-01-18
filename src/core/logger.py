"""
Structured logging for KonseptiKeiju.

Uses structlog for rich, structured logging with support for
JSON output and human-readable console output.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from rich.console import Console
from rich.logging import RichHandler

from .config import settings

# Console for rich output
console = Console()


def configure_logging() -> None:
    """Configure logging for the application."""
    # Determine log level
    log_level = getattr(logging, settings.log_level, logging.INFO)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )

    # Rich handler for console
    handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
    )
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Reduce noise from httpx and other libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Bound logger instance
    """
    return structlog.get_logger(name)


class RunLogger:
    """
    Logger that writes to both console and a run-specific log file.
    
    This is used during pipeline execution to maintain a complete
    log of all operations for debugging and auditing.
    """

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._logger = get_logger("run")

    def _write_to_file(self, level: str, event: str, **kwargs: Any) -> None:
        """Write a log entry to the JSONL file."""
        import json

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event": event,
            **kwargs,
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(event, **kwargs)
        self._write_to_file("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(event, **kwargs)
        self._write_to_file("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(event, **kwargs)
        self._write_to_file("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(event, **kwargs)
        self._write_to_file("ERROR", event, **kwargs)

    def phase_start(self, phase: str) -> None:
        """Log the start of a phase."""
        self.info(f"Phase started: {phase}", phase=phase, event_type="phase_start")

    def phase_complete(self, phase: str, success: bool, duration_ms: int) -> None:
        """Log the completion of a phase."""
        level = "info" if success else "error"
        getattr(self, level)(
            f"Phase {'completed' if success else 'failed'}: {phase}",
            phase=phase,
            success=success,
            duration_ms=duration_ms,
            event_type="phase_complete",
        )

    def api_call(
        self,
        service: str,
        operation: str,
        duration_ms: int,
        success: bool,
        tokens_used: int | None = None,
    ) -> None:
        """Log an API call."""
        self.info(
            f"API call: {service}.{operation}",
            service=service,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            tokens_used=tokens_used,
            event_type="api_call",
        )

    def artifact_created(self, artifact_type: str, path: str) -> None:
        """Log artifact creation."""
        self.info(
            f"Artifact created: {artifact_type}",
            artifact_type=artifact_type,
            path=path,
            event_type="artifact_created",
        )


# Initialize logging on module import
configure_logging()
