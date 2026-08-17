import json
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from shared.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, SPECIALIST_MAX_TOKENS
from .prompts import *
from .tools import calculator, parallel_search

load_dotenv()

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=deepseek_api_key,
    base_url=DEEPSEEK_BASE_URL,
)


def _parse_json(content: str) -> Dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def generate_search_plan(sub_question: str, user_question: str) -> Dict[str, Any]:
    prompt = SEARCH_PROMPT_EA
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
    search_plan.setdefault("search_intent", "Find official architecture, implementation, and design source material relevant to the engineering question.")
    search_plan["queries"] = list(search_plan["queries"])[:2]

    while len(search_plan["queries"]) < 2:
        search_plan["queries"].append(f"{sub_question} architecture tradeoffs")

    return search_plan


def analyze_engineering(
    route: Dict[str, Any],
    search_plan: Dict[str, Any],
    search_results: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = ENGINEERING_AGENT
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
        max_tokens=SPECIALIST_MAX_TOKENS,
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
    analysis.setdefault("feasibility", "")
    analysis.setdefault("implementation_effort", "")
    analysis.setdefault("dependencies", [])
    analysis.setdefault("constraints", [])
    analysis.setdefault("evidence", [])
    analysis.setdefault("assumptions", [])
    analysis.setdefault("calculation", "")
    analysis.setdefault("engineering_impact", "")
    analysis.setdefault("confidence", "")
    analysis.setdefault("open_issues", [])

    return analysis


def revise_engineering(
    route: Dict[str, Any],
    original_question: str,
    feedback: Dict[str, Any],
    previous_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = ENGINEERING_AGENT_REVISION
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
        max_tokens=SPECIALIST_MAX_TOKENS,
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
    analysis.setdefault("feasibility", "")
    analysis.setdefault("implementation_effort", "")
    analysis.setdefault("dependencies", [])
    analysis.setdefault("constraints", [])
    analysis.setdefault("evidence", [])
    analysis.setdefault("assumptions", [])
    analysis.setdefault("calculation", "")
    analysis.setdefault("engineering_impact", "")
    analysis.setdefault("confidence", "")
    analysis.setdefault("open_issues", [])

    return analysis


def engineering_agent(
    router_output: Any,
    feedback: Optional[Dict[str, Any]] = None,
    mode: str = "initial",
    previous_output: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if isinstance(router_output, str):
        router_output = _parse_json(router_output)

    if mode == "initial":
        routes: List[Dict[str, Any]] = router_output.get("routes", [])
        engineering_routes: List[Dict[str, Any]] = []

        for route in routes:
            primary_agent = route.get("primary_agent")
            secondary_agents = route.get("secondary_agents", []) or []

            if primary_agent != "engineering_agent" and "engineering_agent" not in secondary_agents:
                continue

            sub_question = route.get("sub_question", "")
            user_question = route.get("user_question", "")

            search_plan = generate_search_plan(sub_question, user_question)
            search_results = parallel_search(
                objective=search_plan["objective"],
                search_queries=search_plan["queries"],
            )
            analysis = analyze_engineering(route, search_plan, search_results)

            engineering_routes.append(
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

        return {"engineering_routes": engineering_routes}

    if mode == "revision":
        original_question = str(feedback.get("original_question", "")).strip()
        revision_items = feedback.get("items", []) or feedback.get("rerun_items", [])
        previous_routes = previous_output.get("engineering_routes", [])

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
            revised_analysis = revise_engineering(route, original_question, item, previous_analysis)

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

        return {"engineering_routes": revised_routes}

    raise ValueError("mode must be either 'initial' or 'revision'")
