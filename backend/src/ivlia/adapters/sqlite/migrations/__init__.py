"""Forward-only schema migrations for ivlia's SQLite databases.

Each database has a folder of numbered SQL files, `NNNN_description.sql`,
starting at 0001 with no gaps. `PRAGMA user_version` holds the number of the
last migration applied. Each migration runs in its own transaction, together
with the `user_version` update, so a failure leaves the database as it was.
"""

import re
import sqlite3
from dataclasses import dataclass
from importlib.resources import files
from typing import TYPE_CHECKING

from ivlia.config.errors import StartupError

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

_FILE_NAME = re.compile(r"(\d{4})_[a-z0-9_]+\.sql")


class MigrationError(StartupError):
    """The database cannot be brought up to date, so ivlia must not start."""


@dataclass(frozen=True, slots=True)
class Migration:
    number: int
    name: str
    sql: str


def load_migrations(folder: Traversable) -> list[Migration]:
    migrations = []
    for entry in folder.iterdir():
        match = _FILE_NAME.fullmatch(entry.name)
        if match:
            migrations.append(
                Migration(int(match[1]), entry.name, entry.read_text("utf-8"))
            )
    migrations.sort(key=lambda m: m.number)
    numbers = [m.number for m in migrations]
    if numbers != list(range(1, len(numbers) + 1)):
        msg = (
            f"Migrations in {folder} must be numbered from 0001 with no gaps: {numbers}"
        )
        raise MigrationError(msg)
    return migrations


def memory_migrations() -> list[Migration]:
    return load_migrations(files(__package__).joinpath("memory"))


def migrate(
    connection: sqlite3.Connection, migrations: list[Migration], label: str
) -> None:
    """Apply the pending migrations. The connection must use `autocommit=False`.

    A new database (`user_version` 0) gets every migration. An existing one
    with pending migrations is refused for now: migrating it needs a backup
    first, and backups arrive in slice 2.
    """
    current: int = connection.execute("PRAGMA user_version").fetchone()[0]
    latest = len(migrations)
    if current > latest:
        msg = (
            f"The {label} database is at migration {current}, newer than this "
            f"version of ivlia knows ({latest}). Install a newer ivlia."
        )
        raise MigrationError(msg)
    pending = migrations[current:]
    if current > 0 and pending:
        msg = (
            f"The {label} database has {len(pending)} pending migration(s) and no "
            "backup is available, so ivlia does not start. Migrating needs a backup first."
        )
        raise MigrationError(msg)
    for migration in pending:
        try:
            connection.executescript(migration.sql)
            connection.execute(f"PRAGMA user_version = {migration.number}")
            connection.commit()
        except sqlite3.Error as error:
            connection.rollback()
            msg = f"Migration {migration.name} of the {label} database failed: {error}"
            raise MigrationError(msg) from error
