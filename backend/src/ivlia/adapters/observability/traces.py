"""OpenTelemetry traces to a rotating JSON Lines file in the installation folder."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

TRACE_FILE = Path("logs") / "traces.jsonl"
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5


class JsonLinesSpanExporter(SpanExporter):
    """Writes one span per line. Rotation is left to `logging`."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._handler = RotatingFileHandler(
            path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            record = logging.makeLogRecord({"msg": span.to_json(indent=None)})
            self._handler.emit(record)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        self._handler.close()

    def force_flush(self, timeout_millis: int = 30_000) -> bool:  # noqa: ARG002
        self._handler.flush()
        return True


def tracer_provider(home: Path, version: str, *, console: bool) -> TracerProvider:
    """Always export to the file; also to the console if asked. Nothing leaves the Mac."""
    resource = Resource.create({"service.name": "ivlia", "service.version": version})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(JsonLinesSpanExporter(home / TRACE_FILE))
    )
    if console:
        provider.add_span_processor(
            SimpleSpanProcessor(ConsoleSpanExporter(out=sys.stdout))
        )
    return provider
