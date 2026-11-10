from typing import TYPE_CHECKING

import pytest
from api_client import AUTH, make_client
from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ivlia.api.tracing import RequestSpan

if TYPE_CHECKING:
    from collections.abc import Iterator

_exporter = InMemorySpanExporter()


@pytest.fixture(scope="module", autouse=True)
def _global_provider() -> None:
    # The global provider can be set once per process; only this module reads it.
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(_exporter))
    trace.set_tracer_provider(provider)


@pytest.fixture
def exporter() -> Iterator[InMemorySpanExporter]:
    _exporter.clear()
    yield _exporter
    _exporter.clear()


def test_chat_request_has_a_request_span_and_a_use_case_span(
    exporter: InMemorySpanExporter,
) -> None:
    make_client().post("/api/chat", json={"message": "Hi"}, headers=AUTH)

    spans = {span.name: span for span in exporter.get_finished_spans()}
    request, chat = spans["POST /api/chat"], spans["chat"]
    assert request.attributes is not None
    assert request.attributes["http.response.status_code"] == 200
    assert chat.parent is not None
    assert chat.parent.span_id == request.context.span_id


def test_rejected_requests_are_traced_without_the_query(
    exporter: InMemorySpanExporter,
) -> None:
    make_client().get("/api/session", params={"code": "one-time-code"})

    [span] = exporter.get_finished_spans()
    assert span.name == "GET /api/session"
    assert span.attributes is not None
    assert span.attributes["http.response.status_code"] == 401
    assert "one-time-code" not in str(span.to_json())


def test_fastapi_native_telemetry_stays_off(
    exporter: InMemorySpanExporter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FASTAPI_OTEL_AUTO_CONFIGURE", "true")

    make_client().get("/api/health")

    scopes = {
        span.instrumentation_scope.name if span.instrumentation_scope else None
        for span in exporter.get_finished_spans()
    }
    assert scopes == {"ivlia.api.tracing"}


def test_unhandled_exception_keeps_only_its_type(
    exporter: InMemorySpanExporter,
) -> None:
    app = FastAPI()
    app.add_middleware(RequestSpan)

    @app.get("/boom")
    async def boom() -> None:
        msg = "my private note"
        raise RuntimeError(msg)

    TestClient(app, raise_server_exceptions=False).get("/boom")

    [span] = [
        span
        for span in exporter.get_finished_spans()
        if span.instrumentation_scope
        and span.instrumentation_scope.name == "ivlia.api.tracing"
    ]
    assert span.status.description == "RuntimeError"
    assert span.events == ()
    assert "my private note" not in span.to_json()
