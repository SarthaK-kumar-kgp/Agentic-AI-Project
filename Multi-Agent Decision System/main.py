import os
from openai import OpenAI
from dotenv import load_dotenv
from shared.config import DEEPSEEK_BASE_URL
from top_level_agents.prompts import *
from top_level_agents.qea_agent import *
from top_level_agents.planner_agent import *
from top_level_agents.router_agent import *
from top_level_agents.dispatcher import *
from sub_agents.sub_agents import *
from sub_agents.cost_agent import *
from sub_agents.engineering_agent import *
from sub_agents.security_agent import *
from sub_agents.performance_agent import *
import json 
import re
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")


client = OpenAI(
    api_key=api_key,
    base_url=DEEPSEEK_BASE_URL,
)

user_question = input("Enter your question: ")
print("\n--- User Question ---")
print(user_question)

##--Enrichment Step --##
enriched_question = enrich_question(user_question)
enriched_question = json.loads(enriched_question)
question_list = enriched_question["questions"]
enriched_context = ask_follow_up_questions(question_list)

##--Planning -Routing Step --##
planner_output = planning_agent(user_question, enriched_context)
# print(planner_output)
router_output = routing_agent(user_question, agent_registry, planner_output)
print(router_output)

agent_outputs = dispatch_agents(
    router_output,
    cost_agent,
    engineering_agent,
    security_agent,
    performance_agent,
)
print(agent_outputs)
