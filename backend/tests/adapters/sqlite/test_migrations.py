import sqlite3
from typing import TYPE_CHECKING

import pytest

from ivlia.adapters.sqlite.memory import FILE_NAME, open_memory_db
from ivlia.adapters.sqlite.migrations import (
    Migration,
    MigrationError,
    load_migrations,
    memory_migrations,
    migrate,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

CREATE_A = Migration(1, "0001_a.sql", "CREATE TABLE a (x INTEGER);")
CREATE_B = Migration(2, "0002_b.sql", "CREATE TABLE b (x INTEGER);")
BROKEN = Migration(2, "0002_broken.sql", "CREATE TABLE c (x INTEGER); NOT VALID SQL;")


@pytest.fixture
def db(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(tmp_path / "test.sqlite3", autocommit=False)
    yield connection
    connection.close()


def _version(db: sqlite3.Connection) -> int:
    version: int = db.execute("PRAGMA user_version").fetchone()[0]
    return version


def _tables(db: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }


def test_new_database_gets_every_migration(db: sqlite3.Connection) -> None:
    migrate(db, [CREATE_A, CREATE_B], "test")

    assert _version(db) == 2
    assert _tables(db) == {"a", "b"}


def test_up_to_date_database_is_left_alone(db: sqlite3.Connection) -> None:
    migrate(db, [CREATE_A], "test")

    migrate(db, [CREATE_A], "test")

    assert _version(db) == 1


def test_failing_migration_rolls_back_and_names_the_file(
    db: sqlite3.Connection,
) -> None:
    with pytest.raises(
        MigrationError, match=r"0002_broken\.sql of the test database failed"
    ):
        migrate(db, [CREATE_A, BROKEN], "test")

    assert _version(db) == 1
    assert _tables(db) == {"a"}


def test_existing_database_with_pending_migrations_does_not_start(
    db: sqlite3.Connection,
) -> None:
    migrate(db, [CREATE_A], "test")

    with pytest.raises(MigrationError, match=r"1 pending migration.*no backup"):
        migrate(db, [CREATE_A, CREATE_B], "test")

    assert _version(db) == 1


def test_database_newer_than_ivlia_does_not_start(db: sqlite3.Connection) -> None:
    migrate(db, [CREATE_A, CREATE_B], "test")

    with pytest.raises(MigrationError, match="newer than this version"):
        migrate(db, [CREATE_A], "test")


def test_migration_files_must_have_no_gaps(tmp_path: Path) -> None:
    (tmp_path / "0001_a.sql").write_text("SELECT 1;")
    (tmp_path / "0003_c.sql").write_text("SELECT 1;")

    with pytest.raises(MigrationError, match="no gaps"):
        load_migrations(tmp_path)


def test_memory_migrations_are_packaged() -> None:
    assert [m.name for m in memory_migrations()] == ["0001_installation.sql"]


def test_memory_db_records_the_installation_once(tmp_path: Path) -> None:
    open_memory_db(tmp_path, "0.0.0").close()
    db = open_memory_db(tmp_path, "9.9.9")
    rows = db.execute("SELECT created_by_version FROM installation").fetchall()
    db.close()

    assert rows == [("0.0.0",)]
    assert (tmp_path / FILE_NAME).exists()


def test_memory_db_refuses_a_newer_database(tmp_path: Path) -> None:
    newer = sqlite3.connect(tmp_path / FILE_NAME)
    newer.execute("PRAGMA user_version = 99")
    newer.close()

    with pytest.raises(MigrationError, match="newer than this version"):
        open_memory_db(tmp_path, "0.0.0")
