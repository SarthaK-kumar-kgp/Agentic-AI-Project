from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
    get_checkpoint_metadata,
)

from .run_store import DEFAULT_DB_PATH


CHECKPOINTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS graph_checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    checkpoint_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
CREATE INDEX IF NOT EXISTS idx_graph_checkpoints_thread_ns_id
ON graph_checkpoints (thread_id, checkpoint_ns, checkpoint_id);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SqliteCheckpointSaver(BaseCheckpointSaver[str]):
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        super().__init__()
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(CHECKPOINTS_TABLE_SQL)

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = get_checkpoint_id(config)

        with self._connect() as connection:
            if checkpoint_id is not None:
                row = connection.execute(
                    """
                    SELECT *
                    FROM graph_checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT *
                    FROM graph_checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ?
                    ORDER BY checkpoint_id DESC
                    LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                ).fetchone()

        if row is None:
            return None

        checkpoint = json.loads(row["checkpoint_json"])
        metadata = json.loads(row["metadata_json"])
        parent_config = (
            {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": row["parent_checkpoint_id"],
                }
            }
            if row["parent_checkpoint_id"]
            else None
        )

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": row["checkpoint_id"],
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=[],
        )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        if config is None:
            thread_ids = None
            checkpoint_ns = None
        else:
            thread_ids = (config["configurable"]["thread_id"],)
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        before_checkpoint_id = get_checkpoint_id(before) if before else None

        with self._connect() as connection:
            if thread_ids is None:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM graph_checkpoints
                    ORDER BY checkpoint_id DESC
                    """
                ).fetchall()
            else:
                rows = []
                for thread_id in thread_ids:
                    rows.extend(
                        connection.execute(
                            """
                            SELECT *
                            FROM graph_checkpoints
                            WHERE thread_id = ? AND checkpoint_ns = ?
                            ORDER BY checkpoint_id DESC
                            """,
                            (thread_id, checkpoint_ns),
                        ).fetchall()
                    )

        for row in rows:
            if before_checkpoint_id and row["checkpoint_id"] >= before_checkpoint_id:
                continue

            metadata = json.loads(row["metadata_json"])
            if filter and not all(metadata.get(k) == v for k, v in filter.items()):
                continue

            if limit is not None and limit <= 0:
                break
            if limit is not None:
                limit -= 1

            checkpoint = json.loads(row["checkpoint_json"])
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": row["thread_id"],
                        "checkpoint_ns": row["checkpoint_ns"],
                        "checkpoint_id": row["checkpoint_id"],
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=(
                    {
                        "configurable": {
                            "thread_id": row["thread_id"],
                            "checkpoint_ns": row["checkpoint_ns"],
                            "checkpoint_id": row["parent_checkpoint_id"],
                        }
                    }
                    if row["parent_checkpoint_id"]
                    else None
                ),
                pending_writes=[],
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        del new_versions

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")
        checkpoint_id = checkpoint["id"]
        metadata_json = json.dumps(
            get_checkpoint_metadata(config, metadata),
            ensure_ascii=True,
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO graph_checkpoints (
                    thread_id,
                    checkpoint_ns,
                    checkpoint_id,
                    parent_checkpoint_id,
                    checkpoint_json,
                    metadata_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    checkpoint_ns,
                    checkpoint_id,
                    parent_checkpoint_id,
                    json.dumps(checkpoint, ensure_ascii=True),
                    metadata_json,
                    _utc_now(),
                ),
            )

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: list[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        del config, writes, task_id, task_path

    def delete_thread(self, thread_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM graph_checkpoints
                WHERE thread_id = ?
                """,
                (thread_id,),
            )
