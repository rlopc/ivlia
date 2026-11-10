import json
import logging
from typing import TYPE_CHECKING, Any

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from ivlia.adapters.observability.logs import LOG_FILE, REMOVED, configure_logging

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

MESSAGE_CONTENT = "my private note"  # fake conversation content
logger = logging.getLogger("ivlia.test")


@pytest.fixture
def log_file(tmp_path: Path, request: pytest.FixtureRequest) -> Iterator[Path]:
    log_content: bool = getattr(request, "param", False)
    handler = configure_logging(tmp_path, log_content=log_content)
    yield tmp_path / LOG_FILE
    logging.getLogger().removeHandler(handler)
    handler.close()


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _fail_with_content() -> None:
    content = MESSAGE_CONTENT  # a frame local that must not be logged
    msg = f"model failed on {content}"
    raise RuntimeError(msg)


def test_records_are_json_lines_with_metadata(log_file: Path) -> None:
    logger.info("reply sent", extra={"duration_ms": 12, "color_message": "x"})

    [line] = _lines(log_file)
    assert line["event"] == "reply sent"
    assert line["level"] == "info"
    assert line["logger"] == "ivlia.test"
    assert line["duration_ms"] == 12
    assert "timestamp" in line
    assert "color_message" not in line


def test_content_does_not_reach_the_log_file(log_file: Path) -> None:
    logger.info("user message", extra={"content": MESSAGE_CONTENT})
    try:
        _fail_with_content()
    except RuntimeError:
        logger.exception("reply failed")

    text = log_file.read_text()
    assert MESSAGE_CONTENT not in text
    first, second = _lines(log_file)
    assert first["content"] == REMOVED
    assert second["exception"][0]["exc_type"] == "RuntimeError"


@pytest.mark.parametrize("log_file", [True], indirect=True)
def test_debug_mode_keeps_content(log_file: Path) -> None:
    logger.info("user message", extra={"content": MESSAGE_CONTENT})

    assert _lines(log_file)[0]["content"] == MESSAGE_CONTENT


def test_records_carry_the_current_trace(log_file: Path) -> None:
    tracer = TracerProvider().get_tracer("test")
    with tracer.start_as_current_span("request") as span:
        logger.info("inside a span")
    context = span.get_span_context()

    [line] = _lines(log_file)
    assert line["trace_id"] == trace.format_trace_id(context.trace_id)
    assert line["span_id"] == trace.format_span_id(context.span_id)


def test_exception_groups_and_notes_are_scrubbed(log_file: Path) -> None:
    inner = ValueError(MESSAGE_CONTENT)
    inner.add_note(f"while reading {MESSAGE_CONTENT}")
    try:
        msg = "reply failed"
        raise ExceptionGroup(msg, [inner])  # noqa: TRY301
    except ExceptionGroup:
        logger.exception("reply failed")

    assert MESSAGE_CONTENT not in log_file.read_text()
    [line] = _lines(log_file)
    [group] = line["exception"]
    assert group["is_group"] is True
    [[member]] = group["exceptions"]
    assert member["exc_type"] == "ValueError"
    assert member["exc_value"] == REMOVED
