"""HTTP client of the API: the only module of the CLI that imports httpx2."""

import logging
from typing import TYPE_CHECKING, Self

import httpx2
from pydantic import TypeAdapter, ValidationError

from ivlia.contract.events import Event
from ivlia.contract.sessions import SessionLink

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import TracebackType

    from pydantic import SecretStr

    from ivlia.contract.requests import ChatRequest

logger = logging.getLogger(__name__)

_events: TypeAdapter[Event] = TypeAdapter(Event)

# The first token can take long (a local model may be loading), so a chat
# stream waits for data without limit. Ctrl-C stops it.
_CHAT_TIMEOUT = httpx2.Timeout(5.0, read=None)


class ApiError(Exception):
    """The API could not be used. The message is shown to the user as is."""


class ApiClient:
    def __init__(self, http: httpx2.Client) -> None:
        self._http = http

    @classmethod
    def connect(cls, port: int, token: SecretStr) -> Self:
        """A client of the API on this Mac, authenticated with the token."""
        return cls(
            httpx2.Client(
                base_url=f"http://127.0.0.1:{port}",
                headers={"Authorization": f"Bearer {token.get_secret_value()}"},
                timeout=5.0,
            )
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._http.close()

    def chat(self, request: ChatRequest) -> Iterator[Event]:
        """Send a message and yield the reply's events as they arrive.

        Unknown event types are skipped (tolerant reader), so an older CLI
        keeps working with a newer API.
        """
        body = request.model_dump(mode="json")
        try:
            with self._http.sse(
                "/api/chat", method="POST", json=body, timeout=_CHAT_TIMEOUT
            ) as source:
                # httpx2 does not raise on an error status, and the SSE reader
                # would then fail on the content type and hide it.
                _check_status(source.response)
                for sse in source:
                    event = _parse(sse.data)
                    if event is not None:
                        yield event
        except httpx2.RequestError as error:
            raise ApiError(_describe(error)) from None

    def session_link(self) -> SessionLink:
        """A one-time link that opens the web with a new session."""
        try:
            response = self._http.post("/api/session/link")
        except httpx2.RequestError as error:
            raise ApiError(_describe(error)) from None
        _check_status(response)
        try:
            link = SessionLink.model_validate_json(response.content)
        except ValidationError:
            link = None
        # The link goes to the browser: accept only ivlia's own session page,
        # never whatever another program on the port answers.
        page = self._http.base_url.join("/api/session")
        if link is None or not link.url.startswith(f"{page}?"):
            msg = "The API sent an invalid session link."
            raise ApiError(msg)
        return link


def _parse(data: str) -> Event | None:
    try:
        return _events.validate_json(data)
    except ValidationError as error:
        if all(e["type"] == "union_tag_invalid" for e in error.errors()):
            # Type only: the rest of the event may carry content.
            logger.warning("Ignored an event of unknown type")
            return None
        msg = "The API sent an invalid event."
        raise ApiError(msg) from None


def _check_status(response: httpx2.Response) -> None:
    if response.is_success:
        return
    if response.status_code == httpx2.codes.UNAUTHORIZED:
        msg = "The API rejected the token. Is the server from this installation?"
    else:
        msg = f"The API answered with status {response.status_code}."
    raise ApiError(msg)


def _describe(error: httpx2.RequestError) -> str:
    if isinstance(error, httpx2.ConnectError):
        return "Cannot reach the ivlia server. Is it running? (`ivlia-server`)"
    if isinstance(error, httpx2.TimeoutException):
        return "The ivlia server did not answer in time."
    if isinstance(error, httpx2.SSEError):
        return "The API sent an invalid event stream."
    return "The connection to the ivlia server failed."
