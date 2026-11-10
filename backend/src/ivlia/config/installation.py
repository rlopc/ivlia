"""Installation identity: which installation this is and where its data lives.

It comes only from the environment, because the settings file lives inside
the installation folder.
"""

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

from ivlia.config.errors import ConfigError

if TYPE_CHECKING:
    from collections.abc import Mapping

DEFAULT_HOME = Path.home() / "Library" / "Application Support" / "ivlia"


class Environment(StrEnum):
    USE = "use"
    DEV = "dev"


@dataclass(frozen=True, slots=True)
class Installation:
    env: Environment
    home: Path

    @property
    def settings_file(self) -> Path:
        return self.home / "config.toml"


def resolve_installation(
    environ: Mapping[str, str] = os.environ,
    direct_url: str | None = None,
) -> Installation:
    """Read the installation from `IVLIA_ENV` and `IVLIA_HOME`.

    `direct_url` is this package's PEP 610 `direct_url.json`; by default it is
    read from the installed distribution.
    """
    raw_env = environ.get("IVLIA_ENV", Environment.USE)
    try:
        env = Environment(raw_env)
    except ValueError:
        allowed = ", ".join(e.value for e in Environment)
        msg = f"IVLIA_ENV is {raw_env!r}; it must be one of: {allowed}."
        raise ConfigError(msg) from None

    raw_home = environ.get("IVLIA_HOME")
    # Only releases are the use installation: a run from a source folder must
    # never reach the real data or the system keyring.
    if (env is not Environment.DEV or raw_home is None) and _installed_from_folder(
        direct_url
    ):
        msg = (
            "ivlia runs from a source folder, so it must use the dev installation: "
            "set IVLIA_ENV=dev and IVLIA_HOME. `just` and mise set both."
        )
        raise ConfigError(msg)
    if raw_home is None:
        return Installation(env=env, home=DEFAULT_HOME)

    home = Path(raw_home)
    if not home.is_absolute():
        msg = f"IVLIA_HOME is {raw_home!r}; it must be an absolute path."
        raise ConfigError(msg)
    return Installation(env=env, home=home)


def _installed_from_folder(direct_url: str | None) -> bool:
    """Whether PEP 610 says ivlia was installed from a local folder.

    An editable install from the repository has `dir_info`; a release
    installed from a wheel has `archive_info`.
    """
    if direct_url is None:
        try:
            direct_url = metadata.distribution("ivlia").read_text("direct_url.json")
        except metadata.PackageNotFoundError:
            return False
    if direct_url is None:
        return False
    return "dir_info" in json.loads(direct_url)
