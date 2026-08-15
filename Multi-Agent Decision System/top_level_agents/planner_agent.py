import os
from openai import OpenAI
from dotenv import load_dotenv
from shared.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .prompts import *
import json
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

def planning_agent(original_question:str,context_items:dict):
    prompt = PLANNER_AGENT
    payload = {
        "original_question": original_question,
        "enriched_context": context_items
    }
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content":prompt},
            {"role": "user", "content":json.dumps(payload,indent = 2)}

        ],
        temperature=0.3,
        max_tokens = 1000,
        extra_body={
                    "thinking": {"type": "disabled"}
                }
    )
    return response.choices[0].message.content.strip()
