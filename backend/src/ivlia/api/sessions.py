"""Web sessions: one-time links exchanged for a session cookie.

The web never sees the API token: `ivlia web` asks for a link with the token
and opens it in the browser, which gets a cookie instead. Everything lives in
memory, so restarting the server ends every session.
"""

import secrets
import time
from collections.abc import Callable
from datetime import timedelta

LINK_LIFETIME = timedelta(seconds=60)
SESSION_LIFETIME = timedelta(days=7)
COOKIE_NAME = "ivlia_session"

type Clock = Callable[[], float]


def _new_secret() -> str:
    return secrets.token_urlsafe(32)  # 256 random bits


class SessionStore:
    def __init__(self, clock: Clock = time.monotonic) -> None:
        self._clock = clock
        self._links: dict[str, float] = {}
        self._sessions: dict[str, float] = {}

    def mint_link(self) -> str:
        """Create a one-time link code, valid for `LINK_LIFETIME`."""
        self._prune()
        code = _new_secret()
        self._links[code] = self._clock()
        return code

    def redeem(self, code: str) -> str | None:
        """Exchange a link code for a new session id; each code works once."""
        self._prune()
        if self._links.pop(code, None) is None:
            return None
        session_id = _new_secret()
        self._sessions[session_id] = self._clock()
        return session_id

    def is_valid(self, session_id: str) -> bool:
        self._prune()
        return session_id in self._sessions

    def _prune(self) -> None:
        now = self._clock()
        link_limit = now - LINK_LIFETIME.total_seconds()
        session_limit = now - SESSION_LIFETIME.total_seconds()
        self._links = {k: t for k, t in self._links.items() if t > link_limit}
        self._sessions = {k: t for k, t in self._sessions.items() if t > session_limit}
