from langgraph.graph import StateGraph, START, END
from .states import GraphState
from .nodes import *

builder =StateGraph(GraphState)

builder.add_node("enrich_question", enrich_question_node)
builder.add_node("ask_follow_up_questions", ask_follow_up_questions_node)
builder.add_node("planner_node", planner_agent_node)
builder.add_node("router_node", router_agent_node)



builder.add_edge(START, "enrich_question")
builder.add_edge("enrich_question", "ask_follow_up_questions")
builder.add_edge("ask_follow_up_questions", "planner_node")
builder.add_edge("planner_node", "router_node")
builder.add_edge("router_node", END)




graph  = builder.compile()
