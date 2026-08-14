import json

from .states import GraphState
from top_level_agents.qea_agent import *
from top_level_agents.router_agent import *
from top_level_agents.planner_agent import *

def enrich_question_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    enriched_question = enrich_question(user_question)
    enriched_question = json.loads(enriched_question)
    return {
        "question_list": enriched_question["questions"]
    }

def ask_follow_up_questions_node(state: GraphState) -> GraphState:
    question_list = state["question_list"]
    context = ask_follow_up_questions(question_list)
    return {
        "enriched_context": context
    }

def planner_agent_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    context = state["enriched_context"]
    planner_output = planning_agent(user_question, context)
    return {
        "planner": planner_output
    }

def router_agent_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    planner_output = state["planner"]
    agent_registry = state["agent_registry"]
    router_output = routing_agent(user_question, agent_registry, planner_output)
    return {
        "router": router_output
    }
