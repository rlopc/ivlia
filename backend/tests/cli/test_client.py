import logging
from typing import TYPE_CHECKING

import httpx2
import pytest
from api_client import AUTH, make_client

from ivlia.cli.client import ApiClient, ApiError
from ivlia.contract.events import EndEvent, TokenEvent
from ivlia.contract.sessions import SessionLink

if TYPE_CHECKING:
    from collections.abc import Callable

SSE = {"content-type": "text/event-stream"}


def _fake_api(handler: Callable[[httpx2.Request], httpx2.Response]) -> ApiClient:
    transport = httpx2.MockTransport(handler)
    return ApiClient(httpx2.Client(transport=transport, base_url="http://127.0.0.1"))


def _answer(
    status: int, body: bytes, headers: dict[str, str] | None = None
) -> ApiClient:
    return _fake_api(lambda _: httpx2.Response(status, headers=headers, content=body))


def _failing(error: Exception) -> ApiClient:
    def handler(_: httpx2.Request) -> httpx2.Response:
        raise error

    return _fake_api(handler)


def test_chat_streams_the_events_of_the_real_app() -> None:
    http = make_client()
    http.headers.update(AUTH)
    with ApiClient(http) as client:
        events = list(client.chat("hello"))
    assert events[-1] == EndEvent()
    assert "".join(e.text for e in events if isinstance(e, TokenEvent)) == (
        "Hello, world!"
    )


def test_chat_sends_the_message_as_a_chat_request() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, headers=SSE, content=b'data: {"type":"end"}\n\n')

    assert list(_fake_api(handler).chat("hi")) == [EndEvent()]
    assert seen[0].method == "POST"
    assert seen[0].url.path == "/api/chat"
    assert seen[0].content == b'{"message":"hi"}'


def test_chat_ignores_and_logs_unknown_event_types(
    caplog: pytest.LogCaptureFixture,
) -> None:
    body = b'data: {"type":"future","content":"secret"}\n\ndata: {"type":"end"}\n\n'
    with caplog.at_level(logging.WARNING):
        events = list(_answer(200, body, SSE).chat("hi"))
    assert events == [EndEvent()]
    assert caplog.messages == ["Ignored an event of unknown type"]


@pytest.mark.parametrize(
    "data",
    [b'{"type":"token"}', b'{"text":"no type"}', b"not json"],
    ids=["missing-field", "missing-type", "not-json"],
)
def test_chat_rejects_an_invalid_event(data: bytes) -> None:
    client = _answer(200, b"data: " + data + b"\n\n", SSE)
    with pytest.raises(ApiError, match="invalid event"):
        list(client.chat("hi"))


@pytest.mark.parametrize(
    ("status", "message"),
    [(401, "rejected the token"), (500, "status 500")],
)
def test_chat_reports_an_error_status(status: int, message: str) -> None:
    client = _answer(status, b'{"detail":"x"}', {"content-type": "application/json"})
    with pytest.raises(ApiError, match=message):
        list(client.chat("hi"))


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (httpx2.ConnectError("refused"), "Cannot reach the ivlia server"),
        (httpx2.ReadTimeout("slow"), "did not answer in time"),
        (httpx2.RemoteProtocolError("broken"), "connection to the ivlia server failed"),
    ],
)
def test_chat_reports_a_transport_error(error: Exception, message: str) -> None:
    with pytest.raises(ApiError, match=message):
        list(_failing(error).chat("hi"))


def test_chat_rejects_a_response_that_is_not_an_event_stream() -> None:
    client = _answer(200, b"{}", {"content-type": "application/json"})
    with pytest.raises(ApiError, match="invalid event stream"):
        list(client.chat("hi"))


def test_session_link_returns_the_link() -> None:
    body = b'{"url":"http://127.0.0.1:8765/api/session?code=abc"}'
    link = _answer(200, body).session_link()
    assert link == SessionLink(url="http://127.0.0.1:8765/api/session?code=abc")


def test_session_link_rejects_an_invalid_body() -> None:
    with pytest.raises(ApiError, match="invalid session link"):
        _answer(200, b'{"link":"x"}').session_link()


def test_session_link_reports_an_error_status() -> None:
    with pytest.raises(ApiError, match="rejected the token"):
        _answer(401, b"{}").session_link()


def test_session_link_reports_a_transport_error() -> None:
    with pytest.raises(ApiError, match="Cannot reach the ivlia server"):
        _failing(httpx2.ConnectError("refused")).session_link()
