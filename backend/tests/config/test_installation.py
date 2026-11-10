import json
from importlib import metadata
from typing import TYPE_CHECKING

import pytest

from ivlia.config.errors import ConfigError
from ivlia.config.installation import (
    DEFAULT_HOME,
    Environment,
    Installation,
    resolve_installation,
)

if TYPE_CHECKING:
    from pathlib import Path

FROM_REPO = json.dumps({"url": "file:///repo/backend", "dir_info": {"editable": True}})
FROM_WHEEL = json.dumps({"url": "file:///tmp/ivlia.whl", "archive_info": {}})


def test_dev_installation_from_the_environment(tmp_path: Path) -> None:
    environ = {"IVLIA_ENV": "dev", "IVLIA_HOME": str(tmp_path)}

    assert resolve_installation(environ, FROM_REPO) == Installation(
        env=Environment.DEV, home=tmp_path
    )


def test_release_install_uses_the_default_home() -> None:
    assert resolve_installation({}, FROM_WHEEL) == Installation(
        env=Environment.USE, home=DEFAULT_HOME
    )


def test_run_from_the_repo_without_home_does_not_start() -> None:
    with pytest.raises(ConfigError, match="IVLIA_HOME is not set"):
        resolve_installation({}, FROM_REPO)


def test_reads_pep_610_metadata_of_this_install() -> None:
    # The test suite runs from the editable install of backend/.
    with pytest.raises(ConfigError, match="IVLIA_HOME is not set"):
        resolve_installation({})


def test_unknown_environment_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="IVLIA_ENV is 'prod'"):
        resolve_installation({"IVLIA_ENV": "prod", "IVLIA_HOME": str(tmp_path)})


def test_relative_home_is_rejected() -> None:
    with pytest.raises(ConfigError, match="must be an absolute path"):
        resolve_installation({"IVLIA_HOME": ".dev"}, FROM_REPO)


class _Distribution:
    def __init__(self, direct_url: str | None) -> None:
        self._direct_url = direct_url

    def read_text(self, filename: str) -> str | None:
        assert filename == "direct_url.json"
        return self._direct_url


def test_install_without_pep_610_metadata_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ivlia.config.installation.metadata.distribution",
        lambda _name: _Distribution(None),
    )

    assert resolve_installation({}).home == DEFAULT_HOME


def test_missing_distribution_starts(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> _Distribution:
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr("ivlia.config.installation.metadata.distribution", missing)

    assert resolve_installation({}).home == DEFAULT_HOME
