"""JSON logs to a file in the installation folder.

Code logs through the standard `logging` module; structlog only formats the
records. By default no message content reaches the log ([docs/07]).
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from opentelemetry import trace
from structlog.tracebacks import ExceptionDictTransformer

if TYPE_CHECKING:
    from structlog.typing import EventDict, Processor, WrappedLogger

LOG_FILE = Path("logs") / "ivlia.log"
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

CONTENT_KEYS = frozenset({"content", "text", "prompt", "reply", "messages"})
"""Extra fields that carry conversation content."""
REMOVED = "[removed]"


def add_trace_context(
    _logger: WrappedLogger, _method: str, event: EventDict
) -> EventDict:
    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        event["trace_id"] = trace.format_trace_id(context.trace_id)
        event["span_id"] = trace.format_span_id(context.span_id)
    return event


def drop_color_message(
    _logger: WrappedLogger, _method: str, event: EventDict
) -> EventDict:
    """uvicorn adds a copy of each message with terminal colours."""
    event.pop("color_message", None)
    return event


def remove_content(_logger: WrappedLogger, _method: str, event: EventDict) -> EventDict:
    """Drop content fields and exception messages, which may quote content."""
    for key in CONTENT_KEYS & event.keys():
        event[key] = REMOVED
    exceptions: list[dict[str, Any]] = event.get("exception", [])
    for exception in exceptions:
        if "exc_value" in exception:
            exception["exc_value"] = REMOVED
    return event


def configure_logging(home: Path, *, log_content: bool) -> logging.Handler:
    """Send every log record to the rotating JSON file. Returns its handler."""
    shared: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_trace_context,
        drop_color_message,
    ]
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            # Frame locals would carry content and secrets: never log them.
            structlog.processors.ExceptionRenderer(
                ExceptionDictTransformer(show_locals=False)
            ),
            *([] if log_content else [remove_content]),
            structlog.processors.JSONRenderer(),
        ],
    )
    path = home / LOG_FILE
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    return handler
