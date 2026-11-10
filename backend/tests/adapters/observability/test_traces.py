import json
from typing import TYPE_CHECKING

from ivlia.adapters.observability.traces import (
    TRACE_FILE,
    JsonLinesSpanExporter,
    tracer_provider,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_spans_go_to_the_trace_file_as_json_lines(tmp_path: Path) -> None:
    provider = tracer_provider(tmp_path, "0.0.0", console=False)
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("parent"), tracer.start_as_current_span("child"):
        pass
    provider.shutdown()

    spans = [
        json.loads(line) for line in (tmp_path / TRACE_FILE).read_text().splitlines()
    ]
    assert [span["name"] for span in spans] == ["child", "parent"]
    assert spans[0]["context"]["trace_id"] == spans[1]["context"]["trace_id"]
    assert spans[0]["resource"]["attributes"]["service.name"] == "ivlia"


def test_console_export_is_optional(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = tracer_provider(tmp_path, "0.0.0", console=True)
    with provider.get_tracer("test").start_as_current_span("visible"):
        pass
    provider.shutdown()

    assert '"name": "visible"' in capsys.readouterr().out


def test_exporter_flushes_on_demand(tmp_path: Path) -> None:
    exporter = JsonLinesSpanExporter(tmp_path / TRACE_FILE)

    assert exporter.force_flush() is True
    exporter.shutdown()
