import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

from shared.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .prompts import DECISION_AGENT

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def _parse_json(content: str) -> Dict[str, Any]:
    return json.loads(content)


def _normalize_output(output: Dict[str, Any]) -> Dict[str, Any]:
    output.setdefault("final_recommendation", "")
    output.setdefault("confidence", "")
    output.setdefault("key_evidence", [])
    output.setdefault("open_issues", [])
    output.setdefault("risk_notes", [])
    output.setdefault("short_report", "")
    return output


def decision_agent(
    user_question: str,
    final_specialist_outputs: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = DECISION_AGENT
    payload = {
        "user_question": user_question,
        "final_specialist_outputs": final_specialist_outputs,
    }

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
        temperature=0.2,
        max_tokens=1200,
        extra_body={
            "thinking": {"type": "disabled"}
        },
    )

    content = response.choices[0].message.content.strip()
    output = _parse_json(content)
    return _normalize_output(output)
