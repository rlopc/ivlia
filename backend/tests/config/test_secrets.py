import json
import stat
from typing import TYPE_CHECKING

import pytest
from keyring.errors import NoKeyringError

from ivlia.config.errors import ConfigError
from ivlia.config.installation import Environment, Installation
from ivlia.config.secrets import API_TOKEN, SecretStore, api_token, secret_store

if TYPE_CHECKING:
    from pathlib import Path

SERVICE = "ivlia-test"


class _MemoryKeyring:
    def __init__(self) -> None:
        self.passwords: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.passwords[service, username] = password


class _BrokenKeyring:
    def get_password(self, service: str, username: str) -> str | None:  # noqa: ARG002
        raise NoKeyringError

    def set_password(self, service: str, username: str, password: str) -> None:  # noqa: ARG002
        raise NoKeyringError


def _secrets_file(home: Path) -> Path:
    return home / "secrets.json"


def test_environment_wins_over_keyring_and_file(tmp_path: Path) -> None:
    backend = _MemoryKeyring()
    backend.set_password(SERVICE, API_TOKEN, "from-keyring")
    store = SecretStore(
        tmp_path, SERVICE, backend, environ={"IVLIA_API_TOKEN": "from-env"}
    )

    token = store.get(API_TOKEN)

    assert token is not None
    assert token.get_secret_value() == "from-env"


def test_keyring_wins_over_file(tmp_path: Path) -> None:
    SecretStore(tmp_path, SERVICE, None, environ={}).get_or_create(
        API_TOKEN, lambda: "from-file"
    )
    backend = _MemoryKeyring()
    backend.set_password(SERVICE, API_TOKEN, "from-keyring")

    token = SecretStore(tmp_path, SERVICE, backend, environ={}).get(API_TOKEN)

    assert token is not None
    assert token.get_secret_value() == "from-keyring"


def test_generated_secret_goes_to_keyring_and_is_reused(tmp_path: Path) -> None:
    backend = _MemoryKeyring()
    store = SecretStore(tmp_path, SERVICE, backend, environ={})

    first = api_token(store)
    second = api_token(store)

    assert first.get_secret_value() == second.get_secret_value()
    assert backend.passwords[SERVICE, API_TOKEN] == first.get_secret_value()
    assert not _secrets_file(tmp_path).exists()


def test_broken_keyring_falls_back_to_a_private_file(tmp_path: Path) -> None:
    store = SecretStore(tmp_path / "home", SERVICE, _BrokenKeyring(), environ={})

    token = api_token(store)

    secrets_file = _secrets_file(tmp_path / "home")
    assert json.loads(secrets_file.read_text()) == {API_TOKEN: token.get_secret_value()}
    assert stat.S_IMODE(secrets_file.stat().st_mode) == 0o600
    assert api_token(store).get_secret_value() == token.get_secret_value()


def test_readable_secrets_file_stops_the_start(tmp_path: Path) -> None:
    secrets_file = _secrets_file(tmp_path)
    secrets_file.write_text("{}")
    secrets_file.chmod(0o644)

    with pytest.raises(ConfigError, match="has mode 0644"):
        SecretStore(tmp_path, SERVICE, None, environ={}).get(API_TOKEN)


def test_malformed_secrets_file_is_rejected(tmp_path: Path) -> None:
    secrets_file = _secrets_file(tmp_path)
    secrets_file.write_text('{"api_token": 1}')
    secrets_file.chmod(0o600)

    with pytest.raises(ConfigError, match="JSON object of strings"):
        SecretStore(tmp_path, SERVICE, None, environ={}).get(API_TOKEN)


def test_secret_value_is_hidden_in_repr(tmp_path: Path) -> None:
    token = api_token(SecretStore(tmp_path, SERVICE, None, environ={}))

    assert token.get_secret_value() not in repr(token)


@pytest.fixture
def system_keyring(monkeypatch: pytest.MonkeyPatch) -> _MemoryKeyring:
    backend = _MemoryKeyring()
    monkeypatch.setattr("ivlia.config.secrets.keyring.get_keyring", lambda: backend)
    return backend


def test_dev_installation_never_uses_keyring(
    tmp_path: Path, system_keyring: _MemoryKeyring
) -> None:
    store = secret_store(Installation(env=Environment.DEV, home=tmp_path), SERVICE)

    api_token(store)

    assert system_keyring.passwords == {}
    assert _secrets_file(tmp_path).exists()


def test_use_installation_stores_in_keyring(
    tmp_path: Path, system_keyring: _MemoryKeyring
) -> None:
    store = secret_store(Installation(env=Environment.USE, home=tmp_path), SERVICE)

    token = api_token(store)

    assert system_keyring.passwords == {(SERVICE, API_TOKEN): token.get_secret_value()}
    assert not _secrets_file(tmp_path).exists()


def test_failed_write_leaves_no_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_dump(*_args: object, **_kwargs: object) -> None:
        raise OSError

    monkeypatch.setattr("ivlia.config.secrets.json.dump", broken_dump)
    store = SecretStore(tmp_path, SERVICE, None, environ={})

    with pytest.raises(OSError):  # noqa: PT011 (any write error)
        api_token(store)

    assert list(tmp_path.iterdir()) == []
