import json
from typing import TYPE_CHECKING

import pytest
from api_client import AUTH, TOKEN, make_client

from ivlia.adapters.hello_world_llm import REPLY_CHUNKS
from ivlia.config.installation import Environment

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

VITE = "http://localhost:5173"


def _sse_data(body: str) -> list[dict[str, object]]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


def test_health_needs_no_token(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_streams_the_reply_and_ends(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": "Hi"}, headers=AUTH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    tokens = [{"type": "token", "text": chunk} for chunk in REPLY_CHUNKS]
    assert _sse_data(response.text) == [*tokens, {"type": "end"}]


def test_empty_message_is_rejected(client: TestClient) -> None:
    assert (
        client.post("/api/chat", json={"message": ""}, headers=AUTH).status_code == 422
    )


@pytest.mark.parametrize(
    "headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": TOKEN}]
)
def test_chat_without_a_valid_token_gets_401(
    client: TestClient, headers: dict[str, str]
) -> None:
    response = client.post("/api/chat", json={"message": "Hi"}, headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("host", ["evil.example:8765", "127.0.0.1:9999", "localhost"])
def test_foreign_host_gets_403(client: TestClient, host: str) -> None:
    assert client.get("/api/health", headers={"Host": host}).status_code == 403


def test_localhost_host_is_allowed(client: TestClient) -> None:
    assert (
        client.get("/api/health", headers={"Host": "localhost:8765"}).status_code == 200
    )


@pytest.mark.parametrize(
    "origin", ["http://evil.example", "http://localhost:9999", VITE, "null"]
)
def test_foreign_origin_gets_403_before_auth(client: TestClient, origin: str) -> None:
    response = client.post(
        "/api/chat", json={"message": "Hi"}, headers={"Origin": origin}
    )

    assert response.status_code == 403


@pytest.mark.parametrize("origin", ["http://127.0.0.1:8765", "http://localhost:8765"])
def test_own_origin_is_allowed(client: TestClient, origin: str) -> None:
    assert client.get("/api/health", headers={"Origin": origin}).status_code == 200


def test_vite_origin_is_allowed_only_in_dev() -> None:
    response = make_client(Environment.DEV).get("/api/health", headers={"Origin": VITE})

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("env", "docs_status"), [(Environment.USE, 404), (Environment.DEV, 200)]
)
def test_swagger_ui_only_in_dev(env: Environment, docs_status: int) -> None:
    client = make_client(env)

    assert client.get("/docs").status_code == docs_status
    assert client.get("/openapi.json").status_code == 200


def test_lifespan_passes_through_the_guards() -> None:
    with make_client() as client:
        assert client.get("/api/health").status_code == 200
