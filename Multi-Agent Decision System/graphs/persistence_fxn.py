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
from .nodes import (
    ask_follow_up_questions_node,
    cost_agent_node,
    decision_agent_node,
    dispatcher_agent_node,
    engineering_agent_node,
    enrich_question_node,
    feedback_agent_node,
    planner_agent_node,
    performance_agent_node,
    router_agent_node,
    security_agent_node,
    skeptic_agent_node,
    specialist_review_gate_node,
)


_AGENT_TO_NODE = {
    "cost_agent": "cost_agent_node",
    "engineering_agent": "engineering_agent_node",
    "security_agent": "security_agent_node",
    "performance_agent": "performance_agent_node",
}

_NODE_TO_EVENT_NAME = {
    "enrich_question_node": "enrich_question",
    "ask_follow_up_questions_node": "ask_follow_up_questions",
    "planner_agent_node": "planner_node",
    "router_agent_node": "router_node",
    "dispatcher_agent_node": "dispatcher_node",
    "cost_agent_node": "cost_analysis_node",
    "performance_agent_node": "performance_analysis_node",
    "security_agent_node": "security_analysis_node",
    "engineering_agent_node": "engineering_analysis_node",
    "specialist_review_gate_node": "specialist_review_gate",
    "skeptic_agent_node": "skeptic_node",
    "feedback_agent_node": "feedback_agent",
    "decision_agent_node": "decision_node",
}

_NODE_ALIASES = {
    "cost_analysis_node": "cost_agent_node",
    "performance_analysis_node": "performance_agent_node",
    "security_analysis_node": "security_agent_node",
    "engineering_analysis_node": "engineering_agent_node",
}

_NODE_EXECUTORS = {
    "enrich_question_node": enrich_question_node,
    "ask_follow_up_questions_node": ask_follow_up_questions_node,
    "planner_agent_node": planner_agent_node,
    "router_agent_node": router_agent_node,
    "dispatcher_agent_node": dispatcher_agent_node,
    "cost_agent_node": cost_agent_node,
    "performance_agent_node": performance_agent_node,
    "security_agent_node": security_agent_node,
    "engineering_agent_node": engineering_agent_node,
    "specialist_review_gate_node": specialist_review_gate_node,
    "skeptic_agent_node": skeptic_agent_node,
    "feedback_agent_node": feedback_agent_node,
    "decision_agent_node": decision_agent_node,
}


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
        "current_iteration": 0,
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
        iteration=current_iteration or 0,
        status="failed",
    )


def _selected_specialist_nodes(selected_agents: list[str] | None) -> list[str]:
    if not selected_agents:
        return []
    return [
        _AGENT_TO_NODE[agent]
        for agent in selected_agents
        if agent in _AGENT_TO_NODE
    ]


def route_from_dispatcher(state: dict[str, Any]) -> list[str]:
    selected_agents = state.get("dispatcher", {}).get("selected_agents", [])
    return _selected_specialist_nodes(selected_agents)


def route_after_feedback(state: dict[str, Any]) -> str | list[str]:
    feedback = state.get("feedback", {})
    if feedback.get("decision") == "rerun":
        selected_agents = feedback.get("agents_to_rerun", [])
        return _selected_specialist_nodes(selected_agents) or "decision_agent_node"
    return "decision_agent_node"


def route_from_specialist_gate(state: dict[str, Any]) -> bool:
    return bool(state.get("specialist_review_ready", False))


def _canonical_node_name(node_name: str | None) -> str | None:
    if node_name is None:
        return None
    return _NODE_ALIASES.get(node_name, node_name)


def get_next_node(
    state: dict[str, Any],
    *,
    run_row: dict[str, Any] | None = None,
    last_event: dict[str, Any] | None = None,
) -> str | list[str]:
    if run_row and run_row.get("status") == "completed":
        return "END"

    current_node = _canonical_node_name(
        (last_event or {}).get("node_name") or (run_row or {}).get("current_node")
    )
    if not current_node:
        return "enrich_question"

    if current_node == "enrich_question":
        return "ask_follow_up_questions"
    if current_node == "ask_follow_up_questions":
        return "planner_node"
    if current_node == "planner_node":
        return "router_node"
    if current_node == "router_node":
        return "dispatcher_node"
    if current_node == "dispatcher_node":
        return route_from_dispatcher(state)
    if current_node in _AGENT_TO_NODE.values():
        return "specialist_review_gate"
    if current_node == "specialist_review_gate":
        return "skeptic_agent_node" if route_from_specialist_gate(state) else "END"
    if current_node == "skeptic_node":
        return "feedback_agent_node"
    if current_node == "feedback_agent":
        return route_after_feedback(state)
    if current_node == "decision_node":
        return "END"

    return "enrich_question"


def _latest_successful_output_event(
    run_id: str,
    db_path: str | None = None,
) -> dict[str, Any] | None:
    db_path = db_path or DEFAULT_DB_PATH
    for event in reversed(fetch_run_events(run_id, db_path=db_path)):
        if event.get("event_type") == "output" and event.get("status") == "succeeded":
            return event
    return None


def _run_node_step(state: dict[str, Any], node_name: str) -> None:
    output = _NODE_EXECUTORS[node_name](state)
    if isinstance(output, dict):
        state.update(output)


def resume_run_to_completion(
    run_id: str,
    db_path: str | None = None,
    *,
    agent_registry: dict[str, str] | None = None,
) -> dict[str, Any]:
    db_path = db_path or DEFAULT_DB_PATH
    state = resume_run(run_id, db_path=db_path, agent_registry=agent_registry)
    last_event = _latest_successful_output_event(run_id, db_path=db_path)
    if last_event:
        last_event["node_name"] = _canonical_node_name(last_event.get("node_name"))
    next_node = get_next_node(
        state,
        run_row=fetch_run(run_id, db_path=db_path),
        last_event=last_event,
    )

    while next_node != "END":
        if isinstance(next_node, list):
            for node_name in next_node:
                _run_node_step(state, node_name)
            next_node = "specialist_review_gate_node"
            continue

        _run_node_step(state, next_node)
        last_event = {"node_name": _canonical_node_name(_NODE_TO_EVENT_NAME[next_node])}
        next_node = get_next_node(
            state,
            run_row=fetch_run(run_id, db_path=db_path),
            last_event=last_event,
        )

    state["status"] = "completed"
    update_run(
        run_id,
        db_path=db_path,
        status="completed",
        current_node="END",
        final_output_json=state,
    )
    return state
