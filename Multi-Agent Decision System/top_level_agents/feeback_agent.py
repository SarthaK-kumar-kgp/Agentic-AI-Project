"""Deterministic feedback router for skeptic-driven reruns."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional

from shared.config import DEFAULT_FEEDBACK_MAX_RETRIES


def _normalize_skeptic_output(skeptic_agent_output: Any) -> Dict[str, Any]:
    if type(skeptic_agent_output) is str:
        return json.loads(skeptic_agent_output)
    if type(skeptic_agent_output) is dict:
        return skeptic_agent_output
    return {}


def _extract_decision(skeptic_agent_output: Dict[str, Any]) -> str:
    decision_block = skeptic_agent_output.get("should_we_stop_or_rerun", {})
    if type(decision_block) is dict:
        decision = str(decision_block.get("decision", "")).strip().lower()
    else:
        decision = str(decision_block).strip().lower()
    if "rerun" in decision:
        return "rerun"
    return "stop"


def _extract_reason(skeptic_agent_output: Dict[str, Any]) -> str:
    decision_block = skeptic_agent_output.get("should_we_stop_or_rerun", {})
    if type(decision_block) is dict:
        return str(decision_block.get("reason", "")).strip()
    return ""


def _extract_rerun_items(skeptic_agent_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_items = skeptic_agent_output.get("which_agent_should_revisit_what", [])
    if type(raw_items) is not list:
        return []

    rerun_items: List[Dict[str, Any]] = []
    for item in raw_items:
        if type(item) is not dict:
            continue
        agent = str(item.get("agent", "")).strip()
        if not agent:
            continue
        rerun_items.append(
            {
                "agent": agent,
                "sub_question_id": str(item.get("sub_question_id", "")).strip(),
                "focus": str(item.get("focus", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    return rerun_items


def feedback_agent(
    original_question: str,
    skeptic_agent_output: Optional[dict],
    *,
    current_retry: int = 0,
    max_retries: int = DEFAULT_FEEDBACK_MAX_RETRIES,
) -> Dict[str, Any]:
    """
    Convert skeptic JSON into deterministic rerun instructions.

    Returns:
    - decision: stop | rerun
    - agents_to_rerun: unique agent names
    - rerun_items: normalized skeptic actions
    - rerun_payloads: grouped instructions per agent
    """

    normalized = _normalize_skeptic_output(skeptic_agent_output)

    decision = _extract_decision(normalized)
    reason = _extract_reason(normalized)
    rerun_items = _extract_rerun_items(normalized)

    if current_retry >= max_retries:
        decision = "stop"
        reason = (
            f"max retries reached ({current_retry}/{max_retries})"
            if not reason
            else f"{reason} | max retries reached ({current_retry}/{max_retries})"
        )

    if decision != "rerun" or not rerun_items:
        return {
            "original_question": original_question,
            "decision": "stop",
            "reason": reason or "skeptic requested no rerun",
            "current_retry": current_retry,
            "max_retries": max_retries,
            "agents_to_rerun": [],
            "rerun_items": [],
            "rerun_payloads": {},
        }

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in rerun_items:
        grouped[item["agent"]].append(item)

    rerun_payloads: Dict[str, Dict[str, Any]] = {}
    for agent_name, items in grouped.items():
        rerun_payloads[agent_name] = {
            "agent": agent_name,
            "original_question": original_question,
            "retry_round": current_retry + 1,
            "max_retries": max_retries,
            "items": items,
        }

    return {
        "original_question": original_question,
        "decision": "rerun",
        "reason": reason or "skeptic requested rerun",
        "current_retry": current_retry,
        "max_retries": max_retries,
        "agents_to_rerun": list(grouped.keys()),
        "rerun_items": rerun_items,
        "rerun_payloads": rerun_payloads,
    }
