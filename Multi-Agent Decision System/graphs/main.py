import argparse
import warnings
from pathlib import Path
from typing import Any, Optional

from graphs.graph import graph
from graphs.run_store import DEFAULT_DB_PATH, update_run
from graphs.persistence_fxn import fail_run, fetch_run, resume_run, start_run
from graphs.visualization import render_workflow_graph
from sub_agents.sub_agents import agent_registry

warnings.simplefilter("ignore")
GRAPH_VERSION = "graphs-v1"

def _get_user_question() -> str:
    question = input("Enter your question: ").strip()
    if not question:
        raise ValueError("User question cannot be empty.")
    return question


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str, help="Resume an existing run_id")
    return parser.parse_args()


def _invoke_graph(input_state: Optional[dict[str, Any]], run_id: str):
    try:
        return graph.invoke(
            input_state,
            {"configurable": {"thread_id": run_id}},
            durability="sync",
        )
    except Exception as exc:
        run_row = fetch_run(run_id, db_path=DEFAULT_DB_PATH)
        fail_run(
            run_id,
            db_path=DEFAULT_DB_PATH,
            current_node=run_row["current_node"] if run_row else None,
            current_iteration=run_row["current_iteration"] if run_row else None,
            error_json={
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
        )
        raise


args = _parse_args()

if args.resume:
    run_id = args.resume
    resume_run(
        run_id,
        db_path=DEFAULT_DB_PATH,
        agent_registry=agent_registry,
    )
    result = _invoke_graph(None, run_id)
    update_run(
        run_id,
        db_path=DEFAULT_DB_PATH,
        status="completed",
        current_node="END",
        final_output_json=result,
    )
else:
    user_question = _get_user_question()
    initial_state = start_run(
        user_question,
        db_path=DEFAULT_DB_PATH,
        graph_version=GRAPH_VERSION,
        agent_registry=agent_registry,
    )
    run_id = initial_state["run_id"]
    result = _invoke_graph(initial_state, run_id)
    update_run(
        run_id,
        db_path=DEFAULT_DB_PATH,
        status="completed",
        current_node="END",
        final_output_json=result,
    )

output_path = Path(__file__).with_name("graph.png")
svg_path = Path(__file__).with_name("graph.svg")
dot_path = Path(__file__).with_name("graph.dot")
render_workflow_graph(output_png=output_path, output_dot=dot_path, output_svg=svg_path)

# print(result)
# print(result["planner"])
# print(result["router"])
print(f"Run ID: {run_id}")
print(f"Graph visualization saved to {output_path}")
