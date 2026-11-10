"""The memory database. In Phase 0 it holds only the installation record."""

import sqlite3
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ivlia.adapters.sqlite.migrations import memory_migrations, migrate

if TYPE_CHECKING:
    from pathlib import Path

FILE_NAME = "memory.sqlite3"


def open_memory_db(home: Path, version: str) -> sqlite3.Connection:
    """Open the database, migrate it, and record the installation on first start."""
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    connection = sqlite3.connect(home / FILE_NAME, autocommit=False)
    try:
        migrate(connection, memory_migrations(), "memory")
        if connection.execute("SELECT 1 FROM installation").fetchone() is None:
            connection.execute(
                "INSERT INTO installation VALUES (?, ?, ?)",
                (str(uuid.uuid4()), datetime.now(UTC).isoformat(), version),
            )
            connection.commit()
    except BaseException:
        connection.close()
        raise
    return connection
