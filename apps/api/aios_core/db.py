from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import DB_PATH


# ============================================================================
# Database schema
# ============================================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    state_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_status
ON tasks(status);

CREATE INDEX IF NOT EXISTS idx_tasks_updated_at
ON tasks(updated_at);


CREATE TABLE IF NOT EXISTS task_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY(task_id)
        REFERENCES tasks(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_snapshots_task_id
ON task_snapshots(task_id);


CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    importance INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_memories_category
ON memories(category);

CREATE INDEX IF NOT EXISTS idx_memories_importance
ON memories(importance);

CREATE INDEX IF NOT EXISTS idx_memories_created_at
ON memories(created_at);


CREATE TABLE IF NOT EXISTS semantic_memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    embedding_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_semantic_memories_category
ON semantic_memories(category);

CREATE INDEX IF NOT EXISTS idx_semantic_memories_updated_at
ON semantic_memories(updated_at);


CREATE TABLE IF NOT EXISTS working_memories (
    task_id TEXT PRIMARY KEY,
    data_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TEXT,
    source TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_event_time
ON events(event_time);

CREATE INDEX IF NOT EXISTS idx_events_event_type
ON events(event_type);


CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    due_at TEXT NOT NULL,
    status TEXT NOT NULL,
    event_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT,

    FOREIGN KEY(event_id)
        REFERENCES events(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_reminders_due_at
ON reminders(due_at);

CREATE INDEX IF NOT EXISTS idx_reminders_status
ON reminders(status);


CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    action_type TEXT NOT NULL,
    input_json TEXT NOT NULL DEFAULT '{}',
    output_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,
    reversible INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,

    FOREIGN KEY(task_id)
        REFERENCES tasks(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_actions_task_id
ON actions(task_id);

CREATE INDEX IF NOT EXISTS idx_actions_status
ON actions(status);


CREATE TABLE IF NOT EXISTS environments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    environment_type TEXT NOT NULL,
    status TEXT NOT NULL,
    config_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_environments_type
ON environments(environment_type);

CREATE INDEX IF NOT EXISTS idx_environments_status
ON environments(status);


CREATE TABLE IF NOT EXISTS environment_states (
    environment_id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY(environment_id)
        REFERENCES environments(id)
        ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS environment_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY(environment_id)
        REFERENCES environments(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_environment_snapshots_environment_id
ON environment_snapshots(environment_id);


CREATE TABLE IF NOT EXISTS rollback_snapshots (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    parent_id TEXT,
    snapshot_type TEXT NOT NULL,
    state_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,

    FOREIGN KEY(task_id)
        REFERENCES tasks(id)
        ON DELETE SET NULL,

    FOREIGN KEY(parent_id)
        REFERENCES rollback_snapshots(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_rollback_snapshots_task_id
ON rollback_snapshots(task_id);

CREATE INDEX IF NOT EXISTS idx_rollback_snapshots_parent_id
ON rollback_snapshots(parent_id);

CREATE INDEX IF NOT EXISTS idx_rollback_snapshots_created_at
ON rollback_snapshots(created_at);


CREATE TABLE IF NOT EXISTS connectors (
    name TEXT PRIMARY KEY,
    connector_type TEXT NOT NULL,
    status TEXT NOT NULL,
    config_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_contacts_name
ON contacts(name);

CREATE INDEX IF NOT EXISTS idx_contacts_email
ON contacts(email);


CREATE TABLE IF NOT EXISTS api_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_sessions_user_id
ON api_sessions(user_id);


CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    actor TEXT,
    resource_type TEXT,
    resource_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_action
ON audit_log(action);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
ON audit_log(created_at);
"""


# ============================================================================
# Connection handling
# ============================================================================

def _ensure_database_directory() -> None:
    """
    Make sure the SQLite database parent directory exists.
    """

    path = Path(DB_PATH)

    if path.parent:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


@contextmanager
def conn() -> Iterator[sqlite3.Connection]:
    """
    Open a SQLite connection with AIOS-safe defaults.

    Each call gets its own connection. This works well with FastAPI's
    synchronous route handlers and the application's small local database.
    """

    _ensure_database_directory()

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30.0,
    )

    connection.row_factory = sqlite3.Row

    # Foreign keys are disabled by default in SQLite.
    connection.execute("PRAGMA foreign_keys = ON")

    # WAL allows readers and writers to coexist more safely.
    connection.execute("PRAGMA journal_mode = WAL")

    # Avoid waiting indefinitely for a locked database.
    connection.execute("PRAGMA busy_timeout = 30000")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# ============================================================================
# Time helpers
# ============================================================================

def now() -> str:
    """
    Return the current UTC timestamp as an ISO-8601 string.
    """

    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# Database initialization
# ============================================================================

def init_db() -> None:
    """
    Initialize all AIOS database tables and indexes.

    This function is intentionally idempotent and can safely be called
    every time the API starts.
    """

    _ensure_database_directory()

    with conn() as connection:
        connection.executescript(SCHEMA)

        # --------------------------------------------------------------------
        # Lightweight compatibility migrations
        # --------------------------------------------------------------------
        _ensure_column(
            connection,
            "memories",
            "metadata_json",
            "TEXT NOT NULL DEFAULT '{}'",
        )

        _ensure_column(
            connection,
            "reminders",
            "updated_at",
            "TEXT",
        )

        # --------------------------------------------------------------------
        # Default development contact
        # --------------------------------------------------------------------
        count = connection.execute(
            "SELECT COUNT(*) FROM contacts"
        ).fetchone()[0]

        if count == 0:
            connection.execute(
                """
                INSERT INTO contacts(
                    name,
                    email,
                    phone,
                    metadata_json
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Rahul",
                    "",
                    "",
                    "{}",
                ),
            )


def _ensure_column(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    """
    Add a missing column to an existing SQLite table.

    SQLite does not support CREATE TABLE IF NOT EXISTS for altering an
    existing table, so this small migration helper keeps older AIOS databases
    compatible with newer schema versions.
    """

    columns = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    existing = {
        str(column_info["name"])
        for column_info in columns
    }

    if column not in existing:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


# ============================================================================
# Query helpers
# ============================================================================

def rows(
    sql: str,
    args: tuple[Any, ...] | list[Any] = (),
) -> list[dict[str, Any]]:
    """
    Execute a SELECT query and return all rows as dictionaries.
    """

    with conn() as connection:
        result = connection.execute(
            sql,
            tuple(args),
        ).fetchall()

        return [
            dict(result_row)
            for result_row in result
        ]


def row(
    sql: str,
    args: tuple[Any, ...] | list[Any] = (),
) -> dict[str, Any] | None:
    """
    Execute a SELECT query and return one row as a dictionary.
    """

    with conn() as connection:
        result_row = connection.execute(
            sql,
            tuple(args),
        ).fetchone()

        return (
            dict(result_row)
            if result_row is not None
            else None
        )


def execute(
    sql: str,
    args: tuple[Any, ...] | list[Any] = (),
) -> int:
    """
    Execute an INSERT/UPDATE/DELETE statement.

    Returns the SQLite lastrowid.
    """

    with conn() as connection:
        cursor = connection.execute(
            sql,
            tuple(args),
        )

        return int(cursor.lastrowid)


def execute_many(
    sql: str,
    values: list[tuple[Any, ...]],
) -> None:
    """
    Execute the same SQL statement for multiple rows.
    """

    if not values:
        return

    with conn() as connection:
        connection.executemany(
            sql,
            values,
        )


def execute_script(
    script: str,
) -> None:
    """
    Execute a raw SQLite script.

    Intended for controlled internal schema/migration operations.
    """

    with conn() as connection:
        connection.executescript(script)


# ============================================================================
# JSON helpers
# ============================================================================

def json_dumps(
    value: Any,
) -> str:
    """
    Serialize a Python value for SQLite storage.

    Uses a compact representation and supports common AIOS objects.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
        separators=(",", ":"),
    )


def json_load(
    value: Any,
    default: Any = None,
) -> Any:
    """
    Safely deserialize JSON stored in SQLite.

    Invalid JSON never crashes the caller; the supplied default is returned.
    """

    if value is None:
        return default

    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


# ============================================================================
# Transaction helper
# ============================================================================

@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """
    Explicit transaction context.

    Useful when multiple database operations must succeed or fail together.
    """

    _ensure_database_directory()

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30.0,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# ============================================================================
# Database information
# ============================================================================

def database_info() -> dict[str, Any]:
    """
    Return non-sensitive database information.
    """

    with conn() as connection:
        tables = [
            item["name"]
            for item in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        ]

        return {
            "path": str(DB_PATH),
            "tables": tables,
            "table_count": len(tables),
        }


def table_exists(
    table_name: str,
) -> bool:
    """
    Check whether a database table exists.
    """

    with conn() as connection:
        result = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
            AND name = ?
            LIMIT 1
            """,
            (table_name,),
        ).fetchone()

        return result is not None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SCHEMA",
    "conn",
    "transaction",
    "now",
    "init_db",
    "rows",
    "row",
    "execute",
    "execute_many",
    "execute_script",
    "json_dumps",
    "json_load",
    "database_info",
    "table_exists",
]