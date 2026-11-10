"""Helpers for the API tests."""

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient
from pydantic import SecretStr

from ivlia.adapters.hello_world_llm import HelloWorldLLM
from ivlia.api.app import create_app
from ivlia.application.chat import Chat
from ivlia.application.orchestration.graph import build_graph
from ivlia.config.installation import Environment, Installation
from ivlia.config.settings import Config, Settings

if TYPE_CHECKING:
    from ivlia.api.sessions import SessionStore

TOKEN = "test-token"  # noqa: S105 (fake token)
AUTH = {"Authorization": f"Bearer {TOKEN}"}


def make_client(
    env: Environment = Environment.USE, sessions: SessionStore | None = None
) -> TestClient:
    """A client of the hello-world app, sending ivlia's own Host."""
    config = Config(
        installation=Installation(env=env, home=Path("/nonexistent")),
        settings=Settings.model_construct(),
    )
    chat = Chat(build_graph(HelloWorldLLM()))
    app = create_app(config, SecretStr(TOKEN), chat, sessions)
    return TestClient(
        app, base_url=f"http://127.0.0.1:{config.port}", follow_redirects=False
    )
