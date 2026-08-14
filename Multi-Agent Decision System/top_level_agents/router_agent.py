import os
from openai import OpenAI
from dotenv import load_dotenv
from .prompts import *
load_dotenv()
import json


api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=api_key,base_url="https://api.deepseek.com")

def routing_agent(original_question:str,agent_dictionary:dict,planner_output:dict):
    prompt  = ROUTER_AGENT
    payload = {
        "original_question":original_question,
        "agents": agent_dictionary,
        "planner_output":planner_output
    }
    response = client.chat.completions.create(
                model  = "deepseek-v4-flash",
                messages=[
                    {"role":"system","content":prompt},
                    {"role":"user","content":json.dumps(payload)}
                ],
                 temperature=0.3,
                        max_tokens = 1000,
                        extra_body={
                                    "thinking": {"type": "disabled"}
                                }
    )
    return response.choices[0].message.content.strip()