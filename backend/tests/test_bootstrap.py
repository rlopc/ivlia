import logging
from typing import TYPE_CHECKING

import pytest
from api_client import TOKEN
from fastapi.testclient import TestClient

from ivlia.bootstrap import app_factory, build_server
from ivlia.config.secrets import API_TOKEN

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from opentelemetry.sdk.trace import TracerProvider


@pytest.fixture
def dev_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    home = tmp_path / "home"
    monkeypatch.setenv("IVLIA_ENV", "dev")
    monkeypatch.setenv("IVLIA_HOME", str(home))
    monkeypatch.setenv(f"IVLIA_{API_TOKEN.upper()}", TOKEN)
    # The global tracer provider can be set once per process; keep it for other tests.
    providers: list[TracerProvider] = []
    monkeypatch.setattr("ivlia.bootstrap.trace.set_tracer_provider", providers.append)
    root = logging.getLogger()
    handlers = list(root.handlers)
    yield home
    for handler in set(root.handlers) - set(handlers):
        root.removeHandler(handler)
        handler.close()
    for provider in providers:
        provider.shutdown()


def test_server_starts_with_a_private_home_and_the_hello_world_chat(
    dev_home: Path,
) -> None:
    server = build_server()

    assert server.config.port == 8766
    assert server.log_file == dev_home / "logs" / "ivlia.log"
    assert (dev_home.stat().st_mode & 0o777) == 0o700
    assert (dev_home / "memory.sqlite3").exists()
    client = TestClient(server.app, base_url="http://127.0.0.1:8766")
    response = client.post(
        "/api/chat",
        json={"message": "Hi"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert '"type":"end"' in response.text.replace(" ", "")


def test_app_factory_builds_the_same_app(dev_home: Path) -> None:
    client = TestClient(app_factory(), base_url="http://127.0.0.1:8766")

    assert client.get("/api/health").status_code == 200
    assert dev_home.exists()
