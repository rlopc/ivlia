"""User settings: defaults in code, then the TOML file, then the environment."""

import tomllib
from dataclasses import dataclass

from pydantic import ValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from ivlia.config.errors import ConfigError
from ivlia.config.installation import Environment, Installation

DEFAULT_PORTS = {Environment.USE: 8765, Environment.DEV: 8766}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IVLIA_", extra="forbid")

    port: int | None = None
    """API port. Unset means the default port of the installation."""
    dev_origin: str = "http://localhost:5173"
    """Origin of the Vite dev server, allowed only in the dev installation."""
    keyring_service: str = "ivlia"
    """Service name for this installation's secrets in the system keyring."""
    log_content: bool = False
    """Local debug mode: write message content to the log file."""
    trace_console: bool = False
    """Also print traces to the console."""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Earlier sources win: environment over the TOML file over defaults.
        return init_settings, env_settings, TomlConfigSettingsSource(settings_cls)


@dataclass(frozen=True, slots=True)
class Config:
    installation: Installation
    settings: Settings

    @property
    def port(self) -> int:
        return self.settings.port or DEFAULT_PORTS[self.installation.env]

    @property
    def web_origin(self) -> str:
        """Where the browser opens the web: Vite in dev, else the API itself.

        The session cookie belongs to this origin, so one-time links point here.
        """
        if self.installation.env is Environment.DEV:
            return self.settings.dev_origin
        return f"http://127.0.0.1:{self.port}"


def load_config(installation: Installation) -> Config:
    """Load and validate the settings, or raise `ConfigError` naming what fails."""
    toml_file = installation.settings_file

    # pydantic-settings reads the TOML path only from model_config.
    class _InstallationSettings(Settings):
        model_config = SettingsConfigDict(toml_file=toml_file)

    try:
        settings: Settings = _InstallationSettings()
    except tomllib.TOMLDecodeError as error:
        msg = f"{toml_file} is not valid TOML: {error}"
        raise ConfigError(msg) from None
    except ValidationError as error:
        raise ConfigError(_describe(error, toml_file.as_posix())) from None
    return Config(installation=installation, settings=settings)


def _describe(error: ValidationError, source: str) -> str:
    problems = [
        f"- {'.'.join(str(part) for part in e['loc'])}: {e['msg']} (got {e['input']!r})"
        for e in error.errors()
    ]
    return f"Invalid settings (from {source} or IVLIA_* variables):\n" + "\n".join(
        problems
    )
