-- Identity of this installation: one row, written at first start.
CREATE TABLE installation (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    created_by_version TEXT NOT NULL
) STRICT;
