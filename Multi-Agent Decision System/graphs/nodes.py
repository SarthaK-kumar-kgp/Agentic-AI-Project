import json

from sub_agents.cost_agent import cost_agent
from sub_agents.performance_agent import performance_agent
from sub_agents.security_agent import security_agent
from sub_agents.engineering_agent import engineering_agent

from .states import GraphState
from .run_store import append_event, update_run
from top_level_agents.qea_agent import *
from top_level_agents.router_agent import *
from top_level_agents.planner_agent import *
from top_level_agents.dispatcher import dispatch_agents


GRAPH_VERSION = "graphs-v1"


def _start_event(state: GraphState, node_name: str, agent_name: str, input_json):
    run_id = state["run_id"]
    db_path = state["db_path"]
    update_run(run_id, db_path=db_path, current_node=node_name, current_iteration=0)
    return append_event(
        run_id,
        node_name,
        "input",
        db_path=db_path,
        agent_name=agent_name,
        input_json=input_json,
        status="running",
    )


def _finish_event(state: GraphState, node_name: str, agent_name: str, parent_event_id: str, input_json, output_json):
    run_id = state["run_id"]
    db_path = state["db_path"]
    return append_event(
        run_id,
        node_name,
        "output",
        db_path=db_path,
        agent_name=agent_name,
        parent_event_id=parent_event_id,
        input_json=input_json,
        output_json=output_json,
        status="succeeded",
    )


def _agent_selected(state: GraphState, agent_name: str) -> bool:
    dispatcher = state.get("dispatcher")
    if not dispatcher:
        return True
    return agent_name in dispatcher.get("selected_agents", [])


def enrich_question_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    input_json = {"user_question": user_question}
    event_id = _start_event(state, "enrich_question", "qea_agent", input_json)
    enriched_question = enrich_question(user_question)
    enriched_question = json.loads(enriched_question)
    output_json = {"question_list": enriched_question["questions"]}
    _finish_event(state, "enrich_question", "qea_agent", event_id, input_json, output_json)
    return output_json

def ask_follow_up_questions_node(state: GraphState) -> GraphState:
    question_list = state["question_list"]
    input_json = {"question_list": question_list}
    event_id = _start_event(state, "ask_follow_up_questions", "qea_agent", input_json)
    context = ask_follow_up_questions(question_list)
    output_json = {"enriched_context": context}
    _finish_event(state, "ask_follow_up_questions", "qea_agent", event_id, input_json, output_json)
    return output_json

def planner_agent_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    context = state["enriched_context"]
    input_json = {"user_question": user_question, "enriched_context": context}
    event_id = _start_event(state, "planner_node", "planner_agent", input_json)
    planner_output = planning_agent(user_question, context)
    output_json = {"planner": planner_output}
    _finish_event(state, "planner_node", "planner_agent", event_id, input_json, output_json)
    return output_json

def router_agent_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    planner_output = state["planner"]
    agent_registry = state["agent_registry"]
    input_json = {
        "user_question": user_question,
        "planner_output": planner_output,
        "agent_registry": agent_registry,
    }
    event_id = _start_event(state, "router_node", "router_agent", input_json)
    router_output = routing_agent(user_question, agent_registry, planner_output)
    output_json = {"router": router_output}
    _finish_event(state, "router_node", "router_agent", event_id, input_json, output_json)
    return output_json

def cost_agent_node(state:GraphState) -> GraphState:
    router_output = state["router"]
    input_json = {
        "router_output": router_output,

    }
    event_id = _start_event(state, "cost_analysis_node", "cost_agent", input_json)
    if not _agent_selected(state, "cost_agent"):
        output_json = {"cost_agent": {"cost_routes": []}}
        _finish_event(state, "cost_analysis_node", "cost_agent", event_id, input_json, output_json)
        return output_json
    cost_agent_output = cost_agent(router_output)
    output_json = {"cost_agent": cost_agent_output}
    _finish_event(state, "cost_analysis_node", "cost_agent", event_id, input_json, output_json)
    return output_json

def performance_agent_node(state:GraphState) -> GraphState:
    router_output = state["router"]
    input_json = {
        "router_output": router_output,

    }
    event_id = _start_event(state, "performance_analysis_node", "performance_agent", input_json)
    if not _agent_selected(state, "performance_agent"):
        output_json = {"performance_agent": {"performance_routes": []}}
        _finish_event(state, "performance_analysis_node", "performance_agent", event_id, input_json, output_json)
        return output_json
    performance_agent_output = performance_agent(router_output)
    output_json = {"performance_agent": performance_agent_output}
    _finish_event(state, "performance_analysis_node", "performance_agent", event_id, input_json, output_json)
    return output_json

def security_agent_node(state:GraphState) -> GraphState:
    router_output = state["router"]
    input_json = {
        "router_output": router_output,

    }
    event_id = _start_event(state, "security_analysis_node", "security_agent", input_json)
    if not _agent_selected(state, "security_agent"):
        output_json = {"security_agent": {"security_routes": []}}
        _finish_event(state, "security_analysis_node", "security_agent", event_id, input_json, output_json)
        return output_json
    security_agent_output = security_agent(router_output)
    output_json = {"security_agent": security_agent_output}
    _finish_event(state, "security_analysis_node", "security_agent", event_id, input_json, output_json)
    return output_json

def engineering_agent_node(state:GraphState) -> GraphState:
    router_output = state["router"]
    input_json = {
        "router_output": router_output,

    }
    event_id = _start_event(state, "engineering_analysis_node", "engineering_agent", input_json)
    if not _agent_selected(state, "engineering_agent"):
        output_json = {"engineering_agent": {"engineering_routes": []}}
        _finish_event(state, "engineering_analysis_node", "engineering_agent", event_id, input_json, output_json)
        return output_json
    engineering_agent_output = engineering_agent(router_output)
    output_json = {"engineering_agent": engineering_agent_output}
    _finish_event(state, "engineering_analysis_node", "engineering_agent", event_id, input_json, output_json)
    return output_json


def dispatcher_agent_node(state: GraphState) -> GraphState:
    router_output = state["router"]
    input_json = {"router_output": router_output}
    event_id = _start_event(state, "dispatcher_node", "dispatcher_agent", input_json)
    output_json = {"dispatcher": dispatch_agents(router_output)}
    _finish_event(state, "dispatcher_node", "dispatcher_agent", event_id, input_json, output_json)
    return output_json
