import json
from typing import Any, Dict
from shared.config import DEFAULT_FEEDBACK_MAX_RETRIES

from sub_agents.cost_agent import cost_agent
from sub_agents.performance_agent import performance_agent
from sub_agents.security_agent import security_agent
from sub_agents.engineering_agent import engineering_agent

from .states import GraphState
from .run_store import append_event, update_run
from top_level_agents.qea_agent import *
from top_level_agents.router_agent import routing_agent
from top_level_agents.planner_agent import planning_agent
from top_level_agents.dispatcher import dispatch_agents
from top_level_agents.skeptic_agent import skeptic_agent
from top_level_agents.feeback_agent import feedback_agent
from top_level_agents.decision_agent import decision_agent

GRAPH_VERSION = "graphs-v1"


def _start_event(state: GraphState, node_name: str, agent_name: str, input_json):
    run_id = state["run_id"]
    db_path = state["db_path"]
    current_iteration = state.get("current_iteration", state.get("retry_round", 0))
    update_run(
        run_id,
        db_path=db_path,
        current_node=node_name,
        current_iteration=current_iteration,
    )
    return append_event(
        run_id,
        node_name,
        "input",
        db_path=db_path,
        agent_name=agent_name,
        iteration=current_iteration,
        input_json=input_json,
        status="running",
    )


def _finish_event(state: GraphState, node_name: str, agent_name: str, parent_event_id: str, input_json, output_json):
    run_id = state["run_id"]
    db_path = state["db_path"]
    current_iteration = state.get("current_iteration", state.get("retry_round", 0))
    return append_event(
        run_id,
        node_name,
        "output",
        db_path=db_path,
        agent_name=agent_name,
        parent_event_id=parent_event_id,
        iteration=current_iteration,
        input_json=input_json,
        output_json=output_json,
        status="succeeded",
    )


def _agent_selected(state: GraphState, agent_name: str) -> bool:
    dispatcher = state.get("dispatcher")
    if not dispatcher:
        return True
    return agent_name in dispatcher.get("selected_agents", [])


def _specialist_revision_context(state: GraphState, agent_name: str) -> Dict[str, Any]:
    feedback = state.get("feedback", {}) or {}
    if feedback.get("decision") != "rerun":
        return {}
    if agent_name not in feedback.get("agents_to_rerun", []):
        return {}

    previous_outputs = state.get("previous_specialist_outputs", {}) or {}
    previous_output = previous_outputs.get(agent_name)
    if previous_output is None:
        return {}

    return {
        "feedback": feedback,
        "mode": "revision",
        "previous_output": previous_output,
    }


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
    revision_context = _specialist_revision_context(state, "cost_agent")
    cost_agent_output = cost_agent(router_output, **revision_context)
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
    revision_context = _specialist_revision_context(state, "performance_agent")
    performance_agent_output = performance_agent(router_output, **revision_context)
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
    revision_context = _specialist_revision_context(state, "security_agent")
    security_agent_output = security_agent(router_output, **revision_context)
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
    revision_context = _specialist_revision_context(state, "engineering_agent")
    engineering_agent_output = engineering_agent(router_output, **revision_context)
    output_json = {"engineering_agent": engineering_agent_output}
    _finish_event(state, "engineering_analysis_node", "engineering_agent", event_id, input_json, output_json)
    return output_json


def dispatcher_agent_node(state: GraphState) -> GraphState:
    router_output = state["router"]
    input_json = {"router_output": router_output}
    event_id = _start_event(state, "dispatcher_node", "dispatcher_agent", input_json)
    dispatcher_output = dispatch_agents(router_output)
    if not dispatcher_output.get("selected_agents"):
        dispatcher_output["selected_agents"] = [
            "cost_agent",
            "engineering_agent",
            "security_agent",
            "performance_agent",
        ]
    output_json = {"dispatcher": dispatcher_output}
    _finish_event(state, "dispatcher_node", "dispatcher_agent", event_id, input_json, output_json)
    return output_json


