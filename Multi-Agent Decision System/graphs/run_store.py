"""Minimal SQLite persistence for graph runs and step-by-step events.

Keep this layer generic:
- one row per user request in `runs`
- one append-only row per action/decision/error in `run_events`

That makes it easy to add new agents later without changing the schema.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_DB_PATH = Path(__file__).with_name("runs.sqlite3")


RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    question_hash TEXT,
    user_question TEXT NOT NULL,
    status TEXT NOT NULL,
    current_node TEXT,
    current_iteration INTEGER NOT NULL DEFAULT 0,
    graph_version TEXT,
    final_output_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


RUNS_QUESTION_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_runs_question_hash
ON runs (question_hash);
"""


RUN_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS run_events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    parent_event_id TEXT,
    sequence_no INTEGER NOT NULL,
    node_name TEXT NOT NULL,
    agent_name TEXT,
    event_type TEXT NOT NULL,
    iteration INTEGER NOT NULL DEFAULT 0,
    input_json TEXT,
    output_json TEXT,
    error_json TEXT,
    status TEXT NOT NULL,
    checkpoint_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs (run_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_event_id) REFERENCES run_events (event_id)
);
"""


RUN_EVENTS_SEQUENCE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_run_events_run_sequence
ON run_events (run_id, sequence_no);
"""


RUN_EVENTS_PARENT_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_run_events_parent
ON run_events (parent_event_id);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_question_hash(user_question: str) -> str:
    normalized = " ".join(user_question.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _json_dumps(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True, indent=2)


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as connection:
        connection.executescript(RUNS_TABLE_SQL)
        connection.executescript(RUNS_QUESTION_HASH_INDEX_SQL)
        connection.executescript(RUN_EVENTS_TABLE_SQL)
        connection.executescript(RUN_EVENTS_SEQUENCE_INDEX_SQL)
        connection.executescript(RUN_EVENTS_PARENT_INDEX_SQL)


def create_run(
    user_question: str,
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    run_id: Optional[str] = None,
    question_hash: Optional[str] = None,
    status: str = "running",
    current_node: Optional[str] = None,
    current_iteration: int = 0,
    graph_version: Optional[str] = None,
) -> str:
    init_db(db_path)

    run_id = run_id or str(uuid.uuid4())
    question_hash = question_hash or _stable_question_hash(user_question)
    timestamp = _utc_now()

    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO runs (
                run_id,
                question_hash,
                user_question,
                status,
                current_node,
                current_iteration,
                graph_version,
                final_output_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                question_hash,
                user_question,
                status,
                current_node,
                current_iteration,
                graph_version,
                None,
                timestamp,
                timestamp,
            ),
        )

    return run_id


def update_run(
    run_id: str,
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    status: Optional[str] = None,
    current_node: Optional[str] = None,
    current_iteration: Optional[int] = None,
    final_output_json: Optional[Any] = None,
) -> None:
    init_db(db_path)

    fields = []
    params = []

    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if current_node is not None:
        fields.append("current_node = ?")
        params.append(current_node)
    if current_iteration is not None:
        fields.append("current_iteration = ?")
        params.append(current_iteration)
    if final_output_json is not None:
        fields.append("final_output_json = ?")
        params.append(_json_dumps(final_output_json))

    if not fields:
        return

    fields.append("updated_at = ?")
    params.append(_utc_now())
    params.append(run_id)

    with get_connection(db_path) as connection:
        connection.execute(
            f"UPDATE runs SET {', '.join(fields)} WHERE run_id = ?",
            params,
        )


def append_event(
    run_id: str,
    node_name: str,
    event_type: str,
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    agent_name: Optional[str] = None,
    parent_event_id: Optional[str] = None,
    iteration: int = 0,
    input_json: Optional[Any] = None,
    output_json: Optional[Any] = None,
    error_json: Optional[Any] = None,
    status: str = "succeeded",
    checkpoint_id: Optional[str] = None,
) -> str:
    init_db(db_path)

    event_id = str(uuid.uuid4())
    timestamp = _utc_now()

    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_sequence FROM run_events WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        sequence_no = int(row["next_sequence"]) if row else 1

        connection.execute(
            """
            INSERT INTO run_events (
                event_id,
                run_id,
                parent_event_id,
                sequence_no,
                node_name,
                agent_name,
                event_type,
                iteration,
                input_json,
                output_json,
                error_json,
                status,
                checkpoint_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                run_id,
                parent_event_id,
                sequence_no,
                node_name,
                agent_name,
                event_type,
                iteration,
                _json_dumps(input_json),
                _json_dumps(output_json),
                _json_dumps(error_json),
                status,
                checkpoint_id,
                timestamp,
            ),
        )

    return event_id


def fetch_run_events(
    run_id: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    init_db(db_path)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM run_events
            WHERE run_id = ?
            ORDER BY sequence_no ASC
            """,
            (run_id,),
        ).fetchall()

    return [dict(row) for row in rows]
