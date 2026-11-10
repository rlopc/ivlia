from typing import TYPE_CHECKING

import pytest
from api_client import make_client

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi.testclient import TestClient

INDEX = "<!doctype html><title>ivlia</title>"


@pytest.fixture
def spa(tmp_path: Path) -> TestClient:
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text(INDEX)
    (static / "favicon.svg").write_text("<svg/>")
    (static / "assets" / "index-abc.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("secret")
    return make_client(spa_dir=static)


@pytest.mark.parametrize("path", ["/", "/chat", "/some/deep/route"])
def test_spa_routes_get_the_index(spa: TestClient, path: str) -> None:
    response = spa.get(path)
    assert response.status_code == 200
    assert response.text == INDEX


def test_the_spa_page_forbids_other_origins(spa: TestClient) -> None:
    policy = spa.get("/").headers["content-security-policy"]
    assert "default-src 'self'" in policy
    assert "connect-src 'self'" in policy
    assert "frame-ancestors 'none'" in policy


def test_spa_files_are_served(spa: TestClient) -> None:
    assert spa.get("/assets/index-abc.js").text == "console.log(1)"
    assert spa.get("/favicon.svg").text == "<svg/>"


@pytest.mark.parametrize(
    "path",
    [
        "/..%2Fsecret.txt",
        "/assets/..%2F..%2Fsecret.txt",
        "/assets/%2E%2E/%2E%2E/secret.txt",
    ],
)
def test_no_path_reaches_files_outside_the_spa(spa: TestClient, path: str) -> None:
    assert "secret" not in spa.get(path).text


@pytest.mark.parametrize("path", ["/api", "/api/unknown"])
def test_unknown_api_paths_are_not_found(spa: TestClient, path: str) -> None:
    assert spa.get(path).status_code == 404


def test_the_api_still_works_with_the_spa(spa: TestClient) -> None:
    assert spa.get("/api/health").json() == {"status": "ok"}


def test_without_a_built_spa_only_the_api_answers() -> None:
    client = make_client()
    assert client.get("/").status_code == 404
    assert client.get("/api/health").status_code == 200