def skeptic_agent_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    cost_agent_output = state["cost_agent"]
    performance_agent_output = state["performance_agent"]
    security_agent_output = state["security_agent"]
    engineering_agent_output = state["engineering_agent"]
    input_json = {"user_question": user_question,
                  "cost_agent_output":cost_agent_output,
                  "performance_agent_output":performance_agent_output,
                  "security_agent_output":security_agent_output,
                  "engineering_agent_output":engineering_agent_output
                  }
    event_id = _start_event(state, "skeptic_node", "skeptic_agent", input_json)
    output_json = {"skeptic": skeptic_agent(user_question,
                                            cost_agent_output,
                                            engineering_agent_output,
                                            performance_agent_output,
                                            security_agent_output
                                            )}
    _finish_event(state, "skeptic_node", "skeptic_agent", event_id, input_json, output_json)
    return output_json


def specialist_review_gate_node(state: GraphState) -> GraphState:
    dispatcher = state.get("dispatcher", {})
    feedback = state.get("feedback", {})
    target_agents = feedback.get("agents_to_rerun") or dispatcher.get("selected_agents", [])
    present_agents = [agent for agent in target_agents if state.get(agent) is not None]

    input_json = {
        "target_agents": target_agents,
        "present_agents": present_agents,
    }
    event_id = _start_event(state, "specialist_review_gate", "system", input_json)
    ready = (
        bool(target_agents)
        and len(present_agents) == len(target_agents)
        and not state.get("specialist_review_ready", False)
    )
    output_json = {"specialist_review_ready": ready}
    _finish_event(state, "specialist_review_gate", "system", event_id, input_json, output_json)
    return output_json

def feedback_agent_node(state:GraphState)->GraphState:
    skeptic_output = state['skeptic']
    user_question = state['user_question']
    retry_round = state.get('retry_round', 0)
    allowed_agents = state.get("dispatcher", {}).get("selected_agents", [])
    input_json =  {
        "user_question": user_question,
        "skeptic_output": skeptic_output,
        "retry_count": retry_round,
    }
    event_id = _start_event(state, "feedback_agent", "system", input_json)
    feedback_output = feedback_agent(
        user_question,
        skeptic_output,
        current_retry=retry_round,
        max_retries=DEFAULT_FEEDBACK_MAX_RETRIES,
    )
    requested_rerun_agents = feedback_output.get("agents_to_rerun", [])
    rerun_agents = [agent_name for agent_name in requested_rerun_agents if agent_name in allowed_agents]

    if feedback_output.get("decision") == "rerun" and not rerun_agents:
        feedback_output["decision"] = "stop"
        feedback_output["reason"] = (
            "rerun request filtered out because no originally selected specialist matched"
        )

    feedback_output["agents_to_rerun"] = rerun_agents
    previous_specialist_outputs = {
        agent_name: state.get(agent_name)
        for agent_name in rerun_agents
        if state.get(agent_name) is not None
    }
    output_json = {
        "feedback": feedback_output,
        "retry_round": retry_round + (1 if feedback_output.get("decision") == "rerun" else 0),
        "current_iteration": retry_round + (1 if feedback_output.get("decision") == "rerun" else 0),
        "specialist_review_ready": False,
        "previous_specialist_outputs": previous_specialist_outputs,
    }
    for agent_name in rerun_agents:
        output_json[agent_name] = None
    _finish_event(state, "feedback_agent", "system", event_id, input_json, output_json)
    return output_json


def _collect_final_specialist_outputs(state: GraphState) -> Dict[str, Any]:
    final_specialist_outputs = {
        "cost_agent": state.get("cost_agent"),
        "engineering_agent": state.get("engineering_agent"),
        "security_agent": state.get("security_agent"),
        "performance_agent": state.get("performance_agent"),
    }
    return {
        agent_name: output
        for agent_name, output in final_specialist_outputs.items()
        if output is not None
    }


def decision_agent_node(state: GraphState) -> GraphState:
    user_question = state["user_question"]
    final_specialist_outputs = _collect_final_specialist_outputs(state)
    input_json = {
        "user_question": user_question,
        "final_specialist_outputs": final_specialist_outputs,
    }
    event_id = _start_event(state, "decision_node", "decision_agent", input_json)
    decision_output = decision_agent(user_question, final_specialist_outputs)
    output_json = {
        "final_specialist_outputs": final_specialist_outputs,
        "decision": decision_output,
    }
    _finish_event(state, "decision_node", "decision_agent", event_id, input_json, output_json)
    return output_json
