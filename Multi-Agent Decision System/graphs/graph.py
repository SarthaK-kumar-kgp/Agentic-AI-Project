from langgraph.graph import StateGraph, START, END
from .states import GraphState
from .nodes import *

builder =StateGraph(GraphState)

builder.add_node("enrich_question", enrich_question_node)
builder.add_node("ask_follow_up_questions", ask_follow_up_questions_node)
builder.add_node("planner_node", planner_agent_node)
builder.add_node("router_node", router_agent_node)
builder.add_node("dispatcher_node", dispatcher_agent_node)
builder.add_node("cost_agent_node", cost_agent_node)
builder.add_node("performance_agent_node", performance_agent_node)
builder.add_node("security_agent_node", security_agent_node)
builder.add_node("engineering_agent_node", engineering_agent_node)
builder.add_node("skeptic_agent_node", skeptic_agent_node)
builder.add_node("specialist_review_gate", specialist_review_gate_node)
builder.add_node("feedback_agent_node",feedback_agent_node)
builder.add_node("decision_agent_node",decision_agent_node)


builder.add_edge(START, "enrich_question")
builder.add_edge("enrich_question", "ask_follow_up_questions")
builder.add_edge("ask_follow_up_questions", "planner_node")
builder.add_edge("planner_node", "router_node")
builder.add_edge("router_node", "dispatcher_node")


def route_from_dispatcher(state: GraphState):
    selected_agents = state.get("dispatcher", {}).get("selected_agents", [])
    next_nodes = []

    if "cost_agent" in selected_agents:
        next_nodes.append("cost_agent_node")
    if "engineering_agent" in selected_agents:
        next_nodes.append("engineering_agent_node")
    if "security_agent" in selected_agents:
        next_nodes.append("security_agent_node")
    if "performance_agent" in selected_agents:
        next_nodes.append("performance_agent_node")

    return next_nodes

def route_after_feedback(state: GraphState):
    feedback = state.get("feedback", {})

    if feedback.get("decision") == "rerun":
        selected_agents = feedback.get("agents_to_rerun", [])
        next_nodes = []

        if "cost_agent" in selected_agents:
            next_nodes.append("cost_agent_node")
        if "engineering_agent" in selected_agents:
            next_nodes.append("engineering_agent_node")
        if "security_agent" in selected_agents:
            next_nodes.append("security_agent_node")
        if "performance_agent" in selected_agents:
            next_nodes.append("performance_agent_node")

        return next_nodes

    return "decision_agent_node"

builder.add_conditional_edges("dispatcher_node", route_from_dispatcher)


def route_from_specialist_gate(state: GraphState):
    return bool(state.get("specialist_review_ready", False))


builder.add_edge("cost_agent_node", "specialist_review_gate")
builder.add_edge("performance_agent_node", "specialist_review_gate")
builder.add_edge("security_agent_node", "specialist_review_gate")
builder.add_edge("engineering_agent_node", "specialist_review_gate")
builder.add_conditional_edges(
    "specialist_review_gate",
    route_from_specialist_gate,
    {
        True: "skeptic_agent_node",
        False: END,
    },
)
builder.add_edge("skeptic_agent_node", "feedback_agent_node")
builder.add_conditional_edges("feedback_agent_node", route_after_feedback)
builder.add_edge("decision_agent_node", END)



graph  = builder.compile()
