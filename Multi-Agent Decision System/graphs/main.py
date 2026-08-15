from pathlib import Path
import sys

from graphs.graph import graph
from graphs.run_store import DEFAULT_DB_PATH, create_run, update_run
from sub_agents.sub_agents import agent_registry
import warnings
warnings.simplefilter("ignore")
GRAPH_VERSION = "graphs-v1"

def _get_user_question() -> str:
    question = input("Enter your question: ").strip()
    if not question:
        raise ValueError("User question cannot be empty.")
    return question


user_question = _get_user_question()
run_id = create_run(user_question, db_path=DEFAULT_DB_PATH, graph_version=GRAPH_VERSION)

initial_state = {
    "user_question": user_question,
    "run_id": run_id,
    "db_path": str(DEFAULT_DB_PATH),
    "agent_registry": agent_registry,
}

result = graph.invoke(initial_state)
update_run(
    run_id,
    db_path=DEFAULT_DB_PATH,
    status="completed",
    current_node="END",
    final_output_json=result,
)

output_path = Path(__file__).with_name("graph.png")
graph.get_graph().draw_mermaid_png(output_file_path=str(output_path))

# print(result)
# print(result["planner"])
# print(result["router"])
print(f"Run ID: {run_id}")
print(f"Graph visualization saved to {output_path}")
