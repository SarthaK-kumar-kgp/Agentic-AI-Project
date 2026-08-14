from pathlib import Path

from graphs.graph import graph
from sub_agents.sub_agents import agent_registry

initial_state = {
    "user_question": "Should I migrate my database from Neo4j to Ladybug?",
    "agent_registry": agent_registry,
}

result = graph.invoke(initial_state)

output_path = Path(__file__).with_name("graph.png")
graph.get_graph().draw_mermaid_png(output_file_path=str(output_path))

# print(result)
print(result["planner"])
print(result["router"])
print(f"Graph visualization saved to {output_path}")
