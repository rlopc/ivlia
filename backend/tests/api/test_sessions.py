from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import pytest
from api_client import AUTH, make_client

from ivlia.api.sessions import (
    COOKIE_NAMES,
    LINK_LIFETIME,
    SESSION_LIFETIME,
    SessionStore,
)
from ivlia.config.installation import Environment

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

CHAT = {"message": "Hi"}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def client(clock: FakeClock) -> TestClient:
    return make_client(sessions=SessionStore(clock))


def _link_path(client: TestClient, port: int = 8765) -> str:
    response = client.post("/api/session/link", headers=AUTH)
    assert response.status_code == 200
    url = urlsplit(response.json()["url"])
    assert url.netloc == f"127.0.0.1:{port}"
    return f"{url.path}?{url.query}"


def _open_session(client: TestClient) -> None:
    response = client.get(_link_path(client))
    assert response.status_code == 303


def test_link_redirects_to_the_web_with_a_strict_http_only_cookie(
    client: TestClient,
) -> None:
    response = client.get(_link_path(client))

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE_NAMES[Environment.USE]}=")
    for attribute in ("HttpOnly", "SameSite=strict", "Path=/", "Max-Age=604800"):
        assert attribute in cookie
    assert "Secure" not in cookie


def test_valid_cookie_can_chat(client: TestClient) -> None:
    _open_session(client)

    assert client.post("/api/chat", json=CHAT).status_code == 200


def test_minting_a_link_needs_the_token(client: TestClient) -> None:
    _open_session(client)

    assert client.post("/api/session/link").status_code == 401


def test_link_works_only_once(client: TestClient) -> None:
    path = _link_path(client)
    client.get(path)

    assert client.get(path).status_code == 401


def test_link_expires_after_60_seconds(client: TestClient, clock: FakeClock) -> None:
    path = _link_path(client)
    clock.advance(LINK_LIFETIME.total_seconds())

    assert client.get(path).status_code == 401


def test_unknown_link_is_rejected(client: TestClient) -> None:
    assert client.get("/api/session", params={"code": "made-up"}).status_code == 401


def test_unknown_cookie_gets_401(client: TestClient) -> None:
    client.cookies.set(COOKIE_NAMES[Environment.USE], "made-up")

    assert client.post("/api/chat", json=CHAT).status_code == 401


def test_session_expires_after_7_days(client: TestClient, clock: FakeClock) -> None:
    _open_session(client)
    clock.advance(SESSION_LIFETIME.total_seconds() - 1)
    assert client.post("/api/chat", json=CHAT).status_code == 200

    clock.advance(1)

    assert client.post("/api/chat", json=CHAT).status_code == 401


def test_restart_ends_every_session(client: TestClient) -> None:
    _open_session(client)
    restarted = make_client()
    restarted.cookies = client.cookies

    assert restarted.post("/api/chat", json=CHAT).status_code == 401


def test_cookie_request_from_a_foreign_origin_gets_403(client: TestClient) -> None:
    _open_session(client)

    response = client.post(
        "/api/chat", json=CHAT, headers={"Origin": "http://evil.example"}
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("env", "port"), [(Environment.USE, 8765), (Environment.DEV, 8766)]
)
def test_link_points_at_the_installation_port(env: Environment, port: int) -> None:
    response = make_client(env).post("/api/session/link", headers=AUTH)

    assert urlsplit(response.json()["url"]).port == port


def test_dev_installation_uses_its_own_cookie() -> None:
    client = make_client(Environment.DEV)
    response = client.get(_link_path(client, port=8766))

    assert response.headers["set-cookie"].startswith("ivlia_session_dev=")
    assert client.post("/api/chat", json=CHAT).status_code == 200
