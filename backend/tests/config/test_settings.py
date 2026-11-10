from typing import TYPE_CHECKING

import pytest

from ivlia.config.errors import ConfigError
from ivlia.config.installation import Environment, Installation
from ivlia.config.settings import load_config

if TYPE_CHECKING:
    from pathlib import Path


def _installation(home: Path, env: Environment = Environment.USE) -> Installation:
    return Installation(env=env, home=home)


@pytest.mark.parametrize(
    ("env", "port"), [(Environment.USE, 8765), (Environment.DEV, 8766)]
)
def test_default_port_depends_on_the_installation(
    tmp_path: Path, env: Environment, port: int
) -> None:
    assert load_config(_installation(tmp_path, env)).port == port


def test_toml_overrides_defaults_and_environment_overrides_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "config.toml").write_text(
        'port = 9000\ndev_origin = "http://localhost:3000"\n'
    )
    monkeypatch.setenv("IVLIA_PORT", "9100")

    config = load_config(_installation(tmp_path))

    assert config.port == 9100
    assert config.settings.dev_origin == "http://localhost:3000"


def test_invalid_toml_value_names_the_setting_and_value(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text('port = "eighty"\n')

    with pytest.raises(ConfigError, match=r"- port: .*\(got 'eighty'\)"):
        load_config(_installation(tmp_path))


def test_unknown_toml_key_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text("prot = 9000\n")

    with pytest.raises(ConfigError, match="- prot: Extra inputs are not permitted"):
        load_config(_installation(tmp_path))
