from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from ivlia import server
from ivlia.bootstrap import Server
from ivlia.config.errors import ConfigError
from ivlia.config.installation import Environment, Installation
from ivlia.config.settings import Config, Settings


def _server(env: Environment) -> Server:
    config = Config(
        installation=Installation(env=env, home=Path("/nonexistent")),
        settings=Settings.model_construct(),
    )
    return Server(app=FastAPI(), config=config, log_file=Path("/nonexistent/log"))


@pytest.fixture
def runs(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        "ivlia.server.uvicorn.run",
        lambda target, **kwargs: calls.append({"target": target, **kwargs}),
    )
    return calls


def _build(monkeypatch: pytest.MonkeyPatch, env: Environment) -> Server:
    built = _server(env)
    monkeypatch.setattr(server, "build_server", lambda: built)
    return built


def test_serves_only_on_localhost_without_access_log(
    monkeypatch: pytest.MonkeyPatch, runs: list[dict[str, Any]]
) -> None:
    built = _build(monkeypatch, Environment.USE)

    assert server.main([]) == 0

    [run] = runs
    assert run["target"] is built.app
    assert run["host"] == "127.0.0.1"
    assert run["port"] == 8765
    assert run["access_log"] is False
    assert run["log_config"] is None
    assert run["reload"] is False


def test_reload_uses_the_factory_in_dev(
    monkeypatch: pytest.MonkeyPatch, runs: list[dict[str, Any]], tmp_path: Path
) -> None:
    monkeypatch.setenv("IVLIA_ENV", "dev")
    monkeypatch.setenv("IVLIA_HOME", str(tmp_path))
    _build(monkeypatch, Environment.DEV)

    assert server.main(["--reload"]) == 0

    [run] = runs
    assert run["target"] == "ivlia.bootstrap:app_factory"
    assert run["factory"] is True
    assert run["port"] == 8766


def test_reload_is_refused_outside_dev_before_building(
    monkeypatch: pytest.MonkeyPatch,
    runs: list[dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("IVLIA_HOME", str(tmp_path))
    built: list[bool] = []
    monkeypatch.setattr(server, "build_server", lambda: built.append(True))

    assert server.main(["--reload"]) == 2
    assert runs == []
    assert built == []
    assert "only for the dev installation" in capsys.readouterr().err


def test_startup_error_is_shown_and_does_not_start(
    monkeypatch: pytest.MonkeyPatch,
    runs: list[dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail() -> Server:
        msg = "port: bad value"
        raise ConfigError(msg)

    monkeypatch.setattr(server, "build_server", fail)

    assert server.main([]) == 1
    assert runs == []
    assert capsys.readouterr().err == "ivlia-server: port: bad value\n"
