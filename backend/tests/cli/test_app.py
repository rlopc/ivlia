import logging
import sys
from typing import TYPE_CHECKING

import httpx2
import pytest
from api_client import AUTH, make_client
from typer.testing import CliRunner

from ivlia.api.sessions import SessionStore
from ivlia.cli import app as cli_app
from ivlia.cli.app import build_app, connect_from_config
from ivlia.cli.client import ApiClient
from ivlia.config.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import Path

    import typer
    from fastapi.testclient import TestClient

runner = CliRunner()
SSE = {"content-type": "text/event-stream"}


class _FakeBrowser:
    def __init__(self, *, opens: bool = True) -> None:
        self.opens = opens
        self.urls: list[str] = []

    def __call__(self, url: str) -> bool:
        self.urls.append(url)
        return self.opens


def _real_api(sessions: SessionStore | None = None) -> TestClient:
    http = make_client(sessions=sessions)
    http.headers.update(AUTH)
    return http


def _cli(http: httpx2.Client, browser: _FakeBrowser | None = None) -> typer.Typer:
    return build_app(lambda: ApiClient(http), browser or _FakeBrowser())


def _streaming(body: bytes) -> httpx2.Client:
    transport = httpx2.MockTransport(
        lambda _: httpx2.Response(200, headers=SSE, content=body)
    )
    return httpx2.Client(transport=transport, base_url="http://127.0.0.1")


def _refusing() -> httpx2.Client:
    def handler(_: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("refused")

    return httpx2.Client(
        transport=httpx2.MockTransport(handler), base_url="http://127.0.0.1"
    )


def test_ask_prints_the_answer_of_the_real_app() -> None:
    result = runner.invoke(_cli(_real_api()), ["ask", "hello"])
    assert result.exit_code == 0
    assert result.stdout == "Hello, world!\n"
    assert result.stderr == ""


def test_ask_reports_an_error_event_and_fails() -> None:
    body = b'data: {"type":"token","text":"Hel"}\n\ndata: {"type":"error","message":"It broke."}\n\n'
    result = runner.invoke(_cli(_streaming(body)), ["ask", "hello"])
    assert result.exit_code == 1
    assert result.stdout == "Hel\n"
    assert result.stderr == "ivlia: It broke.\n"


def test_ask_fails_when_the_answer_ends_early() -> None:
    body = b'data: {"type":"token","text":"Hel"}\n\n'
    result = runner.invoke(_cli(_streaming(body)), ["ask", "hello"])
    assert result.exit_code == 1
    assert result.stderr == "ivlia: The answer ended before it was complete.\n"


def test_ask_fails_clearly_without_a_server() -> None:
    result = runner.invoke(_cli(_refusing()), ["ask", "hello"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Cannot reach the ivlia server" in result.stderr


def test_ask_fails_clearly_on_a_configuration_error() -> None:
    def connect() -> ApiClient:
        msg = "IVLIA_ENV is 'x'."
        raise ConfigError(msg)

    result = runner.invoke(build_app(connect, _FakeBrowser()), ["ask", "hello"])
    assert result.exit_code == 1
    assert result.stderr == "ivlia: IVLIA_ENV is 'x'.\n"


def test_web_opens_a_link_that_the_api_accepts_once() -> None:
    sessions = SessionStore()
    http = _real_api(sessions)
    browser = _FakeBrowser()
    result = runner.invoke(_cli(http, browser), ["web"])
    assert result.exit_code == 0
    assert result.stdout == ""
    [url] = browser.urls
    # The browser sends no token: only the link signs it in.
    browser_http = make_client(sessions=sessions)
    assert browser_http.get(url).status_code == 303
    assert "ivlia_session" in browser_http.cookies
    assert browser_http.get(url).status_code == 401


def test_web_prints_the_link_when_no_browser_opens() -> None:
    browser = _FakeBrowser(opens=False)
    result = runner.invoke(_cli(_real_api(), browser), ["web"])
    assert result.exit_code == 0
    assert browser.urls[0] in result.stdout
    assert "within 60 seconds" in result.stdout


def test_web_fails_clearly_without_a_server() -> None:
    browser = _FakeBrowser()
    result = runner.invoke(_cli(_refusing(), browser), ["web"])
    assert result.exit_code == 1
    assert "Cannot reach the ivlia server" in result.stderr
    assert browser.urls == []


def test_ask_rejects_an_empty_message_as_a_usage_error() -> None:
    result = runner.invoke(_cli(_refusing()), ["ask", ""])
    assert result.exit_code == 2
    assert "MESSAGE" in result.stderr
    assert result.stdout == ""


def test_no_command_shows_the_help() -> None:
    result = runner.invoke(_cli(_refusing()), [])
    assert result.exit_code == 2
    assert "ask" in result.output
    assert "web" in result.output


def _dev_installation(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    monkeypatch.setenv("IVLIA_ENV", "dev")
    monkeypatch.setenv("IVLIA_HOME", str(home))


def test_connect_from_config_uses_the_port_and_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _dev_installation(monkeypatch, tmp_path)
    monkeypatch.setenv("IVLIA_API_TOKEN", "t0ken")
    with connect_from_config() as client:
        http = client._http
        assert http.base_url == "http://127.0.0.1:8766"
        assert http.headers["Authorization"] == "Bearer t0ken"


def test_connect_from_config_needs_a_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _dev_installation(monkeypatch, tmp_path)
    with pytest.raises(ConfigError, match="no API token yet"):
        connect_from_config()


def test_cli_logs_one_line_without_traceback() -> None:
    record = logging.LogRecord(
        "ivlia", logging.WARNING, __file__, 1, "Keyring failed", None, None
    )
    try:
        raise RuntimeError("detail")  # noqa: TRY301 (to get real exception info)
    except RuntimeError:
        record.exc_info = sys.exc_info()
    formatter = cli_app._MessageOnly("ivlia: %(message)s")
    assert formatter.format(record) == "ivlia: Keyring failed"


def test_main_runs_the_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ivlia", "--help"])
    with pytest.raises(SystemExit) as exit_info:
        cli_app.main()
    assert exit_info.value.code == 0
