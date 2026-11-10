"""One span per HTTP request."""

from typing import TYPE_CHECKING

from opentelemetry import trace

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

_tracer = trace.get_tracer(__name__)


class RequestSpan:
    """Wraps each request, response body included, in a span.

    Only the method, the path and the status go into it: never the query
    string, which can hold a one-time link code.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        method, path = scope["method"], scope["path"]
        attributes = {"http.request.method": method, "url.path": path}
        with _tracer.start_as_current_span(
            f"{method} {path}", attributes=attributes
        ) as span:

            async def send_with_status(message: Message) -> None:
                if message["type"] == "http.response.start":
                    span.set_attribute("http.response.status_code", message["status"])
                await send(message)

            await self._app(scope, receive, send_with_status)
