from __future__ import annotations

import json
from typing import Any

from .run_store import (
    DEFAULT_DB_PATH,
    append_event,
    create_run,
    fetch_run_events,
    get_connection,
    init_db,
    update_run,
)


def _decode_json(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def fetch_run(run_id: str, db_path: str | None = None) -> dict[str, Any] | None:
    db_path = db_path or DEFAULT_DB_PATH
    init_db(db_path)

    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

    return dict(row) if row else None


def load_run_state(
    run_id: str,
    db_path: str | None = None,
    *,
    agent_registry: dict[str, str] | None = None,
) -> dict[str, Any]:
    db_path = db_path or DEFAULT_DB_PATH
    run_row = fetch_run(run_id, db_path=db_path)
    if run_row is None:
        raise ValueError(f"Run not found: {run_id}")

    state: dict[str, Any] = {
        "run_id": run_row["run_id"],
        "db_path": str(db_path),
        "user_question": run_row["user_question"],
        "status": run_row["status"],
        "current_node": run_row["current_node"],
        "current_iteration": run_row["current_iteration"],
        "graph_version": run_row["graph_version"],
        "agent_registry": agent_registry or {},
    }

    for event in fetch_run_events(run_id, db_path=db_path):
        if event.get("event_type") != "output":
            continue
        if event.get("status") != "succeeded":
            continue

        output_json = _decode_json(event.get("output_json"))
        if isinstance(output_json, dict):
            state.update(output_json)

    return state


def start_run(
    user_question: str,
    db_path: str | None = None,
    *,
    graph_version: str | None = None,
    agent_registry: dict[str, str] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    db_path = db_path or DEFAULT_DB_PATH
    run_id = create_run(
        user_question,
        db_path=db_path,
        run_id=run_id,
        graph_version=graph_version,
    )
    return {
        "run_id": run_id,
        "db_path": str(db_path),
        "user_question": user_question,
        "agent_registry": agent_registry or {},
    }


def pause_run(
    run_id: str,
    db_path: str | None = None,
    *,
    current_node: str | None = None,
    current_iteration: int | None = None,
) -> None:
    db_path = db_path or DEFAULT_DB_PATH
    update_run(
        run_id,
        db_path=db_path,
        status="paused",
        current_node=current_node,
        current_iteration=current_iteration,
    )


def resume_run(
    run_id: str,
    db_path: str | None = None,
    *,
    agent_registry: dict[str, str] | None = None,
) -> dict[str, Any]:
    db_path = db_path or DEFAULT_DB_PATH
    update_run(run_id, db_path=db_path, status="running")
    return load_run_state(run_id, db_path=db_path, agent_registry=agent_registry)


def fail_run(
    run_id: str,
    db_path: str | None = None,
    *,
    current_node: str | None = None,
    current_iteration: int | None = None,
    error_json: Any = None,
) -> None:
    db_path = db_path or DEFAULT_DB_PATH
    if current_node is not None or current_iteration is not None:
        update_run(
            run_id,
            db_path=db_path,
            status="failed",
            current_node=current_node,
            current_iteration=current_iteration,
        )
    else:
        update_run(run_id, db_path=db_path, status="failed")

    append_event(
        run_id,
        node_name=current_node or "system",
        event_type="error",
        db_path=db_path,
        error_json=error_json,
        status="failed",
    )
