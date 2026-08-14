import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from .prompts import *
from .tools import calculator, parallel_search

load_dotenv()

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
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
        model="deepseek-v4-flash",
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
    search_plan.setdefault("search_intent", "Find official pricing and current source material relevant to the cost question.")
    search_plan["queries"] = list(search_plan["queries"])[:3]

    while len(search_plan["queries"]) < 3:
        search_plan["queries"].append(f"{sub_question} pricing")

    return search_plan


def analyze_cost(
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
        model="deepseek-v4-flash",
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
    try:
        analysis = _parse_json(content)
    except Exception:
        analysis = {
            "sub_question": route.get("sub_question", ""),
            "summary": content,
            "vulnerability_patch_posture": "",
            "data_security": "",
            "authentication_access_control": "",
            "encryption": "",
            "api_security": "",
            "network_infrastructure": "",
            "lifecycle_support": "",
            "logging_auditability": "",
            "supply_chain_risk": "",
            "evidence": [],
            "assumptions": [],
            "calculation": "",
            "confidence": "low",
            "open_issues": ["Model output was not valid JSON"],
        }

    if not isinstance(analysis, dict):
        analysis = {
            "sub_question": route.get("sub_question", ""),
            "summary": str(analysis),
            "vulnerability_patch_posture": "",
            "data_security": "",
            "authentication_access_control": "",
            "encryption": "",
            "api_security": "",
            "network_infrastructure": "",
            "lifecycle_support": "",
            "logging_auditability": "",
            "supply_chain_risk": "",
            "evidence": [],
            "assumptions": [],
            "calculation": "",
            "confidence": "low",
            "open_issues": ["Model output was not a JSON object"],
        }

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


def security_agent(router_output: Any) -> Dict[str, Any]:
    if isinstance(router_output, str):
        router_output = _parse_json(router_output)

    if not isinstance(router_output, dict):
        raise ValueError("router_output must be a dict or JSON string")

    routes: List[Dict[str, Any]] = router_output.get("routes", [])
    cost_routes: List[Dict[str, Any]] = []

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
        analysis = analyze_cost(route, search_plan, search_results)

        cost_routes.append(
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

    return {
        "security_routes": cost_routes
    }
