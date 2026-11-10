"""Web session bodies."""

from pydantic import BaseModel


class SessionLink(BaseModel):
    """A one-time link that opens the web with a new session."""

    url: str
