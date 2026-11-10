"""Secret lookup: environment, then the system keyring, then a private file.

Secrets never go into the settings file or the repository. Values are
`SecretStr`, so they do not show up in reprs or logs by accident.
"""

import json
import logging
import os
import secrets
import stat
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import keyring
from keyring.errors import KeyringError
from pydantic import SecretStr

from ivlia.config.errors import ConfigError
from ivlia.config.installation import Environment, Installation

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

logger = logging.getLogger(__name__)

API_TOKEN = "api_token"  # noqa: S105 (the name of a secret, not its value)


class Keyring(Protocol):
    """The part of a `keyring` backend that ivlia uses."""

    def get_password(self, service: str, username: str) -> str | None: ...

    def set_password(self, service: str, username: str, password: str) -> None: ...


class SecretStore:
    def __init__(
        self,
        home: Path,
        keyring_service: str,
        keyring_backend: Keyring | None,
        environ: Mapping[str, str] = os.environ,
    ) -> None:
        self._file = home / "secrets.json"
        self._service = keyring_service
        self._keyring = keyring_backend
        self._environ = environ

    def get(self, name: str) -> SecretStr | None:
        value = self._environ.get(f"IVLIA_{name.upper()}")
        if value is None:
            value = self._from_keyring(name)
        if value is None:
            value = self._read_file().get(name)
        return None if value is None else SecretStr(value)

    def get_or_create(self, name: str, generate: Callable[[], str]) -> SecretStr:
        """Return the secret, generating and storing it on first use."""
        existing = self.get(name)
        if existing is not None:
            return existing
        value = generate()
        if not self._to_keyring(name, value):
            self._write_file({**self._read_file(), name: value})
        return SecretStr(value)

    def _from_keyring(self, name: str) -> str | None:
        if self._keyring is None:
            return None
        try:
            return self._keyring.get_password(self._service, name)
        except KeyringError:
            logger.warning("Keyring unavailable; using the secrets file", exc_info=True)
            return None

    def _to_keyring(self, name: str, value: str) -> bool:
        if self._keyring is None:
            return False
        try:
            self._keyring.set_password(self._service, name, value)
        except KeyringError:
            logger.warning("Keyring unavailable; using the secrets file", exc_info=True)
            return False
        return True

    def _read_file(self) -> dict[str, str]:
        if not self._file.exists():
            return {}
        mode = stat.S_IMODE(self._file.stat().st_mode)
        if mode & 0o077:
            msg = (
                f"{self._file} has mode {mode:04o}, so other users can read it. "
                f"Run `chmod 600 '{self._file}'`."
            )
            raise ConfigError(msg)
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            # The position only: the decoder message never quotes the content.
            msg = f"{self._file} is not valid JSON: {error}"
            raise ConfigError(msg) from None
        if not isinstance(data, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in data.items()
        ):
            msg = f"{self._file} must be a JSON object of strings."
            raise ConfigError(msg)
        return data

    def _write_file(self, data: dict[str, str]) -> None:
        # Write a temporary file in the same folder, then rename it, so a crash
        # never leaves a half-written file. mkstemp creates it with mode 0600.
        self._file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self._file.parent, prefix=".secrets-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f)
            Path(tmp).replace(self._file)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise


def secret_store(installation: Installation, keyring_service: str) -> SecretStore:
    """The store for this installation. The dev installation never uses keyring."""
    backend = None if installation.env is Environment.DEV else keyring.get_keyring()
    return SecretStore(installation.home, keyring_service, backend)


def api_token(store: SecretStore) -> SecretStr:
    return store.get_or_create(API_TOKEN, lambda: secrets.token_urlsafe(32))
