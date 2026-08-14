from typing import Any, Dict, List, TypedDict

class GraphState(TypedDict):
    user_question: str
    question_list: List[str]
    enriched_context: Dict[str, Any]
    planner: Any
    router: Any
    agent_registry: Dict[str, str]
