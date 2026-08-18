from typing import Any, Dict, List, TypedDict


class DispatchPlan(TypedDict):
    selected_agents: List[str]
    agent_routes: Dict[str, List[Dict[str, Any]]]
    routes: List[Dict[str, Any]]

class GraphState(TypedDict):
    user_question: str
    run_id: str
    db_path: str
    current_iteration: int
    question_list: List[str]
    enriched_context: Dict[str, Any]
    planner: Any
    router: Any
    agent_registry: Dict[str, str]
    dispatcher: DispatchPlan
    cost_agent: Dict[str, Any]
    engineering_agent: Dict[str, Any]
    security_agent: Dict[str, Any]
    performance_agent: Dict[str, Any]
    skeptic: Dict[str, Any]
    specialist_review_ready: bool
    feedback: Dict[str,Any]
    retry_round: int
    final_specialist_outputs: Dict[str, Any]
    decision: Dict[str,Any]
