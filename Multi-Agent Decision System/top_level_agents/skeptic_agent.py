import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from .prompts import *
load_dotenv()
import json


api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=api_key,base_url="https://api.deepseek.com")

def skeptic_agent(original_question:str,cost_agent:Optional[dict],
                  engineering_agent:Optional[dict],performance_agent:Optional[dict],security_agent:Optional[dict]):
    prompt  = SKEPTIC_AGENT
    payload = {
            "original_question":original_question,
            "cost_agent": cost_agent,
            "engineering_agent":engineering_agent,
            "performance_agent":performance_agent,
            "security_agent":security_agent
        }
    response = client.chat.completions.create(
                model  = "deepseek-v4-flash",
                messages=[
                    {"role":"system","content":prompt},
                    {"role":"user","content":json.dumps(payload)}
                ],
                    temperature=0.2,
                        max_tokens = 1200,
                        extra_body={
                                    "thinking": {"type": "disabled"}
                                }
    )
    return response.choices[0].message.content.strip()
