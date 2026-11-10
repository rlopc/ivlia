"""Request guards: Host and Origin allowlists, the API token and web sessions."""

import secrets
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse

from ivlia.config.installation import Environment

if TYPE_CHECKING:
    from collections.abc import Collection

    from pydantic import SecretStr
    from starlette.types import ASGIApp, Receive, Scope, Send

    from ivlia.api.sessions import SessionStore
    from ivlia.config.settings import Config


def allowed_hosts(port: int) -> frozenset[str]:
    return frozenset({f"127.0.0.1:{port}", f"localhost:{port}"})


def allowed_origins(config: Config) -> frozenset[str]:
    origins = {f"http://{host}" for host in allowed_hosts(config.port)}
    if config.installation.env is Environment.DEV:
        origins.add(config.settings.dev_origin)
    return frozenset(origins)


class HostOriginGuard:
    """Rejects requests whose Host or Origin is not ivlia's own, with 403.

    This blocks DNS rebinding and cross-site requests. A request without
    Origin, like the CLI's, is not rejected for it: the token covers it.
    """

    def __init__(
        self, app: ASGIApp, hosts: Collection[str], origins: Collection[str]
    ) -> None:
        self._app = app
        self._hosts = hosts
        self._origins = origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in {"http", "websocket"}:
            headers = {
                k.decode("latin-1"): v.decode("latin-1") for k, v in scope["headers"]
            }
            host = headers.get("host", "").lower()
            origin = headers.get("origin")
            if host not in self._hosts or (
                origin is not None and origin not in self._origins
            ):
                response = JSONResponse(
                    {"detail": "Host or Origin not allowed"},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
                await response(scope, receive, send)
                return
        await self._app(scope, receive, send)


# auto_error=False: a missing credential gets the same 401 as a wrong one.
_bearer = HTTPBearer(auto_error=False)

type _Bearer = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


class Auth:
    """FastAPI dependencies that check the API token or a web session."""

    def __init__(
        self, token: SecretStr, sessions: SessionStore, cookie_name: str
    ) -> None:
        self._token = token.get_secret_value().encode()
        self._sessions = sessions
        # The cookie name depends on the installation, so this dependency is
        # built here; FastAPI still declares the cookie in the OpenAPI document.
        cookie = APIKeyCookie(name=cookie_name, auto_error=False)

        async def token_or_session(
            credentials: _Bearer, session_id: Annotated[str | None, Depends(cookie)]
        ) -> None:
            """The API token, or the session cookie of the web."""
            if self._has_token(credentials):
                return
            if session_id is None or not self._sessions.is_valid(session_id):
                raise _unauthorized()

        self.token_or_session = token_or_session

    def _has_token(self, credentials: HTTPAuthorizationCredentials | None) -> bool:
        return credentials is not None and secrets.compare_digest(
            credentials.credentials.encode(), self._token
        )

    async def token(self, credentials: _Bearer) -> None:
        """Only the API token: `Authorization: Bearer <token>`."""
        if not self._has_token(credentials):
            raise _unauthorized()
