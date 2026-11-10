"""FastAPI application."""

from collections.abc import AsyncIterator, Callable
from importlib.metadata import version
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.sse import EventSourceResponse

from ivlia.api.guards import Auth, HostOriginGuard, allowed_hosts, allowed_origins
from ivlia.api.sessions import COOKIE_NAMES, SESSION_LIFETIME, SessionStore
from ivlia.api.tracing import RequestSpan
from ivlia.config.installation import Environment
from ivlia.contract.events import Event
from ivlia.contract.requests import ChatRequest
from ivlia.contract.sessions import SessionLink
from ivlia.domain.agents.state import AgentState, Message

if TYPE_CHECKING:
    from pydantic import SecretStr

    from ivlia.config.settings import Config

type ChatTurn = Callable[[AgentState], AsyncIterator[Event]]


def create_app(
    config: Config,
    token: SecretStr,
    chat: ChatTurn,
    sessions: SessionStore | None = None,
) -> FastAPI:
    dev = config.installation.env is Environment.DEV
    # /openapi.json is served in every installation; Swagger UI only in dev.
    app = FastAPI(
        title="ivlia",
        version=version("ivlia"),
        docs_url="/docs" if dev else None,
        redoc_url=None,
        # FastAPI's own telemetry is off: its spans keep the query string (and
        # so one-time link codes), and an environment variable can make it add
        # exporters that leave the Mac. RequestSpan traces requests instead.
        telemetry={
            "tracing": False,
            "metrics": False,
            "logs": False,
            "operation_spans": False,
            "auto_configure": False,
        },
    )
    app.openapi_version = "3.2.0"
    app.add_middleware(
        HostOriginGuard,
        hosts=allowed_hosts(config.port),
        origins=allowed_origins(config),
    )
    # Added last, so it is the outermost layer and rejected requests get a span too.
    app.add_middleware(RequestSpan)

    sessions = sessions or SessionStore()
    cookie_name = COOKIE_NAMES[config.installation.env]
    auth = Auth(token, sessions, cookie_name)
    api = APIRouter(prefix="/api")

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/session/link", dependencies=[Depends(auth.token)])
    async def mint_session_link() -> SessionLink:
        """A one-time link that opens the web with a session. Needs the token."""
        code = sessions.mint_link()
        return SessionLink(
            url=f"http://127.0.0.1:{config.port}/api/session?code={code}"
        )

    @api.get("/session", status_code=status.HTTP_303_SEE_OTHER)
    async def open_session(code: str) -> RedirectResponse:
        """Exchange a one-time link for the session cookie, then open the web."""
        session_id = sessions.redeem(code)
        if session_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Link is invalid, used or expired",
            )
        response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        # No Secure: Safari drops Secure cookies on http://localhost (WebKit 232088).
        response.set_cookie(
            cookie_name,
            session_id,
            max_age=int(SESSION_LIFETIME.total_seconds()),
            path="/",
            httponly=True,
            samesite="strict",
        )
        return response

    @api.post(
        "/chat",
        response_class=EventSourceResponse,
        dependencies=[Depends(auth.token_or_session)],
    )
    async def post_chat(request: ChatRequest) -> AsyncIterator[Event]:
        state = AgentState(messages=(Message(role="user", content=request.message),))
        async for event in chat(state):
            yield event

    app.include_router(api)
    return app
