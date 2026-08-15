import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from shared.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .prompts import *
from .tools import calculator, parallel_search

load_dotenv()

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=deepseek_api_key,
    base_url=DEEPSEEK_BASE_URL,
)


def _parse_json(content: str) -> Dict[str, Any]:
    return json.loads(content)


def generate_search_plan(sub_question: str, user_question: str) -> Dict[str, Any]:
    prompt = SEARCH_PROMPT_SA
    payload = {
        "user_question": user_question,
        "sub_question": sub_question,
    }

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
        temperature=0.2,
        max_tokens=500,
        extra_body={
            "thinking": {"type": "disabled"}
        },
    )

    content = response.choices[0].message.content.strip()
    search_plan = _parse_json(content)


    search_plan.setdefault("objective", sub_question or user_question)
    search_plan.setdefault("search_intent", "Find official security, compliance, and threat-model source material relevant to the security question.")
    search_plan["queries"] = list(search_plan["queries"])[:3]

    while len(search_plan["queries"]) < 3:
        search_plan["queries"].append(f"{sub_question} security best practices")

    return search_plan


def analyze_security(
    route: Dict[str, Any],
    search_plan: Dict[str, Any],
    search_results: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = SECURITY_AGENT
    payload = {
        "user_question": route.get("user_question", ""),
        "sub_question": route.get("sub_question", ""),
        "search_plan": search_plan,
        "search_results": search_results,
    }

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
        temperature=0.2,
        max_tokens=2000,
        extra_body={
            "thinking": {"type": "disabled"}
        },
    )

    content = response.choices[0].message.content.strip()
    analysis = _parse_json(content)

    calculation_expression = str(analysis.get("calculation", "")).strip()
    if calculation_expression and re.search(r"[0-9]", calculation_expression):
        calculation_result = calculator.invoke({"expression": calculation_expression})
        analysis["calculation_result"] = calculation_result

    analysis.setdefault("sub_question", route.get("sub_question", ""))
    analysis.setdefault("summary", "")
    analysis.setdefault("vulnerability_patch_posture", "")
    analysis.setdefault("data_security", "")
    analysis.setdefault("authentication_access_control", "")
    analysis.setdefault("encryption", "")
    analysis.setdefault("api_security", "")
    analysis.setdefault("network_infrastructure", "")
    analysis.setdefault("lifecycle_support", "")
    analysis.setdefault("logging_auditability", "")
    analysis.setdefault("supply_chain_risk", "")
    analysis.setdefault("evidence", [])
    analysis.setdefault("assumptions", [])
    analysis.setdefault("calculation", "")
    analysis.setdefault("confidence", "")
    analysis.setdefault("open_issues", [])

    return analysis


def revise_security(
    route: Dict[str, Any],
    original_question: str,
    feedback: Dict[str, Any],
    previous_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = SECURITY_AGENT_REVISION
    payload = {
        "original_question": original_question,
        "route": route,
        "feedback": feedback,
        "previous_output": previous_analysis,
    }

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
        temperature=0.2,
        max_tokens=2000,
        extra_body={
            "thinking": {"type": "disabled"}
        },
    )

    content = response.choices[0].message.content.strip()
    analysis = _parse_json(content)

    calculation_expression = str(analysis.get("calculation", "")).strip()
    if calculation_expression and re.search(r"[0-9]", calculation_expression):
        calculation_result = calculator.invoke({"expression": calculation_expression})
        analysis["calculation_result"] = calculation_result

    analysis.setdefault("sub_question", route.get("sub_question", ""))
    analysis.setdefault("summary", "")
    analysis.setdefault("vulnerability_patch_posture", "")
    analysis.setdefault("data_security", "")
    analysis.setdefault("authentication_access_control", "")
    analysis.setdefault("encryption", "")
    analysis.setdefault("api_security", "")
    analysis.setdefault("network_infrastructure", "")
    analysis.setdefault("lifecycle_support", "")
    analysis.setdefault("logging_auditability", "")
    analysis.setdefault("supply_chain_risk", "")
    analysis.setdefault("evidence", [])
    analysis.setdefault("assumptions", [])
    analysis.setdefault("calculation", "")
    analysis.setdefault("confidence", "")
    analysis.setdefault("open_issues", [])

    return analysis


def security_agent(
    router_output: Any,
    feedback: Dict[str, Any] = None,
    mode: str = "initial",
    previous_output: Dict[str, Any] = None,
) -> Dict[str, Any]:
    if isinstance(router_output, str):
        router_output = _parse_json(router_output)

    if mode == "initial":
        routes: List[Dict[str, Any]] = router_output.get("routes", [])
        security_routes: List[Dict[str, Any]] = []

        for route in routes:
            primary_agent = route.get("primary_agent")
            secondary_agents = route.get("secondary_agents", []) or []

            if primary_agent != "security_agent" and "security_agent" not in secondary_agents:
                continue

            sub_question = route.get("sub_question", "")
            user_question = route.get("user_question", "")

            search_plan = generate_search_plan(sub_question, user_question)
            search_results = parallel_search(
                objective=search_plan["objective"],
                search_queries=search_plan["queries"],
            )
            analysis = analyze_security(route, search_plan, search_results)

            security_routes.append(
                {
                    "id": route.get("id"),
                    "sub_question": sub_question,
                    "primary_agent": primary_agent,
                    "secondary_agents": secondary_agents,
                    "search_plan": search_plan,
                    "search_results": search_results,
                    "analysis": analysis,
                }
            )

        return {"security_routes": security_routes}

    original_question = str(feedback.get("original_question", "")).strip()
    revision_items = feedback.get("items", []) or feedback.get("rerun_items", [])
    previous_routes = previous_output.get("security_routes", [])

    revised_routes: List[Dict[str, Any]] = []
    previous_route_map = {str(route.get("id", "")): route for route in previous_routes}

    for item in revision_items:
        route_id = str(item.get("sub_question_id", "")).strip()
        previous_route = previous_route_map.get(route_id)
        if not previous_route:
            continue

        previous_analysis = previous_route.get("analysis", {})
        route = {
            "id": previous_route.get("id"),
            "sub_question": previous_route.get("sub_question", ""),
            "primary_agent": previous_route.get("primary_agent", ""),
            "secondary_agents": previous_route.get("secondary_agents", []) or [],
        }
        revised_analysis = revise_security(route, original_question, item, previous_analysis)

        revised_routes.append(
            {
                "id": previous_route.get("id"),
                "sub_question": previous_route.get("sub_question", ""),
                "primary_agent": previous_route.get("primary_agent", ""),
                "secondary_agents": previous_route.get("secondary_agents", []) or [],
                "feedback": item,
                "previous_analysis": previous_analysis,
                "analysis": revised_analysis,
            }
        )

    return {"security_routes": revised_routes}
